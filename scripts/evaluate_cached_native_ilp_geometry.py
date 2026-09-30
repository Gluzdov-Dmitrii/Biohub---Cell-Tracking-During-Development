"""Evaluate a frozen geometry repair of cached native ILP edges."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from evaluate_cached_native_ilp import degrees
from evaluate_coordinate_consensus import registered_links


DIV_PARENT_MAX_UM = 10.5
DIV_SISTER_MAX_UM = 8.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def geometry_filter(coords, edges, scale):
    """Use source ranking and geometry; retain one edge if a fork is invalid."""
    by_source = defaultdict(list)
    for edge in edges:
        by_source[int(edge[0])].append(edge)
    filtered = []
    stats = {
        "multi_source_count": 0,
        "valid_division_count": 0,
        "bad_division_to_single_count": 0,
        "dropped_edges": 0,
    }
    for source_id, source_edges in by_source.items():
        if len(source_edges) <= 1:
            filtered.extend(source_edges)
            continue
        stats["multi_source_count"] += 1
        ranked = sorted(
            source_edges,
            key=lambda edge: (float(edge[2]), -float(edge[3])),
            reverse=True,
        )
        top1, top2 = ranked[:2]
        target1, target2 = int(top1[1]), int(top2[1])
        sister = float(
            np.linalg.norm((coords[target1, 1:4] - coords[target2, 1:4]) * scale)
        )
        valid = (
            max(float(top1[3]), float(top2[3])) <= DIV_PARENT_MAX_UM
            and sister <= DIV_SISTER_MAX_UM
            and int(coords[target1, 0]) == int(coords[source_id, 0]) + 1
            and int(coords[target2, 0]) == int(coords[source_id, 0]) + 1
        )
        if valid:
            filtered.extend((top1, top2))
            stats["valid_division_count"] += 1
            stats["dropped_edges"] += max(0, len(ranked) - 2)
        else:
            filtered.append(top1)
            stats["bad_division_to_single_count"] += 1
            stats["dropped_edges"] += len(ranked) - 1
    return filtered, stats


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
    arms = {"registered_hungarian": [], "native_ilp_geometry": []}
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
        scale = np.asarray(dataset.scale, dtype=float)
        registered = registered_links(coords, scale)
        candidate, filter_stats = geometry_filter(coords, native, scale)
        estimated = (
            GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}
        ).get("estimated_number_of_nodes")
        movie_stats = {"dataset": name, "filter": filter_stats}
        for arm, edges in (
            ("registered_hungarian", registered),
            ("native_ilp_geometry", candidate),
        ):
            max_in, max_out, divisions = degrees(edges)
            if max_in > 1 or max_out > 2:
                raise ValueError(f"{name} {arm} invalid degree {max_in}/{max_out}")
            graph = build_graph(coords, edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = (
                node_recall(graph, dataset.tracks)
                if graph.num_nodes() and graph.num_edges()
                else 0.0
            )
            arms[arm].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
            movie_stats[arm] = {
                "edges": len(edges),
                "divisions": divisions,
                "maximum_in_degree": max_in,
                "maximum_out_degree": max_out,
            }
        telemetry.append(movie_stats)
        manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_FROZEN_NATIVE_ILP_GEOMETRY_EVALUATION",
        "parameters": {
            "ranking": ["edge_probability_desc", "distance_um_asc"],
            "division_parent_max_um": DIV_PARENT_MAX_UM,
            "division_sister_max_um": DIV_SISTER_MAX_UM,
            "invalid_division_action": "keep_top1",
        },
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
        "selection_warning": "One-shot source-attributed fixed repair; no parameter tuning.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
