"""Evaluate one frozen, attributed safe-division repair from cached predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_safe_divisions(
    coords: np.ndarray,
    links: list[tuple[int, int, float, float]],
    scale: np.ndarray,
    max_new_um: float = 4.7,
    max_existing_um: float = 7.8,
    max_sister_um: float = 7.2,
    min_divergence_growth_um: float = 2.25,
    frame_fraction_cap: float = 0.008,
    global_edge_fraction_cap: float = 0.004,
) -> tuple[list[tuple[int, int, float, float]], dict]:
    outgoing: dict[int, list[int]] = defaultdict(list)
    incoming = set()
    for source, target, *_ in links:
        outgoing[int(source)].append(int(target))
        incoming.add(int(target))
    times: dict[int, list[int]] = defaultdict(list)
    for node_id, row in enumerate(coords):
        times[int(row[0])].append(node_id)
    position = coords[:, 1:4] * scale
    global_cap = max(1, int(round(max(1, len(links)) * global_edge_fraction_cap)))
    proposals_after_frame_caps = 0
    accepted = []
    used_sources = set()
    used_targets = set()
    rejected = defaultdict(int)
    for timepoint in sorted(times):
        sources = [node for node in times[timepoint] if len(outgoing.get(node, [])) == 1]
        orphans = [node for node in times.get(timepoint + 1, []) if node not in incoming]
        if not sources or not orphans:
            continue
        orphan_tree = cKDTree(position[orphans])
        frame_proposals = []
        for source in sources:
            first = outgoing[source][0]
            if int(coords[first, 0]) != timepoint + 1:
                continue
            existing_distance = float(np.linalg.norm(position[first] - position[source]))
            if existing_distance > max_existing_um:
                continue
            _, nearest_index = orphan_tree.query(position[first])
            second = orphans[int(nearest_index)]
            new_distance = float(np.linalg.norm(position[second] - position[source]))
            sister_distance = float(np.linalg.norm(position[second] - position[first]))
            if new_distance > max_new_um or sister_distance > max_sister_um:
                rejected["distance"] += 1
                continue
            first_successors = outgoing.get(first, [])
            second_successors = outgoing.get(second, [])
            if len(first_successors) != 1 or len(second_successors) != 1:
                rejected["continuation"] += 1
                continue
            first_next, second_next = first_successors[0], second_successors[0]
            if int(coords[first_next, 0]) != timepoint + 2 or int(coords[second_next, 0]) != timepoint + 2:
                rejected["continuation_time"] += 1
                continue
            next_separation = float(np.linalg.norm(position[first_next] - position[second_next]))
            if next_separation - sister_distance < min_divergence_growth_um:
                rejected["divergence"] += 1
                continue
            score = new_distance + 0.15 * sister_distance
            frame_proposals.append((score, source, second, new_distance, sister_distance))
        frame_cap = max(1, int(round(max(1, len(sources)) * frame_fraction_cap)))
        proposals_after_frame_caps += min(len(frame_proposals), frame_cap)
        added_this_frame = 0
        for score, source, target, distance, sister_distance in sorted(frame_proposals):
            if len(accepted) >= global_cap:
                rejected["global_cap"] += 1
                break
            if added_this_frame >= frame_cap:
                break
            if source in used_sources or target in used_targets or target in incoming:
                rejected["collision"] += 1
                continue
            accepted.append((source, target, float(np.exp(-distance / 3.0)), distance))
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
        raise AssertionError("safe-division graph degree contract failed")
    return result, {
        "proposals_after_frame_caps": proposals_after_frame_caps,
        "accepted": len(accepted),
        "global_cap": global_cap,
        "rejected": dict(sorted(rejected.items())),
        "max_out_degree": max(out_degree.values(), default=0),
        "max_in_degree": max(in_degree.values(), default=0),
    }


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
    arms = {"registered_hungarian": [], "registered_plus_safe_division": []}
    telemetry = []
    manifest = []
    for name in movies:
        cache = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        base_links = registered_links(coords, scale)
        candidate_links, stats = add_safe_divisions(coords, base_links, scale)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for arm, links in (("registered_hungarian", base_links), ("registered_plus_safe_division", candidate_links)):
            graph = build_graph(coords, links)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({"dataset": name, **per_sample_metrics(metric, float(estimated), recall)})
        telemetry.append({"dataset": name, **stats})
        manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_FROZEN_SAFE_DIVISION_EVALUATION",
        "attribution": "qrz1201/biohub-public-0-941-repro v1 geometric add_safe_divisions_postlink core",
        "parameters": {"max_new_um": 4.7, "max_existing_um": 7.8, "max_sister_um": 7.2, "min_divergence_growth_um": 2.25, "frame_fraction_cap": 0.008, "global_edge_fraction_cap": 0.004},
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
        "selection_warning": "Frozen one-shot attributed mechanism; do not tune these constants on target results."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
