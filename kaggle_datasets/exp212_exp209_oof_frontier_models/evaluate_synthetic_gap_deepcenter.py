"""Evaluate attributed QRZ synthetic gap recovery with a source-trained DeepCenter gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment

from evaluate_coordinate_consensus import registered_links
from evaluate_observed_gap_close import _frame_spacing
from train_deepcenter_explicit_split import (
    DeepCenterUNet3D,
    block_mean_xy,
    normalize_dynamic_range,
    read_frame,
    read_zarr_meta,
)


GAP_CLOSE_UM = 5.0
GAP_CLOSE_REUSE_UM = 3.2
GAP_DENSITY_REFERENCE_UM = 6.5
GAP_DENSITY_GAIN = 0.040
GAP_DENSITY_MAX_STEP_DELTA_UM = 0.125
GAP_CLOSE_MAX_ADDED_FRAC = 0.05
GAP_CLOSE_MAX_ADDED_ABS = 2000
GAP_REFINE_WIN_Z = 1
GAP_REFINE_WIN_YX = 3
GAP_REFINE_MAX_SHIFT_UM = 3.2
DEEPCENTER_THRESHOLD = 0.25
DEEPCENTER_CONFIRM_MIN_SPAN_UM = 8.5
DEEPCENTER_SCORE_WIN_Z = 1
DEEPCENTER_SCORE_WIN_YX = 2
FRAME_CACHE_LIMIT = 8


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_bundle(path: Path, expected_sha256: str) -> dict[str, object]:
    actual = sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"DeepCenter SHA mismatch: expected {expected_sha256}, got {actual}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if int(checkpoint.get("epoch", -1)) != 2:
        raise ValueError("EXP181 requires the frozen EXP180 epoch-2 checkpoint")
    cfg = SimpleNamespace(**checkpoint["config"])
    model = DeepCenterUNet3D(base_channels=int(cfg.base_channels))
    model.load_state_dict(checkpoint["model_state"])
    model.to(device).eval()
    return {"model": model, "cfg": cfg, "device": device, "sha256": actual}


def _trim(cache: dict[int, np.ndarray]) -> None:
    while len(cache) > FRAME_CACHE_LIMIT:
        cache.pop(next(iter(cache)))


def get_frame(
    zarr_path: Path,
    t: int,
    shape: tuple[int, ...],
    dtype: np.dtype,
    cache: dict[int, np.ndarray],
) -> np.ndarray:
    if t not in cache:
        cache[t] = read_frame(zarr_path, t, shape, dtype)
        _trim(cache)
    return cache[t]


def refine_midpoint(
    midpoint_voxel: np.ndarray,
    frame: np.ndarray,
    scale: np.ndarray,
) -> tuple[np.ndarray, str]:
    z, y, x = [int(round(float(value))) for value in midpoint_voxel]
    z0, z1 = max(0, z - GAP_REFINE_WIN_Z), min(frame.shape[0], z + GAP_REFINE_WIN_Z + 1)
    y0, y1 = max(0, y - GAP_REFINE_WIN_YX), min(frame.shape[1], y + GAP_REFINE_WIN_YX + 1)
    x0, x1 = max(0, x - GAP_REFINE_WIN_YX), min(frame.shape[2], x + GAP_REFINE_WIN_YX + 1)
    patch = frame[z0:z1, y0:y1, x0:x1].astype(np.float64)
    if not patch.size:
        return midpoint_voxel, "empty"
    weights = np.maximum(patch - float(np.percentile(patch, 20.0)), 0.0)
    total = float(weights.sum())
    if total <= 0.0:
        return midpoint_voxel, "zero_weight"
    zz = np.arange(z0, z1, dtype=np.float64)[:, None, None]
    yy = np.arange(y0, y1, dtype=np.float64)[None, :, None]
    xx = np.arange(x0, x1, dtype=np.float64)[None, None, :]
    refined = np.array([
        float((weights * zz).sum() / total),
        float((weights * yy).sum() / total),
        float((weights * xx).sum() / total),
    ])
    if float(np.linalg.norm((refined - midpoint_voxel) * scale)) > GAP_REFINE_MAX_SHIFT_UM:
        return midpoint_voxel, "shift_rejected"
    return refined, "refined"


@torch.no_grad()
def deepcenter_heatmap(
    frame: np.ndarray,
    bundle: dict[str, object],
) -> np.ndarray:
    cfg = bundle["cfg"]
    pooled = block_mean_xy(frame, int(cfg.pool_factor))
    image = normalize_dynamic_range(
        pooled,
        float(cfg.norm_lo_pct),
        float(cfg.norm_hi_pct),
        float(cfg.norm_clip_lo),
        float(cfg.norm_clip_hi),
    )
    tensor = torch.from_numpy(image[None, None]).to(
        device=bundle["device"], dtype=torch.float32
    )
    return torch.sigmoid(bundle["model"](tensor))[0, 0].detach().cpu().numpy()


def deepcenter_score(
    point_voxel: np.ndarray,
    heatmap: np.ndarray,
    pool_factor: int,
) -> float:
    factor = max(1, int(pool_factor))
    z = int(round(float(point_voxel[0])))
    y = int(round(float(point_voxel[1]) / factor))
    x = int(round(float(point_voxel[2]) / factor))
    z0, z1 = max(0, z - DEEPCENTER_SCORE_WIN_Z), min(heatmap.shape[0], z + DEEPCENTER_SCORE_WIN_Z + 1)
    y0, y1 = max(0, y - DEEPCENTER_SCORE_WIN_YX), min(heatmap.shape[1], y + DEEPCENTER_SCORE_WIN_YX + 1)
    x0, x1 = max(0, x - DEEPCENTER_SCORE_WIN_YX), min(heatmap.shape[2], x + DEEPCENTER_SCORE_WIN_YX + 1)
    if z0 >= z1 or y0 >= y1 or x0 >= x1:
        return float("-inf")
    return float(np.max(heatmap[z0:z1, y0:y1, x0:x1]))


def close_synthetic_gaps(
    coords: np.ndarray,
    edges: list[tuple[int, int, float, float]],
    scale: np.ndarray,
    zarr_path: Path,
    bundle: dict[str, object] | None,
    *,
    gap_close_um: float = GAP_CLOSE_UM,
    deepcenter_threshold: float = DEEPCENTER_THRESHOLD,
    deepcenter_confirm_min_span_um: float = DEEPCENTER_CONFIRM_MIN_SPAN_UM,
    synthetic_max_fraction: float = GAP_CLOSE_MAX_ADDED_FRAC,
    heatmap_cache_dir: Path | None = None,
) -> tuple[np.ndarray, list[tuple[int, int, float, float]], dict[str, object]]:
    use_veto = bundle is not None
    outgoing = {int(edge[0]) for edge in edges}
    incoming = {int(edge[1]) for edge in edges}
    incident = outgoing | incoming
    by_time: dict[int, list[int]] = defaultdict(list)
    for node_id, row in enumerate(coords):
        by_time[int(row[0])].append(node_id)
    ends = {t: [node for node in ids if node not in outgoing] for t, ids in by_time.items()}
    starts = {t: [node for node in ids if node not in incoming] for t, ids in by_time.items()}
    isolated = {t: [node for node in ids if node not in incident] for t, ids in by_time.items()}
    position_um = coords[:, 1:4] * scale
    spacing = {t: _frame_spacing(position_um, ids) for t, ids in by_time.items()}
    shape, dtype = read_zarr_meta(zarr_path)
    frame_cache: dict[int, np.ndarray] = {}
    heatmap_cache: dict[int, np.ndarray] = {}
    used_starts: set[int] = set()
    used_middle: set[int] = set()
    added_edges: list[tuple[int, int, float, float]] = []
    added_rows: list[list[float]] = []
    max_synthetic = min(
        GAP_CLOSE_MAX_ADDED_ABS,
        max(1, int(round(len(coords) * synthetic_max_fraction))),
    )
    scores: list[float] = []
    stats: dict[str, object] = {
        "endpoint_pairs_allowed": 0,
        "endpoint_pairs_selected": 0,
        "density_candidates_expanded": 0,
        "density_candidates_restricted": 0,
        "observed_middle_reused": 0,
        "synthetic_considered": 0,
        "synthetic_added": 0,
        "synthetic_cap": max_synthetic,
        "refined": 0,
        "refine_shift_rejected": 0,
        "refine_failed": 0,
        "deepcenter_checked": 0,
        "deepcenter_accepted": 0,
        "deepcenter_rejected": 0,
        "deepcenter_bypassed_strong_motion": 0,
    }
    for t in sorted(by_time):
        end_ids = ends.get(t, [])
        start_ids = [node for node in starts.get(t + 2, []) if node not in used_starts]
        if not end_ids or not start_ids:
            continue
        end_pos = position_um[np.asarray(end_ids)]
        start_pos = position_um[np.asarray(start_ids)]
        distance = np.linalg.norm(end_pos[:, None] - start_pos[None, :], axis=2)
        fixed = gap_close_um * 2.0
        threshold = np.full_like(distance, fixed)
        for i, source_id in enumerate(end_ids):
            for j, target_id in enumerate(start_ids):
                local = 0.5 * (
                    spacing[t].get(source_id, GAP_DENSITY_REFERENCE_UM)
                    + spacing[t + 2].get(target_id, GAP_DENSITY_REFERENCE_UM)
                )
                delta = float(np.clip(
                    GAP_DENSITY_GAIN * (local - GAP_DENSITY_REFERENCE_UM),
                    -GAP_DENSITY_MAX_STEP_DELTA_UM,
                    GAP_DENSITY_MAX_STEP_DELTA_UM,
                ))
                threshold[i, j] += 2.0 * delta
        fixed_allowed = distance <= fixed
        allowed = distance <= threshold
        stats["density_candidates_expanded"] += int((allowed & ~fixed_allowed).sum())
        stats["density_candidates_restricted"] += int((fixed_allowed & ~allowed).sum())
        stats["endpoint_pairs_allowed"] += int(allowed.sum())
        if not allowed.any():
            continue
        big = float(np.max(threshold)) * 1000.0 + 1.0
        rows, columns = linear_sum_assignment(np.where(allowed, distance, big))
        for row, column in zip(rows, columns):
            if not allowed[row, column]:
                continue
            source_id = end_ids[int(row)]
            target_id = start_ids[int(column)]
            if source_id in outgoing or target_id in used_starts:
                continue
            midpoint_um = 0.5 * (position_um[source_id] + position_um[target_id])
            middle_ids = [node for node in isolated.get(t + 1, []) if node not in used_middle]
            middle_id = None
            middle_voxel = None
            if middle_ids:
                middle_distance = np.linalg.norm(
                    position_um[np.asarray(middle_ids)] - midpoint_um[None], axis=1
                )
                best = int(np.argmin(middle_distance))
                if float(middle_distance[best]) <= GAP_CLOSE_REUSE_UM:
                    middle_id = middle_ids[best]
                    middle_voxel = coords[middle_id, 1:4].copy()
                    stats["observed_middle_reused"] += 1
            if middle_id is None:
                stats["synthetic_considered"] += 1
                if int(stats["synthetic_added"]) >= max_synthetic:
                    continue
                midpoint_voxel = midpoint_um / scale
                frame = get_frame(zarr_path, t + 1, shape, dtype, frame_cache)
                middle_voxel, refine_state = refine_midpoint(midpoint_voxel, frame, scale)
                if refine_state == "refined":
                    stats["refined"] += 1
                elif refine_state == "shift_rejected":
                    stats["refine_shift_rejected"] += 1
                else:
                    stats["refine_failed"] += 1
                span = float(distance[row, column])
                if use_veto and span >= deepcenter_confirm_min_span_um:
                    stats["deepcenter_checked"] += 1
                    if t + 1 not in heatmap_cache:
                        cache_path = None
                        if heatmap_cache_dir is not None:
                            heatmap_cache_dir.mkdir(parents=True, exist_ok=True)
                            cache_path = heatmap_cache_dir / f"{zarr_path.stem}__t{t + 1:04d}.npy"
                        if cache_path is not None and cache_path.exists():
                            heatmap_cache[t + 1] = np.load(cache_path, allow_pickle=False)
                            stats.setdefault("deepcenter_heatmaps_loaded", 0)
                            stats["deepcenter_heatmaps_loaded"] += 1
                        else:
                            heatmap_cache[t + 1] = deepcenter_heatmap(frame, bundle)
                            stats.setdefault("deepcenter_heatmaps_inferred", 0)
                            stats["deepcenter_heatmaps_inferred"] += 1
                            if cache_path is not None:
                                tmp_path = cache_path.with_suffix(".tmp.npy")
                                np.save(tmp_path, heatmap_cache[t + 1], allow_pickle=False)
                                tmp_path.replace(cache_path)
                        _trim(heatmap_cache)
                    score = deepcenter_score(
                        middle_voxel,
                        heatmap_cache[t + 1],
                        int(bundle["cfg"].pool_factor),
                    )
                    scores.append(score)
                    if score < deepcenter_threshold:
                        stats["deepcenter_rejected"] += 1
                        continue
                    stats["deepcenter_accepted"] += 1
                elif use_veto:
                    stats["deepcenter_bypassed_strong_motion"] += 1
                middle_id = len(coords) + len(added_rows)
                added_rows.append([float(t + 1), *middle_voxel.astype(float).tolist()])
                stats["synthetic_added"] += 1
            first = float(np.linalg.norm((coords[source_id, 1:4] - middle_voxel) * scale))
            second = float(np.linalg.norm((middle_voxel - coords[target_id, 1:4]) * scale))
            added_edges.extend([(source_id, middle_id, 0.0, first), (middle_id, target_id, 0.0, second)])
            outgoing.update((source_id, middle_id))
            incoming.update((middle_id, target_id))
            used_starts.add(target_id)
            if middle_id < len(coords):
                used_middle.add(middle_id)
            stats["endpoint_pairs_selected"] += 1
    output_coords = np.vstack([coords, np.asarray(added_rows, dtype=np.float64)]) if added_rows else coords.copy()
    stats["added_edges"] = len(added_edges)
    if scores:
        stats["deepcenter_score_min"] = float(np.min(scores))
        stats["deepcenter_score_median"] = float(np.median(scores))
        stats["deepcenter_score_max"] = float(np.max(scores))
    return output_coords, [*edges, *added_edges], stats


def degree_stats(edges: list[tuple[int, int, float, float]]) -> dict[str, int]:
    outgoing: dict[int, int] = defaultdict(int)
    incoming: dict[int, int] = defaultdict(int)
    for source, target, *_ in edges:
        outgoing[int(source)] += 1
        incoming[int(target)] += 1
    result = {
        "maximum_out_degree": max(outgoing.values(), default=0),
        "maximum_in_degree": max(incoming.values(), default=0),
    }
    if result["maximum_out_degree"] > 1 or result["maximum_in_degree"] > 1:
        raise ValueError(f"Gap repair degree violation: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", default="source_checkpoint_validation")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gap-close-um", type=float, default=GAP_CLOSE_UM)
    parser.add_argument("--deepcenter-threshold", type=float, default=DEEPCENTER_THRESHOLD)
    parser.add_argument(
        "--deepcenter-confirm-min-span-um",
        type=float,
        default=DEEPCENTER_CONFIRM_MIN_SPAN_UM,
    )
    parser.add_argument(
        "--synthetic-max-fraction", type=float, default=GAP_CLOSE_MAX_ADDED_FRAC
    )
    parser.add_argument("--heatmap-cache-dir", type=Path)
    parser.add_argument("--arm-cache-dir", type=Path)
    args = parser.parse_args()
    if args.gap_close_um <= 0:
        parser.error("--gap-close-um must be positive")
    if not 0 <= args.deepcenter_threshold <= 1:
        parser.error("--deepcenter-threshold must be in [0, 1]")
    if args.deepcenter_confirm_min_span_um < 0:
        parser.error("--deepcenter-confirm-min-span-um must be nonnegative")
    if not 0 < args.synthetic_max_fraction <= 0.25:
        parser.error("--synthetic-max-fraction must be in (0, 0.25]")
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    bundle = load_bundle(args.checkpoint, args.checkpoint_sha256)
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    arms = {name: [] for name in ("registered_hungarian", "synthetic_gap_no_veto", "synthetic_gap_deepcenter")}
    telemetry = []
    cache_manifest = []
    for name in movies:
        cache = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=np.float64)
        base = registered_links(coords, scale)
        no_veto_coords, no_veto_edges, no_veto_stats = close_synthetic_gaps(
            coords,
            base,
            scale,
            args.data_dir / name,
            None,
            gap_close_um=args.gap_close_um,
            synthetic_max_fraction=args.synthetic_max_fraction,
        )
        veto_coords, veto_edges, veto_stats = close_synthetic_gaps(
            coords,
            base,
            scale,
            args.data_dir / name,
            bundle,
            gap_close_um=args.gap_close_um,
            deepcenter_threshold=args.deepcenter_threshold,
            deepcenter_confirm_min_span_um=args.deepcenter_confirm_min_span_um,
            synthetic_max_fraction=args.synthetic_max_fraction,
            heatmap_cache_dir=args.heatmap_cache_dir,
        )
        if args.arm_cache_dir is not None:
            args.arm_cache_dir.mkdir(parents=True, exist_ok=True)
            edge_array = (
                np.asarray(veto_edges, dtype=np.float64).reshape((-1, 4))
                if veto_edges else np.empty((0, 4), dtype=np.float64)
            )
            cache_output = args.arm_cache_dir / f"{Path(name).stem}.npz"
            temporary = cache_output.with_suffix(".npz.tmp")
            with temporary.open("wb") as handle:
                np.savez_compressed(
                    handle,
                    coords=np.asarray(veto_coords, dtype=np.float64),
                    edge_source=edge_array[:, 0].astype(np.int64),
                    edge_target=edge_array[:, 1].astype(np.int64),
                    edge_probability=edge_array[:, 2].astype(np.float64),
                    edge_distance=edge_array[:, 3].astype(np.float64),
                )
            temporary.replace(cache_output)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for arm, arm_coords, arm_edges in (
            ("registered_hungarian", coords, base),
            ("synthetic_gap_no_veto", no_veto_coords, no_veto_edges),
            ("synthetic_gap_deepcenter", veto_coords, veto_edges),
        ):
            degrees = degree_stats(arm_edges)
            graph = build_graph(arm_coords, arm_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({"dataset": name, **per_sample_metrics(metric, float(estimated), recall)})
            if arm == "registered_hungarian":
                base_degrees = degrees
        telemetry.append({
            "dataset": name,
            "base_degrees": base_degrees,
            "no_veto": {**no_veto_stats, **degree_stats(no_veto_edges)},
            "deepcenter": {**veto_stats, **degree_stats(veto_edges)},
        })
        cache_manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_SYNTHETIC_GAP_EVALUATION",
        "parameters": {
            "gap_frames": 1,
            "gap_close_um_per_step": args.gap_close_um,
            "reuse_existing_um": GAP_CLOSE_REUSE_UM,
            "density_reference_um": GAP_DENSITY_REFERENCE_UM,
            "density_gain": GAP_DENSITY_GAIN,
            "density_max_step_delta_um": GAP_DENSITY_MAX_STEP_DELTA_UM,
            "synthetic_max_fraction": args.synthetic_max_fraction,
            "synthetic_max_absolute": GAP_CLOSE_MAX_ADDED_ABS,
            "refine_window_zyx": [GAP_REFINE_WIN_Z, GAP_REFINE_WIN_YX, GAP_REFINE_WIN_YX],
            "refine_max_shift_um": GAP_REFINE_MAX_SHIFT_UM,
            "deepcenter_threshold": args.deepcenter_threshold,
            "deepcenter_confirm_min_span_um": args.deepcenter_confirm_min_span_um,
            "heatmap_cache_dir": str(args.heatmap_cache_dir) if args.heatmap_cache_dir else None,
            "arm_cache_dir": str(args.arm_cache_dir) if args.arm_cache_dir else None,
        },
        "checkpoint_sha256": bundle["sha256"],
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": cache_manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
