"""Local-only checks for SOURCE-INNER byte staging and CPU launch plans."""

import ast
import base64
import hashlib
from pathlib import Path
import sys
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_source_inner_error_decomposition as stage  # noqa: E402
import launch_source_inner_error_decomposition as launch  # noqa: E402


def assigned_literal(source, name):
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing assignment: {name}")


def test_byte_stage_preserves_nested_paths_and_exact_manifest():
    manifest, _ = stage.local_bundle()
    source = stage.stage_source(manifest)
    payload = assigned_literal(source, "files")
    expected = assigned_literal(source, "expected")
    assert set(payload) == set(manifest["files"]) | {"manifest.json"}
    assert "tracking_cellmot_official/metrics.py" in payload
    assert expected["manifest.json"] == stage.MANIFEST_SHA
    for relative, encoded in payload.items():
        original = (stage.BUNDLE / relative).read_bytes()
        assert base64.b64decode(encoded, validate=True) == original
        assert hashlib.sha256(original).hexdigest() == expected[relative]
    assert assigned_literal(source, "manifest_sha") == stage.MANIFEST_SHA
    assert "ast.parse(path.read_bytes().decode('utf-8')" in source


def test_dry_run_stage_and_cpu_commands_have_no_remote_call(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("dry run attempted SSH")

    monkeypatch.setattr(stage, "ssh", forbidden)
    monkeypatch.setattr(launch, "ssh", forbidden)
    stage_plan = stage.dry_run_plan()
    launch_plan = launch.dry_run_plan()
    assert stage_plan["status"] == "DRY_RUN_SOURCE_INNER_STAGE_NO_REMOTE_CALL"
    assert stage_plan["remote_mutation"] is False
    assert stage_plan["import_command"] == [stage.PYTHON, "-B", "-"]
    assert stage_plan["stage_command"] == ["python3", "-B", "-"]
    assert launch_plan["remote_mutation"] is False
    assert launch_plan["command"] == [
        stage.PYTHON, "-B", stage.CODE + "/audit_source_inner.py",
        "--bundle-sha256", stage.MANIFEST_SHA,
    ]
    assert launch_plan["cpu_affinity"] == (24, 25, 26, 27)
    assert launch_plan["ram_bytes"] == 16 * 1024**3
    assert launch_plan["max_seconds"] == 2700

    wrapper = launch.cpu_wrapper_source()
    assert assigned_literal(wrapper, "cmd") == launch.command()
    assert assigned_literal(wrapper, "affinity") == (24, 25, 26, 27)
    assert assigned_literal(wrapper, "ram_bytes") == 16 * 1024**3
    assert assigned_literal(wrapper, "wall_seconds") == 2700
    assert "CUDA_VISIBLE_DEVICES=''" in wrapper
    assert "resource.setrlimit(resource.RLIMIT_AS" in wrapper
    assert "child.wait(timeout=wall_seconds)" in wrapper


def test_read_only_import_preflight_and_launch_source_parse():
    manifest, config = stage.local_bundle()
    preflight = stage.import_preflight_source(config, expect_code=False)
    assert "score_exp227_source_graph10" in preflight
    assert "score_exp236_source_graph10" in preflight
    assert "biohub_tracking.metrics" in preflight
    assert "deny_labels" in preflight
    assert assigned_literal(preflight, "expect_code") is False

    remote_launch = launch.remote_launch_source(manifest)
    wrapper = assigned_literal(remote_launch, "wrapper")
    assert hashlib.sha256(wrapper.encode()).hexdigest() == assigned_literal(
        remote_launch, "wrapper_sha")
    assert assigned_literal(remote_launch, "command") == launch.command()
    ast.parse(wrapper)
    ast.parse(launch.launch_readback_source())


def test_stage_intent_is_durable_before_uncertain_remote_mutation(monkeypatch, tmp_path):
    intent = tmp_path / "stage_intent.json"
    receipt = tmp_path / "stage_receipt.json"
    monkeypatch.setattr(stage, "STAGE_INTENT", intent)
    monkeypatch.setattr(stage, "STAGE_RECEIPT", receipt)
    monkeypatch.setattr(stage, "import_preflight", lambda *_args, **_kwargs: {
        "status": "PASS_SOURCE_INNER_EXACT_IMPORT_PREFLIGHT_NO_LABELS",
        "torch_available": False, "labels_read": False, "code_present": False,
        "run_absent": True, "source_modules": [
            {"experiment": "EXP227"}, {"experiment": "EXP236"}],
    })

    def uncertain_remote(*_args, **_kwargs):
        assert intent.is_file()
        assert not receipt.exists()
        raise RuntimeError("uncertain remote result")

    monkeypatch.setattr(stage, "ssh", uncertain_remote)
    with pytest.raises(RuntimeError, match="uncertain remote result"):
        stage.stage()
    assert intent.is_file()
    assert not receipt.exists()


def test_launch_intent_is_durable_before_uncertain_remote_mutation(monkeypatch, tmp_path):
    intent = tmp_path / "launch_intent.json"
    receipt = tmp_path / "launch_receipt.json"
    stage_receipt = tmp_path / "stage_receipt.json"
    stage_receipt.write_text("{}\n")
    manifest, config = stage.local_bundle()
    monkeypatch.setattr(launch, "LAUNCH_INTENT", intent)
    monkeypatch.setattr(launch, "LAUNCH_RECEIPT", receipt)
    monkeypatch.setattr(launch, "STAGE_RECEIPT", stage_receipt)
    monkeypatch.setattr(launch, "local_gate", lambda: (manifest, config, {}))
    monkeypatch.setattr(launch, "import_preflight", lambda *_args, **_kwargs: {
        "status": "PASS_SOURCE_INNER_EXACT_IMPORT_PREFLIGHT_NO_LABELS",
        "torch_available": False, "labels_read": False, "code_present": True,
        "run_absent": True, "source_modules": [
            {"experiment": "EXP227"}, {"experiment": "EXP236"}],
    })
    calls = []

    def remote(*_args, **_kwargs):
        calls.append(True)
        if len(calls) == 1:
            assert not intent.exists()
            return {"status": "PASS_SOURCE_INNER_REMOTE_STAGE_READBACK",
                    "run_absent": True}
        assert intent.is_file()
        assert not receipt.exists()
        raise RuntimeError("uncertain launch result")

    monkeypatch.setattr(launch, "ssh", remote)
    with pytest.raises(RuntimeError, match="uncertain launch result"):
        launch.launch()
    assert len(calls) == 2
    assert intent.is_file()
    assert not receipt.exists()
