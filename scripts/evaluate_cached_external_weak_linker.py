"""Evaluate an external learned tie-break on fixed cached coordinates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_registered_model import jsonable, registered_graph


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
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", required=True)
    parser.add_argument("--weight", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.weight < 1.0:
        raise ValueError(args.weight)

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    arms = {"registered_hungarian": [], "external_weak_hungarian": []}
    manifest = []
    for movie in movies:
        cache_path = args.cache_dir / f"{Path(movie).stem}.npz"
        with np.load(cache_path) as cache:
            coords = cache["coords"].astype(np.float32)
            edges = list(zip(
                cache["edge_source"], cache["edge_target"],
                cache["edge_probability"], cache["edge_distance"],
            ))
        dataset = open_dataset(args.data_dir / movie, require_tracks=True, load_image=False)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(movie).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for arm, weight in (("registered_hungarian", 0.0), ("external_weak_hungarian", args.weight)):
            graph = registered_graph(coords, edges, dataset.scale, weight, build_graph)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({
                "dataset": movie,
                **per_sample_metrics(metric, float(estimated), recall),
            })
        manifest.append({"dataset": movie, "sha256": sha256(cache_path)})
    result = {
        "status": "PASS_CACHED_EXTERNAL_WEAK_LINKER_EVALUATION",
        "weight": args.weight,
        "edge_probability_floor": 0.02,
        "cache_manifest": manifest,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result["summary_by_arm"]), indent=2))


if __name__ == "__main__":
    main()
