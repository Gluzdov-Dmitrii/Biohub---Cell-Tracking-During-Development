"""Evaluate a fixed family of raw-image centroid refinements on cached detections."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_cached_intensity_centroid_refinement import refine_points, sha256
from evaluate_coordinate_consensus import registered_links


def parse_radius(value: str) -> tuple[int, int, int]:
    try:
        radius = tuple(int(item) for item in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("radius must be z,y,x integers") from error
    if len(radius) != 3 or any(item < 0 for item in radius):
        raise argparse.ArgumentTypeError("radius must contain three nonnegative integers")
    return radius


def radius_label(radius: tuple[int, int, int]) -> str:
    return "intensity_centroid_r" + "_".join(str(item) for item in radius)


def refine_movie_family(
    image: object,
    coords: np.ndarray,
    scale_zyx: np.ndarray,
    radii: list[tuple[int, int, int]],
) -> tuple[dict[str, np.ndarray], dict[str, dict]]:
    """Load each frame once, then apply every preregistered crop radius."""
    original = np.asarray(coords, dtype=np.float64)
    if len(set(radii)) != len(radii):
        raise ValueError("duplicate radii are not allowed")
    if not radii:
        return {}, {}
    labels = [radius_label(radius) for radius in radii]
    refined = {label: original.copy() for label in labels}
    shifts = {label: [] for label in labels}
    zero_weight = {label: 0 for label in labels}
    frames = 0
    times = original[:, 0].astype(int) if len(original) else np.empty(0, dtype=int)
    for timepoint in sorted(set(times.tolist())):
        ids = np.flatnonzero(times == timepoint)
        frame = np.asarray(image[timepoint])
        for radius, label in zip(radii, labels):
            points, delta, failed = refine_points(frame, original[ids, 1:4], radius)
            refined[label][ids, 1:4] = points
            shifts[label].extend(
                np.linalg.norm(delta * scale_zyx[None, :], axis=1).tolist()
            )
            zero_weight[label] += failed
        frames += 1
    telemetry = {}
    for label in labels:
        values = np.asarray(shifts[label], dtype=float)
        telemetry[label] = {
            "nodes": int(len(original)),
            "frames": frames,
            "zero_weight_nodes": zero_weight[label],
            "mean_shift_um": float(np.mean(values)) if len(values) else 0.0,
            "median_shift_um": float(np.median(values)) if len(values) else 0.0,
            "p95_shift_um": float(np.quantile(values, 0.95)) if len(values) else 0.0,
            "max_shift_um": float(np.max(values)) if len(values) else 0.0,
        }
    return refined, telemetry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", default="target_development")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--radius", action="append", type=parse_radius, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if len(set(args.radius)) != len(args.radius):
        raise RuntimeError("duplicate radii are not allowed")
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    import zarr
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    payload = json.loads(args.movies_json.read_text(encoding="utf-8"))
    movies = payload[args.movie_key]
    if not movies:
        raise RuntimeError("empty movie list")
    labels = [radius_label(radius) for radius in args.radius]
    arms: dict[str, list[dict]] = {label: [] for label in ["translation", *labels]}
    telemetry = []
    manifest = []
    for name in movies:
        stem = Path(name).stem
        cache_path = args.cache_dir / f"{stem}.npz"
        with np.load(cache_path) as cache:
            coords = cache["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        if args.radius:
            image = zarr.open(str(args.data_dir / name), mode="r")["0"]
            candidates, movie_telemetry = refine_movie_family(image, coords, scale, args.radius)
        else:
            candidates, movie_telemetry = {}, {}
        candidates = {"translation": coords, **candidates}
        estimated = (GeffMetadata.read(args.data_dir / f"{stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        filter_telemetry = {}
        for label, candidate in candidates.items():
            edges = registered_links(candidate, scale)
            selected_coords, selected_edges, filter_stats = filter_family(
                candidate, edges, {}, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = (
                node_recall(graph, dataset.tracks)
                if graph.num_nodes() and graph.num_edges()
                else 0.0
            )
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
            filter_telemetry[label] = filter_stats
        telemetry.append(
            {
                "dataset": name,
                "by_arm": movie_telemetry,
                "filter_by_arm": filter_telemetry,
            }
        )
        manifest.append({"dataset": name, "path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "complete": True}), flush=True)

    result = {
        "status": "PASS_FIXED_INTENSITY_CENTROID_FAMILY",
        "protocol": "Frozen detector nodes; each frame is loaded once and every preregistered positive-intensity centroid radius is linked and pruned independently.",
        "movie_key": args.movie_key,
        "radii_zyx_voxels": [list(radius) for radius in args.radius],
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "Inspect only source-validation arms before the selector freezes one arm for target evaluation.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
