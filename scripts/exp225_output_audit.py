"""Streaming EXP225 graph audit; safe to append to the production source.

This validates the output and its runtime dataset/shape contract. It does not
by itself prove model provenance or that inference produced the CSV.
"""

import csv as _exp225_csv
import hashlib as _exp225_hashlib
import json as _exp225_json
import os as _exp225_os
import operator as _exp225_operator
from decimal import Decimal as _Exp225Decimal, InvalidOperation as _Exp225InvalidOperation
from pathlib import Path as _Exp225Path


EXP225_COLUMNS = [
    "id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"
]


def _exp225_sha256(path):
    digest = _exp225_hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _exp225_integer(value, column, line):
    try:
        # Decimal avoids float rounding of IDs above 2**53 and fractional fields.
        number = _Exp225Decimal(value)
        if not number.is_finite() or number != number.to_integral_value() or "_" in value:
            raise ValueError
        return int(number)
    except (_Exp225InvalidOperation, ValueError, OverflowError) as exc:
        raise ValueError(f"line {line}: {column} must be a finite integer: {value!r}") from exc


def _exp225_rows(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = _exp225_csv.reader(handle, strict=True)
        if next(reader, None) != EXP225_COLUMNS:
            raise ValueError("incorrect CSV columns or order")
        for line, row in enumerate(reader, 2):
            if len(row) != len(EXP225_COLUMNS):
                raise ValueError(f"line {line}: incorrect field count")
            yield line, row


def audit_submission(csv_path, shapes):
    """Validate one CSV against actual dataset -> (T, Z, Y, X) shapes.

    Rows are streamed twice so edges may precede nodes. Memory is proportional
    to nodes and graph degrees; coordinates and CSV rows are never retained.
    Integral decimal spellings such as ``1.0`` are accepted without rounding.
    Raises ValueError on a failed contract and returns JSON-compatible evidence.
    """
    path = _Exp225Path(csv_path)
    if not shapes:
        raise ValueError("runtime dataset shapes must not be empty")
    dimensions = {}
    for dataset, shape in shapes.items():
        if not isinstance(dataset, str) or not dataset:
            raise ValueError("runtime dataset IDs must be nonempty strings")
        try:
            dims = tuple(_exp225_operator.index(value) for value in shape)
        except TypeError as exc:
            raise ValueError(f"{dataset}: shape must contain four positive integers") from exc
        if len(dims) != 4 or any(value <= 0 for value in dims):
            raise ValueError(f"{dataset}: shape must contain four positive integers")
        dimensions[dataset] = dims

    before_sha = _exp225_sha256(path)
    times = {dataset: {} for dataset in dimensions}
    counts = {dataset: {"nodes": 0, "edges": 0} for dataset in dimensions}
    rows = 0
    numeric_indices = (0, 3, 4, 5, 6, 7, 8, 9)
    for line, row in _exp225_rows(path):
        dataset, kind = row[1], row[2]
        if dataset not in dimensions:
            raise ValueError(f"line {line}: unknown runtime dataset {dataset!r}")
        values = {i: _exp225_integer(row[i], EXP225_COLUMNS[i], line) for i in numeric_indices}
        if values[0] != rows:
            raise ValueError(f"line {line}: global id must be contiguous from zero")
        rows += 1
        if kind == "node":
            node_id = values[3]
            if node_id < 0 or node_id in times[dataset]:
                raise ValueError(f"line {line}: negative or duplicate node ID")
            if values[8] != -1 or values[9] != -1:
                raise ValueError(f"line {line}: node sentinel fields must equal -1")
            if any(not 0 <= values[i] < bound for i, bound in zip((4, 5, 6, 7), dimensions[dataset])):
                raise ValueError(f"line {line}: node coordinate out of runtime bounds")
            times[dataset][node_id] = values[4]
            counts[dataset]["nodes"] += 1
        elif kind == "edge":
            if any(values[i] != -1 for i in (3, 4, 5, 6, 7)):
                raise ValueError(f"line {line}: edge sentinel fields must equal -1")
            if values[8] < 0 or values[9] < 0:
                raise ValueError(f"line {line}: negative edge endpoint")
            counts[dataset]["edges"] += 1
        else:
            raise ValueError(f"line {line}: unknown row_type {kind!r}")
    missing = sorted(dataset for dataset, values in counts.items() if values["nodes"] == 0)
    if missing:
        raise ValueError(f"runtime datasets without any nodes: {missing}")

    parents = {dataset: {} for dataset in dimensions}
    out_degree = {dataset: {} for dataset in dimensions}
    for line, row in _exp225_rows(path):
        if row[2] != "edge":
            continue
        dataset = row[1]
        source = _exp225_integer(row[8], "source_id", line)
        target = _exp225_integer(row[9], "target_id", line)
        node_times = times[dataset]
        if source not in node_times or target not in node_times:
            raise ValueError(f"line {line}: orphan edge endpoint")
        if node_times[target] != node_times[source] + 1:
            raise ValueError(f"line {line}: edge must join consecutive frames")
        if target in parents[dataset]:
            if parents[dataset][target] == source:
                raise ValueError(f"line {line}: duplicate edge")
            raise ValueError(f"line {line}: in-degree exceeds one")
        parents[dataset][target] = source
        degree = out_degree[dataset].get(source, 0) + 1
        if degree > 2:
            raise ValueError(f"line {line}: out-degree exceeds two")
        out_degree[dataset][source] = degree

    after_sha = _exp225_sha256(path)
    if before_sha != after_sha:
        raise ValueError("submission changed while being audited")
    per_dataset = {}
    for dataset in sorted(dimensions):
        node_times, incoming, outgoing = times[dataset], parents[dataset], out_degree[dataset]
        per_dataset[dataset] = {
            **counts[dataset],
            "shape_tzyx": list(dimensions[dataset]),
            "minimum_t": min(node_times.values()),
            "maximum_t": max(node_times.values()),
            "frames_with_nodes": len(set(node_times.values())),
            "maximum_in_degree": 1 if incoming else 0,
            "maximum_out_degree": max(outgoing.values(), default=0),
            "roots": len(node_times) - len(incoming),
            "leaves": len(node_times) - len(outgoing),
            "isolated_nodes": sum(node not in incoming and node not in outgoing for node in node_times),
            "division_nodes": sum(degree == 2 for degree in outgoing.values()),
        }
    return {
        "status": "PASS_EXP225_OUTPUT_AUDIT",
        "submission_sha256": after_sha,
        "submission_bytes": path.stat().st_size,
        "columns": list(EXP225_COLUMNS),
        "rows": rows,
        "nodes": sum(value["nodes"] for value in counts.values()),
        "edges": sum(value["edges"] for value in counts.values()),
        "datasets": sorted(dimensions),
        "runtime_shapes": {dataset: list(dimensions[dataset]) for dataset in sorted(dimensions)},
        "per_dataset": per_dataset,
        "dynamic_runtime_id_equality": True,
        "finite_integer_fields": True,
        "graph_invariants_valid": True,
    }


def run_exp225_output_audit(TEST_DIR, WORKING_DIR, source_evidence_status=None):
    """Read actual runtime Zarr shapes and write the root output audit receipt."""
    import zarr

    test_dir = _Exp225Path(TEST_DIR).resolve()
    working_dir = _Exp225Path(WORKING_DIR).resolve()
    submission = working_dir / "submission.csv"
    candidates = []
    # Filename inventory is deliberately not a glob or an input CSV search.
    for directory, _, filenames in _exp225_os.walk(working_dir):
        if "submission.csv" in filenames:
            candidates.append(_Exp225Path(directory) / "submission.csv")
    if candidates != [submission] or submission.resolve().parent != working_dir:
        raise ValueError(f"expected exactly one root submission.csv: {candidates}")
    runtime_paths = sorted(path for path in test_dir.iterdir() if path.is_dir() and path.suffix == ".zarr")
    if not runtime_paths:
        raise ValueError("runtime test directory has no Zarr datasets")
    shapes = {
        path.stem: tuple(zarr.open_group(str(path), mode="r")["0"].shape)
        for path in runtime_paths
    }
    receipt = audit_submission(submission, shapes)
    receipt.update({
        "status": "PASS_EXP225_RUNTIME_OUTPUT_AUDIT",
        "test_dir": str(test_dir),
        "working_dir": str(working_dir),
        "runtime_datasets": sorted(shapes),
        "runtime_test_paths": [str(path) for path in runtime_paths],
        "runtime_shape_discovery": "zarr.open_group(runtime_test_path, mode='r')['0'].shape",
        "one_root_submission": True,
        "resolved_biohub_environment": {
            key: value for key, value in sorted(_exp225_os.environ.items()) if key.startswith("BIOHUB_")
        },
        "source_evidence_status": source_evidence_status or _exp225_os.environ.get(
            "BIOHUB_SOURCE_EVIDENCE_STATUS", "NOT_PROVIDED"
        ),
        "evidence_scope": "Runtime output/schema/graph audit; inference and source provenance require separate evidence.",
    })
    destination = working_dir / "exp225_runtime_audit.json"
    destination.write_text(_exp225_json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(_exp225_json.dumps({"exp225_runtime_audit": str(destination), "rows": receipt["rows"],
                             "sha256": receipt["submission_sha256"]}))
    return receipt
