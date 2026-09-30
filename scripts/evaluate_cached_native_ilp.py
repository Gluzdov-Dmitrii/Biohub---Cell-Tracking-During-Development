"""Evaluate cached native ILP edges against registered-motion topology."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def degrees(edges: list[tuple[int, int, float, float]]) -> tuple[int, int, int]:
    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    for source, target, *_ in edges:
        outgoing[int(source)] += 1
        incoming[int(target)] += 1
    return (
        max(incoming.values(), default=0),
        max(outgoing.values(), default=0),
        sum(value == 2 for value in outgoing.values()),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    arms = {"registered_hungarian": [], "cached_native_ilp": []}
    telemetry = []
    manifest = []
    for name in movies:
        cache = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache) as payload:
            coords = payload["coords"].astype(np.float64)
            native = list(zip(
                payload["edge_source"].astype(int).tolist(),
                payload["edge_target"].astype(int).tolist(),
                payload["edge_probability"].astype(float).tolist(),
                payload["edge_distance"].astype(float).tolist(),
            ))
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        registered = registered_links(coords, np.asarray(dataset.scale, dtype=float))
        estimated = (
            GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}
        ).get("estimated_number_of_nodes")
        movie_stats = {"dataset": name}
        for arm, edges in (("registered_hungarian", registered), ("cached_native_ilp", native)):
            max_in, max_out, divisions = degrees(edges)
            if max_in > 1 or max_out > 2:
                raise ValueError(f"{name} {arm} invalid degree {max_in}/{max_out}")
            graph = build_graph(coords, edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({"dataset": name, **per_sample_metrics(metric, float(estimated), recall)})
            movie_stats[arm] = {"edges": len(edges), "divisions": divisions, "max_in_degree": max_in, "max_out_degree": max_out}
        telemetry.append(movie_stats)
        manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_FROZEN_CACHED_NATIVE_ILP_EVALUATION",
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
        "selection_warning": "One-shot evaluation of exact cached predict_video ILP edges; no tuning."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
