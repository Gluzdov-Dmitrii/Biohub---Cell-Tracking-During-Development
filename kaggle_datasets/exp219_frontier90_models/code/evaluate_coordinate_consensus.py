"""Evaluate a frozen two-model coordinate consensus without neural inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registered_links(coords: np.ndarray, scale: np.ndarray) -> list[tuple[int, int, float, float]]:
    linked = []
    times = sorted(set(coords[:, 0].astype(int))) if len(coords) else []
    for timepoint in times[:-1]:
        source_ids = np.flatnonzero(coords[:, 0].astype(int) == timepoint)
        target_ids = np.flatnonzero(coords[:, 0].astype(int) == timepoint + 1)
        if not len(source_ids) or not len(target_ids):
            continue
        source = coords[source_ids, 1:4] * scale
        target = coords[target_ids, 1:4] * scale
        tree = cKDTree(target)
        _, nearest = tree.query(source, k=1)
        displacement = target[np.asarray(nearest, dtype=int)] - source
        shift = np.median(displacement, axis=0)
        inliers = np.linalg.norm(displacement - shift, axis=1) <= 4.0
        if int(inliers.sum()) >= 3:
            shift = np.median(displacement[inliers], axis=0)
        residual = np.linalg.norm(
            source[:, None, :] + shift[None, None, :] - target[None, :, :], axis=2
        )
        valid = residual < 7.0
        score = np.exp(-residual / 3.0)
        minimum_score = float(np.exp(-7.0 / 3.0))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score)], axis=1
        )
        rows, columns = linear_sum_assignment(augmented)
        for row, column in zip(rows, columns):
            if column >= len(target) or not valid[row, column] or score[row, column] < minimum_score:
                continue
            linked.append(
                (
                    int(source_ids[row]),
                    int(target_ids[column]),
                    float(score[row, column]),
                    float(np.linalg.norm(source[row] - target[column])),
                )
            )
    return linked


def blend_base_with_donor(
    base: np.ndarray, donor: np.ndarray, scale: np.ndarray, radius_um: float, alpha: float
) -> tuple[np.ndarray, int, list[float]]:
    blended = base.copy()
    matched = 0
    distances = []
    for timepoint in sorted(set(base[:, 0].astype(int))):
        base_ids = np.flatnonzero(base[:, 0].astype(int) == timepoint)
        donor_ids = np.flatnonzero(donor[:, 0].astype(int) == timepoint)
        if not len(base_ids) or not len(donor_ids):
            continue
        base_physical = base[base_ids, 1:4] * scale
        donor_physical = donor[donor_ids, 1:4] * scale
        distance, base_to_donor = cKDTree(donor_physical).query(base_physical, k=1)
        _, donor_to_base = cKDTree(base_physical).query(donor_physical, k=1)
        for local_base, (dist, local_donor) in enumerate(zip(distance, base_to_donor)):
            local_donor = int(local_donor)
            if dist >= radius_um or int(donor_to_base[local_donor]) != local_base:
                continue
            base_index = int(base_ids[local_base])
            donor_index = int(donor_ids[local_donor])
            blended[base_index, 1:4] = (
                (1.0 - alpha) * base[base_index, 1:4] + alpha * donor[donor_index, 1:4]
            )
            matched += 1
            distances.append(float(dist))
    return blended, matched, distances


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--scratch-cache", type=Path, required=True)
    parser.add_argument("--zebrahub-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--radius-um", type=float, default=2.0)
    parser.add_argument("--alpha", type=float, default=0.5)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    arms = {"scratch_topology_consensus_coords": [], "zebrahub_topology_consensus_coords": []}
    matches = []
    input_manifest = []
    for name in movies:
        stem = Path(name).stem
        scratch_path = args.scratch_cache / f"{stem}.npz"
        zebra_path = args.zebrahub_cache / f"{stem}.npz"
        with np.load(scratch_path) as payload:
            scratch = payload["coords"].astype(np.float64)
        with np.load(zebra_path) as payload:
            zebra = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=np.float64)
        estimated = (GeffMetadata.read(args.data_dir / f"{stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        input_manifest.extend(
            [
                {"path": str(scratch_path), "sha256": sha256(scratch_path)},
                {"path": str(zebra_path), "sha256": sha256(zebra_path)},
            ]
        )
        movie_match = {"dataset": name}
        for arm, base, donor in (
            ("scratch_topology_consensus_coords", scratch, zebra),
            ("zebrahub_topology_consensus_coords", zebra, scratch),
        ):
            links = registered_links(base, scale)
            blended, count, distances = blend_base_with_donor(
                base, donor, scale, args.radius_um, args.alpha
            )
            graph = build_graph(blended, links)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[arm].append(
                {
                    "dataset": name,
                    **per_sample_metrics(metric, float(estimated), recall),
                }
            )
            movie_match[arm] = {
                "base_nodes": int(len(base)),
                "matched_nodes": count,
                "match_fraction": count / len(base) if len(base) else 0.0,
                "mean_disagreement_um": float(np.mean(distances)) if distances else None,
                "p95_disagreement_um": float(np.quantile(distances, 0.95)) if distances else None,
                "preserved_links": len(links),
            }
        matches.append(movie_match)

    result = {
        "status": "PASS_FIXED_COORDINATE_CONSENSUS",
        "radius_um": args.radius_um,
        "alpha": args.alpha,
        "topology": "registered links computed on each base before coordinate blending and preserved exactly",
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": input_manifest,
        "match_diagnostics": matches,
        "per_movie_by_arm": arms,
        "summary_by_arm": {name: summarise(rows) for name, rows in arms.items()},
        "selection_warning": "One pre-registered alpha/radius mechanism; do not tune on these scores.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
