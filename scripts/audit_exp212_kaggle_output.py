"""Fail-closed audit of the clean EXP212 Kaggle output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    candidates = list(args.output_dir.rglob("submission.csv"))
    if len(candidates) != 1 or candidates[0].parent.resolve() != args.output_dir.resolve():
        raise AssertionError({"root_submission_candidates": list(map(str, candidates))})
    submission = candidates[0]
    runtime_path = args.output_dir / "exp212_runtime_receipt.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    if runtime.get("status") != "PASS_EXP212_EXP209_OOF_FRONTIER_PRODUCTION":
        raise AssertionError(runtime.get("status"))
    if runtime.get("submission_sha256") != sha256(submission):
        raise AssertionError("runtime/local submission SHA mismatch")

    frame = pd.read_csv(submission)
    if list(frame.columns) != COLUMNS:
        raise AssertionError(list(frame.columns))
    if not np.array_equal(frame["id"].to_numpy(), np.arange(len(frame))):
        raise AssertionError("id is not consecutive")
    if set(frame["row_type"]) != {"node", "edge"}:
        raise AssertionError(sorted(set(frame["row_type"])))
    if not np.isfinite(frame[["node_id", "t", "z", "y", "x", "source_id", "target_id"]].to_numpy(dtype=float)).all():
        raise AssertionError("non-finite numeric value")
    observed_datasets = sorted(frame["dataset"].astype(str).unique())
    if observed_datasets != sorted(runtime["runtime_dataset_ids"]):
        raise AssertionError({"csv": observed_datasets, "runtime": runtime["runtime_dataset_ids"]})

    nodes = frame[frame["row_type"] == "node"].copy()
    edges = frame[frame["row_type"] == "edge"].copy()
    if not (nodes[["source_id", "target_id"]] == -1).all().all():
        raise AssertionError("node sentinel fields")
    if not (edges[["node_id", "t", "z", "y", "x"]] == -1).all().all():
        raise AssertionError("edge sentinel fields")
    if nodes.duplicated(["dataset", "node_id"]).any():
        raise AssertionError("duplicate node id")
    node_time = {(str(row.dataset), int(row.node_id)): int(row.t) for row in nodes.itertuples()}
    for row in edges.itertuples():
        source = (str(row.dataset), int(row.source_id))
        target = (str(row.dataset), int(row.target_id))
        if source not in node_time or target not in node_time:
            raise AssertionError("dangling edge")
        if node_time[target] != node_time[source] + 1:
            raise AssertionError("nonconsecutive edge")
    max_in = int(edges.groupby(["dataset", "target_id"]).size().max()) if len(edges) else 0
    max_out = int(edges.groupby(["dataset", "source_id"]).size().max()) if len(edges) else 0
    if max_in > 1 or max_out > 1:
        raise AssertionError({"max_in": max_in, "max_out": max_out})
    if len(nodes) != int(runtime["nodes"]) or len(edges) != int(runtime["edges"]):
        raise AssertionError("runtime count mismatch")

    receipt = {
        "status": "PASS_EXP212_CLEAN_KAGGLE_OUTPUT_AUDIT",
        "submission_sha256": sha256(submission),
        "runtime_receipt_sha256": sha256(runtime_path),
        "rows": len(frame),
        "nodes": len(nodes),
        "edges": len(edges),
        "datasets": observed_datasets,
        "maximum_in_degree": max_in,
        "maximum_out_degree": max_out,
        "one_root_submission": True,
        "dynamic_runtime_id_equality": True,
        "finite_and_schema_valid": True
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
