"""Focused local contracts for EXP236 v2 source11 epoch10 no-label graph prep."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import launch_exp236_source_graph10_v2 as launch  # noqa: E402
import prepare_exp236_source_graph10_v2 as prepare  # noqa: E402
import run_exp236_source_graph10_v2 as runner  # noqa: E402


def digest(body):
    return hashlib.sha256(body).hexdigest()


def chain():
    rows = []
    for block, epoch in enumerate(runner.EPOCHS, 1):
        code, run = runner.block_paths(block)
        rows.append({"status": "PASS_EXP236_SOURCE_V2_BLOCK_AUDIT", "block": block,
                     "completed_epochs": epoch, "code": code.as_posix(), "run": run.as_posix(),
                     "manifest_sha256": f"{block:064x}", "plan_sha256": f"{block+4:064x}",
                     "checkpoint_sha256": f"{block+8:064x}",
                     "history_sha256": f"{block+12:064x}",
                     "result_sha256": f"{block+16:064x}",
                     "exit_sha256": f"{block+20:064x}", "target_data_opened": False})
    return rows


def plan():
    rows = chain()
    base = json.loads((ROOT / "work/exp236_source6bba_v2_20260927/plan.json").read_text())
    return {"experiment": "EXP236_SOURCE_GRAPH10", "source_embryo": "6bba",
            "target_embryo": "44b6", "fold": 0, "checkpoint_epoch": 10,
            "source_manifest_sha256": runner.SOURCE_MANIFEST_SHA,
            "source_bundle_sha256": runner.SOURCE_BUNDLE_SHA,
            "source_duplicate_policy": runner.POLICY,
            "source_duplicate_map_sha256": runner.DUPLICATE_MAP_SHA,
            "excluded_pairs_by_split": {"train": 824, "inner_validation": 103},
            "removed_sampled_windows_by_split": {"train": 809, "inner_validation": 101},
            "training_chain": rows,
            "training_code_manifest_sha256": rows[-1]["manifest_sha256"],
            "training_plan_sha256": rows[-1]["plan_sha256"],
            "checkpoint": runner.TRAIN_RUN + "/output/fold0/last.pt",
            "checkpoint_sha256": rows[-1]["checkpoint_sha256"],
            "training_run": runner.TRAIN_RUN,
            "training_result_sha256": rows[-1]["result_sha256"],
            "training_history_sha256": rows[-1]["history_sha256"],
            "data_root": runner.REMOTE + "/data/exp213_source_view_20260912",
            "code": runner.CODE, "output": runner.RUN + "/output",
            "movies": [{"dataset": row["dataset_id"], "zarr": row["zarr_path"],
                        "shape": [100, 1, 128, 128]} for row in base["inner_validation"]]}


def staged_text(source, marker):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "write_text" and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    if marker in value.value:
                        return value.value
    raise AssertionError(f"Generated stage lacks {marker}")


def test_exact_inner11_chain_and_duplicate_policy():
    valid = plan()
    runner.validate(valid)
    assert tuple(row["dataset"] for row in valid["movies"]) == runner.INNER_IDS
    for key, value in (("checkpoint_epoch", 9), ("source_duplicate_map_sha256", "0" * 64),
                       ("checkpoint", runner.TRAIN_RUN + "/output/fold0/epoch_010.pt"),
                       ("target_embryo", "6bba")):
        with pytest.raises(AssertionError):
            runner.validate({**valid, key: value})
    bad = json.loads(json.dumps(valid))
    bad["movies"][0]["dataset"] = "44b6_forbidden"
    with pytest.raises(AssertionError):
        runner.validate(bad)
    bad = json.loads(json.dumps(valid))
    bad["training_chain"][2]["completed_epochs"] = 8
    with pytest.raises(AssertionError):
        runner.validate(bad)


def test_no_label_guard_rejects_labels_target_and_other_source_images(tmp_path):
    guard = runner.no_labels_guard(tmp_path, runner.INNER_IDS)
    guard("open", (tmp_path / (runner.INNER_IDS[0] + ".zarr") / "0" / "zarr.json",))
    for path in (tmp_path / (runner.INNER_IDS[0] + ".geff") / "attributes.json",
                 tmp_path / "44b6_forbidden.zarr" / "0" / "zarr.json",
                 tmp_path / "6bba_unlisted.zarr" / "0" / "zarr.json"):
        with pytest.raises(PermissionError):
            guard("open", (path,))


def test_prepare_requires_controller_and_four_released_audits(tmp_path, monkeypatch):
    audits = [{key: value for key, value in row.items() if key not in ("code", "run")}
              for row in chain()]
    original_path = tmp_path / "original.json"
    original_path.write_text('{"status":"STOPPED_EXP236_SOURCE_V2_CONTINUATION"}')
    controller_path = tmp_path / "controller.json"
    controller = {"status": "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED",
                  "original_receipt_sha256": digest(original_path.read_bytes()),
                  "target_data_opened": False,
                  "final_audit": audits[-1],
                  **{f"block{block:02d}_audit": row for block, row in enumerate(audits, 1)}}
    controller_path.write_text(json.dumps(controller))
    monkeypatch.setattr(prepare, "CONTROLLER_RECEIPT", controller_path)
    monkeypatch.setattr(prepare, "ORIGINAL_CONTROLLER_RECEIPT", original_path)
    parent_plan = json.loads((ROOT / "work/exp236_source6bba_v2_20260927/plan.json").read_text())

    def local_block(block, launched):
        assert launched is True
        row = chain()[block - 1]
        p = {**parent_plan, "block_end_epoch": runner.EPOCHS[block - 1]}
        return ({"stage": {"manifest_sha256": row["manifest_sha256"],
                            "plan_sha256": row["plan_sha256"]}},
                {"alias": "nsu-a100", "code": row["code"], "run": row["run"]}, p,
                {"lease": {"state": "RESERVED"}})

    monkeypatch.setattr(prepare, "local_block", local_block)
    monkeypatch.setattr(prepare, "queue_status", lambda: {"requests": []})
    monkeypatch.setattr(prepare, "lease_for", lambda _, block: {
        "state": "RELEASED", "alias": "nsu-a100", "run_path": chain()[block - 1]["run"]})
    monkeypatch.setattr(prepare, "audit_block", lambda block, parent: audits[block - 1])
    result, controller_sha = prepare.verify_parent_chain()
    assert result == chain() and controller_sha == digest(controller_path.read_bytes())
    controller["block03_audit"] = {**audits[2], "checkpoint_sha256": "0" * 64}
    controller_path.write_text(json.dumps(controller))
    with pytest.raises(AssertionError):
        prepare.verify_parent_chain()
    controller["block03_audit"] = audits[2]
    controller["status"] = "STOPPED_EXP236_SOURCE_V2_CONTINUATION"
    controller_path.write_text(json.dumps(controller))
    with pytest.raises(AssertionError):
        prepare.verify_parent_chain()


def test_prepare_builds_pinned_plan_and_parsable_stage(tmp_path, monkeypatch):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "reports").mkdir()
    for name in ("run_exp236_source_graph10_v2.py", "run_exp223_inference.py"):
        shutil.copy2(ROOT / "scripts" / name, tmp_path / "scripts" / name)
    rows = chain()
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "PLAN_PATH", tmp_path / "reports/exp236_source_graph10_v2_plan_20260927.json")
    monkeypatch.setattr(prepare, "CONFIG_PATH", tmp_path / "reports/exp236_source_graph10_v2_config_20260927.json")
    monkeypatch.setattr(prepare, "PREPARE_PATH", tmp_path / "reports/exp236_source_graph10_v2_prepare_20260927.json")
    monkeypatch.setattr(prepare, "verify_parent_chain", lambda: (rows, "a" * 64))
    calls = []

    def fake_ssh(alias, command, source):
        calls.append((alias, source))
        ast.parse(source)
        if "PASS_EXP236_SOURCE10_V2_PARENT_PREFLIGHT" in source:
            assert runner.DUPLICATE_MAP_SHA in source
            assert "PASS_EXP236_SOURCE_BLOCK_10_OF_50" in source
            return {"status": "PASS_EXP236_SOURCE10_V2_PARENT_PREFLIGHT",
                    "checkpoint_sha256": rows[-1]["checkpoint_sha256"],
                    "training_result_sha256": rows[-1]["result_sha256"],
                    "training_history_sha256": rows[-1]["history_sha256"],
                    "movies": plan()["movies"]}
        staged_plan = staged_text(source, '"experiment": "EXP236_SOURCE_GRAPH10"')
        staged_runner = staged_text(source, "Freeze eleven EXP236 v2 epoch10")
        assert "run_exp236_source_graph10_v2.py" in source
        return {"status": "STAGED_EXP236_SOURCE_GRAPH10_V2", "code": runner.CODE,
                "manifest_sha256": "f" * 64,
                "plan_sha256": digest(staged_plan.encode()),
                "runner_sha256": digest(staged_runner.encode()),
                "duplicate_map_sha256": runner.DUPLICATE_MAP_SHA}

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    prepare.main()
    assert len(calls) == 2
    saved_plan = json.loads(prepare.PLAN_PATH.read_text())
    runner.validate(saved_plan)
    assert saved_plan["checkpoint_sha256"] == rows[-1]["checkpoint_sha256"]
    assert saved_plan["training_chain"] == rows
    receipt = json.loads(prepare.PREPARE_PATH.read_text())
    assert receipt["source_labels_read"] is False and receipt["target_data_opened"] is False
    assert sha_file(prepare.PLAN_PATH) == receipt["stage"]["plan_sha256"]


def sha_file(path):
    return digest(Path(path).read_bytes())


@pytest.mark.parametrize("run_exists", [False, True])
def test_gpu_prelaunch_release_only_when_run_absent(tmp_path, monkeypatch, run_exists):
    graph_plan = plan()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(graph_plan))
    controller_path = tmp_path / "controller.json"
    controller_path.write_text("{}")
    config_path = tmp_path / "config.json"
    parent_path = tmp_path / "parent.json"
    prepare_path = tmp_path / "prepare.json"
    graph_config = {"experiment": "EXP236", "max_seconds": 7200,
                    "code": runner.CODE, "run": runner.RUN,
                    "script": "run_exp236_source_graph10_v2.py",
                    "arguments": [runner.CODE + "/plan.json", "--plan-sha256", sha_file(plan_path)],
                    "lease_id": "exp236-source-graph10-v2-20260927", "token": "token"}
    config_path.write_text(json.dumps(graph_config))
    parent_path.write_text(json.dumps({"code": graph_plan["training_chain"][-1]["code"],
                                      "run": runner.TRAIN_RUN,
                                      "lease_id": "exp236-horaz-source6bba-block04-v2-20260927"}))
    prepare_path.write_text(json.dumps({"status": "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS",
                                        "source_labels_read": False, "target_labels_read": False,
                                        "target_data_opened": False, "movies": 11,
                                        "controller_receipt_sha256": sha_file(controller_path),
                                        "training_chain": graph_plan["training_chain"],
                                        "stage": {"code": runner.CODE,
                                                  "plan_sha256": sha_file(plan_path),
                                                  "manifest_sha256": "f" * 64}}))
    monkeypatch.setattr(launch, "CONFIG_PATH", config_path)
    monkeypatch.setattr(launch, "PREPARE_PATH", prepare_path)
    monkeypatch.setattr(launch, "PLAN_PATH", plan_path)
    monkeypatch.setattr(launch, "CONTROLLER_RECEIPT", controller_path)
    monkeypatch.setattr(launch, "PARENT_CONFIG", parent_path)
    calls = []

    def fake_ssh(alias, command, source=None):
        calls.append((alias, command))
        if command.endswith(" status"):
            return {"requests": [{"id": "exp236-horaz-source6bba-block04-v2-20260927",
                                  "state": "RELEASED", "run_path": runner.TRAIN_RUN}]}
        if "--verified-stopped" in command:
            return {"state": "RELEASED"}
        if source and "PASS_EXP236_SOURCE_GRAPH10_V2_STAGE_RECHECK" in source:
            ast.parse(source)
            return {"status": "PASS_EXP236_SOURCE_GRAPH10_V2_STAGE_RECHECK"}
        if source and "run_exists" in source:
            return {"run_exists": run_exists}
        if source and "nvidia-smi" in source:
            ast.parse(source)
            lines = source.splitlines()
            assert next(i for i, line in enumerate(lines) if "nvidia-smi" in line) < (
                next(i for i, line in enumerate(lines) if "run.mkdir" in line))
            raise RuntimeError("GPU occupied")
        raise AssertionError("Unexpected SSH call")

    monkeypatch.setattr(launch, "ssh", fake_ssh)
    monkeypatch.setattr(launch, "queue_request", lambda *args: {
        "state": "RESERVED", "gpus": ["GPU-test"], "alias": "nsu-a100"})
    with pytest.raises(RuntimeError, match="GPU occupied"):
        launch.main()
    releases = [command for _, command in calls if "--verified-stopped" in command]
    assert len(releases) == (0 if run_exists else 1)
