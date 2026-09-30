"""Evaluate a two-pass constant-velocity linker on frozen OOF coordinates."""
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


def global_shift(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    tree = cKDTree(target)
    _, nearest = tree.query(source, k=1)
    displacement = target[np.asarray(nearest, dtype=int)] - source
    shift = np.median(displacement, axis=0)
    inliers = np.linalg.norm(displacement - shift, axis=1) <= 4.0
    if int(inliers.sum()) >= 3:
        shift = np.median(displacement[inliers], axis=0)
    return np.asarray(shift, dtype=float)


def velocity_links(
    coords: np.ndarray,
    scale: np.ndarray,
    alpha: float,
    gate_um: float = 7.0,
    motion_scale_um: float = 3.0,
) -> list[tuple[int, int, float, float]]:
    """Blend global frame drift with a predecessor-derived velocity."""
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    linked: list[tuple[int, int, float, float]] = []
    incoming: dict[int, int] = {}
    integer_times = coords[:, 0].astype(int) if len(coords) else np.empty(0, dtype=int)
    times = sorted(set(integer_times.tolist()))
    for timepoint in times[:-1]:
        source_ids = np.flatnonzero(integer_times == timepoint)
        target_ids = np.flatnonzero(integer_times == timepoint + 1)
        if not len(source_ids) or not len(target_ids):
            continue
        source = coords[source_ids, 1:4] * scale
        target = coords[target_ids, 1:4] * scale
        shift = global_shift(source, target)
        predicted = source + shift
        if alpha > 0:
            for local_index, source_id in enumerate(source_ids.tolist()):
                predecessor_id = incoming.get(int(source_id))
                if predecessor_id is None:
                    continue
                previous = coords[predecessor_id, 1:4] * scale
                velocity = source[local_index] - previous
                predicted[local_index] = source[local_index] + (
                    (1.0 - alpha) * shift + alpha * velocity
                )
        residual = np.linalg.norm(predicted[:, None, :] - target[None, :, :], axis=2)
        valid = residual < gate_um
        score = np.exp(-residual / motion_scale_um)
        minimum_score = float(np.exp(-gate_um / motion_scale_um))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score)], axis=1
        )
        rows, columns = linear_sum_assignment(augmented)
        for row, column in zip(rows, columns):
            if column >= len(target) or not valid[row, column] or score[row, column] < minimum_score:
                continue
            source_id = int(source_ids[row])
            target_id = int(target_ids[column])
            linked.append(
                (
                    source_id,
                    target_id,
                    float(score[row, column]),
                    float(np.linalg.norm(source[row] - target[column])),
                )
            )
            incoming[target_id] = source_id
    return linked


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--alpha", type=float, action="append", required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(set(args.alpha)) != len(args.alpha):
        parser.error("alphas must be unique")

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    labels = {alpha: f"velocity_a{alpha:.2f}" for alpha in args.alpha}
    arms = {label: [] for label in labels.values()}
    manifest = []
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        scale = np.asarray(dataset.scale, dtype=float)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for alpha, label in labels.items():
            edges = velocity_links(coords, scale, alpha)
            probabilities = {(int(s), int(t)): float(p) for s, t, p, _ in edges}
            selected_coords, selected_edges, _ = filter_family(
                coords, edges, probabilities, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
    result = {
        "status": "PASS_CACHED_CONSTANT_VELOCITY_LINKER",
        "protocol": "Frozen detector coordinates; two-pass predecessor velocity blended with registered global drift.",
        "parameters": {
            label: {"alpha": alpha, "gate_um": 7.0, "motion_scale_um": 3.0}
            for alpha, label in labels.items()
        },
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "Use nested movie-level selection; full-development ranking is diagnostic only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
