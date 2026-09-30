"""Local-only source6 cancelled-attempt and distinct fair attempt1 contracts."""

import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp238_source6_waitsafe_a01 as a01
import reconcile_exp238_source6_attempt0 as attempt0


def queue_fixture(source44="RUNNING", foreign_waiting=False, second_allocated=False):
    pool = ["GPU-a", "GPU-b"]
    rows = [
        {"id": a01.OLD_LEASE_ID, "state": "CANCELLED", "gpus": [],
         "process": None, "pool": "a100", "project": a01.PROJECT},
        {"id": a01.SOURCE44_LEASE_ID, "state": source44,
         "gpus": ["GPU-a"] if source44 == "RUNNING" else [],
         "pool": "a100", "project": a01.PROJECT},
    ]
    if foreign_waiting:
        rows.append({"id": "foreign-wait", "state": "WAITING_RESOURCE",
                     "gpus": [], "pool": "a100", "project": "other-project"})
    if second_allocated:
        rows.append({"id": "other-running", "state": "RUNNING",
                     "gpus": ["GPU-b"], "pool": "a100", "project": "other-project"})
    return {"requests": rows, "pools": {"a100": {"gpus": pool}}}


def test_attempt0_receipt_is_cancelled_and_has_no_worker_or_gpu():
    assert attempt0.sha(attempt0.RECEIPT) == a01.ATTEMPT0_RECEIPT_SHA
    receipt = json.loads(attempt0.RECEIPT.read_text())
    assert receipt["lease"]["state"] == "CANCELLED"
    assert receipt["lease"]["gpus"] == [] and receipt["lease"]["process"] is None
    assert len(receipt["remote_probes"]) == 2
    assert all(not row["run_exists"] and row["matched_processes"] == []
               and row["gpu_matches"] == [] for row in receipt["remote_probes"])
    assert receipt["gpu_requested_again"] is False and receipt["remote_mutation"] is False


def test_distinct_attempt1_lease_and_same_sealed_code_plan_run():
    plan, local, stage = a01.local_gate()
    config = a01.launch_config(plan, stage["stage"]["manifest_sha256"],
                               local["plan_sha256"])
    assert a01.NEW_LEASE_ID != a01.OLD_LEASE_ID
    assert config["code"] == plan["code"] and config["run"] == plan["run"]
    assert config["arguments"][2] == local["plan_sha256"]
    assert stage["stage"]["plan_sha256"] == local["plan_sha256"]
    assert not any(a01.artifact(name).exists() for name in
                   ("intent", "reservation", "partial", "launch", "wait", "failure"))


@pytest.mark.parametrize("queue,busy,reason", [
    (queue_fixture(source44="RUNNING"), None, "SOURCE44_NOT_RELEASED"),
    (queue_fixture(source44="RELEASED", foreign_waiting=True), None, "FOREIGN_WAITING"),
    (queue_fixture(source44="RELEASED", second_allocated=True), {"GPU-a"},
     "NO_PHYSICALLY_IDLE_QUEUE_FREE_A100"),
    (queue_fixture(source44="RELEASED"), None, "PHYSICAL_GPU_STATUS_UNCHECKED"),
])
def test_fair_gate_defers_without_queue_request(queue, busy, reason):
    result = a01.fair_capacity(queue, busy)
    assert result["ready"] is False and result["reason"] == reason


def test_fair_gate_requires_released_source44_and_idle_queue_free_gpu():
    result = a01.fair_capacity(queue_fixture(source44="RELEASED"), {"GPU-a"})
    assert result == {"ready": True, "reason": "FAIR_A100_READY",
                      "queue_free": 2, "idle_gpu_uuids": ["GPU-b"]}


def test_default_review_makes_no_ssh_or_queue_request(monkeypatch, capsys):
    monkeypatch.setattr(a01, "ssh", lambda *args, **kwargs: pytest.fail("review called SSH"))
    monkeypatch.setattr(a01, "queue_request", lambda *args, **kwargs: pytest.fail("review queued"))
    monkeypatch.setattr(sys, "argv", ["launch_exp238_source6_waitsafe_a01.py"])
    a01.main()
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "EXP238_SOURCE6_A01_LOCAL_REVIEW_ONLY"
    assert result["gpu_request"] is False


def test_waiting_resource_is_recorded_once_without_worker(monkeypatch, tmp_path):
    plan, local, stage = a01.local_gate()
    monkeypatch.setattr(a01, "PREFIX", tmp_path / "exp238_a01")
    monkeypatch.setattr(a01, "remote_launch_preflight", lambda *args: {
        "status": "PASS_EXP238_LAUNCH_PREFLIGHT_NO_LABELS", "movies": 11,
        "run_absent": True, "labels_read": False})
    calls = []

    def waiting(args, request_id, token):
        calls.append((args, request_id, token))
        raise RuntimeError("Queue returned WAITING_RESOURCE; cancelled unlaunched request " + request_id)

    monkeypatch.setattr(a01, "queue_request", waiting)
    monkeypatch.setattr(a01, "confirm_waiting_cancelled", lambda p, c, e: {
        "status": "WAITING_RESOURCE_CANCELLED_UNLAUNCHED_EXP238_SOURCE6_ATTEMPT1",
        "error": e})
    result = a01.launch_once(plan, local, stage, {"ready": True, "reason": "FAIR_A100_READY"})
    assert result["status"].endswith("ATTEMPT1")
    assert len(calls) == 1 and calls[0][1] == a01.NEW_LEASE_ID
    assert a01.artifact("intent").exists()
    assert not a01.artifact("reservation").exists()
    assert not a01.artifact("partial").exists()


def test_remote_scripts_parse_without_launch(monkeypatch):
    plan, local, stage = a01.local_gate()
    scripts = []

    def capture(alias, command, source):
        assert alias == "nsu-a100" and command == "python3 -"
        ast.parse(source)
        scripts.append(source)
        return {"busy_gpu_uuids": []}

    monkeypatch.setattr(a01, "ssh", capture)
    assert a01.physical_busy() == set()
    assert len(scripts) == 1
    assert "nvidia-smi" in scripts[0]
