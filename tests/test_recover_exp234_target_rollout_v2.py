"""Resume only frozen EXP234 chunks after the stopped coordinator's five releases."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import recover_exp234_target_rollout_v2 as recovery  # noqa: E402


def records():
    return [{"source": source, "chunk": index,
             "movies": (14 if source == "6bba" and index == 3 else
                        15 if source == "6bba" or index < 4 else 14),
             "plan_sha256": f"plan-{source}-{index}",
             "csv_sha256": f"csv-{source}-{index}"}
            for source, index in recovery.SEQUENCE]


def make_fixture(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    chosen = {"44b6": {"selected_threshold": "0.965",
                       "result_sha256": "result44", "gate_sha256": "gate44"},
              "6bba": {"selected_threshold": "0.940",
                       "result_sha256": "result6", "gate_sha256": "gate6"}}
    original = {"status": "STOPPED_EXP234_TARGET_ROLLOUT", "target_labels_read": False,
                "code_manifest_sha256": "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4",
                "source_choices": chosen, "completed": records()[:5],
                "error": "RuntimeError('Target 44b6_chunk01 launch failed')",
                "finished_or_stopped": 100}
    (reports / "exp234_target_coordinator_v2_20260927.json").write_text(json.dumps(original))
    (reports / "exp234_target_44b6_chunk01_config_v2_20260927_coordinator_launch.log").write_text(
        "AssertionError: Other project is waiting")
    prepared = {"status": "PREPARED_EXP234_TARGET175_NO_LABELS", "target_labels_read": False,
                "stage": {"manifest_sha256": original["code_manifest_sha256"],
                          "plan_sha256": {f"{source}_chunk{index:02d}_plan.json":
                                          f"plan-{source}-{index}"
                                          for source, index in recovery.SEQUENCE}},
                "assignment_sha256": "assignment", "source_choices": chosen}
    (reports / "exp234_target_prepare_v2_20260927.json").write_text(json.dumps(prepared))
    (reports / "exp234_target_chunk_assignment_20260926.json").write_text("assignment")
    for source, index in recovery.SEQUENCE[5:]:
        token = f"{source}_chunk{index:02d}"
        config = {"code": recovery.CODE, "script": "run_exp234_target_chunk.py",
                  "run": recovery.ROOT.as_posix() + f"/runs/exp234_target_{token}_v2_20260927",
                  "arguments": [recovery.CODE + f"/{token}_plan.json", "--plan-sha256",
                                f"plan-{source}-{index}"],
                  "lease_id": f"exp234-target-{token}",
                  "resources": {"cpu": 8, "ram_gib": 64}}
        (reports / f"exp234_target_{token}_config_v2_20260927.json").write_text(json.dumps(config))
    return original, prepared, chosen


def test_original_prefix_rechecks_five_and_refuses_duplicate(tmp_path):
    original, prepared, chosen = make_fixture(tmp_path)
    real_sha = recovery.sha

    def sha(path):
        if Path(path).name == "exp234_target_chunk_assignment_20260926.json":
            return "assignment"
        return real_sha(path)

    with ExitStack() as stack:
        stack.enter_context(patch.object(recovery, "ROOT", tmp_path))
        stack.enter_context(patch.object(recovery, "ORIGINAL", tmp_path / "reports/exp234_target_coordinator_v2_20260927.json"))
        stack.enter_context(patch.object(recovery, "TARGET_PREPARE", tmp_path / "reports/exp234_target_prepare_v2_20260927.json"))
        stack.enter_context(patch.object(recovery, "sha", sha))
        full_choices = {source: {**item, "status": "VERIFIED_EXP234_SOURCE_SELECTION"}
                        for source, item in chosen.items()}
        stack.enter_context(patch.object(recovery, "local_freeze", return_value=({}, full_choices)))
        checked = stack.enter_context(patch.object(recovery, "check_release", side_effect=lambda source, index, *_:
                                      next(row for row in records() if row["source"] == source
                                           and row["chunk"] == index)))
        assert recovery.original_prefix()[0] == original
        assert checked.call_count == 5
        duplicate = tmp_path / "reports/exp234_target_44b6_chunk01_config_v2_20260927_launch.json"
        duplicate.write_text("{}")
        with pytest.raises(AssertionError, match="already launched"):
            recovery.original_prefix()


def test_fairness_requires_no_foreign_waiter_and_available_a100():
    gpus = ["gpu0", "gpu1"]
    config = {"lease_id": "our-next", "resources": {"cpu": 8, "ram_gib": 64}}
    active = {"id": "other", "state": "RESERVED", "project": "other",
              "pool": "a100", "gpus": ["gpu0"], "cpu": 8, "ram_gib": 32}
    state = {"pools": {"a100": {"gpus": gpus, "cpu": 112, "ram_gib": 240}},
             "requests": [active]}
    assert recovery.fair_resource_available(state, config)
    waiter = {"id": "other-waiting", "state": "WAITING_RESOURCE", "project": "other",
              "pool": "a100", "gpus": [], "cpu": 8, "ram_gib": 32}
    assert not recovery.fair_resource_available({**state, "requests": [active, waiter]}, config)
    assert not recovery.fair_resource_available({**state, "requests": [active,
        {**active, "id": "other2", "gpus": ["gpu1"]}]}, config)
    with pytest.raises(AssertionError, match="Existing lease"):
        recovery.fair_resource_available({**state, "requests": [{**active, "id": "our-next"}]}, config)


def test_queue_race_retry_only_before_reservation(tmp_path):
    make_fixture(tmp_path)
    config = json.loads((tmp_path / "reports/exp234_target_44b6_chunk01_config_v2_20260927.json").read_text())
    fairness = SimpleNamespace(returncode=1, stdout="", stderr="AssertionError: Other project is waiting")
    result = {}
    with ExitStack() as stack:
        stack.enter_context(patch.object(recovery, "ROOT", tmp_path))
        stack.enter_context(patch.object(recovery, "save"))
        run = stack.enter_context(patch.object(recovery.subprocess, "run", return_value=fairness))
        stack.enter_context(patch.object(recovery, "queue_status", return_value={"requests": []}))
        stack.enter_context(patch.object(recovery, "ssh", return_value={"run_absent": True}))
        assert recovery.launch_one("44b6", 1, config, result) is False
        assert run.call_count == 1
    assert not (tmp_path / "reports/exp234_target_44b6_chunk01_config_v2_20260927_launch.json").exists()
    with ExitStack() as stack:
        stack.enter_context(patch.object(recovery, "ROOT", tmp_path))
        stack.enter_context(patch.object(recovery, "save"))
        stack.enter_context(patch.object(recovery.subprocess, "run", return_value=SimpleNamespace(
            returncode=1, stdout="", stderr="RuntimeError: actual failure")))
        with pytest.raises(RuntimeError, match="launch failed"):
            recovery.launch_one("44b6", 1, config, result)


def test_main_launches_only_remaining_seven(tmp_path):
    original = {"completed": records()[:5], "source_choices": {}}
    prepare = {"stage": {"manifest_sha256": "manifest"}}
    receipt = tmp_path / "recovery.json"
    original_path = tmp_path / "original.json"
    original_path.write_text("original")
    launched = []

    def fake_launch(source, index, config, result):
        launched.append((source, index))
        return True

    with ExitStack() as stack:
        stack.enter_context(patch.object(recovery, "RECEIPT", receipt))
        stack.enter_context(patch.object(recovery, "ORIGINAL", original_path))
        stack.enter_context(patch.object(recovery, "original_prefix", return_value=(original, {}, {}, prepare)))
        stack.enter_context(patch.object(recovery, "assert_unlaunched", return_value={}))
        stack.enter_context(patch.object(recovery, "wait_fair"))
        stack.enter_context(patch.object(recovery, "launch_one", side_effect=fake_launch))
        stack.enter_context(patch.object(recovery, "wait_and_verify_chunk", side_effect=lambda source, index, *_:
                            next(row for row in records() if row["source"] == source
                                 and row["chunk"] == index)))
        recovery.main()
    assert launched == list(recovery.SEQUENCE[5:])
    final = json.loads(receipt.read_text())
    assert final["completed"][:5] == original["completed"]
    assert final["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    assert sum(row["movies"] for row in final["completed"]) == 175
