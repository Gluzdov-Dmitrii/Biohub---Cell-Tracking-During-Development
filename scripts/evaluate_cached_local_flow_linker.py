"""Evaluate a smooth local residual-flow linker on frozen OOF coordinates."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

from evaluate_cached_coherent_motion_linker import mutual_pairs, translation_shift
from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_residual_field(
    source: np.ndarray,
    target: np.ndarray,
    shift: np.ndarray,
    neighbours: int,
    max_correction_um: float = 2.0,
) -> tuple[np.ndarray, int]:
    if neighbours < 1:
        raise ValueError("neighbours must be positive")
    source_ids, target_ids = mutual_pairs(source, target, shift)
    if len(source_ids) < 4:
        return np.zeros_like(source), int(len(source_ids))
    paired_source = source[source_ids]
    residual = target[target_ids] - paired_source - shift
    count = min(neighbours, len(paired_source))
    _, indices = cKDTree(paired_source).query(source, k=count)
    if count == 1:
        indices = np.asarray(indices, dtype=int)[:, None]
    correction = np.median(residual[np.asarray(indices, dtype=int)], axis=1)
    norm = np.linalg.norm(correction, axis=1)
    shrink = np.minimum(1.0, max_correction_um / np.maximum(norm, 1e-12))
    return correction * shrink[:, None], int(len(source_ids))


def local_flow_links(
    coords: np.ndarray,
    scale_xyz: np.ndarray,
    neighbours: int,
    alpha: float,
    gate_um: float = 7.0,
    motion_scale_um: float = 3.0,
) -> tuple[list[tuple[int, int, float, float]], list[dict]]:
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    linked: list[tuple[int, int, float, float]] = []
    telemetry: list[dict] = []
    integer_times = coords[:, 0].astype(int) if len(coords) else np.empty(0, dtype=int)
    times = sorted(set(integer_times.tolist()))
    for timepoint in times[:-1]:
        source_ids = np.flatnonzero(integer_times == timepoint)
        target_ids = np.flatnonzero(integer_times == timepoint + 1)
        if not len(source_ids) or not len(target_ids):
            continue
        source = coords[source_ids, 1:4] * scale_xyz
        target = coords[target_ids, 1:4] * scale_xyz
        shift = translation_shift(source, target)
        correction, pair_count = local_residual_field(source, target, shift, neighbours)
        predicted = source + shift + alpha * correction
        residual = np.linalg.norm(predicted[:, None, :] - target[None, :, :], axis=2)
        valid = residual < gate_um
        score = np.exp(-residual / motion_scale_um)
        minimum_score = float(np.exp(-gate_um / motion_scale_um))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score)], axis=1
        )
        rows, columns = linear_sum_assignment(augmented)
        accepted = 0
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
            accepted += 1
        telemetry.append(
            {
                "time": int(timepoint),
                "mutual_pairs": pair_count,
                "median_correction_um": float(np.median(np.linalg.norm(correction, axis=1))),
                "p95_correction_um": float(np.quantile(np.linalg.norm(correction, axis=1), 0.95)),
                "accepted_edges": accepted,
            }
        )
    return linked, telemetry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    variants = {
        "translation": None,
        "flow_k16_a025": (16, 0.25),
        "flow_k16_a050": (16, 0.50),
        "flow_k32_a025": (32, 0.25),
        "flow_k32_a050": (32, 0.50),
    }
    arms = {label: [] for label in variants}
    telemetry = []
    manifest = []
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        physical_scale = np.asarray(dataset.scale, dtype=float)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        movie_telemetry = {"dataset": name, "variants": {}}
        for label, configuration in variants.items():
            if configuration is None:
                edges = registered_links(coords, physical_scale)
                frame_telemetry = []
            else:
                edges, frame_telemetry = local_flow_links(
                    coords, physical_scale, configuration[0], configuration[1]
                )
            selected_coords, selected_edges, filter_stats = filter_family(
                coords, edges, {}, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
            movie_telemetry["variants"][label] = {
                "filter": filter_stats,
                "frames": frame_telemetry,
            }
        telemetry.append(movie_telemetry)
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "complete": True}), flush=True)

    result = {
        "status": "PASS_CACHED_LOCAL_FLOW_LINKER",
        "protocol": "Frozen detector coordinates; local median residual field from inference-only mutual nearest pseudo-correspondences.",
        "parameters": {
            "fit_radius_um": 4.0,
            "maximum_correction_um": 2.0,
            "gate_um": 7.0,
            "motion_scale_um": 3.0,
            "variants": variants,
        },
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
        "selection_warning": "Use nested movie-level selection; full-development ranking is diagnostic only.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
