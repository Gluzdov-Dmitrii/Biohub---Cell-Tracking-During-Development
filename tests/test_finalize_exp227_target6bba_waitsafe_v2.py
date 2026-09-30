"""Focused future-only finalizer tests; no SSH, labels, queue request or GPU."""
import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import coordinate_exp227_target6bba as coord  # noqa: E402
import finalize_exp227_target6bba_waitsafe_v2 as final  # noqa: E402


def put(path, body):
    path.write_text(json.dumps(body, indent=2) + "\n")


def setup_attempt(tmp_path, monkeypatch, attempt):
    base = tmp_path / "attempt"

    def paths(index):
        return {name: base.with_name(f"attempt{index:02d}_{name}.json")
                for name in ("intent", "reservation", "partial", "result",
                             "prelaunch_release")}

    monkeypatch.setattr(final, "attempt_paths", paths)
    stage = json.loads(final.STAGE.read_text())
    base_config = json.loads(final.CONFIG.read_text())
    if attempt == 1:
        put(paths(0)["result"], {
            "status": "WAITING_RESOURCE_CANCELLED_NO_RUN", "attempt": 0,
            "lease_id": stage["lease_id"], "run": stage["run"],
            "cancelled": {"queue_row": {"state": "CANCELLED", "gpus": [],
                                         "process": None},
                          "run_worker": {"run_absent": True,
                                         "matching_processes": [],
                                         "matching_gpu_pids": []}},
            "target_labels_read": False, "kaggle_post": False})
    actual_lease = final.attempt_lease(stage["lease_id"], attempt)
    request = {**base_config, "lease_id": actual_lease}
    assigned = {**request, "gpu": "GPU-TEST", "alias": "nsu-a100"}
    lease = {"state": "RESERVED", "id": actual_lease, "run_path": stage["run"],
             "token": stage["token"], "owner": "biohub-agent",
             "project": "biohub-cell-tracking-during-development",
             "pool": "a100", "alias": "nsu-a100", "gpus": ["GPU-TEST"]}
    preflight = {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                 "manifest_sha256": final.MANIFEST_SHA,
                 "plan_sha256": final.PLAN_SHA, "run_absent": True}
    fair = {"status": "FAIR_IDLE_A100_AVAILABLE", "gpu": "GPU-TEST",
            "physical": {"all_gpus": ["GPU-TEST"], "busy_gpus": [],
                         "idle_gpus": ["GPU-TEST"]},
            "exp236_active_or_waiting": []}
    partial = {"status": "PARTIAL_EXP227_CHUNK07_V2_LAUNCH",
               "attempt": attempt, "lease": lease, "config": assigned,
               "launch": {"wrapper": 111, "observe": 112},
               "remote_preflight": preflight, "fair": fair,
               "stage_sha256": final.STAGE_SHA, "target_labels_read": False}
    result = {**partial, "status": "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V2",
              "control": {"controller_pid": 113}, "kaggle_post": False}
    put(paths(attempt)["intent"], {
        "status": "INTENT_EXP227_CHUNK07_V2_QUEUE_REQUEST",
        "attempt": attempt, "config": request, "remote_preflight": preflight,
        "fair": fair, "stage_sha256": final.STAGE_SHA,
        "target_labels_read": False, "kaggle_post": False})
    put(paths(attempt)["reservation"], {
        "status": "RESERVED_EXP227_CHUNK07_V2", "attempt": attempt,
        "lease": lease, "config": request, "fair": fair})
    put(paths(attempt)["partial"], partial)
    put(paths(attempt)["result"], result)
    return paths, result


class FakeOps:
    def __init__(self, local):
        self.local = local
        self.stopped = local["stopped"]
        self.run_index = {}
        self.queue = {"requests": []}
        for index in range(8):
            if index < 7:
                chunk = self.stopped["chunks"][index]
                stage = chunk["stage"]["result"]
                lease = chunk["launch"]["result"]["lease"]
                row = copy.deepcopy(chunk["postrun"]["queue_row"])
            else:
                stage = local["stage"]
                lease = local["result"]["lease"]
                row = {**lease, "state": "RELEASED", "gpus": [],
                       "process": {"pid": 1017, "start": "123456"}}
            self.run_index[stage["run"]] = (index, stage, row)
            self.queue["requests"].append(row)
        for prior in local["earlier_attempts"]:
            if prior["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN":
                self.queue["requests"].append({
                    "id": prior["lease_id"], "state": "CANCELLED",
                    "gpus": [], "process": None})

    def queue_status(self):
        return self.queue

    def completion(self, run):
        _, _, row = self.run_index[run]
        exit_record = {"returncode": 0, "hard_timeout": False}
        return {"exit": exit_record,
                "complete": {"status": "RELEASED_AFTER_VERIFIED_EXIT",
                             "exit": exit_record},
                "control": {"action": "release", "queue": row}}

    def postrun(self, stage):
        index = self.run_index[stage["run"]][0]
        if index < 7:
            return copy.deepcopy(self.stopped["chunks"][index]["postrun"]["gate"])
        return {"status": "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS",
                "chunk_index": 7, "movies": stage["movies"],
                "graph_hashes": [{"dataset": name, "csv_sha256": "a" * 64,
                                  "receipt_sha256": "b" * 64}
                                 for name in stage["movies"]],
                "manifest_sha256": stage["manifest_sha256"],
                "plan_sha256": stage["plan_sha256"],
                "checkpoint_sha256": stage["checkpoint_sha256"],
                "status_sha256": "c" * 64, "exit_sha256": "d" * 64,
                "supervision_sha256": "e" * 64, "control_sha256": "f" * 64,
                "queue_state_in_control": "RELEASED", "target_labels_read": False}

    def process(self, config):
        row = self.run_index[config["run"]][2]
        return {"launch": row["process"], "identity_alive": False,
                "group_alive": False, "matching_processes": [],
                "matching_gpu_pids": []}


@pytest.mark.parametrize("attempt", [0, 1])
def test_actual_attempt_is_sealed_and_default_is_check_only(tmp_path, monkeypatch, attempt):
    setup_attempt(tmp_path, monkeypatch, attempt)
    local = final.local_sources(attempt)
    ops = FakeOps(local)
    output = tmp_path / "final.json"
    summary = final.finalize(attempt, ops=ops, process_probe=ops.process, receipt=output)
    assert summary["mode"] == "CHECK_ONLY" and summary["graph_count"] == 116
    assert summary["actual_lease_id"] == final.attempt_lease(local["stage"]["lease_id"], attempt)
    assert not output.exists()
    written = final.finalize(attempt, write_receipt=True, ops=ops,
                             process_probe=ops.process, receipt=output)
    state = coord._read_state(output)
    assert written["receipt_sha256"] == coord.sha(output)
    assert state["successor_audit"]["actual_attempt"] == attempt
    assert state["chunks"][7]["stage"]["result"]["lease_id"] == summary["actual_lease_id"]
    assert state["chunks"][7]["stage"]["source_stage_lease_id"] == local["stage"]["lease_id"]
    assert len(state["successor_audit"]["first_seven_receipts"]) == 7
    with pytest.raises(ValueError, match="one-shot"):
        final.finalize(attempt, write_receipt=True, ops=ops,
                       process_probe=ops.process, receipt=output)


@pytest.mark.parametrize("damage", ["first_seven_hash", "last_receipt_hash",
                                    "timeout", "gpu_worker", "release"])
def test_failed_gate_never_writes(tmp_path, monkeypatch, damage):
    setup_attempt(tmp_path, monkeypatch, 0)
    local = final.local_sources(0)
    ops = FakeOps(local)
    probe = ops.process
    if damage == "first_seven_hash":
        postrun = ops.postrun
        def bad_postrun(stage):
            gate = postrun(stage)
            if gate["chunk_index"] == 0:
                gate["graph_hashes"][0]["csv_sha256"] = "0" * 64
            return gate
        ops.postrun = bad_postrun
    elif damage == "last_receipt_hash":
        postrun = ops.postrun
        def bad_postrun(stage):
            gate = postrun(stage)
            if gate["chunk_index"] == 7:
                gate["graph_hashes"][0]["receipt_sha256"] = "short"
            return gate
        ops.postrun = bad_postrun
    elif damage == "timeout":
        complete = ops.completion
        def bad_completion(run):
            body = complete(run)
            if ops.run_index[run][0] == 7:
                body["exit"]["hard_timeout"] = True
            return body
        ops.completion = bad_completion
    elif damage == "gpu_worker":
        def bad_process(config):
            body = ops.process(config)
            if ops.run_index[config["run"]][0] == 7:
                body["matching_gpu_pids"] = [1017]
            return body
        probe = bad_process
    else:
        ops.run_index[local["stage"]["run"]][2]["state"] = "RUNNING"
    output = tmp_path / "final.json"
    with pytest.raises((AssertionError, ValueError)):
        final.finalize(0, write_receipt=True, ops=ops,
                       process_probe=probe, receipt=output)
    assert not output.exists()


def test_no_actual_launch_fails_before_remote(monkeypatch):
    paths = lambda index: {name: ROOT / f"reports/__never_exp227_{index}_{name}.json"
                           for name in ("intent", "reservation", "partial", "result",
                                        "prelaunch_release")}
    monkeypatch.setattr(final, "attempt_paths", paths)
    class NoRemote:
        def queue_status(self):
            pytest.fail("remote call before launch receipt")
    with pytest.raises(FileNotFoundError):
        final.finalize(0, ops=NoRemote())
    assert not final.RECEIPT.exists()
