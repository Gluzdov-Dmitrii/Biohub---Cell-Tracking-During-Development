"""Synthetic, label-free checks for the 175-graph reconstruction gate."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_exp209_reconstruction_graphs_v1 as verifier  # noqa: E402


ARCHIVE = ROOT / "outputs/research/exp209_selected_centroid_confirmation_20260912"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def rows(movie: str) -> list[list[str]]:
    return [
        ["0", movie, "node", "0", "0", "1.5", "2", "3", "-1", "-1"],
        ["1", movie, "node", "1", "1", "1.6", "2", "3", "-1", "-1"],
        ["2", movie, "edge", "-1", "-1", "-1", "-1", "-1", "0", "1"],
    ]


def graph_files(run_root: Path, chunk: str, movie: str) -> tuple[Path, Path, Path]:
    output = run_root / "chunks" / chunk / "output"
    return (output / f"graph__{movie}.csv",
            output / f"graph__{movie}.receipt.json", output / "status.json")


def reseal_graph(run_root: Path, chunk: str, movie: str, values: list[list[str]]) -> None:
    csv_path, receipt_path, status_path = graph_files(run_root, chunk, movie)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(verifier.COLUMNS)
        writer.writerows(values)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["csv_sha256"] = sha(csv_path)
    receipt["nodes"] = sum(row[2] == "node" for row in values)
    receipt["edges"] = sum(row[2] == "edge" for row in values)
    save(receipt_path, receipt)
    status = json.loads(status_path.read_text(encoding="utf-8"))
    record = next(row for row in status["records"] if row["dataset"] == movie)
    record.update(csv_sha256=sha(csv_path), receipt_sha256=sha(receipt_path),
                  nodes=receipt["nodes"], edges=receipt["edges"])
    save(status_path, status)


@pytest.fixture
def synthetic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    """Build every exact historical ID with tiny prediction graphs and fake controls."""
    data_manifest = tmp_path / "historical_data_manifest.json"
    data_audit = tmp_path / "historical_data_audit.json"
    save(data_manifest, {"historical_image_manifest": True})
    save(data_audit, {"status": "PASS_EXP192_DATA_AUDIT"})
    monkeypatch.setattr(verifier, "DATA_MANIFEST_SHA", sha(data_manifest))
    monkeypatch.setattr(verifier, "DATA_AUDIT_SHA", sha(data_audit))
    result = ARCHIVE / "forward_plus_exp191_confirmation.json"
    cohort = verifier.selected_movies(json.loads(result.read_text(encoding="utf-8")))
    run_root = tmp_path / verifier.RUN_NAME
    chunks_root = run_root / "chunks"
    chunks_root.mkdir(parents=True)
    chunks = []
    for direction, sizes in verifier.CHUNK_SIZES.items():
        start = 0
        for index, size in enumerate(sizes):
            name = f"{direction}_{index:02d}"
            movies = cohort[direction][start:start + size]
            start += size
            output = chunks_root / name / "output"
            output.mkdir(parents=True)
            cache_hashes = {movie: digest("cache-" + movie) for movie in movies}
            gap_hashes = {movie: digest("gap-" + movie) for movie in movies} if direction == "reverse" else {}
            chunk = {"name": name, "direction": direction, "movies": movies,
                     "input_cache_sha256": cache_hashes, "gap_cache_sha256": gap_hashes}
            chunks.append(chunk)
            records = []
            for movie in movies:
                csv_path, receipt_path, _ = graph_files(run_root, name, movie)
                with csv_path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(verifier.COLUMNS)
                    writer.writerows(rows(movie))
                receipt = {"dataset": movie, "csv_sha256": sha(csv_path),
                           "nodes": 2, "edges": 1, "shape": [3, 20, 20, 20],
                           "input_cache_sha256": cache_hashes[movie],
                           "image_tree_sha256": digest("image-" + movie),
                           "labels_read": False}
                if direction == "reverse":
                    receipt["gap_cache_sha256"] = gap_hashes[movie]
                save(receipt_path, receipt)
                records.append({"dataset": movie, "csv_sha256": sha(csv_path),
                                "receipt_sha256": sha(receipt_path), "nodes": 2, "edges": 1})
            save(output / "status.json",
                 {"status": "PASS_EXP209_RECONSTRUCTION_CHUNK_NO_LABELS",
                  "chunk": name, "direction": direction, "movies": movies,
                  "records": records, "labels_read": False})
            save(output.parent / "completion.json",
                 {"status": "EXIT0", "exit_code": 0, "timed_out": False,
                  "worker_pid": 900000 + index + (100 if direction == "reverse" else 0),
                  "worker_start_tick": 1000 + index})
            completion = json.loads((output.parent / "completion.json").read_text())
            save(output.parent / "release.json",
                 {"status": "RELEASED", "worker_pid": completion["worker_pid"],
                  "worker_start_tick": completion["worker_start_tick"], "worker_absent": True})
    images = {movie: digest("image-" + movie)
              for direction in ("forward", "reverse") for movie in cohort[direction]}
    image_manifest_path = tmp_path / "image_only_sha_manifest.json"
    save(image_manifest_path,
         {"movie_count": 175, "data_audit_sha256": verifier.DATA_AUDIT_SHA,
          "data_manifest_sha256": verifier.DATA_MANIFEST_SHA,
          "image_tree_sha256_by_movie": images})
    contract = {"experiment": verifier.EXPERIMENT, "run_root": str(run_root),
                "code_dir": str((ROOT / "scripts").resolve()),
                "labels_read": False, "current_organizer_score": None,
                "frozen_policy": verifier.FROZEN_POLICY,
                "source_function_sha256": verifier.SOURCE_FUNCTION_SHA,
                "reference_graph_builder_sha256": verifier.GRAPH_BUILDER_SHA,
                "historical_result": str(result.resolve()),
                "historical_result_sha256": verifier.HISTORICAL_RESULT_SHA,
                "archive_manifest": str((ARCHIVE / "SHA256SUMS").resolve()),
                "archive_manifest_sha256": verifier.ARCHIVE_MANIFEST_SHA,
                "data_manifest": str(data_manifest.resolve()),
                "data_manifest_sha256": verifier.DATA_MANIFEST_SHA,
                "data_audit": str(data_audit.resolve()),
                "data_audit_sha256": verifier.DATA_AUDIT_SHA,
                "forward_source_selection": str((ROOT / "outputs/research/exp208_source_centroid_family_20260911/results/forward_selection.json").resolve()),
                "forward_source_selection_sha256": verifier.FORWARD_SELECTION_SHA,
                "source_trainer_manifests": {
                    "forward": {"path": str((ROOT / "outputs/research/exp130_official24_private_first/trainer_44b6_source.json").resolve()),
                                "sha256": verifier.SOURCE_TRAINER_SHA["forward"]},
                    "reverse": {"path": str((ROOT / "outputs/research/exp130_official24_private_first/exp137_remote_artifacts/trainer_6bba_source.json").resolve()),
                                "sha256": verifier.SOURCE_TRAINER_SHA["reverse"]}},
                "image_sha_manifest": str(image_manifest_path.resolve()),
                "image_sha_manifest_sha256": sha(image_manifest_path),
                "chunks": chunks}
    contract_path = tmp_path / "contract.json"
    save(contract_path, contract)
    contract_sha = sha(contract_path)
    save(run_root / "launch_intent.json",
         {"status": "LAUNCH_INTENT_CPU_ONLY_NO_LABELS", "contract_sha256": contract_sha,
          "labels_read": False, "gpu_used": False})
    preflight_path = run_root / "preflight.json"
    save(preflight_path,
         {"status": "PASS_EXP209_RECONSTRUCTION_INPUTS_NO_LABELS",
          "contract_sha256": contract_sha, "raw_candidate_count": 175,
          "reverse_gap_cache_count": 59, "image_count": 175,
          "image_tree_sha256_by_movie": images,
          "historical_image_manifest_sha256": verifier.DATA_MANIFEST_SHA,
          "historical_data_audit_sha256": verifier.DATA_AUDIT_SHA,
          "labels_read": False, "gpu_used": False})
    save(run_root / "preflight_completion.json",
         {"status": "EXIT0", "exit_code": 0, "timed_out": False,
          "worker_pid": 999999, "worker_start_tick": 12345, "worker_absent": True})
    save(run_root / "supervisor_complete.json",
         {"status": "ALL_EIGHT_CHUNKS_EXIT0_RELEASED_NO_LABELS",
          "contract_sha256": contract_sha, "movie_count": 175,
          "labels_read": False, "gpu_used": False})
    for chunk in chunks:
        status_path = run_root / "chunks" / chunk["name"] / "output" / "status.json"
        status = json.loads(status_path.read_text())
        status["contract_sha256"] = contract_sha
        status["preflight_sha256"] = sha(preflight_path)
        save(status_path, status)
    return contract_path, run_root, tmp_path / "no-proc"


def first_graph(synthetic: tuple[Path, Path, Path]) -> tuple[Path, str, str]:
    contract_path, run_root, _ = synthetic
    first = json.loads(contract_path.read_text())["chunks"][0]
    return run_root, first["name"], first["movies"][0]


def test_valid_175_graph_gate_and_one_shot(synthetic: tuple[Path, Path, Path]) -> None:
    contract_path, run_root, proc_root = synthetic
    gate = verifier.gate(contract_path, run_root, proc_root)
    assert gate["status"] == "PASS_EXP209_RECONSTRUCTION175_NO_METRIC_GATE"
    assert gate["movie_count"] == 175 and gate["direction_counts"] == {"forward": 116, "reverse": 59}
    assert len(gate["graph_hashes"]) == 175 and gate["labels_read"] is False
    assert gate["current_organizer_score"] is None
    output = run_root / "no_metric_gate.json"
    verifier.write_once_durable(output, gate)
    assert json.loads(output.read_text()) == gate
    with pytest.raises(verifier.GateError, match="existing gate"):
        verifier.write_once_durable(output, gate)


@pytest.mark.parametrize("tamper", ["csv", "receipt", "cache_pin", "cohort_pin",
                                    "preflight_image", "image_manifest"])
def test_hash_receipt_and_source_tamper_fail_closed(
    synthetic: tuple[Path, Path, Path], tamper: str
) -> None:
    contract_path, run_root, proc_root = synthetic
    _, chunk, movie = first_graph(synthetic)
    csv_path, receipt_path, status_path = graph_files(run_root, chunk, movie)
    if tamper == "csv":
        csv_path.write_bytes(csv_path.read_bytes() + b"\n")
    elif tamper == "receipt":
        receipt = json.loads(receipt_path.read_text())
        receipt["labels_read"] = True
        save(receipt_path, receipt)
        status = json.loads(status_path.read_text())
        status["records"][0]["receipt_sha256"] = sha(receipt_path)
        save(status_path, status)
    elif tamper == "preflight_image":
        preflight_path = run_root / "preflight.json"
        preflight = json.loads(preflight_path.read_text())
        preflight["image_tree_sha256_by_movie"][movie] = digest("wrong image")
        save(preflight_path, preflight)
        status = json.loads(status_path.read_text())
        status["preflight_sha256"] = sha(preflight_path)
        save(status_path, status)
    elif tamper == "image_manifest":
        contract = json.loads(contract_path.read_text())
        manifest_path = Path(contract["image_sha_manifest"])
        manifest = json.loads(manifest_path.read_text())
        manifest["image_tree_sha256_by_movie"][movie] = digest("wrong pinned image")
        save(manifest_path, manifest)
    else:
        contract = json.loads(contract_path.read_text())
        if tamper == "cache_pin":
            contract["chunks"][0]["input_cache_sha256"][movie] = digest("wrong")
        else:
            contract["historical_result_sha256"] = digest("wrong")
        save(contract_path, contract)
    with pytest.raises(verifier.GateError):
        verifier.gate(contract_path, run_root, proc_root)
    assert not (run_root / "no_metric_gate.json").exists()


@pytest.mark.parametrize("change", ["missing", "extra", "extra_chunk"])
def test_missing_or_extra_outputs_fail_closed(
    synthetic: tuple[Path, Path, Path], change: str
) -> None:
    contract_path, run_root, proc_root = synthetic
    _, chunk, movie = first_graph(synthetic)
    csv_path, _, _ = graph_files(run_root, chunk, movie)
    if change == "missing":
        csv_path.unlink()
    elif change == "extra":
        (csv_path.parent / "stray.csv").write_text("stray")
    else:
        (run_root / "chunks/forward_05").mkdir()
    with pytest.raises(verifier.GateError):
        verifier.gate(contract_path, run_root, proc_root)


@pytest.mark.parametrize("change", ["nonfinite", "wrong_time", "two_parents", "out_of_bounds"])
def test_semantically_invalid_resealed_graph_fails(
    synthetic: tuple[Path, Path, Path], change: str
) -> None:
    contract_path, run_root, proc_root = synthetic
    _, chunk, movie = first_graph(synthetic)
    values = rows(movie)
    if change == "nonfinite":
        values[0][5] = "nan"
    elif change == "wrong_time":
        values[1][4] = "0"
    elif change == "two_parents":
        values += [["3", movie, "node", "2", "0", "2", "2", "3", "-1", "-1"],
                   ["4", movie, "edge", "-1", "-1", "-1", "-1", "-1", "2", "1"]]
    else:
        values[0][5] = "20"
    reseal_graph(run_root, chunk, movie, values)
    with pytest.raises(verifier.GateError):
        verifier.gate(contract_path, run_root, proc_root)


@pytest.mark.parametrize("change", ["exit", "timeout", "release", "identity", "live_pid"])
def test_worker_exit_timeout_and_release_fail_closed(
    synthetic: tuple[Path, Path, Path], change: str
) -> None:
    contract_path, run_root, proc_root = synthetic
    folder = run_root / "chunks/forward_00"
    completion_path = folder / "completion.json"
    release_path = folder / "release.json"
    completion = json.loads(completion_path.read_text())
    release = json.loads(release_path.read_text())
    if change == "exit":
        completion["exit_code"] = 1
    elif change == "timeout":
        completion["timed_out"] = True
    elif change == "release":
        release["status"] = "RUNNING"
    elif change == "identity":
        release["worker_start_tick"] += 1
    else:
        stat = proc_root / str(completion["worker_pid"]) / "stat"
        stat.parent.mkdir(parents=True)
        # After field 2's closing parenthesis, start tick is field 22/index 19.
        fields = ["S"] + ["0"] * 18 + [str(completion["worker_start_tick"])]
        stat.write_text(f"{completion['worker_pid']} (synthetic worker) " + " ".join(fields))
    save(completion_path, completion)
    save(release_path, release)
    with pytest.raises(verifier.GateError):
        verifier.gate(contract_path, run_root, proc_root)


def test_wrong_historical_partition_is_rejected(synthetic: tuple[Path, Path, Path]) -> None:
    contract_path, run_root, proc_root = synthetic
    contract = json.loads(contract_path.read_text())
    left = contract["chunks"][0]["movies"]
    left[0], left[1] = left[1], left[0]
    save(contract_path, contract)
    with pytest.raises(verifier.GateError, match="partition"):
        verifier.gate(contract_path, run_root, proc_root)


@pytest.mark.parametrize("change", ["preflight_exit", "preflight_timeout", "supervisor",
                                    "policy", "source_selection_pin", "trainer_pin"])
def test_full_run_controls_fail_closed(
    synthetic: tuple[Path, Path, Path], change: str
) -> None:
    contract_path, run_root, proc_root = synthetic
    if change.startswith("preflight"):
        path = run_root / "preflight_completion.json"
        control = json.loads(path.read_text())
        control["exit_code" if change == "preflight_exit" else "timed_out"] = (
            1 if change == "preflight_exit" else True)
    elif change == "supervisor":
        path = run_root / "supervisor_complete.json"
        control = json.loads(path.read_text())
        control["status"] = "INCOMPLETE"
    else:
        path = contract_path
        control = json.loads(path.read_text())
        if change == "policy":
            control["frozen_policy"]["forward"]["minimum_length"] = 7
        elif change == "source_selection_pin":
            control["forward_source_selection_sha256"] = digest("wrong")
        else:
            control["source_trainer_manifests"]["reverse"]["sha256"] = digest("wrong")
    save(path, control)
    with pytest.raises(verifier.GateError):
        verifier.gate(contract_path, run_root, proc_root)
