"""V4 graph gate, successor binding and label-order controls with fake graphs."""
import hashlib
import json
from pathlib import Path
import sys
import types

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import score_exp227_target6bba_current_v3 as v3  # noqa: E402
import score_exp227_target6bba_current_v4 as scorer  # noqa: E402
import stage_exp227_target6bba_scorer_v4 as stager  # noqa: E402
import launch_exp227_target6bba_scorer_v4 as launcher  # noqa: E402
import verify_exp227_target6bba_scorer_v4 as verifier  # noqa: E402
from test_exp227_target6bba_current_scorer_v3 import fixture as v3_fixture  # noqa: E402
from test_exp227_target6bba_official_scorer import put, write  # noqa: E402


def test_reviewed_finalizer_correction_binds_source_test_and_final_receipt(tmp_path, monkeypatch):
    source = tmp_path / "finalizer.py"
    test = tmp_path / "test_finalizer.py"
    correction_path = tmp_path / "correction.json"
    source.write_text("corrected finalizer\n")
    test.write_text("real queue process fixture\n")
    final_sha = "f" * 64
    original_sha = "a" * 64
    correction = {
        "status": "PASS_EXP227_V3_FINALIZER_REAL_QUEUE_PROCESS_IDENTITY_CORRECTION",
        "old_finalizer_source_sha256": original_sha,
        "corrected_finalizer_source_sha256": stager.sha(source),
        "corrected_test_source_sha256": stager.sha(test),
        "final_receipt_sha256": final_sha,
        "check_only_graph_count": 116,
        "target_labels_read": False,
        "target_score_computed": False,
        "kaggle_post": False,
    }
    correction_path.write_text(json.dumps(correction))
    monkeypatch.setattr(stager, "FINALIZER_SOURCE", source)
    monkeypatch.setattr(stager, "FINALIZER_TEST", test)
    monkeypatch.setattr(stager, "FINALIZER_CORRECTION", correction_path)
    monkeypatch.setattr(stager, "FINALIZER_CORRECTION_SHA", stager.sha(correction_path))
    monkeypatch.setattr(stager, "FINALIZER_TEST_PRE_RECEIPT_SHA", stager.sha(test))
    monkeypatch.setattr(stager, "FINALIZER_TEST_CURRENT_SHA", stager.sha(test))
    stager.reviewed_finalizer_source({"future_finalizer_source_sha256": original_sha}, final_sha)
    with pytest.raises(AssertionError):
        stager.reviewed_finalizer_source({"future_finalizer_source_sha256": original_sha}, "0" * 64)
    test.write_text("tampered test fixture\n")
    with pytest.raises(AssertionError):
        stager.reviewed_finalizer_source({"future_finalizer_source_sha256": original_sha}, final_sha)


def fixture(tmp_path, monkeypatch, attempt=0):
    config, path, _, queue, root = v3_fixture(tmp_path, monkeypatch)
    for key in ("REMOTE", "ASSIGNMENT_SHA", "CHECKPOINT_SHA", "COHORT_SHA",
                "BASELINE_SHA", "CURRENT_METRICS_SHA", "CURRENT_DIVISION_SHA"):
        monkeypatch.setattr(scorer, key, getattr(v3, key))
    monkeypatch.setattr(scorer, "current_import_gate", lambda _: (
        {"profile": "fake"}, {"status": "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"}))
    monkeypatch.setattr(scorer, "image_metadata", lambda _, __, names: [
        {"dataset": name, "scale": [1.625, 0.40625, 0.40625]} for name in names])
    coord_path = Path(config["coordinator"])
    coordinator = json.loads(coord_path.read_text())
    final = coordinator["chunks"][7]
    stage = final["stage"]["result"]
    code = Path(stage["code"])
    run = Path(stage["run"])
    token = code.name
    base_lease = "exp227-target6bba-chunk07-v3-20260927"
    actual_lease = (base_lease if attempt == 0 else
                    base_lease.replace("-v3-", f"-v3a{attempt:02d}-"))
    runner_sha = write(code / "run_exp227_target_chunk.py", "# synthetic runner\n")
    manifest_sha = put(code / "code_manifest.json", {
        "plan.json": stage["plan_sha256"],
        "run_exp227_target_chunk.py": runner_sha})
    stage["manifest_sha256"] = manifest_sha
    stage["lease_id"] = actual_lease
    final["postrun"]["gate"]["manifest_sha256"] = manifest_sha
    control_path = run / "supervision/control.json"
    control = json.loads(control_path.read_text())
    control["queue"]["id"] = actual_lease
    final["postrun"]["gate"]["control_sha256"] = put(control_path, control)
    queue["requests"][7]["id"] = actual_lease
    successor = {"status": "PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY",
                 "identity": {"token": token, "code": stage["code"],
                              "run": stage["run"], "lease_id": base_lease},
                 "plan_sha256": stage["plan_sha256"],
                 "runner_sha256": runner_sha,
                 "actual_runner_contract": {"status": "PASS_EXP227_CHUNK07_V3_ACTUAL_VALIDATE_PLAN"}}
    successor_path = tmp_path / "successor_prepare.json"
    successor_sha = put(successor_path, successor)
    successor_stage = {"status": "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS",
                       "code": stage["code"], "run": stage["run"],
                       "lease_id": base_lease, "plan_sha256": stage["plan_sha256"],
                       "manifest_sha256": manifest_sha,
                       "staged": {"runner_sha256": runner_sha},
                       "runner_contract": successor["actual_runner_contract"],
                       "local_prepare_sha256": successor_sha,
                       "target_labels_read": False}
    successor_stage_path = tmp_path / "successor_stage.json"
    successor_stage_sha = put(successor_stage_path, successor_stage)
    successor_config = {"code": stage["code"], "run": stage["run"],
                        "token": token, "lease_id": base_lease, "pool": "a100",
                        "arguments": [stage["code"] + "/plan.json", "--plan-sha256",
                                      stage["plan_sha256"]]}
    successor_config_path = tmp_path / "successor_config.json"
    successor_config_sha = put(successor_config_path, successor_config)
    for key, value in (("SUCCESSOR_PREPARE_SHA", successor_sha),
                       ("SUCCESSOR_STAGE_SHA", successor_stage_sha),
                       ("SUCCESSOR_CONFIG_SHA", successor_config_sha),
                       ("SUCCESSOR_MANIFEST_SHA", manifest_sha),
                       ("SUCCESSOR_PLAN_SHA", stage["plan_sha256"]),
                       ("SUCCESSOR_RUNNER_SHA", runner_sha),
                       ("SUCCESSOR_TOKEN", token),
                       ("SUCCESSOR_BASE_LEASE", base_lease)):
        monkeypatch.setattr(scorer, key, value)
    final["stage"].update({"source_stage_lease_id": base_lease,
                           "actual_launch_lease_id": actual_lease,
                           "source_receipt_sha256": successor_stage_sha,
                           "result_is_derived_lease_binding": attempt > 0})
    final["launch"] = {"validated": True, "attempt": attempt,
                       "result": {"attempt": attempt, "config": {"lease_id": actual_lease},
                                  "lease": {"id": actual_lease}}}
    final["postrun"]["queue_row"] = {"id": actual_lease}
    hashes = [row for entry in coordinator["chunks"]
              for row in entry["postrun"]["gate"]["graph_hashes"]]
    graph_sha = hashlib.sha256(json.dumps(hashes, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    coordinator["successor_audit"] = {
        "status": "PASS_EXP227_TARGET6BBA_WAITSAFE_V3_FINAL_NO_LABELS",
        "source_stopped_sha256": scorer.STOPPED_SHA,
        "failed_v2_reconciliation_sha256": scorer.FAILED_V2_SHA,
        "successor_prepare_sha256": successor_sha,
        "successor_stage_sha256": successor_stage_sha,
        "successor_config_sha256": successor_config_sha,
        "remote_manifest_sha256": manifest_sha,
        "remote_plan_sha256": stage["plan_sha256"],
        "remote_runner_sha256": runner_sha,
        "actual_attempt": attempt, "actual_lease_id": actual_lease,
        "graph_hashes_sha256": graph_sha,
        "target_labels_read": False, "target_score_computed": False}
    coordinator["state_sha256"] = scorer.state_digest(coordinator)
    config["coordinator_sha256"] = put(coord_path, coordinator)
    config["experiment"] = "EXP227_SOURCE44_TARGET6BBA_CURRENT116_V4"
    config["successor_prepare"] = str(successor_path)
    config["successor_prepare_sha256"] = successor_sha
    config["successor_stage"] = str(successor_stage_path)
    config["successor_stage_sha256"] = successor_stage_sha
    config["successor_config"] = str(successor_config_path)
    config["successor_config_sha256"] = successor_config_sha
    config["final_graph_hashes_sha256"] = graph_sha
    config["python"] = sys.executable
    digest = put(path, config)
    return config, path, digest, queue, coordinator


@pytest.mark.parametrize("attempt", [0, 1])
def test_all116_gate_exact_graphs_and_actual_lease(tmp_path, monkeypatch, attempt):
    config, path, digest, queue, _ = fixture(tmp_path, monkeypatch, attempt)
    monkeypatch.setattr(scorer, "label_manifest", lambda *_: pytest.fail("labels opened"))
    gate = scorer.run(path, digest, queue_state=queue, gate_only=True)
    assert gate["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    assert gate["candidate_count"] == gate["baseline_count"] == 116
    assert len(gate["graph_hashes"]) == 116
    assert [row["dataset"] for row in gate["graph_hashes"]] == config["target_ids"]
    assert gate["successor_actual_lease_id"] == queue["requests"][7]["id"]
    assert not Path(config["output"]).exists()


@pytest.mark.parametrize("damage", ["graph_hash", "ids", "stage_sha", "lease"])
def test_tamper_blocks_before_labels(tmp_path, monkeypatch, damage):
    config, path, digest, queue, coordinator = fixture(tmp_path, monkeypatch)
    if damage == "graph_hash":
        coordinator["successor_audit"]["graph_hashes_sha256"] = "0" * 64
        coordinator["state_sha256"] = scorer.state_digest(coordinator)
        config["coordinator_sha256"] = put(Path(config["coordinator"]), coordinator)
    elif damage == "ids":
        config["target_ids"] = list(reversed(config["target_ids"]))
    elif damage == "stage_sha":
        config["successor_stage_sha256"] = "0" * 64
    else:
        coordinator["successor_audit"]["actual_lease_id"] = "wrong-lease"
        coordinator["state_sha256"] = scorer.state_digest(coordinator)
        config["coordinator_sha256"] = put(Path(config["coordinator"]), coordinator)
    digest = put(path, config)
    monkeypatch.setattr(scorer, "label_manifest", lambda *_: pytest.fail("labels opened"))
    with pytest.raises((AssertionError, ValueError)):
        scorer.run(path, digest, queue_state=queue)
    assert not Path(config["output"]).exists()


def test_durable_gate_then_paired_score_and_replay_contract(tmp_path, monkeypatch):
    config, path, digest, queue, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(scorer, "label_manifest", lambda *_: {"fake": "hash"})
    def labels(cfg, *_):
        gate = json.loads((Path(cfg["output"]) / "no_metric_gate.json").read_text())
        assert gate["target_labels_read"] is False
        return [], [], [], {"score": 0.4}, {"score": 0.5}, {"score": 0.6}
    monkeypatch.setattr(scorer, "score_with_labels", labels)
    result = scorer.run(path, digest, queue_state=queue)
    assert result["status"] == "PASS_EXP227_SOURCE44_TARGET6BBA_CURRENT116_V4"
    assert result["baseline_replay"] == "PASS_1e-12"
    assert result["delta_vs_current_baseline"] == pytest.approx(0.1)
    assert result["no_metric_gate_sha256"] == scorer.sha(
        Path(config["output"]) / "no_metric_gate.json")


def test_actual_exp214_row_replay_precedes_current_candidate(tmp_path, monkeypatch):
    name = "6bba_00000000"
    evaluator = tmp_path / "evaluator.json"
    evaluator.write_text("{}")
    config = {"target_ids": [name], "evaluator_config": str(evaluator),
              "repo": str(tmp_path / "repo")}
    legacy_evaluate = object()
    geff = types.ModuleType("geff")
    geff.GeffMetadata = types.SimpleNamespace(read=lambda _: types.SimpleNamespace(
        extra={"estimated_number_of_nodes": 2}))
    package = types.ModuleType("biohub_tracking")
    package.__path__ = []
    metrics = types.ModuleType("biohub_tracking.metrics")
    metrics.evaluate = legacy_evaluate
    metrics.node_recall = object()
    metrics.per_sample_metrics = object()
    metrics.summarise = lambda rows: {"score": rows[0]["score"], "n": 116}
    tracksdata = types.ModuleType("tracksdata")
    tracksdata.graph = types.SimpleNamespace(IndexedRXGraph=types.SimpleNamespace(
        from_geff=lambda _: object()))
    current_pkg = types.ModuleType("current_official")
    current_pkg.__path__ = []
    current_metric = types.ModuleType("current_official.metrics")
    current_metric.evaluate = lambda *_args, **_kwargs: None
    current_metric.node_recall = object()
    current_metric.per_sample_metrics = object()
    current_metric.summarise = metrics.summarise
    for key, module in {"geff": geff, "biohub_tracking": package,
                        "biohub_tracking.metrics": metrics,
                        "tracksdata": tracksdata,
                        "current_official": current_pkg,
                        "current_official.metrics": current_metric}.items():
        monkeypatch.setitem(sys.modules, key, module)
    monkeypatch.setattr(scorer, "evaluator_pins", lambda _: None)
    calls = []
    def wrong_baseline(dataset, graph, _dataset, _estimate, evaluator_fn, *_):
        calls.append((graph, evaluator_fn is legacy_evaluate))
        return {"dataset": dataset, "score": 0.51 if evaluator_fn is legacy_evaluate else 0.6,
                "num_pred_nodes": 1}
    monkeypatch.setattr(scorer, "score_one", wrong_baseline)
    before = list(sys.path)
    try:
        with pytest.raises(SystemExit):
            scorer.score_with_labels(config, {name: {"zarr": "synthetic.zarr"}},
                                     {name: {"nodes": {1: None}}}, {name: "old"},
                                     {name: {"dataset": name, "score": 0.5, "num_pred_nodes": 1}}, {},
                                     [{"dataset": name, "scale": [1.625, 0.40625, 0.40625]}])
        assert calls == [("old", True)]
        calls.clear()
        def replayed(dataset, graph, _dataset, _estimate, evaluator_fn, *_):
            calls.append((graph, evaluator_fn is legacy_evaluate))
            score = 0.5 if evaluator_fn is legacy_evaluate else (0.52 if graph == "old" else 0.6)
            return {"dataset": dataset, "score": score, "num_pred_nodes": 1}
        monkeypatch.setattr(scorer, "score_one", replayed)
        _, old_rows, new_rows, _, old_summary, new_summary = scorer.score_with_labels(
            config, {name: {"zarr": "synthetic.zarr"}},
            {name: {"nodes": {1: None}}}, {name: "old"},
            {name: {"dataset": name, "score": 0.5, "num_pred_nodes": 1}}, {},
            [{"dataset": name, "scale": [1.625, 0.40625, 0.40625]}])
        assert calls[0] == ("old", True)
        assert old_rows[0]["score"] == old_summary["score"] == 0.52
        assert new_rows[0]["score"] == new_summary["score"] == 0.6
    finally:
        sys.path[:] = before


def test_production_pins_and_future_stage_gate():
    assert scorer.SUCCESSOR_TOKEN == "exp227_target6bba_chunk07_v3_20260927"
    assert scorer.SUCCESSOR_BASE_LEASE == "exp227-target6bba-chunk07-v3-20260927"
    assert scorer.SUCCESSOR_RUNNER_SHA == "43e0b87893242d2fcf830d514f184ed3da8485ebebf3d32dee7ace370f0cec35"
    assert stager.ATTEMPT1_RESULT_SHA == "800c78e010bef37eac0f6f167f9ddb28fca819577b2aa41c6a1092c30599b9bf"
    assert stager.ATTEMPT1_LEASE == "exp227-target6bba-chunk07-v3a01-20260927"
    with pytest.raises(AssertionError):
        stager.local_gate(stager.STOPPED_COORDINATOR, "0" * 64)
    prepared = {"stage": {"manifest_sha256": "a" * 64,
                          "score_config_sha256": "b" * 64},
                "coordinator_local_sha256": "c" * 64,
                "config": {"output": verifier.RUN + "/output"}}
    remote_launch = launcher.source(prepared)
    assert "score_exp227_target6bba_current_v4.py" in remote_launch
    compile(remote_launch, "remote_launch", "exec")
    compile(verifier.remote_probe(prepared, {"wrapper_pid": 123}),
            "remote_probe", "exec")


def test_attempt1_and_final_sha_are_exact_stage_pins(tmp_path, monkeypatch):
    launch_result = tmp_path / "attempt01_result.json"
    launch_sha = put(launch_result, {"status": "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V3",
                                     "attempt": 1,
                                     "lease": {"id": stager.ATTEMPT1_LEASE}})
    monkeypatch.setattr(stager, "ATTEMPT1_RESULT", launch_result)
    monkeypatch.setattr(stager, "ATTEMPT1_RESULT_SHA", launch_sha)
    chunks = [{} for _ in range(7)] + [{"launch": {"result": {
        "lease": {"id": stager.ATTEMPT1_LEASE}}}}]
    coordinator = {"successor_audit": {"actual_attempt": 1,
        "actual_lease_id": stager.ATTEMPT1_LEASE,
        "attempt_receipts": {"result_sha256": launch_sha}}, "chunks": chunks}
    final = tmp_path / "final.json"
    final_sha = put(final, coordinator)
    stager.exact_final_pin(coordinator, final_sha, final)
    with pytest.raises(AssertionError):
        stager.exact_final_pin(coordinator, "0" * 64, final)
    coordinator["successor_audit"]["actual_attempt"] = 0
    with pytest.raises(AssertionError):
        stager.exact_final_pin(coordinator, final_sha, final)
    coordinator["successor_audit"]["actual_attempt"] = 1
    coordinator["successor_audit"]["attempt_receipts"]["result_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        stager.exact_final_pin(coordinator, final_sha, final)


def test_launch_requires_reviewed_final_sha_before_remote_access(tmp_path, monkeypatch):
    final = tmp_path / "final.json"
    final_sha = put(final, {"synthetic": True})
    stage = tmp_path / "stage.json"
    put(stage, {"status": "STAGED_EXP227_TARGET116_CURRENT_SCORER_V4_NO_LABELS",
                "target_labels_read": False, "target_score_computed": False,
                "gate_only": {"status": "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"},
                "coordinator_local_path": str(final),
                "coordinator_local_sha256": final_sha})
    monkeypatch.setattr(launcher, "STAGE", stage)
    monkeypatch.setattr(launcher, "FINAL", final)
    monkeypatch.setattr(launcher, "INTENT", tmp_path / "intent.json")
    monkeypatch.setattr(launcher, "RECEIPT", tmp_path / "receipt.json")
    monkeypatch.setattr(launcher, "ssh_gate_only", lambda *_: pytest.fail("remote access"))
    with pytest.raises(AssertionError):
        launcher.launch("0" * 64)
    assert not (tmp_path / "intent.json").exists()
