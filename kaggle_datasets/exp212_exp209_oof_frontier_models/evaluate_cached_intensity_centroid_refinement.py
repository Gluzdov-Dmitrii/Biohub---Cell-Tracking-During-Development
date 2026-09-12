"""Evaluate one fixed raw-image centroid refinement on frozen detector coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refine_points(
    frame: np.ndarray,
    points_zyx: np.ndarray,
    radius_zyx: tuple[int, int, int] = (2, 5, 5),
) -> tuple[np.ndarray, np.ndarray, int]:
    """Move each point to the positive-intensity centroid of its fixed local crop."""
    frame = np.asarray(frame)
    points = np.asarray(points_zyx, dtype=np.float64)
    if frame.ndim != 3 or points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("expected frame ZYX and points Nx3")
    if any(radius < 0 for radius in radius_zyx):
        raise ValueError("radii must be nonnegative")
    refined = points.copy()
    shift_voxels = np.zeros_like(points)
    zero_weight = 0
    shape = np.asarray(frame.shape, dtype=int)
    radii = np.asarray(radius_zyx, dtype=int)
    for index, point in enumerate(points):
        center = np.rint(point).astype(int)
        lower = np.maximum(0, center - radii)
        upper = np.minimum(shape, center + radii + 1)
        crop = frame[
            lower[0] : upper[0], lower[1] : upper[1], lower[2] : upper[2]
        ].astype(np.float64, copy=False)
        if not crop.size:
            zero_weight += 1
            continue
        weights = np.clip(crop - float(np.min(crop)), 0.0, None)
        total = float(weights.sum())
        if not np.isfinite(total) or total <= 0.0:
            zero_weight += 1
            continue
        axes = np.ogrid[tuple(slice(lower[axis], upper[axis]) for axis in range(3))]
        centroid = np.asarray(
            [float((weights * axes[axis]).sum() / total) for axis in range(3)]
        )
        if not np.all(np.isfinite(centroid)):
            zero_weight += 1
            continue
        refined[index] = centroid
        shift_voxels[index] = centroid - point
    return refined, shift_voxels, zero_weight


def refine_movie(
    image: object,
    coords: np.ndarray,
    scale_zyx: np.ndarray,
    radius_zyx: tuple[int, int, int] = (2, 5, 5),
) -> tuple[np.ndarray, dict]:
    refined = np.asarray(coords, dtype=np.float64).copy()
    times = refined[:, 0].astype(int) if len(refined) else np.empty(0, dtype=int)
    physical_shifts: list[float] = []
    zero_weight = 0
    frames = 0
    for timepoint in sorted(set(times.tolist())):
        ids = np.flatnonzero(times == timepoint)
        if not len(ids):
            continue
        frame = np.asarray(image[timepoint])
        points, shifts, failed = refine_points(frame, refined[ids, 1:4], radius_zyx)
        refined[ids, 1:4] = points
        physical_shifts.extend(np.linalg.norm(shifts * scale_zyx[None, :], axis=1).tolist())
        zero_weight += failed
        frames += 1
    shift_array = np.asarray(physical_shifts, dtype=float)
    telemetry = {
        "nodes": int(len(refined)),
        "frames": frames,
        "zero_weight_nodes": zero_weight,
        "mean_shift_um": float(np.mean(shift_array)) if len(shift_array) else 0.0,
        "median_shift_um": float(np.median(shift_array)) if len(shift_array) else 0.0,
        "p95_shift_um": float(np.quantile(shift_array, 0.95)) if len(shift_array) else 0.0,
        "max_shift_um": float(np.max(shift_array)) if len(shift_array) else 0.0,
    }
    return refined, telemetry


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
    import zarr
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    if not movies:
        raise RuntimeError("empty movie list")
    arms = {"translation": [], "intensity_centroid_r2_5_5": []}
    telemetry = []
    manifest = []
    for name in movies:
        stem = Path(name).stem
        cache_path = args.cache_dir / f"{stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        image = zarr.open(str(args.data_dir / name), mode="r")["0"]
        refined, movie_telemetry = refine_movie(image, coords, scale)
        estimated = (GeffMetadata.read(args.data_dir / f"{stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for label, candidate in (("translation", coords), ("intensity_centroid_r2_5_5", refined)):
            edges = registered_links(candidate, scale)
            selected_coords, selected_edges, filter_stats = filter_family(
                candidate, edges, {}, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
            movie_telemetry[f"{label}_filter"] = filter_stats
        movie_telemetry["dataset"] = name
        telemetry.append(movie_telemetry)
        manifest.append({"dataset": name, "path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "complete": True}), flush=True)

    result = {
        "status": "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT",
        "protocol": "Frozen detector node count; exact local positive-intensity centroid in radius (z=2,y=5,x=5), then registered translation linking and fixed short-track pruning.",
        "radius_zyx_voxels": [2, 5, 5],
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "One fixed source-attributed mechanism; no parameter tuning on these movies.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
