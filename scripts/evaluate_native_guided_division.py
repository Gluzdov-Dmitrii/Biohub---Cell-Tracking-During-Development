"""Evaluate native-edge-guided conservative division additions."""

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


def add_native_guided_divisions(coords, links, native_edges, scale):
    """Use sparse learned edges only as a candidate source for a second child."""
    outgoing = defaultdict(list)
    incoming = set()
    for source, target, *_ in links:
        outgoing[int(source)].append(int(target))
        incoming.add(int(target))
    native_by_source = defaultdict(list)
    for edge in native_edges:
        native_by_source[int(edge[0])].append(edge)
    times = defaultdict(list)
    for node_id, row in enumerate(coords):
        times[int(row[0])].append(node_id)
    position = coords[:, 1:4] * scale
    global_cap = max(1, int(round(max(1, len(links)) * 0.004)))
    accepted = []
    rejected = defaultdict(int)
    used_sources = set()
    used_targets = set()
    for timepoint in sorted(times):
        sources = [node for node in times[timepoint] if len(outgoing.get(node, [])) == 1]
        frame_proposals = []
        for source in sources:
            first = outgoing[source][0]
            if int(coords[first, 0]) != timepoint + 1:
                continue
            existing_distance = float(np.linalg.norm(position[first] - position[source]))
            if existing_distance > 7.8:
                continue
            candidates = []
            for edge in native_by_source.get(source, []):
                second = int(edge[1])
                if second == first or second in incoming or int(coords[second, 0]) != timepoint + 1:
                    continue
                new_distance = float(np.linalg.norm(position[second] - position[source]))
                sister_distance = float(np.linalg.norm(position[second] - position[first]))
                if new_distance > 4.7 or sister_distance > 7.2:
                    rejected["distance"] += 1
                    continue
                first_next = outgoing.get(first, [])
                second_next = outgoing.get(second, [])
                if len(first_next) != 1 or len(second_next) != 1:
                    rejected["continuation"] += 1
                    continue
                next_separation = float(
                    np.linalg.norm(position[first_next[0]] - position[second_next[0]])
                )
                if next_separation - sister_distance < 2.25:
                    rejected["divergence"] += 1
                    continue
                candidates.append((float(edge[2]), -new_distance, edge))
            if candidates:
                probability, _, edge = max(candidates)
                frame_proposals.append((probability, source, int(edge[1]), float(edge[3])))
        frame_cap = max(1, int(round(max(1, len(sources)) * 0.008)))
        added_this_frame = 0
        for probability, source, target, distance in sorted(frame_proposals, reverse=True):
            if len(accepted) >= global_cap or added_this_frame >= frame_cap:
                rejected["cap"] += 1
                continue
            if source in used_sources or target in used_targets or target in incoming:
                rejected["collision"] += 1
                continue
            accepted.append((source, target, probability, distance))
            used_sources.add(source)
            used_targets.add(target)
            added_this_frame += 1
    result = [*links, *accepted]
    out_degree = defaultdict(int)
    in_degree = defaultdict(int)
    for source, target, *_ in result:
        out_degree[int(source)] += 1
        in_degree[int(target)] += 1
    if max(out_degree.values(), default=0) > 2 or max(in_degree.values(), default=0) > 1:
        raise AssertionError("native-guided division graph degree contract failed")
    return result, {
        "accepted": len(accepted),
        "global_cap": global_cap,
        "rejected": dict(sorted(rejected.items())),
        "maximum_out_degree": max(out_degree.values(), default=0),
        "maximum_in_degree": max(in_degree.values(), default=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-min-probability", type=float, default=0.5)
    parser.add_argument("--movie-key", default="target_development")
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    arms = {"registered_hungarian": [], "registered_plus_native_guided_division": []}
    telemetry = []
    manifest = []
    for name in movies:
        cache = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache) as payload:
            coords = payload["coords"].astype(np.float64)
            native_edges = list(zip(
                payload["edge_source"].astype(int).tolist(),
                payload["edge_target"].astype(int).tolist(),
                payload["edge_probability"].astype(float).tolist(),
                payload["edge_distance"].astype(float).tolist(),
            ))
        native_edges = [edge for edge in native_edges if float(edge[2]) > args.native_min_probability]
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        base_links = registered_links(coords, scale)
        candidate_links, stats = add_native_guided_divisions(
            coords, base_links, native_edges, scale
        )
        estimated = (
            GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}
        ).get("estimated_number_of_nodes")
        for arm, links_for_arm in (
            ("registered_hungarian", base_links),
            ("registered_plus_native_guided_division", candidate_links),
        ):
            graph = build_graph(coords, links_for_arm)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = (
                node_recall(graph, dataset.tracks)
                if graph.num_nodes() and graph.num_edges()
                else 0.0
            )
            arms[arm].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
        telemetry.append({"dataset": name, **stats})
        manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_FROZEN_NATIVE_GUIDED_DIVISION_EVALUATION",
        "parameters": {
            "native_candidate_threshold": args.native_min_probability,
            "max_new_um": 4.7,
            "max_existing_um": 7.8,
            "max_sister_um": 7.2,
            "min_divergence_growth_um": 2.25,
            "frame_fraction_cap": 0.008,
            "global_edge_fraction_cap": 0.004,
        },
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
        "selection_warning": "One-shot frozen learned-guided repair; no target tuning.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
