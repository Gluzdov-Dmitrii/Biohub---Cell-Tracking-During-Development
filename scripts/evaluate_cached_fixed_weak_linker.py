"""Evaluate one fixed learned-probability/motion linker from immutable caches."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_cached_short_track_family import filter_family, sha256
from evaluate_registered_model import jsonable, registered_graph


def cached_edges(payload: dict[str, np.ndarray]) -> list[tuple[int, int, float, float]]:
    return [
        (int(source), int(target), float(probability), float(distance))
        for source, target, probability, distance in zip(
            payload["edge_source"],
            payload["edge_target"],
            payload["edge_probability"],
            payload["edge_distance"],
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", default="target_development")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--probability-weight", type=float, default=0.1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.minimum_length < 1:
        parser.error("minimum length must be positive")
    if not 0.0 < args.probability_weight < 1.0:
        parser.error("probability weight must be strictly between zero and one")

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies_payload = json.loads(args.movies_json.read_text(encoding="utf-8"))
    movies = list(movies_payload[args.movie_key])
    if not movies:
        raise RuntimeError("empty movie list")

    rows = []
    cache_manifest = []
    telemetry = []
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
            native_edges = cached_edges(payload)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        _, weak_edges = registered_graph(
            coords,
            native_edges,
            dataset.scale,
            args.probability_weight,
            lambda values, edges: (values, edges),
        )
        probability_lookup = {
            (int(source), int(target)): float(score)
            for source, target, score, _ in weak_edges
        }
        selected_coords, selected_edges, filter_stats = filter_family(
            coords,
            weak_edges,
            probability_lookup,
            args.minimum_length,
            rescue=False,
        )
        graph = build_graph(selected_coords, selected_edges)
        metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
        recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        rows.append(
            {
                "dataset": name,
                **per_sample_metrics(metric, float(estimated), recall),
            }
        )
        telemetry.append(
            {
                "dataset": name,
                "native_candidates": len(native_edges),
                "weak_links": len(weak_edges),
                "filter": filter_stats,
            }
        )
        cache_manifest.append(
            {"path": str(cache_path), "bytes": cache_path.stat().st_size, "sha256": sha256(cache_path)}
        )

    arm = f"registered_weak_p{int(round(args.probability_weight * 1000)):03d}_min{args.minimum_length}"
    result = {
        "status": "PASS_FIXED_CACHED_WEAK_LINKER",
        "selection": "none",
        "arm": arm,
        "parameters": {
            "probability_weight": args.probability_weight,
            "motion_weight": 1.0 - args.probability_weight,
            "registered_gate_um": 7.0,
            "registered_motion_scale_um": 3.0,
            "minimum_component_nodes": args.minimum_length,
        },
        "movies_source": str(args.movies_json),
        "movies_source_sha256": sha256(args.movies_json),
        "movie_key": args.movie_key,
        "cache_manifest": cache_manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": {arm: rows},
        "summary_by_arm": {arm: summarise(rows)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result["summary_by_arm"]), indent=2))


if __name__ == "__main__":
    main()
