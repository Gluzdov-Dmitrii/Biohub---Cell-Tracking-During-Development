"""Evaluate a high-confidence external edge bonus on fixed coordinates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from evaluate_registered_model import jsonable, registered_graph


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confidence_gated_graph(coords, edges, scale, probability_floor, bonus_weight, build_graph):
    """Keep the registered linker unchanged except for sparse confident bonuses."""
    coords_array = np.asarray(coords, dtype=float)
    scale_array = np.asarray(scale, dtype=float)
    linked = []
    times = sorted(set(coords_array[:, 0].astype(int))) if len(coords_array) else []
    for timepoint in times[:-1]:
        source_ids = np.flatnonzero(coords_array[:, 0].astype(int) == timepoint)
        target_ids = np.flatnonzero(coords_array[:, 0].astype(int) == timepoint + 1)
        if not len(source_ids) or not len(target_ids):
            continue
        source = coords_array[source_ids, 1:4] * scale_array
        target = coords_array[target_ids, 1:4] * scale_array
        tree = cKDTree(target)
        _, nearest = tree.query(source, k=1)
        displacement = target[np.asarray(nearest, dtype=int)] - source
        shift = np.median(displacement, axis=0)
        residual_to_shift = np.linalg.norm(displacement - shift, axis=1)
        inliers = residual_to_shift <= 4.0
        if int(inliers.sum()) >= 3:
            shift = np.median(displacement[inliers], axis=0)

        residual = np.linalg.norm(
            source[:, None, :] + shift[None, None, :] - target[None, :, :], axis=2
        )
        motion_score = np.exp(-residual / 3.0)
        learned_probability = np.zeros_like(residual)
        source_rows = {int(node_id): row for row, node_id in enumerate(source_ids)}
        target_columns = {int(node_id): column for column, node_id in enumerate(target_ids)}
        for edge_source, edge_target, edge_probability, _ in edges:
            row = source_rows.get(int(edge_source))
            column = target_columns.get(int(edge_target))
            if row is not None and column is not None:
                learned_probability[row, column] = max(
                    learned_probability[row, column], float(edge_probability)
                )

        confident = learned_probability >= probability_floor
        score = motion_score + bonus_weight * learned_probability * confident
        valid = residual < 7.0
        minimum_score = float(np.exp(-7.0 / 3.0))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score, dtype=float)], axis=1
        )
        rows, columns = linear_sum_assignment(augmented)
        for row, column in zip(rows, columns):
            if column >= len(target) or not valid[row, column] or score[row, column] < minimum_score:
                continue
            linked.append((
                int(source_ids[row]), int(target_ids[column]), float(score[row, column]),
                float(np.linalg.norm(source[row] - target[column])),
            ))
    return build_graph(coords, linked)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", required=True)
    parser.add_argument("--probability-floor", type=float, required=True)
    parser.add_argument("--bonus-weight", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.probability_floor < 1.0:
        raise ValueError(args.probability_floor)
    if not 0.0 < args.bonus_weight < 1.0:
        raise ValueError(args.bonus_weight)

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    arms = {"registered_hungarian": [], "external_confidence_gate": []}
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
        graphs = {
            "registered_hungarian": registered_graph(coords, edges, dataset.scale, 0.0, build_graph),
            "external_confidence_gate": confidence_gated_graph(
                coords, edges, dataset.scale, args.probability_floor, args.bonus_weight, build_graph
            ),
        }
        for arm, graph in graphs.items():
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({"dataset": movie, **per_sample_metrics(metric, float(estimated), recall)})
        manifest.append({"dataset": movie, "sha256": sha256(cache_path)})

    result = {
        "status": "PASS_CACHED_EXTERNAL_CONFIDENCE_GATE_EVALUATION",
        "probability_floor": args.probability_floor,
        "bonus_weight": args.bonus_weight,
        "cache_manifest": manifest,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result["summary_by_arm"]), indent=2))


if __name__ == "__main__":
    main()
