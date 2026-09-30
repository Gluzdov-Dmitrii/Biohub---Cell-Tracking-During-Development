"""Evaluate one frozen local-flow policy plus its exact translation control."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from evaluate_cached_local_flow_linker import local_flow_links
from evaluate_coordinate_consensus import registered_links


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--neighbours", type=int, choices=(16, 32), required=True)
    parser.add_argument("--alpha", type=float, choices=(0.25, 0.5), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    from evaluate_cached_short_track_family import filter_family
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    arms = {"translation": [], "fixed_local_flow": []}
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
        control_edges = registered_links(coords, physical_scale)
        candidate_edges, frame_telemetry = local_flow_links(
            coords, physical_scale, args.neighbours, args.alpha
        )
        for label, edges in (("translation", control_edges), ("fixed_local_flow", candidate_edges)):
            selected_coords, selected_edges, _ = filter_family(
                coords, edges, {}, args.minimum_length
            )
            graph = build_graph(selected_coords, selected_edges)
            metric = evaluate(graph, dataset.tracks, scale=dataset.scale)
            recall = node_recall(graph, dataset.tracks) if graph.num_nodes() and graph.num_edges() else 0.0
            arms[label].append(
                {"dataset": name, **per_sample_metrics(metric, float(estimated), recall)}
            )
        telemetry.append({"dataset": name, "frames": frame_telemetry})
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})
        print(json.dumps({"dataset": name, "complete": True}), flush=True)

    result = {
        "status": "PASS_CACHED_FIXED_LOCAL_FLOW",
        "protocol": "EXP201 policy frozen before untouched confirmation inference.",
        "parameters": {
            "neighbours": args.neighbours,
            "alpha": args.alpha,
            "fit_radius_um": 4.0,
            "maximum_correction_um": 2.0,
            "gate_um": 7.0,
            "motion_scale_um": 3.0,
            "minimum_component_nodes": args.minimum_length,
        },
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "telemetry": telemetry,
        "per_movie_by_arm": arms,
        "summary_by_arm": {label: summarise(rows) for label, rows in arms.items()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "movies": len(movies)}))


if __name__ == "__main__":
    main()
