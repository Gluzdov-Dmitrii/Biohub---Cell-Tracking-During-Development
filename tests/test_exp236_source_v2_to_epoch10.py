"""Local-only checks for the finite EXP236 v2 training handoff."""
import ast
import os
from pathlib import Path
import sys
import time

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continue_exp236_source_v2_to_epoch10 as controller


def released(block):
    epoch = controller.EPOCHS[block]
    ex = {"returncode": 0, "hard_timeout": False}
    return {"queue_state": "RELEASED", "remote": {
        "epochs": epoch, "last_epoch": epoch,
        "result_status": f"PASS_EXP236_SOURCE_BLOCK_{epoch}_OF_50",
        "completed_epochs": epoch, "target_data_opened": False,
        "exit": ex, "complete_status": "RELEASED_AFTER_VERIFIED_EXIT",
        "supervision_exit_matches": True, "control_state": "RELEASED",
        "control_run_matches": True}}


@pytest.mark.parametrize("block", (1, 2, 3, 4))
def test_only_exact_released_epoch_passes(block):
    assert controller.block_released(block, released(block)) is True
    waiting = released(block)
    waiting["queue_state"] = "RUNNING"
    assert controller.block_released(block, waiting) is False


@pytest.mark.parametrize("change", ("failed_exit", "failed_result", "target_access",
                                     "bad_release", "short_history"))
def test_block_anomaly_stops_before_next_stage(change):
    observed = released(1)
    remote = observed["remote"]
    if change == "failed_exit":
        remote["exit"]["returncode"] = 1
    elif change == "failed_result":
        remote["result_status"] = "FAILED_EXP236_SOURCE_BLOCK01"
    elif change == "target_access":
        remote["target_data_opened"] = "attempt_blocked"
    elif change == "bad_release":
        remote["control_state"] = "RUNNING"
    else:
        remote["epochs"] = 2
    with pytest.raises((RuntimeError, AssertionError)):
        controller.block_released(1, observed)


def test_fair_resource_waits_for_other_project_and_free_gpu(monkeypatch):
    _, parent_run = controller.paths(1)
    parent = {"id": "exp236-horaz-source6bba-block01-v2-20260927",
              "run_path": parent_run, "pool": "a100", "state": "RELEASED",
              "project": controller.PROJECT, "gpus": []}
    queue = {"pools": {"a100": {"gpus": ["gpu-a", "gpu-b"]}},
             "requests": [parent, {"id": "other-waiting", "project": "other",
                                   "pool": "a100", "state": "WAITING_RESOURCE", "gpus": []}]}
    monkeypatch.setattr(controller, "queue_status", lambda: queue)
    observed = controller.resource_probe(1, 2)
    assert observed == {"other_projects_waiting": ["other-waiting"],
                        "free_queue_gpu_count": 2}
    queue["requests"].pop()
    queue["requests"].extend([
        {"id": "active-a", "project": controller.PROJECT,
         "pool": "a100", "state": "RUNNING", "gpus": ["gpu-a"]},
        {"id": "active-b", "project": "other",
         "pool": "a100", "state": "RESERVED", "gpus": ["gpu-b"]},
    ])
    occupied = controller.resource_probe(1, 2)
    assert occupied["free_queue_gpu_count"] == 0
    assert occupied["other_projects_waiting"] == []
    queue["requests"].pop()
    assert controller.resource_probe(1, 2) == {"other_projects_waiting": [],
                                               "free_queue_gpu_count": 1}


def test_terminal_anomaly_is_not_repolled(monkeypatch):
    monkeypatch.setattr(controller, "save", lambda _state: None)
    monkeypatch.setattr(controller.time, "sleep", lambda _seconds: pytest.fail("unexpected sleep"))
    calls = []
    def bad_probe():
        calls.append(1)
        raise controller.TerminalAnomaly("bad release")
    with pytest.raises(controller.TerminalAnomaly):
        controller.wait_for("release", 3600, bad_probe, lambda _value: False, {})
    assert len(calls) == 1


def test_block01_rejected_prelaunch_stops_immediately(tmp_path, monkeypatch):
    files = {name: tmp_path / name for name in ("launch", "reservation", "partial",
                                               "prelaunch_release")}
    files["prelaunch_release"].write_text("rejected")
    monkeypatch.setattr(controller, "local_paths", lambda _block: files)
    with pytest.raises(controller.TerminalAnomaly):
        controller.block01_launch_probe()
    files["prelaunch_release"].unlink()
    files["partial"].write_text("partial")
    old = time.time() - 901
    os.utime(files["partial"], (old, old))
    with pytest.raises(controller.TerminalAnomaly):
        controller.block01_launch_probe()


def test_remote_audit_template_and_parent_hash_chain(monkeypatch):
    parent = {"checkpoint_sha256": "c" * 64, "history_sha256": "h" * 64,
              "result_sha256": "r" * 64, "plan_sha256": "p" * 64,
              "manifest_sha256": "m" * 64}
    prepared = {"stage": {"manifest_sha256": "a" * 64,
                          "plan_sha256": "b" * 64}}
    config = {"alias": "nsu-a100"}
    plan = {"parent_completed_epochs": 3, "parent_checkpoint_sha256": "c" * 64,
            "parent_history_sha256": "h" * 64, "parent_result_sha256": "r" * 64,
            "parent_plan_sha256": "p" * 64,
            "parent_code_manifest_sha256": "m" * 64}
    monkeypatch.setattr(controller, "local_block",
                        lambda _block, launched: (prepared, config, plan, {}))
    seen = []
    def fake_ssh(alias, command, source):
        assert alias == "nsu-a100" and command == "python3 -"
        ast.parse(source)
        assert "@@" not in source
        seen.append(source)
        return {"status": "PASS_EXP236_SOURCE_V2_BLOCK_AUDIT", "block": 2,
                "completed_epochs": 6, "manifest_sha256": "a" * 64,
                "plan_sha256": "b" * 64, "target_data_opened": False}
    monkeypatch.setattr(controller, "ssh", fake_ssh)
    assert controller.audit_block(2, parent)["completed_epochs"] == 6
    assert len(seen) == 1
    plan["parent_checkpoint_sha256"] = "wrong"
    with pytest.raises(AssertionError):
        controller.audit_block(2, parent)
    assert len(seen) == 1


def test_existing_child_artifact_prevents_controller_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, "ROOT", tmp_path)
    monkeypatch.setattr(controller, "RECEIPT", tmp_path / "reports/controller.json")
    child_config = controller.local_paths(2)["config"]
    child_config.parent.mkdir(parents=True)
    child_config.write_text("existing")
    with pytest.raises(AssertionError):
        controller.main()
    assert not controller.RECEIPT.exists()
