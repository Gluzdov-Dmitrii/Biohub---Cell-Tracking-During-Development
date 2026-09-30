"""Regression and stop gates for the staged EXP236 v2 recovery."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continue_exp236_source_v2_to_epoch10 as chain
import prepare_exp236_source_resume_v2 as prepare
import recover_exp236_source_v2_to_epoch10 as recovery


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_resume_plan_hash_normalizes_only_windows_line_endings(tmp_path):
    path = tmp_path / "plan.json"
    staged = b'{\n  "experiment": "EXP236",\n  "block_end_epoch": 6\n}\n'
    path.write_bytes(staged.replace(b"\n", b"\r\n"))
    assert chain.staged_plan_sha(path, 2) == digest(staged)
    assert prepare.staged_parent_plan_sha(path, 2) == digest(staged)
    assert chain.staged_plan_sha(path, 1) == digest(path.read_bytes())
    assert prepare.staged_parent_plan_sha(path, 1) == digest(path.read_bytes())
    assert chain.staged_plan_sha(path, 1) != digest(staged)
    path.write_bytes(path.read_bytes().replace(b'"EXP236"', b'"EXP236" '))
    assert chain.staged_plan_sha(path, 2) != digest(staged)
    assert prepare.staged_parent_plan_sha(path, 2) != digest(staged)
    path.write_bytes(staged.replace(b"\n", b"\r"))
    with pytest.raises(AssertionError, match="unexpected CR"):
        chain.staged_plan_sha(path, 2)
    with pytest.raises(AssertionError, match="unexpected CR"):
        prepare.staged_parent_plan_sha(path, 2)


def test_existing_artifact_blocks_recovery_stage(tmp_path, monkeypatch):
    files = {name: tmp_path / f"{name}.json" for name in
             ("config", "prepare", "plan", "launch", "reservation",
              "partial", "prelaunch_release")}
    monkeypatch.setattr(chain, "local_paths", lambda _block: files)
    for name in ("launch", "reservation", "partial", "prelaunch_release"):
        files[name].write_text("existing")
        with pytest.raises(recovery.Reconcile, match=name):
            recovery.unused_artifacts(2)
        files[name].unlink()


def test_existing_child_queue_claim_blocks_recovery(monkeypatch):
    parent_code, parent_run = recovery.paths(1)
    child_code, child_run = recovery.paths(2)
    parent = {"id": "exp236-horaz-source6bba-block01-v2-20260927",
              "run_path": parent_run, "pool": "a100", "state": "RELEASED"}
    child = {"id": "other-id", "run_path": child_run,
             "pool": "a100", "state": "WAITING_RESOURCE"}
    queue = {"requests": [parent, child]}
    monkeypatch.setattr(chain, "queue_status", lambda: queue)
    with pytest.raises(recovery.Reconcile, match="queue claim"):
        recovery.queue_gate(1, 2)
    child["run_path"] = "/different/run"
    child["id"] = "exp236-horaz-source6bba-block02-v2-20260927"
    with pytest.raises(recovery.Reconcile, match="queue claim"):
        recovery.queue_gate(1, 2)
    child["id"] = "other-id"
    assert recovery.queue_gate(1, 2) is queue


def test_read_only_default_never_claims_or_launches(monkeypatch, capsys):
    proof = {"status": "PASS_EXP236_SOURCE_V2_RECOVERY_PREFLIGHT"}
    monkeypatch.setattr(recovery, "preflight", lambda: proof)
    monkeypatch.setattr(recovery, "run", lambda _proof: pytest.fail("launched"))
    monkeypatch.setattr(sys, "argv", ["recover_exp236_source_v2_to_epoch10.py"])
    recovery.main()
    assert json.loads(capsys.readouterr().out) == proof
