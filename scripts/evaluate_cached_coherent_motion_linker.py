"""Evaluate robust rigid/similarity frame-motion linkers on frozen OOF coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def translation_shift(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    tree = cKDTree(target)
    _, nearest = tree.query(source, k=1)
    displacement = target[np.asarray(nearest, dtype=int)] - source
    shift = np.median(displacement, axis=0)
    inliers = np.linalg.norm(displacement - shift, axis=1) <= 4.0
    if int(inliers.sum()) >= 3:
        shift = np.median(displacement[inliers], axis=0)
    return np.asarray(shift, dtype=float)


def mutual_pairs(
    source: np.ndarray, target: np.ndarray, shift: np.ndarray, radius_um: float = 4.0
) -> tuple[np.ndarray, np.ndarray]:
    shifted = source + shift
    distance, source_to_target = cKDTree(target).query(shifted, k=1)
    _, target_to_source = cKDTree(shifted).query(target, k=1)
    source_ids = np.arange(len(source), dtype=int)
    target_ids = np.asarray(source_to_target, dtype=int)
    keep = (distance <= radius_um) & (target_to_source[target_ids] == source_ids)
    return source_ids[keep], target_ids[keep]


def fit_transform(
    source: np.ndarray, target: np.ndarray, mode: str
) -> tuple[np.ndarray, np.ndarray, float]:
    if mode not in {"rigid", "similarity"}:
        raise ValueError(f"unsupported mode: {mode}")
    if len(source) < 4 or source.shape != target.shape:
        raise ValueError("at least four paired 3D points are required")
    source_mean = source.mean(axis=0)
    target_mean = target.mean(axis=0)
    x = source - source_mean
    y = target - target_mean
    u, singular, vt = np.linalg.svd(x.T @ y)
    rotation = u @ vt
    if np.linalg.det(rotation) < 0:
        u[:, -1] *= -1
        rotation = u @ vt
    scale = 1.0
    if mode == "similarity":
        denominator = float(np.sum(x * x))
        if denominator > 1e-12:
            scale = float(np.clip(np.sum(singular) / denominator, 0.97, 1.03))
    offset = target_mean - scale * (source_mean @ rotation)
    return rotation, offset, scale


def robust_transform(
    source: np.ndarray, target: np.ndarray, shift: np.ndarray, mode: str
) -> tuple[np.ndarray, np.ndarray, float, int]:
    source_ids, target_ids = mutual_pairs(source, target, shift)
    if len(source_ids) < 4:
        return np.eye(3), shift.copy(), 1.0, int(len(source_ids))
    paired_source = source[source_ids]
    paired_target = target[target_ids]
    rotation, offset, scale = fit_transform(paired_source, paired_target, mode)
    residual = np.linalg.norm(
        scale * (paired_source @ rotation) + offset - paired_target, axis=1
    )
    median = float(np.median(residual))
    mad = float(np.median(np.abs(residual - median)))
    limit = min(4.0, median + 2.5 * max(1.4826 * mad, 0.05))
    inliers = residual <= limit
    if int(inliers.sum()) >= 4:
        rotation, offset, scale = fit_transform(
            paired_source[inliers], paired_target[inliers], mode
        )
    return rotation, offset, scale, int(inliers.sum())


def coherent_links(
    coords: np.ndarray,
    scale_xyz: np.ndarray,
    mode: str,
    alpha: float,
    gate_um: float = 7.0,
    motion_scale_um: float = 3.0,
) -> tuple[list[tuple[int, int, float, float]], list[dict]]:
    if mode not in {"rigid", "similarity"} or not 0.0 <= alpha <= 1.0:
        raise ValueError("invalid coherent-motion configuration")
    linked: list[tuple[int, int, float, float]] = []
    telemetry: list[dict] = []
    integer_times = coords[:, 0].astype(int) if len(coords) else np.empty(0, dtype=int)
    times = sorted(set(integer_times.tolist()))
    for timepoint in times[:-1]:
        source_ids = np.flatnonzero(integer_times == timepoint)
        target_ids = np.flatnonzero(integer_times == timepoint + 1)
        if not len(source_ids) or not len(target_ids):
            continue
        source = coords[source_ids, 1:4] * scale_xyz
        target = coords[target_ids, 1:4] * scale_xyz
        shift = translation_shift(source, target)
        rotation, offset, fitted_scale, inliers = robust_transform(
            source, target, shift, mode
        )
        translation_prediction = source + shift
        coherent_prediction = fitted_scale * (source @ rotation) + offset
        predicted = (1.0 - alpha) * translation_prediction + alpha * coherent_prediction
        residual = np.linalg.norm(predicted[:, None, :] - target[None, :, :], axis=2)
        valid = residual < gate_um
        score = np.exp(-residual / motion_scale_um)
        minimum_score = float(np.exp(-gate_um / motion_scale_um))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score)], axis=1
        )
        rows, columns = linear_sum_assignment(augmented)
        accepted = 0
        for row, column in zip(rows, columns):
            if column >= len(target) or not valid[row, column] or score[row, column] < minimum_score:
                continue
            linked.append(
                (
                    int(source_ids[row]),
                    int(target_ids[column]),
                    float(score[row, column]),
                    float(np.linalg.norm(source[row] - target[column])),
                )
            )
            accepted += 1
        telemetry.append(
            {
                "time": int(timepoint),
                "fit_inliers": inliers,
                "fitted_scale": fitted_scale,
                "accepted_edges": accepted,
            }
        )
    return linked, telemetry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    variants = {
        "translation": None,
        "rigid_a025": ("rigid", 0.25),
        "rigid_a050": ("rigid", 0.50),
        "similarity_a025": ("similarity", 0.25),
        "similarity_a050": ("similarity", 0.50),
    }
    arms = {label: [] for label in variants}
    telemetry = []
    manifest = []
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        physical_scale = np.asarray(dataset.scale, dtype=float)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        movie_telemetry = {"dataset": name, "variants": {}}
        for label, configuration in variants.items():
            if configuration is None:
                edges = registered_links(coords, physical_scale)
                frame_telemetry = []
            else:
                edges, frame_telemetry = coherent_links(
                    coords, physical_scale, configuration[0], configuration[1]
                )
            selected_coords, selected_edges, filter_stats = filter_family(
                coords, edges, {}, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
            movie_telemetry["variants"][label] = {
                "filter": filter_stats,
                "frames": frame_telemetry,
            }
        telemetry.append(movie_telemetry)
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "complete": True}), flush=True)

    result = {
        "status": "PASS_CACHED_COHERENT_MOTION_LINKER",
        "protocol": "Frozen detector coordinates; robust mutual-nearest rigid/similarity frame transform blended with the registered translation prediction.",
        "parameters": {
            "fit_radius_um": 4.0,
            "gate_um": 7.0,
            "motion_scale_um": 3.0,
            "similarity_scale_clip": [0.97, 1.03],
            "variants": variants,
        },
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "Use nested movie-level selection; full-development ranking is diagnostic only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
