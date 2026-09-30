"""EXP234 target score handoff stays behind the exact no-label release gate."""
import ast
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import continue_exp234_after_target_rollout as handoff  # noqa: E402
import verify_exp234_target_official_scorer as verifier  # noqa: E402


def final_receipt():
    return {"status": "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED",
            "pid": 35608, "started": 100, "finished_or_stopped": 200,
            "target_labels_read": False,
            "original_coordinator_sha256": "originhash",
            "code_manifest_sha256": "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4",
            "source_choices": {"44b6": {"selected_threshold": "0.965",
                                         "result_sha256": "result44", "gate_sha256": "gate44"},
                               "6bba": {"selected_threshold": "0.940",
                                         "result_sha256": "result6", "gate_sha256": "gate6"}},
            "completed": [
                {"source": source, "chunk": index, "movies": 14 if source == "6bba" and index == 3
                 else 15 if source == "6bba" or index < 4 else 14,
                 "plan_sha256": f"plan-{source}-{index}", "csv_sha256": f"csv-{source}-{index}"}
                for source, index in handoff.SEQUENCE]}


def test_wait_requires_successful_coordinator_receipt(tmp_path):
    path = tmp_path / "coordinator.json"
    final = final_receipt()
    assert sum(item["movies"] for item in final["completed"]) == 175
    path.write_text(json.dumps(final))
    with patch.object(handoff, "COORDINATOR", path), \
         patch.object(handoff.psutil, "Process", side_effect=handoff.psutil.NoSuchProcess(35608)):
        assert handoff.wait_coordinator() == final
        for bad in ({**final, "status": "WAITING_FOR_FAIR_A100"},
                    {**final, "target_labels_read": True},
                    {**final, "completed": final["completed"][:-1]}):
            path.write_text(json.dumps(bad))
            with pytest.raises(AssertionError):
                handoff.wait_coordinator()


def test_exact_release_recheck_blocks_changed_hash(tmp_path):
    prepared = {"status": "PREPARED_EXP234_TARGET175_NO_LABELS",
                "target_labels_read": False,
                "stage": {"manifest_sha256": final_receipt()["code_manifest_sha256"],
                          "plan_sha256": {f"{source}_chunk{index:02d}_plan.json":
                                          f"plan-{source}-{index}"
                                          for source, index in handoff.SEQUENCE}},
                "assignment_sha256": "assignment", "source_choices": final_receipt()["source_choices"]}
    target_prepare = tmp_path / "prepare.json"
    target_prepare.write_text(json.dumps(prepared))
    assignment = tmp_path / "reports/exp234_target_chunk_assignment_20260926.json"
    assignment.parent.mkdir()
    assignment.write_text("assignment")
    coordinator = tmp_path / "coordinator.json"
    coordinator.write_text(json.dumps(final_receipt()))
    original = tmp_path / "original.json"
    original.write_text(json.dumps({"status": "STOPPED_EXP234_TARGET_ROLLOUT",
                                    "target_labels_read": False,
                                    "completed": final_receipt()["completed"][:5]}))
    original_sha = handoff.sha

    def fake_sha(path):
        if Path(path) == assignment:
            return "assignment"
        if Path(path) == original:
            return "originhash"
        return original_sha(path)

    with ExitStack() as stack:
        stack.enter_context(patch.object(handoff, "ROOT", tmp_path))
        stack.enter_context(patch.object(handoff, "TARGET_PREPARE", target_prepare))
        stack.enter_context(patch.object(handoff, "COORDINATOR", coordinator))
        stack.enter_context(patch.object(handoff, "ORIGINAL", original))
        stack.enter_context(patch.object(handoff, "sha", fake_sha))
        full_choices = {source: {**item, "status": "VERIFIED_EXP234_SOURCE_SELECTION"}
                        for source, item in prepared["source_choices"].items()}
        stack.enter_context(patch.object(handoff, "local_freeze", return_value=({}, full_choices)))
        stack.enter_context(patch.object(handoff, "check_release", side_effect=lambda source, index, *_:
                            next(item for item in final_receipt()["completed"]
                                 if item["source"] == source and item["chunk"] == index)))
        assert handoff.verify_coordinator(final_receipt())["movies"] == 175
        bad = final_receipt()
        bad["completed"][0]["csv_sha256"] = "changed"
        with pytest.raises(AssertionError):
            handoff.verify_coordinator(bad)


def test_score_exit_fails_closed():
    assert handoff.check_score_exit({"exit": None}) is False
    assert handoff.check_score_exit({"exit": {"returncode": 0, "timeout": False}})
    for exit_record in ({"returncode": 1, "timeout": False},
                        {"returncode": 0, "timeout": True}):
        with pytest.raises(RuntimeError):
            handoff.check_score_exit({"exit": exit_record})


def test_handoff_stops_after_one_verified_score(tmp_path):
    paths = {key: tmp_path / key for key in (
        "RECEIPT", "RELEASE", "SCORE_PREPARE", "SCORE_LAUNCH", "SCORE_VERIFIED")}
    steps = []

    def fake_run(name, script, result):
        steps.append(name)
        if name == "prepare_score":
            paths["RELEASE"].write_text("{}")
            paths["SCORE_PREPARE"].write_text(json.dumps({
                "status": "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS",
                "coordinator_receipt_sha256": "coordhash"}))
        elif name == "launch_score":
            paths["SCORE_LAUNCH"].write_text(json.dumps({
                "status": "EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED", "run": handoff.SCORE_RUN}))
        else:
            paths["SCORE_VERIFIED"].write_text(json.dumps({
                "status": "VERIFIED_EXP234_TARGET175_OFFICIAL", "rows": 175,
                "baseline_replay": "PASS_1e-12", "official_score": 0.83,
                "coordinator_receipt_sha256": "coordhash"}))

    with ExitStack() as stack:
        for key, path in paths.items():
            stack.enter_context(patch.object(handoff, key, path))
        stack.enter_context(patch.object(handoff, "wait_coordinator", side_effect=lambda: steps.append("wait_coordinator") or final_receipt()))
        stack.enter_context(patch.object(handoff, "verify_coordinator", side_effect=lambda _: steps.append("release_audit") or {"coordinator_sha256": "coordhash"}))
        stack.enter_context(patch.object(handoff, "run_step", side_effect=fake_run))
        stack.enter_context(patch.object(handoff, "wait_score_exit", side_effect=lambda _: steps.append("wait_score_exit")))
        handoff.main()
    assert steps == ["wait_coordinator", "release_audit", "prepare_score", "launch_score",
                     "wait_score_exit", "verify_score"]
    assert json.loads(paths["RECEIPT"].read_text())["status"] == "PASS_EXP234_TARGET175_OFFICIAL_SCORE_HANDOFF"
    with patch.object(handoff, "RECEIPT", paths["RECEIPT"]), pytest.raises(AssertionError):
        handoff.main()


def test_remote_verifier_template_is_parsable_and_pins_score():
    prepared = {"stage": {"code": verifier.REMOTE + "/code/exp234_target_official_scorer_v1_20260927",
                          "manifest_sha256": "manifest", "score_config_sha256": "config",
                          "release_manifest_sha256": "release"},
                "config": {"experiment": "EXP234_OFFICIAL_TARGET175", "output": "run/output"}}
    launched = {"run": "run", "wrapper_pid": 42,
                "status": "EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED"}
    source = verifier.remote_probe(prepared, launched)
    ast.parse(source)
    assert "PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS" in source
    assert "baseline_replay']=='PASS_1e-12'" in source
    assert "math.isfinite(result['candidate_summary']['score'])" in source
    assert "fields[2]" in source and "cpu_wrapper.py" in source
    assert "tokens=['44b6_chunk%02d'%i for i in range(8)]+['6bba_chunk%02d'%i for i in range(4)]" in source
    assert "manifest['score_exp234_target_official.py']==" in source


def test_verifier_pins_original_and_recovery_before_remote_read(tmp_path):
    paths = {key: tmp_path / key for key in (
        "PREPARE", "LAUNCH", "COORDINATOR", "ORIGINAL", "RELEASE", "RECEIPT")}
    original = {"status": "STOPPED_EXP234_TARGET_ROLLOUT",
                "completed": final_receipt()["completed"][:5]}
    paths["ORIGINAL"].write_text(json.dumps(original))
    recovered = final_receipt()
    recovered["original_coordinator_sha256"] = verifier.sha(paths["ORIGINAL"])
    paths["COORDINATOR"].write_text(json.dumps(recovered))
    paths["RELEASE"].write_text("{}")
    run = verifier.REMOTE + "/runs/exp234_target_official_score175_20260927"
    prepared = {"status": "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS",
                "target_labels_read": False,
                "coordinator_receipt_sha256": verifier.sha(paths["COORDINATOR"]),
                "original_coordinator_receipt_sha256": verifier.sha(paths["ORIGINAL"]),
                "release_manifest_local_sha256": verifier.sha(paths["RELEASE"]),
                "stage": {"code": verifier.REMOTE + "/code/exp234_target_official_scorer_v1_20260927",
                          "manifest_sha256": "manifest", "score_config_sha256": "config",
                          "release_manifest_sha256": "release"},
                "config": {"experiment": "EXP234_OFFICIAL_TARGET175", "output": run + "/output"}}
    paths["PREPARE"].write_text(json.dumps(prepared))
    paths["LAUNCH"].write_text(json.dumps({
        "status": "EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED",
        "run": run, "score_config_sha256": "config", "wrapper_pid": 42}))
    with ExitStack() as stack:
        for key, path in paths.items():
            stack.enter_context(patch.object(verifier, key, path))
        remote = stack.enter_context(patch.object(verifier, "ssh", return_value={
            "status": "VERIFIED_EXP234_TARGET175_OFFICIAL", "rows": 175,
            "baseline_replay": "PASS_1e-12", "official_score": 0.83}))
        verifier.main()
        assert remote.call_count == 1
        saved = json.loads(paths["RECEIPT"].read_text())
        assert saved["status"] == "VERIFIED_EXP234_TARGET175_OFFICIAL"
        assert saved["metric_identity"] == "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY"
        assert saved["current_organizer_score"] is None
        paths["RECEIPT"].unlink()
        assert verifier.verify(write_receipt=False)["official_score"] == 0.83
        assert not paths["RECEIPT"].exists()
        assert remote.call_count == 2
        paths["ORIGINAL"].write_text(json.dumps({**original, "altered": True}))
        with pytest.raises(AssertionError):
            verifier.main()
        assert remote.call_count == 2
