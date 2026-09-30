"""Stop and parent contracts for EXP236 recovered source11 handoff."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recover_exp236_source11_handoff as recovery


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_original_handoff_must_have_stopped_before_graph_stage(tmp_path, monkeypatch):
    original_path = tmp_path / "original.json"
    row = {"status": "STOPPED_EXP236_SOURCE11_HANDOFF",
           "training_run": recovery.handoff.TRAIN_RUN,
           "source_graph_run": recovery.handoff.GRAPH_RUN,
           "source_score_run": recovery.handoff.SCORE_RUN,
           "source_labels_opened_before_graphs": False,
           "target_data_opened": False, "started": 1, "finished_or_stopped": 2,
           "error": "TerminalAnomaly('EXP236 training controller stopped: AssertionError()')"}
    original_path.write_text(json.dumps(row))
    monkeypatch.setattr(recovery, "ORIGINAL", original_path)
    monkeypatch.setattr(recovery, "live_original_pids", lambda: [])
    assert recovery.original_gate() == digest(original_path)
    row["prepare_graph_returncode"] = 0
    original_path.write_text(json.dumps(row))
    with pytest.raises(AssertionError):
        recovery.original_gate()
    row.pop("prepare_graph_returncode")
    row["target_data_opened"] = True
    original_path.write_text(json.dumps(row))
    with pytest.raises(AssertionError):
        recovery.original_gate()


def test_training_recovery_waits_for_new_receipt_and_exact_final_chain(tmp_path, monkeypatch):
    stopped = tmp_path / "stopped.json"
    stopped.write_text("{}")
    live = tmp_path / "recovery.json"
    recovery_row = {"status": "WAITING_FOR_EXP236_BLOCK02_V2_RELEASE",
                    "original_receipt_sha256": digest(stopped),
                    "target_data_opened": False,
                    "block01_audit": {"completed_epochs": 3}}
    live.write_text(json.dumps(recovery_row))
    monkeypatch.setattr(recovery, "ORIGINAL_CONTROLLER_RECEIPT", stopped)
    monkeypatch.setattr(recovery, "TRAIN_RECOVERY", live)
    monkeypatch.setattr(recovery, "verify_parent_chain",
                        lambda: pytest.fail("audited before PASS"))
    assert recovery.recovery_receipt_gate() == {"status": recovery_row["status"]}
    recovery_row["status"] = "STOPPED_EXP236_SOURCE_V2_RECOVERY"
    recovery_row["error"] = "worker failed"
    live.write_text(json.dumps(recovery_row))
    with pytest.raises(recovery.Reconcile, match="stopped"):
        recovery.recovery_receipt_gate()
    recovery_row.pop("error")
    recovery_row["status"] = "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    chain = [{"completed_epochs": epoch} for epoch in (3, 6, 9)]
    chain.append({"completed_epochs": 10, "run": recovery.handoff.TRAIN_RUN,
                  "checkpoint_sha256": "c" * 64, "result_sha256": "r" * 64})
    recovery_row["final_audit"] = {key: value for key, value in chain[-1].items()
                                   if key != "run"}
    live.write_text(json.dumps(recovery_row))
    monkeypatch.setattr(recovery, "verify_parent_chain", lambda: (chain, digest(live)))
    observed = recovery.recovery_receipt_gate()
    assert observed["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    assert observed["controller_sha256"] == digest(live)
    chain[2]["completed_epochs"] = 8
    with pytest.raises(AssertionError):
        recovery.recovery_receipt_gate()


def test_graph_artifact_or_queue_claim_prevents_preflight(tmp_path, monkeypatch):
    for key in ("GRAPH_PLAN", "GRAPH_CONFIG", "GRAPH_PREPARED", "GRAPH_LAUNCHED",
                "GRAPH_RESERVATION", "GRAPH_PARTIAL", "GRAPH_PRELAUNCH_RELEASE",
                "SCORE_PREPARED", "SCORE_LAUNCHED", "SCORE_VERIFIED"):
        monkeypatch.setattr(recovery.handoff, key, tmp_path / key)
    recovery.handoff.GRAPH_RESERVATION.write_text("existing")
    with pytest.raises(recovery.Reconcile, match="artifact"):
        recovery.no_local_stage_artifacts()
    recovery.handoff.GRAPH_RESERVATION.unlink()
    monkeypatch.setattr(recovery.handoff, "queue_status", lambda: {"requests": [{
        "id": "other", "run_path": recovery.handoff.GRAPH_RUN}]})
    with pytest.raises(recovery.Reconcile, match="queue claim"):
        recovery.graph_queue_absent()


def test_fair_graph_probe_requires_capacity_and_physical_idle(tmp_path, monkeypatch):
    for key in ("GRAPH_RESERVATION", "GRAPH_PARTIAL",
                "GRAPH_PRELAUNCH_RELEASE", "GRAPH_LAUNCHED"):
        monkeypatch.setattr(recovery.handoff, key, tmp_path / key)
    parent = {"id": "exp236-horaz-source6bba-block04-v2-20260927",
              "run_path": recovery.handoff.TRAIN_RUN, "pool": "a100",
              "state": "RELEASED", "project": recovery.handoff.PROJECT}
    queue = {"pools": {"a100": {"gpus": ["GPU-a"], "cpu": 7,
                                 "ram_gib": 64}}, "requests": [parent]}
    monkeypatch.setattr(recovery.handoff, "queue_status", lambda: queue)
    monkeypatch.setattr(recovery.handoff, "physical_busy", lambda: set())
    assert recovery.fair_graph_probe()["ready"] is False
    queue["pools"]["a100"]["cpu"] = 8
    assert recovery.fair_graph_probe()["ready"] is True
    monkeypatch.setattr(recovery.handoff, "physical_busy", lambda: {"GPU-a"})
    assert recovery.fair_graph_probe()["ready"] is False
    queue["requests"].append({"id": "foreign", "run_path": "/other/run",
                              "pool": "a100", "state": "WAITING_RESOURCE",
                              "project": "other"})
    assert recovery.fair_graph_probe()["waiting"] == ["foreign"]


def test_read_only_default_never_claims_or_stages(monkeypatch, capsys):
    proof = {"status": "PASS_EXP236_SOURCE11_RECOVERY_PREFLIGHT",
             "training_recovery_status": "WAITING_FOR_EXP236_BLOCK02_V2_RELEASE"}
    monkeypatch.setattr(recovery, "preflight", lambda: proof)
    monkeypatch.setattr(recovery, "run", lambda _proof: pytest.fail("launched"))
    monkeypatch.setattr(sys, "argv", ["recover_exp236_source11_handoff.py"])
    recovery.main()
    assert json.loads(capsys.readouterr().out) == proof
