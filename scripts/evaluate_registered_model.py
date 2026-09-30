"""Evaluate one frozen checkpoint with the registered Biohub linker.

This script never tunes on the supplied movies.  Detector threshold, physical
gate and learned tie-break weight are command-line inputs that must be frozen
in the experiment receipt before execution.  It saves sufficient per-movie
statistics and candidate caches so downstream linker comparisons are CPU-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonable(value: object) -> object:
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def registered_graph(coords, edges, scale, probability_weight, build_graph):
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
        gate_um = 7.0
        motion_score = np.exp(-residual / 3.0)
        learned_probability = np.zeros_like(residual)
        if probability_weight:
            source_rows = {int(node_id): row for row, node_id in enumerate(source_ids)}
            target_columns = {int(node_id): column for column, node_id in enumerate(target_ids)}
            for edge_source, edge_target, edge_probability, _ in edges:
                row = source_rows.get(int(edge_source))
                column = target_columns.get(int(edge_target))
                if row is not None and column is not None:
                    learned_probability[row, column] = max(
                        learned_probability[row, column], float(edge_probability)
                    )
        score = probability_weight * learned_probability + (1.0 - probability_weight) * motion_score
        valid = residual < gate_um
        minimum_score = float((1.0 - probability_weight) * np.exp(-gate_um / 3.0))
        cost = np.where(valid, 1.0 - score, 1e6)
        augmented = np.concatenate(
            [cost, np.full((len(source), len(source)), 1.0 - minimum_score, dtype=float)], axis=1
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
    return build_graph(coords, linked)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--secondary-weights", type=Path, default=None)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", default="target_development")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--det-threshold", type=float, default=0.985)
    parser.add_argument("--edge-threshold", type=float, default=0.5)
    parser.add_argument("--weak-probability-weight", type=float, default=0.1)
    parser.add_argument("--unet-batch-size", type=int, default=4)
    parser.add_argument("--secondary-detection-weight", type=float, default=0.5)
    parser.add_argument("--min-candidate-retention", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=314159)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import PredictConfig, build_graph, load_model, predict_video

    movies_payload = json.loads(args.movies_json.read_text(encoding="utf-8"))
    movies = list(movies_payload[args.movie_key])
    if not movies:
        raise RuntimeError("empty movie list")
    for name in movies:
        if not (args.data_dir / name).is_dir() or not (args.data_dir / f"{Path(name).stem}.geff").is_dir():
            raise FileNotFoundError(name)

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.backends.cudnn.benchmark = False
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, window_size, downsample = load_model(args.weights, device)
    model.eval()
    secondary_model = None
    if args.secondary_weights is not None:
        secondary_model, secondary_window_size, secondary_downsample = load_model(
            args.secondary_weights, device
        )
        secondary_model.eval()
        if secondary_window_size != window_size or tuple(secondary_downsample) != tuple(downsample):
            raise ValueError(
                "primary/secondary inference-grid mismatch: "
                f"primary={window_size}/{downsample}, "
                f"secondary={secondary_window_size}/{secondary_downsample}"
            )
    cfg = PredictConfig(
        det_threshold=args.det_threshold,
        det_tta=True,
        pool_kernel_um=3.0,
        edge_activation="softmax",
        threshold=args.edge_threshold,
        use_ilp=True,
    )
    cache_dir = args.output.parent / f"{args.output.stem}_candidate_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    arms = {"registered_hungarian": [], "registered_weak_hungarian": []}
    cache_manifest = []
    detector_fusion_telemetry = []
    for name in movies:
        coords, edges = predict_video(
            model,
            args.data_dir / name,
            device,
            cfg=cfg,
            window_size=window_size,
            unet_batch_size=args.unet_batch_size,
            downsample=downsample,
            secondary_model=secondary_model,
            secondary_detection_weight=args.secondary_detection_weight,
            min_candidate_retention=args.min_candidate_retention,
            detector_fusion_telemetry=detector_fusion_telemetry,
        )
        coordinate_array = np.asarray(coords, dtype=np.float32)
        edge_array = np.asarray(edges, dtype=np.float64).reshape((-1, 4)) if len(edges) else np.empty((0, 4))
        cache_path = cache_dir / f"{Path(name).stem}.npz"
        np.savez_compressed(
            cache_path,
            coords=coordinate_array,
            edge_source=edge_array[:, 0].astype(np.int64),
            edge_target=edge_array[:, 1].astype(np.int64),
            edge_probability=edge_array[:, 2].astype(np.float32),
            edge_distance=edge_array[:, 3].astype(np.float32),
        )
        cache_manifest.append(
            {"dataset": name, "bytes": cache_path.stat().st_size, "sha256": sha256(cache_path)}
        )
        dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        estimated = (GeffMetadata.read(args.data_dir / f"{Path(name).stem}.geff").extra or {}).get(
            "estimated_number_of_nodes"
        )
        for arm, weight in (
            ("registered_hungarian", 0.0),
            ("registered_weak_hungarian", args.weak_probability_weight),
        ):
            graph = registered_graph(coords, edges, dataset.scale, weight, build_graph)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            row = {
                "dataset": name,
                **per_sample_metrics(metric, float(estimated) if estimated is not None else float("nan"), recall),
            }
            arms[arm].append(row)
        print(json.dumps(jsonable({"dataset": name, "arms": {key: value[-1] for key, value in arms.items()}})), flush=True)

    result = {
        "status": "PASS_FROZEN_REGISTERED_MODEL_EVALUATION",
        "weights": str(args.weights),
        "weights_sha256": sha256(args.weights),
        "secondary_weights": str(args.secondary_weights) if args.secondary_weights else None,
        "secondary_weights_sha256": sha256(args.secondary_weights) if args.secondary_weights else None,
        "secondary_detection_weight": args.secondary_detection_weight if args.secondary_weights else None,
        "min_candidate_retention": args.min_candidate_retention if args.secondary_weights else None,
        "data_dir": str(args.data_dir),
        "movies_source": str(args.movies_json),
        "movies_source_sha256": sha256(args.movies_json),
        "movie_key": args.movie_key,
        "movies": movies,
        "det_threshold": args.det_threshold,
        "registered_gate_um": 7.0,
        "registered_motion_scale_um": 3.0,
        "weak_probability_weight": args.weak_probability_weight,
        "per_movie_by_arm": arms,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in arms.items()},
        "candidate_cache_manifest": cache_manifest,
        "detector_fusion_telemetry": detector_fusion_telemetry,
        "detector_fusion_summary": {
            "frames": len(detector_fusion_telemetry),
            "fallback_frames": sum(
                int(row["used_primary_fallback"]) for row in detector_fusion_telemetry
            ),
            "primary_candidates": sum(
                int(row["primary_candidates"]) for row in detector_fusion_telemetry
            ),
            "fused_candidates": sum(
                int(row["fused_candidates"]) for row in detector_fusion_telemetry
            ),
            "selected_candidates": sum(
                int(row["selected_candidates"]) for row in detector_fusion_telemetry
            ),
        },
        "selection_warning": "No parameter is selected on these movies; values must be frozen in the experiment receipt before execution.",
        "edge_threshold": args.edge_threshold,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result["summary_by_arm"]), indent=2))


if __name__ == "__main__":
    main()
