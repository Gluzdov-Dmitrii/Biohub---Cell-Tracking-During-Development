"""Local-only contracts for the one-shot EXP236 source11 graph/score handoff."""
import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import continue_exp236_after_epoch10_to_source_score as handoff  # noqa: E402


def graph_observation():
    names = list(handoff.INNER_IDS)
    return {"lease_state": "RELEASED", "checkpoint_sha256": "c" * 64,
            "plan_sha256": "p" * 64,
            "remote": {"status": "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS",
                       "movies": names, "records": names,
                       "checkpoint_sha256": "c" * 64, "plan_sha256": "p" * 64,
                       "source_labels_read": False, "target_labels_read": False,
                       "target_data_opened": False,
                       "hashes": [{"dataset": name, "csv_sha256": "a" * 64,
                                   "receipt_sha256": "b" * 64} for name in names],
                       "audit_error": None,
                       "exit": {"returncode": 0, "hard_timeout": False},
                       "complete_status": "RELEASED_AFTER_VERIFIED_EXIT",
                       "supervision_exit_matches": True, "control_state": "RELEASED",
                       "control_run_matches": True,
                       "output_names": ["status.json"] +
                       ["graph__" + name + suffix for name in names
                        for suffix in (".csv", ".json")]}}


def score_observation():
    return {"exit": {"returncode": 0, "timeout": False},
            "result_status": "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL",
            "rows": list(handoff.INNER_IDS), "source_score": 0.82,
            "source_labels_read": True, "target_labels_read": False,
            "target_data_opened": False,
            "gate_status": "PASS_EXP236_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"}


def test_controller_requires_exact_released_four_block_chain(tmp_path, monkeypatch):
    receipt = tmp_path / "controller.json"
    audit = {"status": "PASS_EXP236_SOURCE_V2_BLOCK_AUDIT", "block": 4,
             "completed_epochs": 10, "checkpoint_sha256": "c" * 64,
             "result_sha256": "r" * 64}
    controller = {"status": "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED",
                  "final_audit": audit}
    receipt.write_text(json.dumps(controller))
    monkeypatch.setattr(handoff, "TRAIN_CONTROLLER", receipt)
    chain = [{"completed_epochs": epoch} for epoch in (3, 6, 9)]
    chain.append({**audit, "code": "code", "run": handoff.TRAIN_RUN})
    monkeypatch.setattr(handoff, "verify_parent_chain", lambda: (chain, handoff.sha(receipt)))
    assert handoff.controller_released(handoff.controller_probe())
    chain[2]["completed_epochs"] = 8
    with pytest.raises(handoff.TerminalAnomaly):
        handoff.controller_probe()
    controller["status"] = "STOPPED_EXP236_SOURCE_V2_CONTINUATION"
    receipt.write_text(json.dumps(controller))
    with pytest.raises(handoff.TerminalAnomaly):
        handoff.controller_probe()


@pytest.mark.parametrize("change", (
    "running_lease", "failed_exit", "bad_id", "bad_hash", "target_access",
    "missing_output", "bad_release", "bad_checkpoint",
))
def test_graph_release_requires_exact_no_label_hashed_inner11(change):
    observed = graph_observation()
    remote = observed["remote"]
    if change == "running_lease":
        observed["lease_state"] = "RUNNING"
        assert handoff.graph_released(observed) is False
        return
    if change == "failed_exit":
        remote["exit"]["returncode"] = 1
    elif change == "bad_id":
        remote["records"][0] = "44b6_forbidden"
    elif change == "bad_hash":
        remote["audit_error"] = "CSV SHA mismatch"
    elif change == "target_access":
        remote["target_data_opened"] = True
    elif change == "missing_output":
        remote["output_names"].pop()
    elif change == "bad_release":
        remote["control_state"] = "RUNNING"
    else:
        remote["checkpoint_sha256"] = "wrong"
    with pytest.raises((AssertionError, handoff.TerminalAnomaly)):
        handoff.graph_released(observed)


def test_graph_release_accepts_exact_inner11():
    assert handoff.graph_released(graph_observation()) is True


@pytest.mark.parametrize("change", ("failed_exit", "short_rows", "nan", "no_gate", "target"))
def test_score_requires_finite_source_only_result(change):
    observed = score_observation()
    if change == "failed_exit":
        observed["exit"]["returncode"] = 1
    elif change == "short_rows":
        observed["rows"].pop()
    elif change == "nan":
        observed["source_score"] = float("nan")
    elif change == "no_gate":
        observed["gate_status"] = None
    else:
        observed["target_labels_read"] = True
    with pytest.raises((AssertionError, handoff.TerminalAnomaly)):
        handoff.score_exited(observed)
    assert handoff.score_exited(score_observation()) is True


def test_resource_waits_for_fair_physical_capacity(tmp_path, monkeypatch):
    for key in ("GRAPH_RESERVATION", "GRAPH_PARTIAL", "GRAPH_PRELAUNCH_RELEASE",
                "GRAPH_LAUNCHED"):
        monkeypatch.setattr(handoff, key, tmp_path / key)
    parent = {"id": "exp236-horaz-source6bba-block04-v2-20260927",
              "run_path": handoff.TRAIN_RUN, "pool": "a100", "state": "RELEASED",
              "project": handoff.PROJECT, "gpus": []}
    queue = {"pools": {"a100": {"gpus": ["GPU-a", "GPU-b"]}},
             "requests": [parent, {"id": "foreign", "project": "other", "pool": "a100",
                                    "state": "WAITING_RESOURCE", "gpus": []}]}
    monkeypatch.setattr(handoff, "queue_status", lambda: queue)
    monkeypatch.setattr(handoff, "physical_busy", lambda: {"GPU-a"})
    assert not handoff.resource_ready(handoff.resource_probe())
    queue["requests"].pop()
    assert handoff.resource_ready(handoff.resource_probe())
    queue["requests"].append({"id": handoff.GRAPH_LEASE, "run_path": handoff.GRAPH_RUN,
                              "pool": "a100", "state": "RESERVED", "project": handoff.PROJECT})
    with pytest.raises(handoff.TerminalAnomaly):
        handoff.resource_probe()


def test_remote_probes_are_valid_python(monkeypatch, tmp_path):
    controller = tmp_path / "controller.json"
    controller.write_text("{}")
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    prepared = tmp_path / "prepared.json"
    prepared.write_text(json.dumps({"status": "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS",
                                    "controller_receipt_sha256": handoff.sha(controller),
                                    "stage": {"plan_sha256": handoff.sha(plan)},
                                    "preflight": {"checkpoint_sha256": "c" * 64}}))
    config = tmp_path / "config.json"
    cfg = {"alias": "nsu-a100"}
    config.write_text(json.dumps(cfg))
    launch = tmp_path / "launch.json"
    launch.write_text(json.dumps({"config": cfg, "lease": {"id": handoff.GRAPH_LEASE}}))
    for key, path in (("TRAIN_CONTROLLER", controller), ("GRAPH_PLAN", plan),
                      ("GRAPH_PREPARED", prepared), ("GRAPH_CONFIG", config),
                      ("GRAPH_LAUNCHED", launch)):
        monkeypatch.setattr(handoff, key, path)
    monkeypatch.setattr(handoff, "queue_status", lambda: {"requests": [{
        "id": handoff.GRAPH_LEASE, "run_path": handoff.GRAPH_RUN,
        "pool": "a100", "alias": "nsu-a100", "state": "RUNNING"}]})
    seen = []

    def fake_ssh(alias, command, source):
        assert command == "python3 -" and "@@" not in source
        ast.parse(source)
        seen.append((alias, source))
        if "--query-compute-apps" in source:
            return {"busy_gpu_uuids": []}
        return graph_observation()["remote"] if alias == "nsu-a100" else score_observation()

    monkeypatch.setattr(handoff, "ssh", fake_ssh)
    assert handoff.graph_probe()["lease_state"] == "RUNNING"
    assert handoff.score_probe()["result_status"] == "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL"
    handoff.physical_busy()
    assert [alias for alias, _ in seen] == ["nsu-a100", "nsu-quadro", "nsu-a100"]


def test_main_runs_finite_order_and_no_restart(tmp_path, monkeypatch):
    paths = {key: tmp_path / (key + ".json") for key in (
        "TRAIN_CONTROLLER", "RECEIPT", "GRAPH_PLAN", "GRAPH_CONFIG",
        "GRAPH_PREPARED", "GRAPH_LAUNCHED", "GRAPH_RESERVATION", "GRAPH_PARTIAL",
        "GRAPH_PRELAUNCH_RELEASE", "SCORE_PREPARED", "SCORE_LAUNCHED", "SCORE_VERIFIED")}
    for key, path in paths.items():
        monkeypatch.setattr(handoff, key, path)
    paths["TRAIN_CONTROLLER"].write_text('{"status":"PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"}')
    monkeypatch.setattr(handoff, "ROOT", tmp_path)
    events = []
    parent = {"controller_sha256": handoff.sha(paths["TRAIN_CONTROLLER"]),
              "checkpoint_sha256": "c" * 64}

    def fake_wait(name, _seconds, _probe, _check, _state):
        events.append("wait_" + name)
        return parent if name == "training" else {}

    def fake_step(name, _script, _timeout, _state):
        events.append(name)
        if name == "prepare_graph":
            paths["GRAPH_PLAN"].write_text("{}")
            paths["GRAPH_CONFIG"].write_text("{}")
            paths["GRAPH_PREPARED"].write_text(json.dumps({
                "controller_receipt_sha256": parent["controller_sha256"],
                "preflight": {"checkpoint_sha256": parent["checkpoint_sha256"]}}))
        elif name == "launch_graph":
            paths["GRAPH_LAUNCHED"].write_text("{}")
        elif name == "prepare_score":
            paths["SCORE_PREPARED"].write_text(json.dumps({"preflight": {
                "status": "PASS_EXP236_SOURCE10_SCORER_PREFLIGHT",
                "hashes": [{"dataset": item} for item in handoff.INNER_IDS]}}))
        elif name == "launch_score":
            paths["SCORE_LAUNCHED"].write_text("{}")
        elif name == "verify_score":
            paths["SCORE_VERIFIED"].write_text(json.dumps({
                "status": "VERIFIED_EXP236_SOURCE10_OFFICIAL", "rows": 11,
                "source_score": 0.82, "source_labels_read": True,
                "target_labels_read": False}))

    monkeypatch.setattr(handoff, "wait_for", fake_wait)
    monkeypatch.setattr(handoff, "run_step", fake_step)
    handoff.main()
    assert events == ["wait_training", "prepare_graph", "wait_graph_resource",
                      "launch_graph", "wait_graph", "prepare_score", "launch_score",
                      "wait_score", "verify_score"]
    assert json.loads(paths["RECEIPT"].read_text())["status"] == (
        "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF")
    with pytest.raises(AssertionError):
        handoff.main()


def test_failed_parent_stops_before_any_stage(tmp_path, monkeypatch):
    controller = tmp_path / "controller.json"
    controller.write_text('{"status":"STOPPED_EXP236_SOURCE_V2_CONTINUATION"}')
    monkeypatch.setattr(handoff, "TRAIN_CONTROLLER", controller)
    monkeypatch.setattr(handoff, "RECEIPT", tmp_path / "handoff.json")
    for key in ("GRAPH_PLAN", "GRAPH_CONFIG", "GRAPH_PREPARED", "GRAPH_LAUNCHED",
                "GRAPH_RESERVATION", "GRAPH_PARTIAL", "GRAPH_PRELAUNCH_RELEASE",
                "SCORE_PREPARED", "SCORE_LAUNCHED", "SCORE_VERIFIED"):
        monkeypatch.setattr(handoff, key, tmp_path / (key + ".json"))
    monkeypatch.setattr(handoff, "run_step", lambda *_args: pytest.fail("stage attempted"))
    with pytest.raises(handoff.TerminalAnomaly):
        handoff.main()
    assert json.loads(handoff.RECEIPT.read_text())["status"] == (
        "STOPPED_EXP236_SOURCE11_HANDOFF")
