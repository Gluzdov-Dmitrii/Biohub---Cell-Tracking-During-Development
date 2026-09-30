"""V3 fixes the runner/plan namespace before any remote stage or launch."""
import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp227_chunk07_waitsafe_v3 as launcher  # noqa: E402
import prepare_exp227_chunk07_waitsafe_v3 as prepare  # noqa: E402
import stage_exp227_chunk07_waitsafe_v3 as stage  # noqa: E402
from stage_exp227_target_chunk import remote_preflight_source, remote_stage_source  # noqa: E402


def test_actual_generated_plan_contract_rejects_v2_identity():
    receipt = json.loads(prepare.RECEIPT.read_text())
    bundle = Path(receipt["bundle"])
    plan = json.loads((bundle / "plan.json").read_text())
    assert prepare.sha(bundle / "local_bundle_manifest.json") == receipt["bundle_manifest_sha256"]
    assert prepare.validate_actual_runner(bundle, plan) == receipt["actual_runner_contract"]
    runner = bundle / "run_exp227_target_chunk.py"
    namespace = {"__name__": "exp227_v3_test_contract", "__file__": str(runner)}
    exec(compile(runner.read_bytes(), str(runner), "exec"), namespace)
    local_plan = {**plan, "assignment": str(bundle / "assignment.json"),
                  "selection": str(bundle / "selection.json")}
    assert namespace["validate_plan"](local_plan)["checkpoint_sha256"] == \
        receipt["checkpoint_sha256"]
    with pytest.raises(AssertionError):
        namespace["validate_plan"]({**local_plan, "code": prepare.V2_LOCAL_IDENTITY["code"]})
    with pytest.raises(AssertionError):
        namespace["validate_plan"]({**local_plan,
                                     "output": prepare.V2_LOCAL_IDENTITY["run"] + "/output"})
    assert plan["code"] == prepare.IDENTITY["code"]
    assert plan["output"] == prepare.IDENTITY["run"] + "/output"
    assert "_v3_20260927" in (bundle / "run_exp227_target_chunk.py").read_text()
    assert plan["movies"] == receipt["movies"] and len(plan["movies"]) == 14


def test_v3_stage_dry_run_pins_exact_runner_and_parent():
    prepared, chosen, plan, recipe, manifest = stage.local_gate()
    assert manifest["run_exp227_target_chunk.py"] == prepared["runner_sha256"]
    assert prepared["failed_v2_reconciliation_sha256"] == stage.EXPECTED_AUDIT_SHA
    identity = prepared["identity"]
    files = {name: (Path(prepared["bundle"]) / name).read_bytes()
             for name in recipe["overlay_files"]}
    ast.parse(remote_preflight_source(identity, chosen))
    ast.parse(remote_stage_source(identity, recipe,
                                  {name: manifest[name] for name in files}, files))
    assert identity["code"] != json.loads(stage.AUDIT.read_text())["identity"]["code"]
    assert not stage.STAGE.exists() and not stage.CONFIG.exists()


def setup_launch(tmp_path, monkeypatch):
    prepared = json.loads(launcher.LOCAL.read_text())
    identity = prepared["identity"]
    staged = {"status": "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS",
              "chunk_index": 7, **identity,
              "manifest_sha256": "a" * 64,
              "plan_sha256": prepared["plan_sha256"],
              "checkpoint_sha256": prepared["checkpoint_sha256"],
              "selection_sha256": prepared["selection_sha256"],
              "assignment_sha256": prepared["assignment_sha256"],
              "movies": prepared["movies"],
              "source_stopped_sha256": prepared["source_stopped_sha256"],
              "local_prepare_sha256": launcher.sha(launcher.LOCAL),
              "failed_v2_reconciliation_sha256": launcher.sha(launcher.AUDIT),
              "runner_contract": prepared["actual_runner_contract"],
              "remote_run_created": False, "gpu_claimed": False,
              "target_labels_read": False, "kaggle_post": False}
    config = {"experiment": "EXP227_TARGET6BBA_CHUNK", "chunk_index": 7,
              **identity, "pool": "a100", "max_seconds": 10800,
              "resources": {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4},
              "script": "run_exp227_target_chunk.py",
              "arguments": [identity["code"] + "/plan.json", "--plan-sha256",
                            prepared["plan_sha256"]]}
    stage_path = tmp_path / "stage.json"
    config_path = tmp_path / "config.json"
    stage_path.write_text(json.dumps(staged))
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(launcher, "STAGE", stage_path)
    monkeypatch.setattr(launcher, "CONFIG", config_path)
    monkeypatch.setattr(launcher, "paths", lambda n: {
        name: tmp_path / f"attempt{n:02d}_{name}.json"
        for name in ("intent", "reservation", "partial", "result", "prelaunch_release")})
    return staged, config


def test_v3_launch_local_gate_and_fresh_attempt_identity(tmp_path, monkeypatch):
    staged, config = setup_launch(tmp_path, monkeypatch)
    assert launcher.local_gate(0) == (staged, config)
    assert launcher.attempt_lease(config["lease_id"], 1) == \
        "exp227-target6bba-chunk07-v3a01-20260927"
    with pytest.raises(AssertionError):
        launcher.attempt_lease("exp227-target6bba-chunk07-v2-20260927", 0)


def test_v3_fair_wait_does_not_request_gpu(tmp_path, monkeypatch):
    staged, config = setup_launch(tmp_path, monkeypatch)
    monkeypatch.setattr(launcher, "no_run_worker", lambda _: {
        "run_absent": True, "matching_processes": [], "matching_gpu_pids": []})
    def fake_ssh(alias, command, source=None):
        if alias == "nsu-a100" and source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
            return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                    "manifest_sha256": staged["manifest_sha256"],
                    "plan_sha256": staged["plan_sha256"], "run_absent": True}
        if alias == "nsu-quadro" and "status" in command:
            return {"requests": [{"id": "exp236-target44b6-chunk00-v1-20260927",
                                  "state": "RUNNING", "project": "biohub-cell-tracking-during-development",
                                  "gpus": ["GPU-TEST"]}]}
        if alias == "nsu-a100" and source == launcher.PHYSICAL_IDLE_SOURCE:
            return {"all_gpus": ["GPU-TEST"], "busy_gpus": ["GPU-TEST"],
                    "idle_gpus": []}
        raise AssertionError("Unexpected remote operation")
    monkeypatch.setattr(launcher, "ssh", fake_ssh)
    monkeypatch.setattr(launcher, "queue_request",
                        lambda *_: pytest.fail("GPU queue request forbidden"))
    result = launcher.launch_attempt(0)
    assert result["status"] == "WAITING_FOR_FAIR_A100_NO_REQUEST"
    assert result["lease_id"] == config["lease_id"]
    assert result["fair"]["status"] == "EXP236_TARGET_COORDINATOR_ACTIVE_OR_WAITING"
    assert launcher.paths(0)["result"].exists()
    assert not launcher.paths(0)["intent"].exists()


def test_v3_queue_race_cancels_without_run(tmp_path, monkeypatch):
    staged, config = setup_launch(tmp_path, monkeypatch)
    monkeypatch.setattr(launcher, "no_run_worker", lambda _: {
        "run_absent": True, "matching_processes": [], "matching_gpu_pids": []})
    def fake_ssh(alias, command, source=None):
        if alias == "nsu-a100" and source and "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT" in source:
            return {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                    "manifest_sha256": staged["manifest_sha256"],
                    "plan_sha256": staged["plan_sha256"], "run_absent": True}
        if alias == "nsu-quadro" and "status" in command:
            return {"requests": []}
        if alias == "nsu-a100" and source == launcher.PHYSICAL_IDLE_SOURCE:
            return {"all_gpus": ["GPU-TEST"], "busy_gpus": [],
                    "idle_gpus": ["GPU-TEST"]}
        raise AssertionError("Unexpected remote operation")
    monkeypatch.setattr(launcher, "ssh", fake_ssh)
    monkeypatch.setattr(launcher, "queue_request", lambda *_: (
        (_ for _ in ()).throw(RuntimeError(
            "Queue returned WAITING_RESOURCE; cancelled unlaunched request "
            + config["lease_id"]))))
    monkeypatch.setattr(launcher, "cancelled_unlaunched", lambda _: {
        "queue_row": {"state": "CANCELLED", "gpus": [], "process": None},
        "run_worker": {"run_absent": True, "matching_processes": [],
                       "matching_gpu_pids": []}})
    result = launcher.launch_attempt(0)
    assert result["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN"
    assert result["lease_id"] == config["lease_id"]
    assert launcher.paths(0)["intent"].exists() and launcher.paths(0)["result"].exists()
    assert not launcher.paths(0)["partial"].exists()
