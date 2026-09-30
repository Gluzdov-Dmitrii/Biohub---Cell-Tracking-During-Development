"""Seal EXP209 reconstruction v1 graphs before any target-label access.

This is a one-shot, label-free postrun gate. It reads the pinned historical
result only for its selected movie IDs; it never imports a scorer or opens GEFF.
The scorer must independently pin the SHA of the resulting no_metric_gate.json.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import uuid
from pathlib import Path
from typing import Any


RUN_NAME = "exp209_current_metric_reconstruction_v1_20260927"
EXPERIMENT = "EXP209_CURRENT_METRIC_RECONSTRUCTION_V1"
HISTORICAL_RESULT_SHA = "bcc57aeef14a9419daab17ca10398774d229f499926f53176948eab331c05e0c"
ARCHIVE_MANIFEST_SHA = "1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a"
DATA_MANIFEST_SHA = "ddf71e7f5cf52a0da152ef8fe32a8e1ff505e8534184a084b04e2e1b9a673add"
DATA_AUDIT_SHA = "1abde88cb6feea73db1ce78ac6fe0994620e3c74e58bfee46455b691052768de"
GRAPH_BUILDER_SHA = "f698f97c6b00ec92e41aec032bf24d317d565d4f14bab56610f7d4697c441d70"
FORWARD_SELECTION_SHA = "bd98ebbc70a37912a1307c1f3c7b5cc285ea4d6838e2391423694bd27023fc42"
SOURCE_TRAINER_SHA = {
    "forward": "296d307f9ff174ce3d3db9bc77b8b12c2674178b8b09598fed129574c4b458a4",
    "reverse": "5eb0c0426c8b2cc5331c4e2ea0b34e79d3caf48e8eef822def89c69da0b11b0b",
}
SOURCE_FUNCTION_SHA = {
    "evaluate_cached_intensity_centroid_family.py": "36a7fa07f7d87ee0a8052a52c8fed759615cda6f095ae812cd740c06b9e9e942",
    "evaluate_cached_intensity_centroid_refinement.py": "0f812c4b4af24cf8512c59cc1cbda6323e0c17f698f46a3b5621dd011971d04b",
    "evaluate_cached_short_track_family.py": "a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3",
    "evaluate_coordinate_consensus.py": "426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2",
}
FROZEN_POLICY = {"forward": {"centroid_radius_zyx": [3, 5, 5], "minimum_length": 8},
                 "reverse": {"arm": "EXP191 gap selected edges", "minimum_length": 6}}
COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
CHUNK_SIZES = {"forward": (24, 24, 24, 24, 20), "reverse": (24, 24, 11)}
EXPECTED_CHUNKS = [f"{direction}_{index:02d}" for direction, sizes in CHUNK_SIZES.items()
                   for index in range(len(sizes))]
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
MOVIE = re.compile(r"(?:6bba|44b6)_[0-9a-f]{8}\Z")


class GateError(ValueError):
    """A required label-free integrity check failed."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise GateError(reason)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    require(path.is_file(), f"missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid JSON: {path}") from exc


def pinned(path: Path, expected: str, label: str) -> None:
    require(path.is_file(), f"missing {label}: {path}")
    require(sha256(path) == expected, f"{label} SHA256 mismatch: {path}")


def hex_digest(value: Any, label: str) -> str:
    require(isinstance(value, str) and HEX64.fullmatch(value) is not None,
            f"invalid {label} SHA256")
    return value


def selected_movies(result: dict[str, Any]) -> dict[str, list[str]]:
    require(result.get("status") == "PASS_FROZEN_CONFIRMATION_ASSEMBLY",
            "historical result status mismatch")
    selected: dict[str, list[str]] = {}
    for direction, prefix, count in (("forward", "6bba_", 116), ("reverse", "44b6_", 59)):
        rows = result["directions"][direction]["selected_rows"]
        require(isinstance(rows, list) and len(rows) == count,
                f"historical {direction} selected-row count mismatch")
        names = []
        for row in rows:
            value = row["dataset"]
            require(isinstance(value, str) and value.endswith(".zarr"),
                    f"invalid historical {direction} dataset")
            name = value[:-5]
            require(MOVIE.fullmatch(name) is not None and name.startswith(prefix),
                    f"historical {direction} embryo mismatch: {value}")
            names.append(name)
        require(len(set(names)) == count, f"historical {direction} duplicate dataset")
        selected[direction] = names
    require(not (set(selected["forward"]) & set(selected["reverse"])),
            "historical direction overlap")
    return selected


def validate_contract(path: Path, run_root: Path) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, str]]:
    require(run_root.name == RUN_NAME, "run namespace mismatch")
    contract = load_json(path)
    require(isinstance(contract, dict) and contract.get("experiment") == EXPERIMENT,
            "contract experiment mismatch")
    require(contract.get("run_root") == str(run_root), "contract run root mismatch")
    require(contract.get("labels_read") is False and contract.get("current_organizer_score") is None,
            "contract contains label/score state")
    require(contract.get("frozen_policy") == FROZEN_POLICY and
            contract.get("source_function_sha256") == SOURCE_FUNCTION_SHA and
            contract.get("reference_graph_builder_sha256") == GRAPH_BUILDER_SHA,
            "contract reconstruction policy/source pins mismatch")
    code_dir = Path(contract["code_dir"])
    require(code_dir.is_absolute() and code_dir.is_dir(), "missing absolute reconstruction code directory")
    for filename, digest in SOURCE_FUNCTION_SHA.items():
        pinned(code_dir / filename, digest, f"reconstruction source {filename}")
    pins = (
        ("historical_result", "historical_result_sha256", HISTORICAL_RESULT_SHA),
        ("archive_manifest", "archive_manifest_sha256", ARCHIVE_MANIFEST_SHA),
        ("data_manifest", "data_manifest_sha256", DATA_MANIFEST_SHA),
        ("data_audit", "data_audit_sha256", DATA_AUDIT_SHA),
    )
    for path_key, sha_key, expected in pins:
        require(contract.get(sha_key) == expected, f"contract {sha_key} pin mismatch")
        source = Path(contract[path_key])
        require(source.is_absolute(), f"contract {path_key} must be absolute")
        pinned(source, expected, path_key)
    require(contract.get("forward_source_selection_sha256") == FORWARD_SELECTION_SHA,
            "forward source-selection pin mismatch")
    selection_path = Path(contract["forward_source_selection"])
    require(selection_path.is_absolute(), "forward source-selection path must be absolute")
    pinned(selection_path, FORWARD_SELECTION_SHA, "forward source selection")
    trainers = contract.get("source_trainer_manifests")
    require(isinstance(trainers, dict) and set(trainers) == set(SOURCE_TRAINER_SHA),
            "source trainer manifest directions mismatch")
    for direction, digest in SOURCE_TRAINER_SHA.items():
        spec = trainers[direction]
        require(isinstance(spec, dict) and spec.get("sha256") == digest,
                f"{direction} source trainer pin mismatch")
        trainer_path = Path(spec["path"])
        require(trainer_path.is_absolute(), f"{direction} source trainer path must be absolute")
        pinned(trainer_path, digest, f"{direction} source trainer manifest")
    historical_path = Path(contract["historical_result"])
    require(historical_path.name in {"forward_plus_exp191_confirmation.json", "historical_result.json"},
            "historical result basename mismatch")
    manifest_text = Path(contract["archive_manifest"]).read_text(encoding="utf-8")
    match = re.findall(r"^([0-9a-f]{64})  \./forward_plus_exp191_confirmation\.json$",
                       manifest_text, flags=re.MULTILINE)
    require(match == [HISTORICAL_RESULT_SHA], "archive manifest does not pin historical result")
    cohort = selected_movies(load_json(historical_path))
    image_manifest_path = Path(contract["image_sha_manifest"])
    require(image_manifest_path.is_absolute(), "image-only SHA manifest path must be absolute")
    image_manifest_sha = hex_digest(contract.get("image_sha_manifest_sha256"), "image-only manifest")
    pinned(image_manifest_path, image_manifest_sha, "image-only SHA manifest")
    image_manifest = load_json(image_manifest_path)
    require(isinstance(image_manifest, dict), "image-only SHA manifest is not an object")
    expected_movies = set(cohort["forward"] + cohort["reverse"])
    image_hashes = image_manifest.get("image_tree_sha256_by_movie")
    require(type(image_manifest.get("movie_count")) is int and image_manifest["movie_count"] == 175 and
            image_manifest.get("data_audit_sha256") == DATA_AUDIT_SHA and
            image_manifest.get("data_manifest_sha256") == DATA_MANIFEST_SHA and
            isinstance(image_hashes, dict) and set(image_hashes) == expected_movies,
            "image-only SHA manifest cohort/pin mismatch")
    for movie, digest in image_hashes.items():
        hex_digest(digest, f"image-only manifest/{movie}")

    chunks = contract.get("chunks")
    require(isinstance(chunks, list) and len(chunks) == 8, "contract needs eight chunks")
    require([row.get("name") for row in chunks] == EXPECTED_CHUNKS,
            "contract chunk names/order mismatch")
    for row in chunks:
        direction = row["direction"]
        name = row["name"]
        require(direction in CHUNK_SIZES and name.startswith(direction + "_"),
                f"{name}: direction mismatch")
        index = int(name[-2:])
        start = sum(CHUNK_SIZES[direction][:index])
        expected = cohort[direction][start:start + CHUNK_SIZES[direction][index]]
        require(row.get("movies") == expected, f"{name}: historical movie partition mismatch")
        caches = row.get("input_cache_sha256")
        require(isinstance(caches, dict) and set(caches) == set(expected),
                f"{name}: input-cache SHA coverage mismatch")
        for movie in expected:
            hex_digest(caches[movie], f"{name}/{movie} input-cache")
        gaps = row.get("gap_cache_sha256", {})
        require(isinstance(gaps, dict), f"{name}: gap-cache map is invalid")
        require(set(gaps) == (set(expected) if direction == "reverse" else set()),
                f"{name}: gap-cache SHA coverage mismatch")
        for movie, digest in gaps.items():
            hex_digest(digest, f"{name}/{movie} gap-cache")
    require(len(cohort["forward"]) + len(cohort["reverse"]) == 175,
            "historical cohort is not 175 movies")
    return contract, cohort, image_hashes


def _integer(value: str, label: str, minimum: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GateError(f"invalid integer {label}: {value!r}") from exc
    require(parsed >= minimum, f"{label} below {minimum}")
    return parsed


def _coordinate(value: str, label: str, bound: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise GateError(f"invalid coordinate {label}: {value!r}") from exc
    require(math.isfinite(parsed) and 0 <= parsed < bound, f"{label} out of bounds or nonfinite")
    return parsed


def checked_graph(path: Path, dataset: str, shape: list[int]) -> dict[str, int]:
    require(path.is_file(), f"missing graph: {path}")
    require(isinstance(shape, list) and len(shape) == 4 and
            all(type(size) is int and size > 0 for size in shape), f"{dataset}: invalid image shape")
    nodes: dict[int, tuple[int, float, float, float]] = {}
    edges: list[tuple[int, int]] = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == COLUMNS, f"{dataset}: CSV columns mismatch")
        for row_index, row in enumerate(reader):
            require(None not in row and row.get(None) is None, f"{dataset}: malformed CSV row")
            require(_integer(row["id"], "row id") == row_index,
                    f"{dataset}: nonconsecutive CSV row id")
            require(row["dataset"] == dataset, f"{dataset}: cross-dataset CSV row")
            kind = row["row_type"]
            if kind == "node":
                node = _integer(row["node_id"], "node id")
                require(node not in nodes, f"{dataset}: duplicate node id")
                t = _integer(row["t"], "node time")
                require(t < shape[0], f"{dataset}: node time outside image")
                zyx = tuple(_coordinate(row[key], key, size)
                            for key, size in zip(("z", "y", "x"), shape[1:]))
                require(row["source_id"] == row["target_id"] == "-1",
                        f"{dataset}: node edge sentinels mismatch")
                nodes[node] = (t, *zyx)
            elif kind == "edge":
                require(all(row[key] == "-1" for key in ("node_id", "t", "z", "y", "x")),
                        f"{dataset}: edge node sentinels mismatch")
                source = _integer(row["source_id"], "edge source")
                target = _integer(row["target_id"], "edge target")
                edges.append((source, target))
            else:
                raise GateError(f"{dataset}: invalid row type {kind!r}")
    require(bool(nodes), f"{dataset}: empty graph")
    require(set(nodes) == set(range(len(nodes))), f"{dataset}: nonconsecutive node IDs")
    require(len(edges) == len(set(edges)), f"{dataset}: duplicate edges")
    indegree: dict[int, int] = {}
    outdegree: dict[int, int] = {}
    for source, target in edges:
        require(source in nodes and target in nodes, f"{dataset}: dangling edge")
        require(nodes[target][0] == nodes[source][0] + 1,
                f"{dataset}: edge violates directed consecutive time")
        indegree[target] = indegree.get(target, 0) + 1
        outdegree[source] = outdegree.get(source, 0) + 1
    require(max(indegree.values(), default=0) <= 1, f"{dataset}: multiple parents")
    require(max(outdegree.values(), default=0) <= 2, f"{dataset}: more than two children")
    return {"nodes": len(nodes), "edges": len(edges),
            "parented_nodes": len(indegree),
            "division_parents": sum(degree == 2 for degree in outdegree.values())}


def _worker_absent(pid: int, start_tick: int, proc_root: Path) -> None:
    if not proc_root.is_dir():
        return  # Synthetic Windows validation; remote Linux has /proc.
    stat = proc_root / str(pid) / "stat"
    if not stat.exists():
        return
    raw = stat.read_text(encoding="utf-8")
    fields = raw[raw.rfind(")") + 2:].split()
    require(len(fields) > 19, f"worker {pid}: malformed live /proc stat")
    require(fields[0] == "Z" or int(fields[19]) != start_tick,
            f"worker {pid}: original process still live")


def _chunk_gate(run_root: Path, chunk: dict[str, Any], proc_root: Path,
                contract_sha: str, preflight_sha: str,
                preflight_images: dict[str, str]) -> dict[str, Any]:
    name = chunk["name"]
    movies = chunk["movies"]
    folder = run_root / "chunks" / name
    output = folder / "output"
    require(output.is_dir(), f"{name}: missing output directory")
    expected_files = {"status.json"} | {
        f"graph__{movie}{suffix}" for movie in movies
        for suffix in (".csv", ".receipt.json")
    }
    require({item.name for item in output.iterdir()} == expected_files and
            all(item.is_file() and not item.is_symlink() for item in output.iterdir()),
            f"{name}: missing or extra output file")
    completion_path = folder / "completion.json"
    release_path = folder / "release.json"
    completion = load_json(completion_path)
    release = load_json(release_path)
    require(completion.get("status") == "EXIT0" and type(completion.get("exit_code")) is int and
            completion["exit_code"] == 0 and completion.get("timed_out") is False,
            f"{name}: worker did not exit 0 without timeout")
    pid = completion.get("worker_pid")
    tick = completion.get("worker_start_tick")
    require(type(pid) is int and pid > 0 and type(tick) is int and tick > 0,
            f"{name}: invalid worker identity")
    require(release.get("status") == "RELEASED" and release.get("worker_absent") is True and
            release.get("worker_pid") == pid and release.get("worker_start_tick") == tick,
            f"{name}: CPU lease/worker release mismatch")
    _worker_absent(pid, tick, proc_root)
    status_path = output / "status.json"
    status = load_json(status_path)
    require(status.get("status") == "PASS_EXP209_RECONSTRUCTION_CHUNK_NO_LABELS" and
            status.get("chunk") == name and status.get("direction") == chunk["direction"] and
            status.get("movies") == movies and status.get("labels_read") is False and
            status.get("contract_sha256") == contract_sha and
            status.get("preflight_sha256") == preflight_sha,
            f"{name}: output status mismatch")
    records = status.get("records")
    require(isinstance(records, list) and len(records) == len(movies),
            f"{name}: record count mismatch")
    graph_hashes = []
    for movie, record in zip(movies, records):
        require(isinstance(record, dict) and record.get("dataset") == movie,
                f"{name}: record dataset/order mismatch")
        csv_path = output / f"graph__{movie}.csv"
        receipt_path = output / f"graph__{movie}.receipt.json"
        csv_sha = sha256(csv_path)
        receipt_sha = sha256(receipt_path)
        require(record.get("csv_sha256") == csv_sha and
                record.get("receipt_sha256") == receipt_sha,
                f"{name}/{movie}: status graph/receipt hash mismatch")
        receipt = load_json(receipt_path)
        require(receipt.get("dataset") == movie and receipt.get("labels_read") is False and
                receipt.get("csv_sha256") == csv_sha,
                f"{name}/{movie}: graph receipt identity mismatch")
        require(receipt.get("input_cache_sha256") == chunk["input_cache_sha256"][movie],
                f"{name}/{movie}: input-cache pin mismatch")
        image_sha = hex_digest(receipt.get("image_tree_sha256"), f"{name}/{movie} image-tree")
        require(image_sha == preflight_images[movie], f"{name}/{movie}: preflight image hash mismatch")
        if chunk["direction"] == "reverse":
            require(receipt.get("gap_cache_sha256") == chunk["gap_cache_sha256"][movie],
                    f"{name}/{movie}: gap-cache pin mismatch")
        else:
            require(receipt.get("gap_cache_sha256") is None,
                    f"{name}/{movie}: unexpected gap cache")
        counts = checked_graph(csv_path, movie, receipt.get("shape"))
        for key in ("nodes", "edges"):
            require(receipt.get(key) == counts[key], f"{name}/{movie}: graph {key} mismatch")
        for key in ("parented_nodes", "division_parents"):
            if key in receipt:
                require(receipt[key] == counts[key], f"{name}/{movie}: graph {key} mismatch")
        require(record.get("nodes") == counts["nodes"] and record.get("edges") == counts["edges"],
                f"{name}/{movie}: status graph counts mismatch")
        graph_hashes.append({"dataset": movie, "csv_sha256": csv_sha,
                             "receipt_sha256": receipt_sha, "image_tree_sha256": image_sha,
                             **counts})
    return {"chunk": name, "direction": chunk["direction"], "movies": movies,
            "status_sha256": sha256(status_path),
            "completion_sha256": sha256(completion_path),
            "release_sha256": sha256(release_path), "graph_hashes": graph_hashes,
            "worker_exit_code": 0, "worker_timed_out": False, "cpu_lease": "RELEASED"}


def gate(contract_path: Path, run_root: Path, proc_root: Path = Path("/proc")) -> dict[str, Any]:
    """Validate all eight chunks in memory; this function never reads labels."""
    contract_path = Path(contract_path)
    run_root = Path(run_root)
    contract, cohort, pinned_images = validate_contract(contract_path, run_root)
    contract_sha = sha256(contract_path)
    intent_path = run_root / "launch_intent.json"
    intent = load_json(intent_path)
    require(intent.get("status") == "LAUNCH_INTENT_CPU_ONLY_NO_LABELS" and
            intent.get("contract_sha256") == contract_sha and
            intent.get("labels_read") is False and intent.get("gpu_used") is False,
            "launch intent mismatch")
    preflight_path = run_root / "preflight.json"
    require(preflight_path.is_file(), "missing full175 preflight")
    preflight_sha = sha256(preflight_path)
    preflight = load_json(preflight_path)
    require(preflight.get("status") == "PASS_EXP209_RECONSTRUCTION_INPUTS_NO_LABELS" and
            preflight.get("contract_sha256") == contract_sha and
            preflight.get("raw_candidate_count") == 175 and
            preflight.get("reverse_gap_cache_count") == 59 and
            preflight.get("image_count") == 175 and
            preflight.get("historical_image_manifest_sha256") == DATA_MANIFEST_SHA and
            preflight.get("historical_data_audit_sha256") == DATA_AUDIT_SHA and
            preflight.get("labels_read") is False and preflight.get("gpu_used") is False,
            "full175 preflight mismatch")
    images = preflight.get("image_tree_sha256_by_movie")
    require(isinstance(images, dict) and set(images) == set(cohort["forward"] + cohort["reverse"]),
            "full175 preflight image hash coverage mismatch")
    for movie, image_sha in images.items():
        hex_digest(image_sha, f"preflight/{movie} image-tree")
    require(images == pinned_images,
            "preflight image hashes differ from pinned image-only SHA manifest")
    preflight_completion_path = run_root / "preflight_completion.json"
    preflight_completion = load_json(preflight_completion_path)
    require(preflight_completion.get("status") == "EXIT0" and
            type(preflight_completion.get("exit_code")) is int and
            preflight_completion["exit_code"] == 0 and
            preflight_completion.get("timed_out") is False and
            preflight_completion.get("worker_absent") is True and
            type(preflight_completion.get("worker_pid")) is int and
            preflight_completion["worker_pid"] > 0 and
            type(preflight_completion.get("worker_start_tick")) is int and
            preflight_completion["worker_start_tick"] > 0,
            "preflight worker exit/release mismatch")
    _worker_absent(preflight_completion["worker_pid"],
                   preflight_completion["worker_start_tick"], proc_root)
    supervisor_path = run_root / "supervisor_complete.json"
    supervisor = load_json(supervisor_path)
    require(supervisor.get("status") == "ALL_EIGHT_CHUNKS_EXIT0_RELEASED_NO_LABELS" and
            supervisor.get("contract_sha256") == contract_sha and
            supervisor.get("movie_count") == 175 and
            supervisor.get("labels_read") is False and supervisor.get("gpu_used") is False,
            "supervisor completion mismatch")
    chunk_root = run_root / "chunks"
    require(chunk_root.is_dir() and {item.name for item in chunk_root.iterdir()} == set(EXPECTED_CHUNKS) and
            all(item.is_dir() and not item.is_symlink() for item in chunk_root.iterdir()),
            "run has missing or extra chunk directories")
    validations = [_chunk_gate(run_root, row, proc_root, contract_sha, preflight_sha, images)
                   for row in contract["chunks"]]
    hashes = [entry for validation in validations for entry in validation["graph_hashes"]]
    require(len(hashes) == 175 and len({entry["dataset"] for entry in hashes}) == 175,
            "175-graph coverage mismatch")
    require([entry["dataset"] for entry in hashes] == cohort["forward"] + cohort["reverse"],
            "graph hashes do not match historical ordered cohort")
    return {"status": "PASS_EXP209_RECONSTRUCTION175_NO_METRIC_GATE",
            "experiment": EXPERIMENT, "run_namespace": RUN_NAME,
            "movie_count": 175, "direction_counts": {"forward": 116, "reverse": 59},
            "chunk_count": 8, "labels_read": False, "scientific_metrics_emitted": False,
            "current_organizer_score": None,
            "source_pins": {"contract_sha256": contract_sha,
                            "historical_result_sha256": HISTORICAL_RESULT_SHA,
                            "archive_manifest_sha256": ARCHIVE_MANIFEST_SHA,
                            "data_manifest_sha256": DATA_MANIFEST_SHA,
                            "data_audit_sha256": DATA_AUDIT_SHA,
                            "image_sha_manifest_sha256": contract["image_sha_manifest_sha256"],
                            "graph_builder_sha256": GRAPH_BUILDER_SHA,
                            "source_function_sha256": SOURCE_FUNCTION_SHA,
                            "forward_source_selection_sha256": FORWARD_SELECTION_SHA,
                            "source_trainer_manifest_sha256": SOURCE_TRAINER_SHA,
                            "frozen_policy": FROZEN_POLICY},
            "control_hashes": {"launch_intent_sha256": sha256(intent_path),
                               "preflight_sha256": preflight_sha,
                               "preflight_completion_sha256": sha256(preflight_completion_path),
                               "supervisor_complete_sha256": sha256(supervisor_path)},
            "chunks": validations, "graph_hashes": hashes}


def write_once_durable(path: Path, payload: dict[str, Any]) -> None:
    """Publish a complete synced JSON file without replacing an existing gate."""
    require(not path.exists(), f"existing gate requires reconciliation: {path}")
    require(path.parent.is_dir(), f"missing gate parent directory: {path.parent}")
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    data = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # atomic no-replace publication
        if os.name != "nt":
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.output.resolve() == (args.run_root / "no_metric_gate.json").resolve(),
            "no_metric_gate output must be at run root")
    require(not args.output.exists(), "existing no_metric_gate requires reconciliation")
    result = gate(args.contract, args.run_root)
    write_once_durable(args.output, result)
    print(json.dumps({"status": result["status"], "movies": result["movie_count"],
                      "chunks": result["chunk_count"], "gate_sha256": sha256(args.output)}))


if __name__ == "__main__":
    main()
