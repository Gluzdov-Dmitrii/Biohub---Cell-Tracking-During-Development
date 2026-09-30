"""Evaluate component-length filters on cached, already-selected graph edges."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_cached_short_track_family import filter_family


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, action="append", required=True)
    args = parser.parse_args()
    lengths = args.minimum_length
    if any(length < 1 for length in lengths) or len(set(lengths)) != len(lengths):
        parser.error("minimum lengths must be unique positive integers")
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    labels = {length: ("no_filter" if length == 1 else f"min{length}") for length in lengths}
    arms = {label: [] for label in labels.values()}
    telemetry, manifest = [], []
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
            edges = list(zip(
                payload["edge_source"].astype(int).tolist(),
                payload["edge_target"].astype(int).tolist(),
                payload["edge_probability"].astype(float).tolist(),
                payload["edge_distance"].astype(float).tolist(),
            ))
        probabilities = {(int(s), int(t)): float(p) for s, t, p, _ in edges}
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        movie_stats = {"dataset": name, "variants": {}}
        for length, label in labels.items():
            arm_coords, arm_edges, stats = filter_family(coords, edges, probabilities, length)
            graph = build_graph(arm_coords, arm_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append({"dataset": name, **per_sample_metrics(metric, float(estimated), recall)})
            movie_stats["variants"][label] = stats
        telemetry.append(movie_stats)
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
    result = {
        "status": "PASS_CACHED_SELECTED_EDGE_SHORT_TRACKS",
        "lengths": lengths,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
