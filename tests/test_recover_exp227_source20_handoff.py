"""Fail-closed contracts for the separate EXP227 fair-resource recovery."""
import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recover_exp227_source20_handoff as recovery  # noqa: E402


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) if not isinstance(value, str) else value)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def training_observation():
    return {"exit": {"returncode": 0, "hard_timeout": False},
            "result_status": "PASS_FULL_SOURCE_BLOCK_20_OF_50",
            "completed_epochs": 20, "epochs": 20, "last_epoch": 20,
            "target_data_opened": False, "checkpoint20_exists": True,
            "complete_status": "RELEASED_AFTER_VERIFIED_EXIT", "control_state": "RELEASED"}


def stopped_handoff(root):
    log = root / "reports/exp227_source20_handoff_launch_graph_20260927.log"
    put(log, "--- stderr ---\nAssertionError: Other project waiting; defer\n")
    original = {"status": "STOPPED_EXP227_SOURCE20_HANDOFF",
                "training_run": recovery.TRAIN_RUN, "source_graph_run": recovery.RUN,
                "source_score_run": recovery.SCORE_RUN,
                "source_labels_opened_before_inference": False,
                "target_labels_opened": False, "started": 1, "finished_or_stopped": 2,
                "prepare_graph_returncode": 0, "launch_graph_returncode": 1,
                "launch_graph_log": str(log), "error": "RuntimeError('launch_graph returned 1')",
                "training_release_or_exit": [
                    {"id": recovery.TRAIN_LEASE, "state": "RELEASED",
                     "run_path": recovery.TRAIN_RUN}, training_observation()]}
    receipt = root / "handoff.json"
    put(receipt, original)
    return receipt, original


def test_original_must_be_terminal_fair_stop_and_no_live_process(tmp_path, monkeypatch):
    receipt, original = stopped_handoff(tmp_path)
    monkeypatch.setattr(recovery, "ROOT", tmp_path)
    monkeypatch.setattr(recovery, "HANDOFF", receipt)
    monkeypatch.setattr(recovery, "live_handoff_pids", lambda: [])
    assert recovery.original_gate()[0] == original
    monkeypatch.setattr(recovery, "live_handoff_pids", lambda: [25908])
    with pytest.raises(recovery.Reconcile, match="still alive"):
        recovery.original_gate()
    monkeypatch.setattr(recovery, "live_handoff_pids", lambda: [])
    for change in ({"status": "WAITING_FOR_EXP227_BLOCK03_RELEASE"},
                   {"launch_graph_returncode": 0},
                   {"source_labels_opened_before_inference": True}):
        put(receipt, {**original, **change})
        with pytest.raises(AssertionError):
            recovery.original_gate()
    put(receipt, original)
    put(tmp_path / "reports/exp227_source20_handoff_launch_graph_20260927.log",
        "--- stderr ---\nAssertionError: unrelated failure\n")
    with pytest.raises(AssertionError, match="fair-resource"):
        recovery.original_gate()


def stage_fixture(root, monkeypatch):
    reports = root / "reports"
    scripts = root / "scripts"
    scripts.mkdir()
    put(scripts / "run_exp227_source_graph20.py", "# exact runner bytes\n")
    movies = [{"dataset": name, "zarr": "/data/" + name + ".zarr",
               "shape": [10, 2, 3, 4]} for name in recovery.INNER_IDS]
    plan = {"experiment": "EXP227_SOURCE_GRAPH20", "source_embryo": "44b6",
            "target_embryo": "6bba", "fold": 1, "checkpoint_epoch": 20,
            "source_manifest_sha256": recovery.SOURCE_MANIFEST_SHA,
            "training_code_manifest_sha256": recovery.TRAIN_MANIFEST_SHA,
            "training_plan_sha256": recovery.TRAIN_PLAN_SHA,
            "training_run": recovery.TRAIN_RUN,
            "checkpoint": recovery.TRAIN_RUN + "/output/fold1/epoch_020.pt",
            "checkpoint_sha256": "a" * 64, "training_result_sha256": "b" * 64,
            "training_history_sha256": "c" * 64,
            "code": recovery.CODE, "output": recovery.RUN + "/output",
            "data_root": recovery.REMOTE + "/data/exp213_source_view_20260912",
            "movies": movies}
    plan_path = reports / "plan.json"
    put(plan_path, plan)
    stage = {"status": "STAGED_EXP227_SOURCE_GRAPH20", "code": recovery.CODE,
             "manifest_sha256": "d" * 64, "plan_sha256": digest(plan_path),
             "runner_sha256": digest(scripts / "run_exp227_source_graph20.py")}
    prepared = {"status": "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS",
                "target_labels_read": False, "movies": 8, "stage": stage,
                "preflight": {"status": "PASS_EXP227_SOURCE20_PARENT_PREFLIGHT",
                              "movies": movies, "checkpoint_sha256": "a" * 64,
                              "training_result_sha256": "b" * 64,
                              "training_history_sha256": "c" * 64}}
    config = {"experiment": "EXP227", "lease_id": recovery.GRAPH_LEASE,
              "token": "exp227_source_graph20_v1_20260927", "code": recovery.CODE,
              "run": recovery.RUN, "max_seconds": 3600, "cpu_affinity": "0-7",
              "script": "run_exp227_source_graph20.py",
              "arguments": [recovery.CODE + "/plan.json", "--plan-sha256", digest(plan_path)]}
    prepare_path = reports / "prepare.json"
    config_path = reports / "config.json"
    put(prepare_path, prepared)
    put(config_path, config)
    monkeypatch.setattr(recovery, "ROOT", root)
    monkeypatch.setattr(recovery, "GRAPH_PREPARED", prepare_path)
    monkeypatch.setattr(recovery, "GRAPH_PLAN", plan_path)
    monkeypatch.setattr(recovery, "GRAPH_CONFIG", config_path)
    monkeypatch.setattr(recovery, "SCORE_PREPARED", reports / "score_prepare.json")
    monkeypatch.setattr(recovery, "SCORE_LAUNCHED", reports / "score_launch.json")
    monkeypatch.setattr(recovery, "SCORE_VERIFIED", reports / "score_verified.json")
    return prepared, plan, config


def test_exact_stage_and_config_gate_rejects_partial_or_changed_state(tmp_path, monkeypatch):
    prepared, plan, config = stage_fixture(tmp_path, monkeypatch)
    assert recovery.local_artifact_gate() == (prepared, plan, config)
    put(recovery.GRAPH_CONFIG.with_name(recovery.GRAPH_CONFIG.stem + "_reservation.json"), {})
    with pytest.raises(recovery.Reconcile, match="reservation"):
        recovery.local_artifact_gate()
    recovery.GRAPH_CONFIG.with_name(recovery.GRAPH_CONFIG.stem + "_reservation.json").unlink()
    put(recovery.GRAPH_CONFIG, {**config, "gpu": "GPU-test"})
    with pytest.raises(AssertionError, match="config changed"):
        recovery.local_artifact_gate()
    put(recovery.GRAPH_CONFIG, config)
    put(recovery.GRAPH_PREPARED, {**prepared, "preflight": {**prepared["preflight"],
                                                       "checkpoint_sha256": "e" * 64}})
    with pytest.raises(AssertionError):
        recovery.local_artifact_gate()


def queue_fixture(extra=()):
    return {"requests": [{"id": recovery.TRAIN_LEASE, "state": "RELEASED",
                           "run_path": recovery.TRAIN_RUN, "pool": "a100",
                           "project": recovery.PROJECT, "gpus": [], "cpu": 8, "ram_gib": 32},
                          *extra],
            "pools": {"a100": {"gpus": ["GPU-free", "GPU-occupied"],
                                "cpu": 24, "ram_gib": 96}}}


def test_queue_claim_in_any_state_is_ambiguous_and_foreign_waiter_blocks():
    for state in ("CANCELLED", "WAITING_RESOURCE", "RESERVED", "RUNNING", "RELEASED"):
        row = {"id": recovery.GRAPH_LEASE, "run_path": recovery.RUN, "state": state,
               "pool": "a100", "project": recovery.PROJECT, "gpus": [],
               "cpu": 8, "ram_gib": 32}
        with pytest.raises(recovery.Reconcile, match="claim exists"):
            recovery.queue_gate(queue_fixture([row]), {})
    foreign = {"id": "another-project", "run_path": "/other", "state": "WAITING_RESOURCE",
               "pool": "a100", "project": "kaggriculture", "gpus": [],
               "cpu": 8, "ram_gib": 32}
    observed = recovery.queue_gate(queue_fixture([foreign]), {})
    assert not observed["ready_for_physical_probe"]
    assert observed["foreign_or_a100_waiting"] == ["another-project"]
    occupied = {**foreign, "state": "RUNNING", "gpus": ["GPU-occupied"]}
    observed = recovery.queue_gate(queue_fixture([occupied]), {})
    assert observed["queue_free"] == ["GPU-free"]
    assert observed["ready_for_physical_probe"]


def test_remote_gate_is_full_parent_and_staged_code_audit(tmp_path, monkeypatch):
    prepared, plan, _ = stage_fixture(tmp_path, monkeypatch)
    put(tmp_path / "scripts/run_exp223_inference.py", "# helper bytes\n")
    seen = []

    def fake_ssh(alias, command, source):
        assert alias == "nsu-a100" and command == "python3 -"
        ast.parse(source)
        assert "@@" not in source
        seen.append(source)
        return {"status": "PASS_EXP227_SOURCE20_FAIR_RECOVERY_REMOTE_GATE",
                "checkpoint_sha256": plan["checkpoint_sha256"],
                "training_result_sha256": plan["training_result_sha256"],
                "training_history_sha256": plan["training_history_sha256"],
                "graph_manifest_sha256": prepared["stage"]["manifest_sha256"],
                "graph_plan_sha256": prepared["stage"]["plan_sha256"],
                "graph_run_absent": True, "score_run_absent": True}

    monkeypatch.setattr(recovery, "ssh", fake_ssh)
    recovery.remote_gate(prepared, plan)
    assert "RELEASED_AFTER_VERIFIED_EXIT" in seen[0]
    assert "not run.exists()" in seen[0]
    assert "not score_code.exists()" in seen[0]


def test_physical_idle_requires_compute_app_uuid_readback(monkeypatch):
    def fake_ssh(alias, command, source):
        assert "nvidia-smi" in source
        ast.parse(source)
        return {"busy_gpu_uuids": ["GPU-occupied"]}

    monkeypatch.setattr(recovery, "ssh", fake_ssh)
    assert recovery.physical_idle(["GPU-free", "GPU-occupied"]) == ["GPU-free"]
    monkeypatch.setattr(recovery, "ssh", lambda *_: {"busy_gpu_uuids": ["unknown"]})
    with pytest.raises(AssertionError):
        recovery.physical_idle(["GPU-free"])


def test_graph_probe_stops_immediately_on_ambiguous_lease_or_run(tmp_path, monkeypatch):
    config = {"token": "graph-token", "gpu": "GPU-free", "alias": "nsu-a100"}
    config_path = tmp_path / "config.json"
    put(config_path, config)
    monkeypatch.setattr(recovery, "GRAPH_CONFIG", config_path)
    missing = queue_fixture()
    monkeypatch.setattr(recovery, "queue_status", lambda: missing)
    with pytest.raises(recovery.Reconcile, match="ambiguous"):
        recovery.graph_probe()
    lease = {"id": recovery.GRAPH_LEASE, "run_path": recovery.RUN, "token": "graph-token",
             "gpus": ["GPU-free"], "alias": "nsu-a100", "state": "RUNNING",
             "pool": "a100", "project": recovery.PROJECT, "cpu": 8, "ram_gib": 32}
    monkeypatch.setattr(recovery, "queue_status", lambda: queue_fixture([lease]))
    monkeypatch.setattr(recovery, "ssh", lambda *_: {"run_exists": False})
    with pytest.raises(recovery.Reconcile, match="remote run"):
        recovery.graph_probe()


def test_verified_wait_does_not_retry_reconcile(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "RECEIPT", tmp_path / "recovery.json")
    state = {"status": "waiting"}
    recovery.claim(state)
    calls = []

    def ambiguous():
        calls.append(1)
        raise recovery.Reconcile("lease ambiguous")

    with pytest.raises(recovery.Reconcile, match="lease ambiguous"):
        recovery.wait_verified("graph", 5, 1, ambiguous, lambda _: True, state)
    assert calls == [1]


def test_one_shot_launcher_failure_persists_attempt_without_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "ROOT", tmp_path)
    monkeypatch.setattr(recovery, "RECEIPT", tmp_path / "recovery.json")
    (tmp_path / "reports").mkdir()
    state = {"status": "waiting"}
    recovery.claim(state)
    calls = []

    def failed(*args, **kwargs):
        calls.append(1)
        return SimpleNamespace(stdout="", stderr="fairness changed", returncode=1)

    monkeypatch.setattr(recovery.subprocess, "run", failed)
    with pytest.raises(recovery.Reconcile, match="no retry"):
        recovery.run_step("graph_launch", tmp_path / "launcher.py", state)
    assert calls == [1] and state["graph_launch_attempted"] is True
    assert json.loads(recovery.RECEIPT.read_text())["graph_launch_returncode"] == 1
    with pytest.raises(AssertionError, match="Existing recovery step log"):
        recovery.run_step("graph_launch", tmp_path / "launcher.py", state)
    assert calls == [1]


def test_controller_orders_one_graph_and_guarded_cpu_score(tmp_path, monkeypatch):
    receipt, original = stopped_handoff(tmp_path)
    monkeypatch.setattr(recovery, "HANDOFF", receipt)
    monkeypatch.setattr(recovery, "RECEIPT", tmp_path / "recovery.json")
    monkeypatch.setattr(recovery, "GRAPH_LAUNCHED", tmp_path / "graph_launch.json")
    monkeypatch.setattr(recovery, "SCORE_PREPARED", tmp_path / "score_prepare.json")
    monkeypatch.setattr(recovery, "SCORE_LAUNCHED", tmp_path / "score_launch.json")
    monkeypatch.setattr(recovery, "SCORE_VERIFIED", tmp_path / "score_verified.json")
    order = []
    monkeypatch.setattr(recovery, "original_gate", lambda: (original, digest(receipt)))
    monkeypatch.setattr(recovery, "local_artifact_gate", lambda: ({}, {}, {}))
    monkeypatch.setattr(recovery, "queue_status", lambda: {})
    monkeypatch.setattr(recovery, "queue_gate", lambda *_: {
        "ready_for_physical_probe": True, "queue_free": ["GPU-free"]})
    monkeypatch.setattr(recovery, "remote_gate", lambda *_: {})
    monkeypatch.setattr(recovery, "physical_idle", lambda *_: ["GPU-free"])
    monkeypatch.setattr(recovery, "wait_fair", lambda *_: order.append("wait_fair"))
    monkeypatch.setattr(recovery, "graph_launch_readback", lambda *_: {})

    def step(name, script, state):
        order.append(name)
        if name == "graph_launch":
            put(recovery.GRAPH_LAUNCHED, {})
        elif name == "score_prepare":
            put(recovery.SCORE_PREPARED, {})
        elif name == "score_launch":
            put(recovery.SCORE_LAUNCHED, {})
        elif name == "score_verify":
            put(recovery.SCORE_VERIFIED, {"status": "VERIFIED_EXP227_SOURCE20_OFFICIAL",
                                          "source_labels_read": True, "target_labels_read": False,
                                          "rows": 8, "source_score": 0.82})

    def wait(name, seconds, interval, probe, check, state):
        order.append("wait_" + name)

    monkeypatch.setattr(recovery, "run_step", step)
    monkeypatch.setattr(recovery, "wait_verified", wait)
    recovery.main()
    assert order == ["wait_fair", "graph_launch", "wait_graph", "score_prepare",
                     "score_launch", "wait_score", "score_verify"]
    result = json.loads(recovery.RECEIPT.read_text())
    assert result["status"] == "PASS_EXP227_SOURCE20_OFFICIAL_FAIR_RECOVERY"
    assert result["original_handoff_sha256"] == digest(receipt)
    assert json.loads(receipt.read_text()) == original
