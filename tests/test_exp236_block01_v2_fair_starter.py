"""No remote launch tests for the EXP236 v2 one-shot fair starter."""
import ast
import json
from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import start_exp236_source_block01_v2_when_fair as starter


def empty_files(tmp_path):
    return {name: tmp_path / name for name in ("reservation", "partial",
                                              "prelaunch_release", "launch", "prepare")}


def test_fair_capacity_excludes_foreign_reserved_gpu_but_allows_free_second(tmp_path, monkeypatch):
    files = empty_files(tmp_path)
    monkeypatch.setattr(starter.continuation, "local_paths", lambda _block: files)
    queue = {"pools": {"a100": {"gpus": ["gpu-a", "gpu-b"]}},
             "requests": [{"id": "foreign-reserved", "project": "other",
                           "pool": "a100", "state": "RESERVED", "gpus": ["gpu-a"]}]}
    monkeypatch.setattr(starter.continuation, "queue_status", lambda: queue)
    monkeypatch.setattr(starter, "physical_busy", lambda: set())
    assert starter.fair_capacity() == {"foreign_waiting": [], "queue_free": 1,
                                      "physically_idle_queue_free": 1}
    monkeypatch.setattr(starter, "physical_busy", lambda: {"gpu-b"})
    assert starter.fair_capacity()["physically_idle_queue_free"] == 0
    queue["requests"].append({"id": "other-waiting", "project": "other",
                              "pool": "a100", "state": "WAITING_RESOURCE", "gpus": []})
    assert starter.fair_capacity()["foreign_waiting"] == ["other-waiting"]


def test_existing_reservation_or_lease_is_terminal(tmp_path, monkeypatch):
    files = empty_files(tmp_path)
    monkeypatch.setattr(starter.continuation, "local_paths", lambda _block: files)
    queue = {"pools": {"a100": {"gpus": ["gpu-a"]}}, "requests": []}
    monkeypatch.setattr(starter.continuation, "queue_status", lambda: queue)
    files["reservation"].write_text("exists")
    with pytest.raises(starter.TerminalAnomaly):
        starter.fair_capacity()
    files["reservation"].unlink()
    queue["requests"].append({"id": "exp236-horaz-source6bba-block01-v2-20260927",
                              "project": starter.PROJECT, "pool": "a100",
                              "state": "RESERVED", "gpus": ["gpu-a"]})
    with pytest.raises(starter.TerminalAnomaly):
        starter.fair_capacity()


def test_immutable_remote_gate_template_compiles(monkeypatch):
    prepared = {"stage": {"manifest_sha256": starter.CODE_MANIFEST_SHA256,
                          "plan_sha256": starter.PLAN_SHA256}}
    config = {"code": "/remote/code", "run": "/remote/run"}
    captured = []
    def fake_ssh(alias, command, source):
        assert alias == "nsu-a100" and command == "python3 -"
        ast.parse(source)
        assert "@@" not in source
        captured.append(source)
        return {"status": "PASS_EXP236_V2_BLOCK01_STARTER_STAGE_GATE",
                "manifest_sha256": starter.CODE_MANIFEST_SHA256,
                "plan_sha256": starter.PLAN_SHA256, "run_exists": False}
    monkeypatch.setattr(starter, "ssh", fake_ssh)
    assert starter.remote_stage_gate(prepared, config)["run_exists"] is False
    assert len(captured) == 1


def test_physical_gpu_probe_is_read_only_and_parses_uuid(monkeypatch):
    def fake_ssh(alias, command, source):
        assert alias == "nsu-a100" and command == "python3 -"
        ast.parse(source)
        assert "nvidia-smi" in source and "query-compute-apps" in source
        return {"busy_gpu_uuids": ["GPU-busy"]}
    monkeypatch.setattr(starter, "ssh", fake_ssh)
    assert starter.physical_busy() == {"GPU-busy"}


def test_launch_once_records_only_one_attempt(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(starter, "ROOT", tmp_path)
    monkeypatch.setattr(starter, "RECEIPT", reports / "starter.json")
    monkeypatch.setattr(starter, "assert_fresh", lambda: None)
    attempts = []
    def fake_run(args, **_kwargs):
        attempts.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="launched\n", stderr="")
    monkeypatch.setattr(starter.subprocess, "run", fake_run)
    state = {"status": "waiting", "launch_attempted": False}
    starter.claim(state)
    starter.launch_once(state)
    assert state["launch_attempted"] is True and state["launch_returncode"] == 0
    assert len(attempts) == 1
    assert (reports / "exp236_block01_v2_fair_starter_launch_20260927.log").is_file()


def test_hidden_continuation_handoff_claims_its_receipt(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(starter, "ROOT", tmp_path)
    monkeypatch.setattr(starter, "RECEIPT", reports / "starter.json")
    monkeypatch.setattr(starter.continuation, "RECEIPT", reports / "continuation.json")
    state = {"status": "launched"}
    starter.claim(state)
    spawned = []
    class FakeProcess:
        pid = 81234
        def poll(self):
            return None
    def fake_popen(args, **kwargs):
        spawned.append((args, kwargs["creationflags"]))
        starter.continuation.RECEIPT.write_text(json.dumps({"status": "WAITING_FOR_RELEASE"}))
        return FakeProcess()
    monkeypatch.setattr(starter.subprocess, "Popen", fake_popen)
    handoff = starter.start_continuation(state)
    assert handoff["pid"] == 81234 and handoff["status"] == "WAITING_FOR_RELEASE"
    assert len(spawned) == 1
    assert (reports / "exp236_source_v2_to_epoch10_20260927.stdout.log").is_file()


def test_launch_readback_requires_live_worker_and_queue_identity(tmp_path, monkeypatch):
    files = empty_files(tmp_path)
    files["launch"].write_text("launch")
    files["prepare"].write_text("prepare")
    prepared = {"stage": {"manifest_sha256": starter.CODE_MANIFEST_SHA256}}
    config = {"code": "/remote/code", "run": "/remote/run", "alias": "nsu-a100",
              "gpu": "gpu-a", "token": "token"}
    launch = {"lease": {"gpus": ["gpu-a"]},
              "launch": {"wrapper": 123, "observe": 124},
              "control": {"controller_pid": 125}}
    monkeypatch.setattr(starter.continuation, "local_block",
                        lambda _block, launched: (prepared, config, {}, launch))
    monkeypatch.setattr(starter.continuation, "local_paths", lambda _block: files)
    monkeypatch.setattr(starter.continuation, "queue_status", lambda: {"requests": []})
    lease = {"owner": "biohub-agent", "project": starter.PROJECT, "token": "token",
             "state": "RUNNING", "alias": "nsu-a100", "gpus": ["gpu-a"]}
    monkeypatch.setattr(starter.continuation, "lease_for", lambda _queue, _block: lease)
    hosts = []
    def fake_ssh(alias, command, source):
        assert command == "python3 -"
        ast.parse(source)
        assert "@@" not in source
        hosts.append(alias)
        if alias == "nsu-a100":
            assert "wrapper_live" in source and "observer_live" in source
            assert "controller_live" not in source
            return {"run_exists": True, "exit": None,
                    "wrapper_live": True, "observer_live": True}
        assert alias == "nsu-quadro" and "controller_live" in source
        assert "wrapper_live" not in source and "observer_live" not in source
        return {"controller_live": True}
    monkeypatch.setattr(starter, "ssh", fake_ssh)
    assert starter.launch_readback()["queue_state"] == "RUNNING"
    assert hosts == ["nsu-a100", "nsu-quadro"]
    def missing_wrapper(alias, _command, _source):
        return ({"run_exists": True, "exit": None,
                 "wrapper_live": False, "observer_live": True}
                if alias == "nsu-a100" else {"controller_live": True})
    monkeypatch.setattr(starter, "ssh", missing_wrapper)
    with pytest.raises(AssertionError):
        starter.launch_readback()
    def missing_controller(alias, _command, _source):
        return ({"run_exists": True, "exit": None,
                 "wrapper_live": True, "observer_live": True}
                if alias == "nsu-a100" else {"controller_live": False})
    monkeypatch.setattr(starter, "ssh", missing_controller)
    with pytest.raises(AssertionError):
        starter.launch_readback()


def test_main_one_shot_handoff_and_ambiguous_failure_stop(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    prepare = reports / "prepared.json"
    prepare.write_text("prepared")
    monkeypatch.setattr(starter, "ROOT", tmp_path)
    monkeypatch.setattr(starter, "RECEIPT", reports / "starter.json")
    monkeypatch.setattr(starter, "assert_fresh", lambda: None)
    monkeypatch.setattr(starter.continuation, "local_paths", lambda _block: {"prepare": prepare})
    prepared = {"status": "prepared"}
    config = {"run": "/remote/run"}
    monkeypatch.setattr(starter, "local_stage_gate", lambda: (prepared, config))
    monkeypatch.setattr(starter, "fair_capacity", lambda: {"foreign_waiting": [],
        "queue_free": 1, "physically_idle_queue_free": 1})
    monkeypatch.setattr(starter, "remote_stage_gate", lambda *_args: {"status": "pass"})
    monkeypatch.setattr(starter, "launch_readback", lambda: {"status": "verified"})
    monkeypatch.setattr(starter, "start_continuation", lambda _state: {"status": "started"})
    attempts = []
    def launch_once(state):
        attempts.append(1)
        state["launch_attempted"] = True
    monkeypatch.setattr(starter, "launch_once", launch_once)
    starter.main()
    saved = json.loads(starter.RECEIPT.read_text())
    assert saved["status"] == "PASS_EXP236_BLOCK01_V2_FAIR_STARTER_HANDOFF"
    assert len(attempts) == 1

    starter.RECEIPT.unlink()
    attempts.clear()
    def ambiguous(state):
        attempts.append(1)
        state["launch_attempted"] = True
        raise starter.TerminalAnomaly("ambiguous launch")
    monkeypatch.setattr(starter, "launch_once", ambiguous)
    monkeypatch.setattr(starter, "reconcile_failed_launch", lambda: {"run_exists": True})
    with pytest.raises(starter.TerminalAnomaly):
        starter.main()
    saved = json.loads(starter.RECEIPT.read_text())
    assert saved["status"] == "STOPPED_EXP236_BLOCK01_V2_FAIR_STARTER"
    assert saved["launch_failure_reconciliation"] == {"run_exists": True}
    assert len(attempts) == 1
