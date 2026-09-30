"""Decompose official edge errors on frozen submission CSV graphs.

This is the submission-CSV counterpart to ``analyze_cached_edge_failure_modes``.
It verifies input hashes from a recorded metrics file, rebuilds each movie graph,
lets the official evaluator perform node matching, then partitions edge errors
without changing predictions or choosing thresholds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_graphs(path: Path) -> dict[str, dict[str, Any]]:
    graphs: dict[str, dict[str, Any]] = {}
    ids: set[int] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path}: unexpected columns {reader.fieldnames}")
        for row in reader:
            row_id = int(row["id"])
            if row_id in ids:
                raise ValueError(f"{path}: duplicate id {row_id}")
            ids.add(row_id)
            graph = graphs.setdefault(row["dataset"], {"nodes": {}, "edges": []})
            if row["row_type"] == "node":
                node_id = int(row["node_id"])
                if node_id in graph["nodes"] or node_id < 0:
                    raise ValueError(f"{path}: invalid node id {node_id} in {row['dataset']}")
                point = tuple(float(row[key]) for key in ("z", "y", "x"))
                if not all(math.isfinite(value) and value >= 0 for value in point):
                    raise ValueError(f"{path}: invalid coordinates for node {node_id}")
                t = int(row["t"])
                if t < 0 or int(row["source_id"]) != -1 or int(row["target_id"]) != -1:
                    raise ValueError(f"{path}: invalid node row for node {node_id}")
                graph["nodes"][node_id] = (t, *point)
            elif row["row_type"] == "edge":
                if any(float(row[key]) != -1 for key in ("node_id", "t", "z", "y", "x")):
                    raise ValueError(f"{path}: invalid edge sentinel columns")
                graph["edges"].append((int(row["source_id"]), int(row["target_id"])))
            else:
                raise ValueError(f"{path}: unexpected row_type {row['row_type']}")
    for dataset, graph in graphs.items():
        edges = graph["edges"]
        nodes = graph["nodes"]
        if len(edges) != len(set(edges)):
            raise ValueError(f"{path}: duplicate edge in {dataset}")
        incoming: dict[int, int] = {}
        outgoing: dict[int, int] = {}
        for source, target in edges:
            if source not in nodes or target not in nodes:
                raise ValueError(f"{path}: edge references missing node in {dataset}")
            if nodes[target][0] != nodes[source][0] + 1:
                raise ValueError(f"{path}: non-consecutive edge in {dataset}")
            incoming[target] = incoming.get(target, 0) + 1
            outgoing[source] = outgoing.get(source, 0) + 1
        if max(incoming.values(), default=0) > 1 or max(outgoing.values(), default=0) > 2:
            raise ValueError(f"{path}: graph degree violation in {dataset}")
    return graphs


def edge_fn_counts(row: dict[str, int]) -> tuple[int, int, int]:
    endpoint = (
        row["fn_missing_both_endpoints"]
        + row["fn_missing_source_endpoint"]
        + row["fn_missing_target_endpoint"]
    )
    association = row["fn_both_endpoints_matched_link_missing"]
    return endpoint, association, endpoint + association


def classified_edge_fp(row: dict[str, int]) -> int:
    return (
        row["fp_both_endpoints_matched_wrong_association"]
        + row["fp_source_anchor_target_unmatched"]
        + row["fp_target_anchor_source_unmatched"]
    )


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    endpoint, association, total_fn = edge_fn_counts(row)
    edge_fp = classified_edge_fp(row)
    return {
        **row,
        "edge_fn": total_fn,
        "edge_fp": edge_fp,
        "endpoint_limited_fn": endpoint,
        "association_limited_fn": association,
        "endpoint_limited_fn_fraction": endpoint / total_fn if total_fn else math.nan,
        "association_limited_fn_fraction": association / total_fn if total_fn else math.nan,
    }


def validate_against_recorded_metrics(
    arm: str,
    dataset: str,
    row: dict[str, Any],
    recorded_lookup: dict[str, dict[str, Any]],
) -> None:
    recorded = recorded_lookup.get(dataset)
    if recorded is None:
        raise ValueError(f"{arm}/{dataset}: missing recorded metrics row")
    endpoint, association, edge_fn = edge_fn_counts(row)
    checks = {
        "edge_tp": row["edge_tp"],
        "edge_fn": edge_fn,
        "edge_fp": classified_edge_fp(row),
    }
    for key, value in checks.items():
        if int(recorded[key]) != int(value):
            raise ValueError(
                f"{arm}/{dataset}: decomposition {key}={value} disagrees with recorded {recorded[key]}"
            )
    if endpoint + association != int(recorded["edge_fn"]):
        raise ValueError(f"{arm}/{dataset}: FN partition mismatch")


def load_helpers(repo: Path):
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts"), str(repo)]
    try:
        from analyze_cached_edge_failure_modes import (  # type: ignore
            decompose_edges,
            graph_edges,
            matched_maps,
            summarize,
        )
    except ModuleNotFoundError:
        from scripts.analyze_cached_edge_failure_modes import (  # type: ignore
            decompose_edges,
            graph_edges,
            matched_maps,
            summarize,
        )
    import tracksdata as td  # type: ignore
    from biohub_tracking.io import open_dataset  # type: ignore
    from biohub_tracking.metrics import evaluate  # type: ignore
    from predict_unet_transformer import build_graph  # type: ignore

    return decompose_edges, graph_edges, matched_maps, summarize, td, open_dataset, evaluate, build_graph


def merge_verified_csv_graphs(metrics: dict[str, Any], arm: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    merged: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, str]] = []
    for item in metrics["input_hashes"][arm]:
        csv_path = Path(item["csv"])
        digest = sha256(csv_path)
        if digest != item["sha256"]:
            raise ValueError(f"{csv_path}: sha256 {digest} disagrees with recorded {item['sha256']}")
        graphs = read_graphs(csv_path)
        overlap = set(merged) & set(graphs)
        if overlap:
            raise ValueError(f"{csv_path}: duplicate datasets across shards: {sorted(overlap)[:5]}")
        merged.update(graphs)
        manifest.append({"csv": str(csv_path), "sha256": digest})
    return merged, manifest


def top_movies(rows: list[dict[str, Any]], key: str, limit: int) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: (row[key], row["edge_fn"], row["dataset"]), reverse=True)
    return [
        {
            "dataset": row["dataset"],
            "edge_fn": row["edge_fn"],
            "edge_fp": row["edge_fp"],
            "endpoint_limited_fn": row["endpoint_limited_fn"],
            "association_limited_fn": row["association_limited_fn"],
            "endpoint_limited_fn_fraction": row["endpoint_limited_fn_fraction"],
            "association_limited_fn_fraction": row["association_limited_fn_fraction"],
        }
        for row in ranked[:limit]
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--metrics-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", action="append")
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()

    metrics = json.loads(args.metrics_json.read_text(encoding="utf-8"))
    arms = args.arm or list(metrics["input_hashes"])
    helpers = load_helpers(args.repo)
    decompose_edges, graph_edges, matched_maps, summarize, td, open_dataset, evaluate, build_graph = helpers

    result: dict[str, Any] = {
        "status": "PASS_OFFICIAL_MATCH_SUBMISSION_EDGE_FAILURE_DECOMPOSITION",
        "protocol": (
            "Input CSV hashes are verified from metrics.json; each graph is rebuilt, "
            "the official evaluator performs node matching, and the decomposition is "
            "asserted against official and recorded TP/FP/FN counts."
        ),
        "metrics_json": str(args.metrics_json),
        "metrics_json_sha256": sha256(args.metrics_json),
        "data_dir": str(args.data_dir),
        "arms": {},
    }

    for arm in arms:
        graphs, manifest = merge_verified_csv_graphs(metrics, arm)
        recorded_lookup = {str(row["dataset"]): row for row in metrics["rows"][arm]}
        if set(graphs) != set(recorded_lookup):
            missing = sorted(set(recorded_lookup) - set(graphs))
            extra = sorted(set(graphs) - set(recorded_lookup))
            raise ValueError(f"{arm}: graph/metric movie mismatch missing={missing[:5]} extra={extra[:5]}")
        rows_for_summary: list[dict[str, Any]] = []
        enriched_rows: list[dict[str, Any]] = []
        for dataset in sorted(graphs):
            source = graphs[dataset]
            ordered_nodes = sorted(source["nodes"])
            index = {node_id: offset for offset, node_id in enumerate(ordered_nodes)}
            coords = np.asarray([source["nodes"][node_id] for node_id in ordered_nodes], dtype=np.float64)
            edges = [(index[s], index[t], 1.0, 0.0) for s, t in source["edges"]]
            pred_graph = build_graph(coords.reshape((-1, 4)), edges)
            gt_dataset = open_dataset(args.data_dir / f"{dataset}.zarr", require_tracks=True, load_image=False)
            official = evaluate(pred_graph, gt_dataset.tracks, scale=gt_dataset.scale)
            pred_to_gt, gt_to_pred = matched_maps(pred_graph, td)
            row = {
                "dataset": dataset,
                **decompose_edges(
                    graph_edges(pred_graph, td),
                    graph_edges(gt_dataset.tracks, td),
                    pred_to_gt,
                    gt_to_pred,
                ),
            }
            endpoint, association, edge_fn = edge_fn_counts(row)
            edge_fp = classified_edge_fp(row)
            if row["edge_tp"] != official.edge_tp:
                raise ValueError(f"{arm}/{dataset}: TP decomposition disagrees with official evaluator")
            if edge_fn != official.edge_fn:
                raise ValueError(f"{arm}/{dataset}: FN decomposition disagrees with official evaluator")
            if edge_fp != official.edge_fp:
                raise ValueError(f"{arm}/{dataset}: FP decomposition disagrees with official evaluator")
            validate_against_recorded_metrics(arm, dataset, row, recorded_lookup)
            rows_for_summary.append(row)
            enriched = enrich(row)
            enriched.update(
                {
                    "gt_edge_count": len(graph_edges(gt_dataset.tracks, td)),
                    "pred_edge_count": len(graph_edges(pred_graph, td)),
                }
            )
            enriched_rows.append(enriched)
            print(
                json.dumps(
                    {
                        "arm": arm,
                        "dataset": dataset,
                        "edge_fn": edge_fn,
                        "endpoint_limited_fn": endpoint,
                        "association_limited_fn": association,
                    }
                ),
                flush=True,
            )

        pooled = summarize(rows_for_summary)
        by_embryo = {
            prefix: summarize([row for row in rows_for_summary if row["dataset"].startswith(f"{prefix}_")])
            for prefix in ("44b6", "6bba")
        }
        result["arms"][arm] = {
            "recorded_score": metrics["summary"][arm]["score"],
            "recorded_by_embryo_score": {
                prefix: metrics["by_embryo"][arm][prefix]["score"] for prefix in ("44b6", "6bba")
            },
            "input_manifest": manifest,
            "per_movie": enriched_rows,
            "pooled": pooled,
            "by_embryo": by_embryo,
            "top_endpoint_limited_movies": top_movies(enriched_rows, "endpoint_limited_fn", args.top_n),
            "top_association_limited_movies": top_movies(enriched_rows, "association_limited_fn", args.top_n),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    compact = {
        arm: {
            "score": payload["recorded_score"],
            "pooled": payload["pooled"],
            "by_embryo": payload["by_embryo"],
        }
        for arm, payload in result["arms"].items()
    }
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()
