"""Local contracts for v2 EXP236 exact continuation; no remote mutation."""

import ast
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import launch_exp236_source_resume_v2 as launch  # noqa: E402
import prepare_exp236_source_resume_v2 as prepare  # noqa: E402
import run_exp236_source_resume_v2 as runner  # noqa: E402


def sha(body):
    return hashlib.sha256(body).hexdigest()


def audit_summary():
    return {key: value for key, value in prepare.verify_source_audits().items()
            if key != "duplicate_starts"}


def parent_plan_for(block):
    plan = json.loads((ROOT / "work/exp236_source6bba_v2_20260927/plan.json").read_text())
    plan["block_end_epoch"] = {1: 3, 2: 6, 3: 9}[block]
    return plan


def resume_plan_for(parent_block):
    previous, start, end = prepare.SCHEDULE[parent_block]
    parent_code, parent_run = prepare.paths(parent_block)
    _, next_run = prepare.paths(parent_block + 1)
    parent = parent_plan_for(parent_block)
    return {
        "experiment": "EXP236", "purpose": "source_only_reciprocal_horaz_resume",
        "source_embryo": "6bba", "target_embryo": "44b6", "fold": 0,
        "start_epoch": start, "block_end_epoch": end,
        "parent_completed_epochs": previous, "planned_epochs": 50, "resume": True,
        "checkpoint_selection": "deferred_source_graph_10_20_30_40_50",
        "source_bundle_sha256": parent["source_bundle_sha256"],
        "source_manifest_sha256": runner.SOURCE_MANIFEST_SHA,
        "source_duplicate_policy": parent["source_duplicate_policy"],
        "source_duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA,
        "excluded_pairs_by_split": parent["excluded_pairs_by_split"],
        "removed_sampled_windows_by_split": parent["removed_sampled_windows_by_split"],
        "train": parent["train"], "inner_validation": parent["inner_validation"],
        "data_root": parent["data_root"],
        "initial_output_root": prepare.paths(1)[1] + "/output",
        "parent_code": parent_code,
        "parent_plan_sha256": "a" * 64,
        "parent_code_manifest_sha256": "b" * 64,
        "parent_checkpoint": parent_run + "/output/fold0/last.pt",
        "parent_checkpoint_sha256": "c" * 64,
        "parent_history_sha256": "d" * 64,
        "parent_result_sha256": "e" * 64,
        "output": next_run + "/output",
    }


@pytest.mark.parametrize("parent_block", [1, 2, 3])
def test_resume_plan_keeps_v2_source_filter_and_exact_schedule(parent_block):
    plan = resume_plan_for(parent_block)
    runner.validate(plan)
    runner_text = (ROOT / "scripts/run_exp236_source_resume_v2.py").read_text()
    assert '"optimizer", "rng_state"' in runner_text
    assert "train.train_fold(cfg, 0" in runner_text and "resume=True" in runner_text
    assert plan["initial_output_root"] == runner.INITIAL_OUTPUT_ROOT
    assert plan["removed_sampled_windows_by_split"] == {"train": 809,
                                                         "inner_validation": 101}
    for changed in (
        {"source_duplicate_map_sha256": "0" * 64},
        {"parent_code": plan["parent_code"].replace("_v2_", "_")},
        {"initial_output_root": plan["initial_output_root"].replace("_v2_", "_")},
        {"block_end_epoch": plan["block_end_epoch"] + 1},
    ):
        with pytest.raises(AssertionError):
            runner.validate({**plan, **changed})
    bad = json.loads(json.dumps(plan))
    bad["train"][0]["dataset_id"] = "44b6_forbidden"
    with pytest.raises(AssertionError):
        runner.validate(bad)


def extract_written_text(source, marker):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "write_text" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if marker in arg.value:
                        return arg.value
    raise AssertionError(f"Missing stage payload marker: {marker}")


def create_parent_files(root, work, block):
    (root / "reports").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    work.mkdir(exist_ok=True)
    runner_text = (ROOT / "scripts/run_exp236_source_resume_v2.py").read_text()
    (root / "scripts/run_exp236_source_resume_v2.py").write_text(runner_text)
    plan = parent_plan_for(block)
    parent_code, parent_run = prepare.paths(block)
    if block == 1:
        plan_body = (ROOT / "work/exp236_source6bba_v2_20260927/plan.json").read_bytes()
        (work / "plan.json").write_bytes(plan_body)
        manifest_sha = prepare.BLOCK01_CODE_MANIFEST_SHA256
        plan_sha = prepare.BLOCK01_PLAN_SHA256
        status = "PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS"
    else:
        plan_body = (json.dumps(plan, indent=2) + "\n").encode()
        (root / f"reports/exp236_source_block{block:02d}_v2_plan_20260927.json").write_bytes(plan_body)
        manifest_sha = "b" * 64
        plan_sha = sha(plan_body)
        status = "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS"
    prepared = {"status": status, "target_data_opened": False,
                "source_duplicate_audits": audit_summary(),
                "stage": {"status": ("STAGED_EXP236_SOURCE6BBA_BLOCK01_V2" if block == 1
                                      else "STAGED_EXP236_SOURCE_RESUME_V2"),
                          "code": parent_code, "manifest_sha256": manifest_sha,
                          "plan_sha256": plan_sha}}
    (root / f"reports/exp236_source_block{block:02d}_v2_prepare_20260927.json").write_text(
        json.dumps(prepared))
    config = {"experiment": "EXP236", "code": parent_code, "run": parent_run,
              "lease_id": f"exp236-horaz-source6bba-block{block:02d}-v2-20260927"}
    (root / f"reports/exp236_source_block{block:02d}_v2_config_20260927.json").write_text(
        json.dumps(config))
    return runner_text


@pytest.mark.parametrize("parent_block", [1, 2, 3])
def test_prepare_parent_gate_then_parseable_v2_stage(parent_block, tmp_path, monkeypatch):
    work = tmp_path / "work"
    runner_text = create_parent_files(tmp_path, work, parent_block)
    parent_code, parent_run = prepare.paths(parent_block)
    child_code, _ = prepare.paths(parent_block + 1)
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "WORK", work)
    monkeypatch.setattr(sys, "argv", ["prepare_exp236_source_resume_v2.py",
                                      "--parent-block", str(parent_block)])
    calls = []

    def fake_ssh(host, command, source=None):
        calls.append((host, command, source))
        if host == "nsu-quadro":
            return {"requests": [{"id": f"exp236-horaz-source6bba-block{parent_block:02d}-v2-20260927",
                                  "state": "RELEASED", "run_path": parent_run}]}
        ast.parse(source)
        if "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT" in source:
            assert parent_code in source and child_code in source
            assert runner.SOURCE_DUPLICATE_MAP_SHA in source
            return {"status": "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT",
                    "duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA,
                    "checkpoint_sha256": "c" * 64,
                    "history_sha256": "d" * 64,
                    "result_sha256": "e" * 64}
        assert "shutil.copy2(path,destination)" in source
        assert "exp236_source_duplicate_pairs.json" in source
        assert "run_exp236_source_resume_v2.py" in source
        assert ("run_exp236_source_block01_v2.py" if parent_block == 1
                else "run_exp236_source_resume_v2.py") in source
        plan_text = extract_written_text(source, '"purpose": "source_only_reciprocal_horaz_resume"')
        staged_runner = extract_written_text(source, "Exact v2 source6bba continuation")
        assert staged_runner == runner_text
        return {"status": "STAGED_EXP236_SOURCE_RESUME_V2", "code": child_code,
                "manifest_sha256": "f" * 64,
                "plan_sha256": sha(plan_text.encode()),
                "runner_sha256": sha(staged_runner.encode()),
                "duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA}

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    prepare.main()
    assert len(calls) == 3
    child = parent_block + 1
    plan_path = tmp_path / f"reports/exp236_source_block{child:02d}_v2_plan_20260927.json"
    child_plan = json.loads(plan_path.read_text())
    runner.validate(child_plan)
    assert child_plan["parent_code"] == parent_code
    assert child_plan["source_duplicate_map_sha256"] == runner.SOURCE_DUPLICATE_MAP_SHA
    receipt = json.loads((tmp_path / f"reports/exp236_source_block{child:02d}_v2_prepare_20260927.json").read_text())
    assert receipt["source_duplicate_map_sha256"] == runner.SOURCE_DUPLICATE_MAP_SHA
    assert receipt["target_data_opened"] is False


def test_prepare_blocks_unreleased_v2_parent_before_remote_preflight(tmp_path, monkeypatch):
    work = tmp_path / "work"
    create_parent_files(tmp_path, work, 1)
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "WORK", work)
    monkeypatch.setattr(sys, "argv", ["prepare_exp236_source_resume_v2.py", "--parent-block", "1"])
    calls = []

    def fake_ssh(host, command, source=None):
        calls.append(host)
        return {"requests": [{"id": "exp236-horaz-source6bba-block01-v2-20260927",
                              "state": "RUNNING", "run_path": prepare.paths(1)[1]}]}

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    with pytest.raises(AssertionError):
        prepare.main()
    assert calls == ["nsu-quadro"]
    assert not (tmp_path / "reports/exp236_source_block02_v2_plan_20260927.json").exists()


def test_prepare_blocks_failed_v2_parent_without_staging(tmp_path, monkeypatch):
    work = tmp_path / "work"
    create_parent_files(tmp_path, work, 1)
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "WORK", work)
    monkeypatch.setattr(sys, "argv", ["prepare_exp236_source_resume_v2.py", "--parent-block", "1"])
    calls = []

    def fake_ssh(host, command, source=None):
        calls.append(host)
        if host == "nsu-quadro":
            return {"requests": [{"id": "exp236-horaz-source6bba-block01-v2-20260927",
                                  "state": "RELEASED", "run_path": prepare.paths(1)[1]}]}
        ast.parse(source)
        assert "result['status']==EXPECTED_STATUS" in source
        assert "checkpoint_sha256" in source
        return {"status": "FAILED_EXP236_SOURCE_BLOCK01"}

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    with pytest.raises(AssertionError):
        prepare.main()
    assert calls == ["nsu-quadro", "nsu-a100"]
    assert not (tmp_path / "reports/exp236_source_block02_v2_plan_20260927.json").exists()


@pytest.mark.parametrize("other_waiting", [False, True])
def test_launcher_fairness_and_prelaunch_release(tmp_path, monkeypatch, other_waiting):
    block = 2
    root = tmp_path
    (root / "reports").mkdir()
    parent_code, parent_run = prepare.paths(1)
    child_code, child_run = prepare.paths(block)
    (root / "reports/exp236_source_block01_v2_config_20260927.json").write_text(
        json.dumps({"lease_id": "exp236-horaz-source6bba-block01-v2-20260927",
                    "run": parent_run, "code": parent_code}))
    child_config = {"experiment": "EXP236", "max_seconds": 10800,
                    "code": child_code, "run": child_run,
                    "lease_id": "exp236-horaz-source6bba-block02-v2-20260927",
                    "token": "exp236_horaz_source6bba_block02_v2_20260927",
                    "script": "run_exp236_source_resume_v2.py",
                    "arguments": [child_code + "/plan.json", "--plan-sha256", "a" * 64]}
    config_path = root / "reports/exp236_source_block02_v2_config_20260927.json"
    config_path.write_text(json.dumps(child_config))
    summary = audit_summary()
    prepared = {"status": "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS",
                "target_data_opened": False, "parent_block": 1, "next_block": 2,
                "source_duplicate_audits": summary,
                "source_duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA,
                "preflight": {"status": "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT",
                              "duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA},
                "stage": {"status": "STAGED_EXP236_SOURCE_RESUME_V2",
                          "code": child_code, "plan_sha256": "a" * 64,
                          "manifest_sha256": "b" * 64,
                          "duplicate_map_sha256": runner.SOURCE_DUPLICATE_MAP_SHA}}
    (root / "reports/exp236_source_block02_v2_prepare_20260927.json").write_text(json.dumps(prepared))
    monkeypatch.setattr(launch, "ROOT", root)
    monkeypatch.setattr(sys, "argv", ["launch_exp236_source_resume_v2.py", "--block", "2"])
    calls = []

    def fake_ssh(host, command, source=None):
        calls.append((host, command, source))
        if host == "nsu-quadro" and command.endswith(" status"):
            requests = [{"id": "exp236-horaz-source6bba-block01-v2-20260927",
                         "state": "RELEASED", "run_path": parent_run}]
            if other_waiting:
                requests.append({"id": "other-project", "state": "WAITING",
                                 "project": "other-project"})
            return {"requests": requests}
        if host == "nsu-a100" and source and "nvidia-smi" in source:
            ast.parse(source)
            assert runner.SOURCE_DUPLICATE_MAP_SHA in source
            raise RuntimeError("GPU occupied")
        if host == "nsu-a100" and source and "run_exists" in source:
            return {"run_exists": False}
        if host == "nsu-quadro" and " release" in command:
            return {"state": "RELEASED"}
        raise AssertionError((host, command))

    monkeypatch.setattr(launch, "ssh", fake_ssh)
    monkeypatch.setattr(launch, "queue_request", (
        (lambda *_args: pytest.fail("fairness gate must block reservation"))
        if other_waiting else
        (lambda *_args: {"state": "RESERVED", "gpus": ["GPU-occupied"],
                          "alias": "nsu-a100"})
    ))
    if other_waiting:
        with pytest.raises(AssertionError, match="Other project waiting"):
            launch.main()
        assert not config_path.with_name(config_path.stem + "_reservation.json").exists()
        return
    with pytest.raises(RuntimeError, match="GPU occupied"):
        launch.main()
    release_path = config_path.with_name(config_path.stem + "_prelaunch_release.json")
    assert json.loads(release_path.read_text())["queue"]["state"] == "RELEASED"
    assert not config_path.with_name(config_path.stem + "_partial_launch.json").exists()
