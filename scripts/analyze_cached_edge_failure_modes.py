"""Decompose official edge errors on cached full-movie OOF predictions.

The official evaluator is the authority for node matching and TP/FP/FN.  This
script only classifies those counts after ``evaluate`` has written its exact
matching onto the prediction graph.  It therefore does not substitute a local
matching implementation for the competition metric.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decompose_edges(
    pred_edges: list[tuple[int, int]],
    gt_edges: list[tuple[int, int]],
    pred_to_gt: dict[int, int],
    gt_to_pred: dict[int, int],
) -> dict[str, int]:
    """Partition official edge FNs and valid predicted non-TP edges."""
    gt_edge_set = set(gt_edges)
    pred_edge_set = set(pred_edges)
    gt_out: dict[int, set[int]] = {}
    gt_in: dict[int, set[int]] = {}
    for source, target in gt_edge_set:
        gt_out.setdefault(source, set()).add(target)
        gt_in.setdefault(target, set()).add(source)

    result = {
        "edge_tp": 0,
        "fn_missing_both_endpoints": 0,
        "fn_missing_source_endpoint": 0,
        "fn_missing_target_endpoint": 0,
        "fn_both_endpoints_matched_link_missing": 0,
        "fp_both_endpoints_matched_wrong_association": 0,
        "fp_source_anchor_target_unmatched": 0,
        "fp_target_anchor_source_unmatched": 0,
        "ignored_pred_edges": 0,
    }
    for source, target in gt_edge_set:
        pred_source = gt_to_pred.get(source)
        pred_target = gt_to_pred.get(target)
        if pred_source is None and pred_target is None:
            result["fn_missing_both_endpoints"] += 1
        elif pred_source is None:
            result["fn_missing_source_endpoint"] += 1
        elif pred_target is None:
            result["fn_missing_target_endpoint"] += 1
        elif (pred_source, pred_target) in pred_edge_set:
            result["edge_tp"] += 1
        else:
            result["fn_both_endpoints_matched_link_missing"] += 1

    for pred_source, pred_target in pred_edge_set:
        gt_source = pred_to_gt.get(pred_source)
        gt_target = pred_to_gt.get(pred_target)
        if (
            gt_source is not None
            and gt_target is not None
            and (gt_source, gt_target) in gt_edge_set
        ):
            continue
        source_anchor = gt_source is not None and bool(gt_out.get(gt_source))
        target_anchor = gt_target is not None and bool(gt_in.get(gt_target))
        if not source_anchor and not target_anchor:
            result["ignored_pred_edges"] += 1
        elif gt_source is not None and gt_target is not None:
            result["fp_both_endpoints_matched_wrong_association"] += 1
        elif source_anchor:
            result["fp_source_anchor_target_unmatched"] += 1
        else:
            result["fp_target_anchor_source_unmatched"] += 1
    return result


def summarize(rows: list[dict]) -> dict:
    count_keys = [key for key in rows[0] if key != "dataset"]
    totals = {key: sum(int(row[key]) for row in rows) for key in count_keys}
    endpoint_fn = sum(
        totals[key]
        for key in (
            "fn_missing_both_endpoints",
            "fn_missing_source_endpoint",
            "fn_missing_target_endpoint",
        )
    )
    association_fn = totals["fn_both_endpoints_matched_link_missing"]
    total_fn = endpoint_fn + association_fn
    totals.update(
        {
            "edge_fn": total_fn,
            "edge_fp": totals["fp_both_endpoints_matched_wrong_association"]
            + totals["fp_source_anchor_target_unmatched"]
            + totals["fp_target_anchor_source_unmatched"],
            "endpoint_limited_fn": endpoint_fn,
            "association_limited_fn": association_fn,
            "endpoint_limited_fn_fraction": endpoint_fn / total_fn if total_fn else math.nan,
            "association_limited_fn_fraction": association_fn / total_fn if total_fn else math.nan,
        }
    )
    return totals


def graph_edges(graph, td) -> list[tuple[int, int]]:
    attrs = graph.edge_attrs(
        attr_keys=[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE, td.DEFAULT_ATTR_KEYS.EDGE_TARGET]
    )
    return [
        (int(row[td.DEFAULT_ATTR_KEYS.EDGE_SOURCE]), int(row[td.DEFAULT_ATTR_KEYS.EDGE_TARGET]))
        for row in attrs.iter_rows(named=True)
    ]


def matched_maps(graph, td) -> tuple[dict[int, int], dict[int, int]]:
    attrs = graph.node_attrs(
        attr_keys=[td.DEFAULT_ATTR_KEYS.NODE_ID, td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID]
    )
    pred_to_gt: dict[int, int] = {}
    for row in attrs.iter_rows(named=True):
        matched = row[td.DEFAULT_ATTR_KEYS.MATCHED_NODE_ID]
        if matched is None or int(matched) == -1:
            continue
        pred_to_gt[int(row[td.DEFAULT_ATTR_KEYS.NODE_ID])] = int(matched)
    gt_to_pred = {gt: pred for pred, gt in pred_to_gt.items()}
    if len(gt_to_pred) != len(pred_to_gt):
        raise ValueError("official matching is not one-to-one")
    return pred_to_gt, gt_to_pred


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--cache-mode", choices=("relink", "selected"), required=True)
    parser.add_argument("--minimum-length", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.minimum_length < 1:
        parser.error("minimum length must be positive")

    sys.path.insert(0, str(args.repo / "src"))
    sys.path.insert(0, str(args.repo / "scripts"))
    # Keep production-only dependencies lazy so the pure decomposition can be
    # unit-tested without the remote tracking environment.
    from evaluate_cached_short_track_family import edge_probability_lookup, filter_family
    from evaluate_coordinate_consensus import registered_links
    import tracksdata as td
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate
    from predict_unet_transformer import build_graph

    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))["target_development"]
    rows: list[dict] = []
    manifest: list[dict] = []
    for name in movies:
        cache_path = args.cache_dir / f"{Path(name).stem}.npz"
        with np.load(cache_path) as payload:
            coords = payload["coords"].astype(np.float64)
            probabilities = edge_probability_lookup(payload)
            if args.cache_mode == "relink":
                dataset_for_scale = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
                edges = registered_links(coords, np.asarray(dataset_for_scale.scale, dtype=float))
                dataset = dataset_for_scale
            else:
                edges = list(
                    zip(
                        payload["edge_source"].astype(int).tolist(),
                        payload["edge_target"].astype(int).tolist(),
                        payload["edge_probability"].astype(float).tolist(),
                        payload["edge_distance"].astype(float).tolist(),
                    )
                )
                dataset = open_dataset(args.data_dir / name, require_tracks=True, load_image=False)
        selected_coords, selected_edges, _ = filter_family(
            coords, edges, probabilities, args.minimum_length
        )
        graph = build_graph(selected_coords, selected_edges)
        official = evaluate(graph, dataset.tracks, scale=dataset.scale)
        pred_to_gt, gt_to_pred = matched_maps(graph, td)
        row = {
            "dataset": name,
            **decompose_edges(
                graph_edges(graph, td),
                graph_edges(dataset.tracks, td),
                pred_to_gt,
                gt_to_pred,
            ),
        }
        endpoint_fn = sum(
            row[key]
            for key in (
                "fn_missing_both_endpoints",
                "fn_missing_source_endpoint",
                "fn_missing_target_endpoint",
            )
        )
        classified_fp = sum(
            row[key]
            for key in (
                "fp_both_endpoints_matched_wrong_association",
                "fp_source_anchor_target_unmatched",
                "fp_target_anchor_source_unmatched",
            )
        )
        if row["edge_tp"] != official.edge_tp:
            raise ValueError(f"{name}: TP decomposition disagrees with official evaluator")
        if endpoint_fn + row["fn_both_endpoints_matched_link_missing"] != official.edge_fn:
            raise ValueError(f"{name}: FN decomposition disagrees with official evaluator")
        if classified_fp != official.edge_fp:
            raise ValueError(f"{name}: FP decomposition disagrees with official evaluator")
        rows.append(row)
        manifest.append({"path": str(cache_path), "sha256": sha256(cache_path)})

    result = {
        "status": "PASS_OFFICIAL_MATCH_EDGE_FAILURE_DECOMPOSITION",
        "protocol": "Official evaluator performs matching first; decomposition is asserted against its exact TP/FP/FN counts.",
        "cache_mode": args.cache_mode,
        "minimum_length": args.minimum_length,
        "movies_source_sha256": sha256(args.movies_json),
        "input_cache_manifest": manifest,
        "per_movie": rows,
        "pooled": summarize(rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["pooled"], indent=2))


if __name__ == "__main__":
    main()
