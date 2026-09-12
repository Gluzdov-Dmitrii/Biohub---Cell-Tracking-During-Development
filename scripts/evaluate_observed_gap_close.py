"""Evaluate the attributed QRZ observed-node single-frame gap repair.

The public implementation can also synthesize a missing detection and consult
DeepCenter.  This isolated ablation deliberately admits only an already
observed, otherwise isolated middle-frame node, so it needs no image/model
dependency and cannot fabricate competition detections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from evaluate_coordinate_consensus import registered_links


GAP_CLOSE_UM = 5.0
GAP_CLOSE_REUSE_UM = 3.2
GAP_DENSITY_REFERENCE_UM = 6.5
GAP_DENSITY_GAIN = 0.040
GAP_DENSITY_MAX_STEP_DELTA_UM = 0.125
GAP_DENSITY_NEIGHBORS = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frame_spacing(position_um: np.ndarray, ids: list[int]) -> dict[int, float]:
    if len(ids) <= 1:
        return {node_id: GAP_DENSITY_REFERENCE_UM for node_id in ids}
    points = position_um[np.asarray(ids, dtype=int)]
    k = min(len(ids), max(2, GAP_DENSITY_NEIGHBORS + 1))
    distances, _ = cKDTree(points).query(points, k=k)
    if distances.ndim == 1:
        distances = distances[:, None]
    result = {}
    for index, node_id in enumerate(ids):
        neighbours = distances[index, 1:]
        neighbours = neighbours[np.isfinite(neighbours)]
        result[node_id] = (
            float(np.median(neighbours))
            if neighbours.size
            else GAP_DENSITY_REFERENCE_UM
        )
    return result


def close_observed_single_frame_gaps(
    coords: np.ndarray,
    edges: list[tuple[int, int, float, float]],
    scale: np.ndarray,
    *,
    adaptive: bool,
) -> tuple[list[tuple[int, int, float, float]], dict[str, int | float]]:
    """Reproduce the QRZ gap assignment while forbidding synthetic nodes."""
    outgoing = {int(edge[0]) for edge in edges}
    incoming = {int(edge[1]) for edge in edges}
    incident = outgoing | incoming
    by_time: dict[int, list[int]] = defaultdict(list)
    for node_id, row in enumerate(coords):
        by_time[int(row[0])].append(node_id)
    ends = {
        t: [node_id for node_id in ids if node_id not in outgoing]
        for t, ids in by_time.items()
    }
    starts = {
        t: [node_id for node_id in ids if node_id not in incoming]
        for t, ids in by_time.items()
    }
    isolated = {
        t: [node_id for node_id in ids if node_id not in incident]
        for t, ids in by_time.items()
    }
    position_um = coords[:, 1:4].astype(np.float64) * np.asarray(scale, dtype=np.float64)
    spacing = {t: _frame_spacing(position_um, ids) for t, ids in by_time.items()}
    used_starts: set[int] = set()
    used_middle: set[int] = set()
    added: list[tuple[int, int, float, float]] = []
    stats: dict[str, int | float] = {
        "endpoint_pairs_allowed": 0,
        "endpoint_pairs_selected": 0,
        "observed_middle_reused": 0,
        "rejected_no_observed_middle": 0,
        "density_candidates_expanded": 0,
        "density_candidates_restricted": 0,
        "density_selected_outside_fixed": 0,
        "added_edges": 0,
    }
    fixed_threshold = GAP_CLOSE_UM * 2.0
    for t in sorted(by_time):
        end_ids = ends.get(t, [])
        start_ids = [node_id for node_id in starts.get(t + 2, []) if node_id not in used_starts]
        if not end_ids or not start_ids:
            continue
        end_pos = position_um[np.asarray(end_ids, dtype=int)]
        start_pos = position_um[np.asarray(start_ids, dtype=int)]
        distance = np.linalg.norm(end_pos[:, None, :] - start_pos[None, :, :], axis=2)
        threshold = np.full_like(distance, fixed_threshold)
        if adaptive:
            for i, source_id in enumerate(end_ids):
                for j, target_id in enumerate(start_ids):
                    local_spacing = 0.5 * (
                        spacing[t].get(source_id, GAP_DENSITY_REFERENCE_UM)
                        + spacing[t + 2].get(target_id, GAP_DENSITY_REFERENCE_UM)
                    )
                    delta = float(np.clip(
                        GAP_DENSITY_GAIN * (local_spacing - GAP_DENSITY_REFERENCE_UM),
                        -GAP_DENSITY_MAX_STEP_DELTA_UM,
                        GAP_DENSITY_MAX_STEP_DELTA_UM,
                    ))
                    threshold[i, j] += 2.0 * delta
        fixed_allowed = distance <= fixed_threshold
        allowed = distance <= threshold
        stats["density_candidates_expanded"] += int((allowed & ~fixed_allowed).sum())
        stats["density_candidates_restricted"] += int((fixed_allowed & ~allowed).sum())
        stats["endpoint_pairs_allowed"] += int(allowed.sum())
        if not allowed.any():
            continue
        big = float(np.max(threshold)) * 1000.0 + 1.0
        rows, columns = linear_sum_assignment(np.where(allowed, distance, big))
        for row, column in zip(rows, columns):
            if not allowed[row, column]:
                continue
            source_id = end_ids[int(row)]
            target_id = start_ids[int(column)]
            if source_id in outgoing or target_id in used_starts:
                continue
            midpoint = 0.5 * (position_um[source_id] + position_um[target_id])
            middle_ids = [
                node_id for node_id in isolated.get(t + 1, [])
                if node_id not in used_middle
            ]
            if not middle_ids:
                stats["rejected_no_observed_middle"] += 1
                continue
            middle_distance = np.linalg.norm(
                position_um[np.asarray(middle_ids, dtype=int)] - midpoint[None, :], axis=1
            )
            best = int(np.argmin(middle_distance))
            if float(middle_distance[best]) > GAP_CLOSE_REUSE_UM:
                stats["rejected_no_observed_middle"] += 1
                continue
            middle_id = middle_ids[best]
            first_distance = float(np.linalg.norm(position_um[source_id] - position_um[middle_id]))
            second_distance = float(np.linalg.norm(position_um[middle_id] - position_um[target_id]))
            added.extend([
                (source_id, middle_id, 0.0, first_distance),
                (middle_id, target_id, 0.0, second_distance),
            ])
            outgoing.update((source_id, middle_id))
            incoming.update((middle_id, target_id))
            used_middle.add(middle_id)
            used_starts.add(target_id)
            stats["endpoint_pairs_selected"] += 1
            stats["observed_middle_reused"] += 1
            stats["added_edges"] += 2
            if not fixed_allowed[row, column]:
                stats["density_selected_outside_fixed"] += 1
    return [*edges, *added], stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", default="source_checkpoint_validation")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    arm_names = ("registered_hungarian", "fixed_observed_gap", "adaptive_observed_gap")
    arms = {name: [] for name in arm_names}
    telemetry = []
    manifest = []
    for name in movies:
        cache = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=np.float64)
        base = registered_links(coords, scale)
        fixed, fixed_stats = close_observed_single_frame_gaps(coords, base, scale, adaptive=False)
        adaptive, adaptive_stats = close_observed_single_frame_gaps(coords, base, scale, adaptive=True)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for arm, links in zip(arm_names, (base, fixed, adaptive)):
            graph = build_graph(coords, links)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append({"dataset": name, **per_sample_metrics(metric, float(estimated), recall)})
        telemetry.append({"dataset": name, "fixed": fixed_stats, "adaptive": adaptive_stats})
        manifest.append({"path": str(cache), "sha256": sha256(cache)})
    result = {
        "status": "PASS_FROZEN_OBSERVED_GAP_SOURCE_EVALUATION",
        "mechanism_source": "qrz1201/biohub-public-0-941-repro v1, observed-node submechanism",
        "parameters": {
            "gap_frames": 1,
            "gap_close_um_per_step": GAP_CLOSE_UM,
            "reuse_existing_um": GAP_CLOSE_REUSE_UM,
            "density_reference_um": GAP_DENSITY_REFERENCE_UM,
            "density_gain": GAP_DENSITY_GAIN,
            "density_max_step_delta_um": GAP_DENSITY_MAX_STEP_DELTA_UM,
            "density_neighbors": GAP_DENSITY_NEIGHBORS,
            "synthetic_nodes": False,
            "deepcenter": False,
        },
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
