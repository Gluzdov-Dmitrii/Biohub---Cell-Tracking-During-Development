"""Local-only tests for EXP239 one-shot stage and bounded CPU launch."""
from __future__ import annotations

import ast
import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_exp239_division_fn_taxonomy as stage  # noqa: E402
import launch_exp239_division_fn_taxonomy as launch  # noqa: E402


def assignment(source: str, key: str):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == key for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing assignment {key}")


def test_exact_eight_file_bundle_and_source19_scale():
    manifest, config = stage.local_bundle()
    assert len(manifest["files"]) == 8
    assert "PREREG.md" in manifest["files"]
    assert "source_inner19_image_scale_audit_v2_20260927.json" in manifest["files"]
    assert "exp234_current_image_scale_audit_20260927.json" not in manifest["files"]
    image = json.loads((stage.BUNDLE / "source_inner19_image_scale_audit_v2_20260927.json").read_text())
    assert image["count"] == 19
    assert [row["dataset"] for row in image["rows"]] == [
        name for cohort in config["cohorts"] for name in cohort["ids"]]
    assert {tuple(row["scale"]) for row in image["rows"]} == {
        (1.625, 0.40625, 0.40625)}


def test_stage_payload_is_exact_bytes_and_ast_checked():
    manifest, _ = stage.local_bundle()
    source = stage.stage_source(manifest)
    files = assignment(source, "files")
    expected = assignment(source, "expected")
    assert set(files) == set(manifest["files"]) | {"manifest.json"}
    assert expected["manifest.json"] == stage.MANIFEST_SHA
    for relative, encoded in files.items():
        original = (stage.BUNDLE / relative).read_bytes()
        assert base64.b64decode(encoded, validate=True) == original
        assert hashlib.sha256(original).hexdigest() == expected[relative]
    assert "assert not code.exists() and not run.exists()" in source
    assert "ast.parse(path.read_bytes().decode('utf-8')" in source
    readback = stage.remote_readback_source(manifest)
    assert "observed==expected" in readback
    assert "not run.exists()" in readback


def test_dry_runs_make_no_remote_call_and_bound_one_cpu_child(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("dry run attempted SSH")

    monkeypatch.setattr(stage, "ssh", forbidden)
    monkeypatch.setattr(launch, "ssh", forbidden)
    stage_plan = stage.dry_run_plan()
    launch_plan = launch.dry_run_plan()
    assert stage_plan["source_files"] == 8
    assert stage_plan["remote_mutation"] is False
    assert launch_plan["remote_mutation"] is False
    assert launch_plan["command"] == [
        stage.PYTHON, "-B", stage.CODE + "/audit_exp239.py",
        "--bundle-sha256", stage.MANIFEST_SHA]
    assert launch_plan["cpu_affinity"] == (24, 25, 26, 27)
    assert launch_plan["ram_bytes"] == 16 * 1024**3
    assert launch_plan["max_seconds"] == 2700
    wrapper = launch.cpu_wrapper_source()
    assert assignment(wrapper, "cmd") == launch.command()
    assert assignment(wrapper, "affinity") == (24, 25, 26, 27)
    assert assignment(wrapper, "ram_bytes") == 16 * 1024**3
    assert assignment(wrapper, "wall_seconds") == 2700
    assert "CUDA_VISIBLE_DEVICES=''" in wrapper
    assert "resource.setrlimit(resource.RLIMIT_AS" in wrapper
    assert "resource.setrlimit(resource.RLIMIT_CPU,(2400,2400))" in wrapper
    assert "child.wait(timeout=wall_seconds)" in wrapper


def test_read_only_preflight_and_launch_sources_parse():
    manifest, config = stage.local_bundle()
    preflight = stage.import_preflight_source(config, expect_code=False)
    assert assignment(preflight, "expect_code") is False
    assert "assert code.exists()==expect_code and not run.exists()" in preflight
    assert "deny_labels" in preflight
    assert "score_exp227_source_graph10" in preflight
    assert "score_exp236_source_graph10" in preflight
    remote = launch.remote_launch_source(manifest)
    wrapper = assignment(remote, "wrapper")
    assert hashlib.sha256(wrapper.encode()).hexdigest() == assignment(remote, "wrapper_sha")
    assert assignment(remote, "command") == launch.command()
    assert "code.is_dir() and not run.exists()" in remote
    ast.parse(wrapper)
    ast.parse(launch.launch_readback_source())


def test_stage_intent_precedes_uncertain_remote_write(monkeypatch, tmp_path):
    intent, receipt = tmp_path / "stage_intent.json", tmp_path / "stage_receipt.json"
    monkeypatch.setattr(stage, "STAGE_INTENT", intent)
    monkeypatch.setattr(stage, "STAGE_RECEIPT", receipt)
    monkeypatch.setattr(stage, "import_preflight", lambda *_args, **_kwargs: {
        "status": "PASS_EXP239_EXACT_IMPORT_PREFLIGHT_NO_LABELS",
        "torch_available": False, "labels_read": False, "code_present": False,
        "run_absent": True,
    })

    def uncertain(*_args, **_kwargs):
        assert intent.is_file() and not receipt.exists()
        raise RuntimeError("uncertain stage result")

    monkeypatch.setattr(stage, "ssh", uncertain)
    with pytest.raises(RuntimeError, match="uncertain stage result"):
        stage.stage()
    assert intent.is_file() and not receipt.exists()


def test_launch_intent_precedes_uncertain_remote_start(monkeypatch, tmp_path):
    intent, receipt = tmp_path / "launch_intent.json", tmp_path / "launch_receipt.json"
    stage_receipt = tmp_path / "stage_receipt.json"
    stage_receipt.write_text("{}\n")
    manifest, config = stage.local_bundle()
    monkeypatch.setattr(launch, "LAUNCH_INTENT", intent)
    monkeypatch.setattr(launch, "LAUNCH_RECEIPT", receipt)
    monkeypatch.setattr(launch, "STAGE_RECEIPT", stage_receipt)
    monkeypatch.setattr(launch, "local_gate", lambda: (manifest, config, {}))
    monkeypatch.setattr(launch, "import_preflight", lambda *_args, **_kwargs: {
        "status": "PASS_EXP239_EXACT_IMPORT_PREFLIGHT_NO_LABELS",
        "torch_available": False, "labels_read": False, "code_present": True,
        "run_absent": True,
    })
    calls = []

    def remote(*_args, **_kwargs):
        calls.append(True)
        if len(calls) == 1:
            assert not intent.exists()
            return {"status": "PASS_EXP239_REMOTE_STAGE_READBACK", "run_absent": True}
        assert intent.is_file() and not receipt.exists()
        raise RuntimeError("uncertain launch result")

    monkeypatch.setattr(launch, "ssh", remote)
    with pytest.raises(RuntimeError, match="uncertain launch result"):
        launch.launch()
    assert len(calls) == 2
    assert intent.is_file() and not receipt.exists()


def test_existing_launch_intent_blocks_duplicate(monkeypatch, tmp_path):
    intent = tmp_path / "already-intended.json"
    intent.write_text("{}\n")
    monkeypatch.setattr(launch, "LAUNCH_INTENT", intent)
    monkeypatch.setattr(launch, "LAUNCH_RECEIPT", tmp_path / "none.json")
    with pytest.raises(AssertionError, match="reconciliation"):
        launch.local_gate()
