"""Focused checks for the read-only EXP238 completion gate."""

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_exp238_peak_cache_completion as verifier


def fake_remote(local):
    rows = [{"dataset": movie["dataset"],
             "graph_csv_sha256": movie["graph_csv_sha256"],
             "record_sha256": "a" * 64,
             "peak_npy_sha256": "b" * 64,
             "peak_metadata_sha256": "c" * 64,
             "peak_count": 1, "peak_payload_bytes": 12}
            for movie in local["plan"]["movies"]]
    return {"status": "PASS_EXP238_PEAK_CACHE_COMPLETION_NO_LABELS",
            "cohort": local["cohort"], "movie_count": len(rows),
            "peak_count": len(rows), "peak_payload_bytes": 12 * len(rows),
            "rows": rows,
            "code_manifest_sha256": local["pins"]["manifest_sha256"],
            "plan_sha256": local["pins"]["plan_sha256"],
            "parent_status_sha256": local["plan"]["parent_status_sha256"],
            "status_sha256": "d" * 64,
            "source_labels_read": False, "target_data_opened": False,
            "identity_alive": False, "group_alive": False,
            "matching_processes": [], "worker_gpu_pids": [],
            "worker_process": {"pid": 123, "start": "456"}}


def fake_queue(_):
    return {"id": "exp238-source44-peak-cache-v1-20260927",
            "state": "RELEASED", "process": {"pid": 123, "start": "456"},
            "gpus": []}


def test_exact_local_source44_and_source6_pins_and_remote_source_compile():
    for cohort in ("source44", "source6"):
        local = verifier.local_gate(cohort)
        assert local["stage_sha256"] == verifier.PINS[cohort]["stage_sha256"]
        assert local["launch_sha256"] == verifier.PINS[cohort]["launch_sha256"]
        source = verifier.remote_source(local)
        compile(source, f"remote_{cohort}.py", "exec")
        assert "struct.iter_unpack('<HHHHf',body)" in source
        assert "parent_status['records']" in source


def test_optimized_local_and_remote_python_rejected():
    probe = subprocess.run([sys.executable, "-O", "-c",
                            "import sys;sys.path.insert(0,'scripts');"
                            "import verify_exp238_peak_cache_completion"],
                           capture_output=True, text=True)
    assert probe.returncode != 0
    assert "requires Python assertions enabled" in probe.stderr
    source = verifier.remote_source(verifier.local_gate("source44"))
    with pytest.raises(RuntimeError, match="requires Python assertions enabled"):
        exec(compile(source, "remote_optimized.py", "exec", optimize=1), {})


def test_local_receipt_tamper_fails_before_remote(monkeypatch):
    pins = copy.deepcopy(verifier.PINS)
    pins["source44"]["launch_sha256"] = "0" * 64
    monkeypatch.setattr(verifier, "PINS", pins)
    with pytest.raises(AssertionError):
        verifier.local_gate("source44")


def test_check_only_then_one_shot_receipt(tmp_path):
    path = tmp_path / "verified.json"
    checked = verifier.verify("source44", queue_reader=fake_queue,
                              remote_reader=fake_remote, receipt_path=path)
    assert checked["status"] == "PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION"
    assert checked["receipt"] is None and not path.exists()
    written = verifier.verify("source44", queue_reader=fake_queue,
                              remote_reader=fake_remote, receipt_path=path,
                              write_receipt=True)
    assert written["receipt_sha256"] == verifier.sha(path)
    with pytest.raises(AssertionError):
        verifier.verify("source44", queue_reader=fake_queue,
                        remote_reader=fake_remote, receipt_path=path,
                        write_receipt=True)


def test_guarded_recheck_keeps_original_and_writes_distinct_receipts(tmp_path, monkeypatch):
    original = json.loads(verifier.ORIGINAL_SOURCE44_RECEIPT.read_text())
    recheck = tmp_path / "recheck.json"
    correction = tmp_path / "correction.json"
    monkeypatch.setattr(verifier, "SOURCE44_RECHECK", recheck)
    monkeypatch.setattr(verifier, "SOURCE44_CORRECTION", correction)
    monkeypatch.setattr(verifier, "verify", lambda *args, **kwargs: original)
    checked = verifier.recheck_source44()
    assert checked["identical_receipt_payload"] is True
    assert not recheck.exists() and not correction.exists()
    written = verifier.recheck_source44(write_receipts=True)
    assert written["recheck_receipt_sha256"] == verifier.sha(recheck)
    assert written["correction_receipt_sha256"] == verifier.sha(correction)
    assert json.loads(recheck.read_text())["verification"] == original
    with pytest.raises(AssertionError):
        verifier.recheck_source44(write_receipts=True)


@pytest.mark.parametrize("damage", ["graph", "labels", "process", "queue"])
def test_bad_remote_evidence_blocks_receipt(tmp_path, damage):
    path = tmp_path / "verified.json"

    def remote(local):
        result = fake_remote(local)
        if damage == "graph":
            result["rows"][0]["graph_csv_sha256"] = "0" * 64
        elif damage == "labels":
            result["source_labels_read"] = True
        elif damage == "process":
            result["worker_gpu_pids"] = [123]
        return result

    def queue(local):
        row = fake_queue(local)
        if damage == "queue":
            row["state"] = "RUNNING"
        return row

    with pytest.raises(AssertionError):
        verifier.verify("source44", queue_reader=queue, remote_reader=remote,
                        receipt_path=path, write_receipt=True)
    assert not path.exists()
