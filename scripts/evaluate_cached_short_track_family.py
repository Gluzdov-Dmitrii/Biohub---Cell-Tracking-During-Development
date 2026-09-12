"""Evaluate short-track filtering and rescue on frozen reciprocal OOF caches."""

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


def edge_probability_lookup(payload: dict[str, np.ndarray]) -> dict[tuple[int, int], float]:
    result: dict[tuple[int, int], float] = {}
    for source, target, probability in zip(
        payload["edge_source"], payload["edge_target"], payload["edge_probability"]
    ):
        key = (int(source), int(target))
        result[key] = max(result.get(key, 0.0), float(probability))
    return result


def components(node_count: int, edges: list[tuple[int, int, float, float]]) -> list[list[int]]:
    parent = list(range(node_count))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for source, target, *_ in edges:
        a, b = find(int(source)), find(int(target))
        if a != b:
            parent[a] = b
    grouped: dict[int, list[int]] = defaultdict(list)
    for node in range(node_count):
        grouped[find(node)].append(node)
    return list(grouped.values())


def filter_family(
    coords: np.ndarray,
    edges: list[tuple[int, int, float, float]],
    probabilities: dict[tuple[int, int], float],
    min_length: int,
    rescue: bool = False,
) -> tuple[np.ndarray, list[tuple[int, int, float, float]], dict]:
    """Filter weak components and optionally rescue exact length-five tracks."""
    if min_length <= 1:
        return coords.copy(), list(edges), {
            "nodes_removed": 0, "edges_removed": 0, "components_rescued": 0,
            "nodes_rescued": 0, "rescue_triggered": False,
        }
    groups = components(len(coords), edges)
    edge_by_component: dict[int, list[tuple[int, int, float, float]]] = defaultdict(list)
    root_for_node = {node: root for root, members in enumerate(groups) for node in members}
    outgoing: dict[int, int] = defaultdict(int)
    for edge in edges:
        edge_by_component[root_for_node[int(edge[0])]].append(edge)
        outgoing[int(edge[0])] += 1

    keep: set[int] = set()
    removed_groups: list[tuple[int, list[int]]] = []
    for root, members in enumerate(groups):
        has_division = any(outgoing[node] >= 2 for node in members)
        if len(members) >= min_length or has_division:
            keep.update(members)
        else:
            removed_groups.append((root, members))
    if not keep:
        return coords.copy(), list(edges), {
            "nodes_removed": 0, "edges_removed": 0, "components_rescued": 0,
            "nodes_rescued": 0, "rescue_triggered": False, "filter_skipped_all": True,
        }
    removed_before_rescue = len(coords) - len(keep)
    rescue_triggered = rescue and removed_before_rescue / max(len(coords), 1) >= 0.10
    rescued_components = 0
    rescued_nodes = 0
    if rescue_triggered:
        budget = min(60, max(0, int(round(len(coords) * 0.006))))
        proposals = []
        for root, members in removed_groups:
            if len(members) != 5:
                continue
            group_edges = edge_by_component[root]
            if not group_edges:
                continue
            mean_probability = float(np.mean([
                probabilities.get((int(edge[0]), int(edge[1])), 0.0) for edge in group_edges
            ]))
            mean_distance = float(np.mean([float(edge[3]) for edge in group_edges]))
            if mean_probability >= 0.90 and mean_distance <= 2.75:
                score = mean_probability - 0.02 * mean_distance + 0.004 * len(members)
                proposals.append((score, members))
        for _, members in sorted(proposals, reverse=True):
            if rescued_nodes + len(members) > budget:
                continue
            keep.update(members)
            rescued_nodes += len(members)
            rescued_components += 1

    selected = sorted(keep)
    old_to_new = {old: new for new, old in enumerate(selected)}
    kept_edges = [
        (old_to_new[int(source)], old_to_new[int(target)], score, distance)
        for source, target, score, distance in edges
        if int(source) in keep and int(target) in keep
    ]
    return coords[selected], kept_edges, {
        "nodes_removed": len(coords) - len(selected),
        "edges_removed": len(edges) - len(kept_edges),
        "components_rescued": rescued_components,
        "nodes_rescued": rescued_nodes,
        "rescue_triggered": rescue_triggered,
        "filter_skipped_all": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, action="append")
    parser.add_argument("--include-public-rescue", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    lengths = args.minimum_length or [1, 2, 3, 4, 5, 6]
    if any(length < 1 for length in lengths) or len(set(lengths)) != len(lengths):
        parser.error("minimum lengths must be unique positive integers")
    variants = {("no_filter" if length == 1 else f"min{length}"): (length, False) for length in lengths}
    if args.include_public_rescue:
        if 6 not in lengths:
            parser.error("public rescue requires minimum length 6")
        variants["min6_rescue5_p90_d275_cap006"] = (6, True)
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    arms = {label: [] for label in variants}
    telemetry = []
    manifest = []
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
            probabilities = edge_probability_lookup(payload)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        edges = registered_links(coords, scale)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        movie_stats = {"dataset": name, "variants": {}}
        for label, (min_length, rescue) in variants.items():
            filtered_coords, filtered_edges, stats = filter_family(
                coords, edges, probabilities, min_length, rescue
            )
            graph = build_graph(filtered_coords, filtered_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append({
                "dataset": name,
                **per_sample_metrics(metric, float(estimated), recall),
            })
            movie_stats["variants"][label] = stats
        telemetry.append(movie_stats)
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "telemetry": movie_stats["variants"]}), flush=True)
    result = {
        "status": "PASS_CACHED_SHORT_TRACK_FAMILY",
        "protocol": "Frozen reciprocal embryo-disjoint OOF caches; no neural inference.",
        "parameters": {
            label: {"minimum_component_nodes": value[0], "rescue": value[1]}
            for label, value in variants.items()
        },
        "rescue_parameters": {
            "trigger_removed_fraction": 0.10,
            "eligible_component_nodes": 5,
            "minimum_mean_learned_probability": 0.90,
            "maximum_mean_physical_edge_distance_um": 2.75,
            "node_budget_fraction": 0.006,
            "node_budget_absolute": 60,
        },
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "Full-data arm scores are diagnostic; use nested selector for primary score.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
