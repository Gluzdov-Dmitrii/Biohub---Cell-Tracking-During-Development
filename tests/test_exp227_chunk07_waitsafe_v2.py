"""The v2 EXP227 launcher records queue races as safe waits."""
import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp227_chunk07_waitsafe_v2 as launcher  # noqa: E402
import reconcile_exp227_chunk07_waiting as reconcile  # noqa: E402
import stage_exp227_chunk07_waitsafe_v2 as stage  # noqa: E402
from stage_exp227_target_chunk import remote_preflight_source, remote_stage_source  # noqa: E402


def test_cancelled_v1_preserved_and_new_stage_sources_parse(monkeypatch):
    audit = json.loads(reconcile.RECEIPT.read_text())
    assert reconcile.sha(reconcile.SOURCE) == audit["source_stopped_sha256"]
    assert audit["remote"]["queue_row"]["state"] == "CANCELLED"
    assert audit["remote"]["run_absent"] is True
    assert audit["verified_prior_graphs"] == 102
    test_stage = ROOT / "reports/_test_exp227_waitsafe_stage_never_write.json"
    test_config = ROOT / "reports/_test_exp227_waitsafe_config_never_write.json"
    assert not test_stage.exists() and not test_config.exists()
    monkeypatch.setattr(stage, "STAGE", test_stage)
    monkeypatch.setattr(stage, "CONFIG", test_config)
    prepared, chosen, plan, recipe, manifest = stage.local_gate()
    identity = prepared["identity"]
    files = {name: (Path(prepared["bundle"]) / name).read_bytes()
             for name in recipe["overlay_files"]}
    ast.parse(remote_preflight_source(identity, chosen))
    ast.parse(remote_stage_source(identity, recipe,
                                  {name: manifest[name] for name in files}, files))
    assert identity["code"] != json.loads((ROOT / "reports/exp227_target6bba_chunk07_stage_20260927.json").read_text())["code"]
    assert identity["run"] != audit["remote"]["queue_row"]["run_path"]
    assert launcher.attempt_lease(identity["lease_id"], 0) == identity["lease_id"]
    assert launcher.attempt_lease(identity["lease_id"], 1) != identity["lease_id"]


def setup_launcher(monkeypatch, *, exp236_active=False, queue_error=False):
    local = json.loads(launcher.LOCAL.read_text())
    identity = local["identity"]
    stage_row = {"manifest_sha256": "a" * 64,
                 "plan_sha256": local["plan_sha256"],
                 "selection_sha256": local["selection_sha256"],
                 "checkpoint_sha256": local["checkpoint_sha256"],
                 "movies": local["movies"]}
    config = {"lease_id": identity["lease_id"], "token": identity["token"],
              "code": identity["code"], "run": identity["run"],
              "chunk_index": 7,
              "resources": {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4},
              "max_seconds": 10800}
    monkeypatch.setattr(launcher, "local_gate", lambda attempt: (stage_row, config))
    monkeypatch.setattr(launcher, "sha", lambda _: "b" * 64)
    monkeypatch.setattr(launcher, "no_run_worker", lambda _: {
        "run_absent": True, "matching_processes": [], "matching_gpu_pids": []})
    rows = ([{"id": "exp236-target44b6-chunk00-v1-20260927", "state": "RUNNING",
              "project": "biohub-cell-tracking-during-development", "gpus": ["GPU-A"]}]
            if exp236_active else [])
    queue = {"requests": rows}
    physical = {"all_gpus": ["GPU-A", "GPU-B"],
                "busy_gpus": ["GPU-A"] if exp236_active else [],
                "idle_gpus": ["GPU-B"] if exp236_active else ["GPU-A", "GPU-B"]}
    calls = []

    def fake_ssh(alias, command, source=None):
        calls.append((alias, command))
        if alias == "nsu-a100" and source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
            return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                    "manifest_sha256": stage_row["manifest_sha256"],
                    "plan_sha256": stage_row["plan_sha256"], "run_absent": True}
        if alias == "nsu-quadro" and "status" in command:
            return queue
        if alias == "nsu-a100" and source == launcher.PHYSICAL_IDLE_SOURCE:
            return physical
        raise AssertionError("Unexpected SSH call")

    monkeypatch.setattr(launcher, "ssh", fake_ssh)
    written = {}
    monkeypatch.setattr(launcher, "write", lambda path, body: written.setdefault(path.name, body))
    if queue_error:
        def cancelled(*_):
            raise RuntimeError("Queue returned WAITING_RESOURCE; cancelled unlaunched request "
                               + config["lease_id"])
        monkeypatch.setattr(launcher, "queue_request", cancelled)
        monkeypatch.setattr(launcher, "cancelled_unlaunched", lambda _: {
            "queue_row": {"state": "CANCELLED"},
            "run_worker": {"run_absent": True, "matching_processes": [],
                           "matching_gpu_pids": []}})
    else:
        monkeypatch.setattr(launcher, "queue_request", lambda *_: pytest.fail("queue request forbidden"))
    return written, calls


def test_exp236_active_returns_wait_without_request(monkeypatch):
    written, calls = setup_launcher(monkeypatch, exp236_active=True)
    result = launcher.launch_attempt(0)
    assert result["status"] == "WAITING_FOR_FAIR_A100_NO_REQUEST"
    assert result["fair"]["status"] == "EXP236_TARGET_COORDINATOR_ACTIVE_OR_WAITING"
    assert len(written) == 1 and not any("request" in command for _, command in calls)


def test_waiting_resource_race_is_nonfatal_cancelled_wait(monkeypatch):
    written, calls = setup_launcher(monkeypatch, queue_error=True)
    result = launcher.launch_attempt(0)
    assert result["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN"
    assert result["cancelled"]["queue_row"]["state"] == "CANCELLED"
    assert result["cancelled"]["run_worker"]["run_absent"] is True
    assert len(written) == 2 and any("intent" in name for name in written)
    assert not any("exp223_supervisor.py" in command for _, command in calls)
