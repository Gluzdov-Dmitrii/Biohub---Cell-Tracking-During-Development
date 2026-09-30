"""Local EXP209 scorer handoff guards; never contact SSH or open target labels."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_exp209_reconstructed_scorer_v1 as stage  # noqa: E402
import launch_exp209_reconstructed_scorer_v1 as launch  # noqa: E402
import supervise_exp209_reconstructed_scorer_v1 as supervisor  # noqa: E402


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def local_root(tmp_path: Path) -> Path:
    root = tmp_path / "w"
    shutil.copytree(ROOT / stage.LOCAL_BUNDLE, root / stage.LOCAL_BUNDLE)
    (root / "reports").mkdir()
    return root


def remote_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path, Path]:
    """Move generated remote programs into a disposable, label-free namespace."""
    remote = tmp_path / "r"
    code = remote / "code" / stage.NAME
    run = remote / "runs" / stage.NAME
    control = remote / "runs" / ("." + stage.NAME + ".control")
    code.parent.mkdir(parents=True)
    run.parent.mkdir(parents=True)
    monkeypatch.setattr(stage, "REMOTE", str(remote))
    monkeypatch.setattr(stage, "CODE_DIR", str(code))
    monkeypatch.setattr(stage, "RUN_ROOT", str(run))
    monkeypatch.setattr(stage, "STAGE_INTENT", str(code.parent / ("." + stage.NAME + ".stage_intent.json")))
    monkeypatch.setattr(stage, "STAGE_COMPLETE", str(code.parent / ("." + stage.NAME + ".stage_complete.json")))
    monkeypatch.setattr(launch, "REMOTE", str(remote))
    monkeypatch.setattr(launch, "CODE_DIR", str(code))
    monkeypatch.setattr(launch, "RUN_ROOT", str(run))
    monkeypatch.setattr(launch, "CONTROL", str(control))
    monkeypatch.setattr(launch, "PYTHON", sys.executable)
    monkeypatch.setattr(launch, "RECON_GATE", str(remote / "runs" / "reconstruction_gate.json"))
    return code, run, control


def rewrite_zip(payload: bytes, *, extra: str | None = None,
                changed: str | None = None) -> bytes:
    with zipfile.ZipFile(io.BytesIO(payload)) as source, io.BytesIO() as memory:
        with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for name in source.namelist():
                raw = source.read(name)
                if name == changed:
                    raw = bytes([raw[0] ^ 1]) + raw[1:]
                target.writestr(name, raw)
            if extra is not None:
                target.writestr(extra, b"unexpected\n")
        return memory.getvalue()


def test_exact_sealed_zip_preserves_14_nested_payloads_and_crlf() -> None:
    bundle = ROOT / stage.LOCAL_BUNDLE
    payload, hashes = stage.pack_checked_bundle(bundle)
    manifest_raw = (bundle / "bundle_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    names = {row["name"] for row in manifest["files"]}
    assert len(names) == 14 and len(hashes) == 15
    assert any("/" in name for name in names)
    assert hashes["bundle_manifest.json"] == digest(manifest_raw) == stage.MANIFEST_SHA
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.namelist() == sorted(names | {"bundle_manifest.json"})
        for row in manifest["files"]:
            raw = (bundle / row["name"]).read_bytes()
            assert len(raw) == row["bytes"]
            assert archive.read(row["name"]) == raw
            assert digest(raw) == hashes[row["name"]] == row["sha256"]
        # This archived source has CRLF. A text-mode transfer would change its SHA.
        crlf_name = "score_exp223_official.py"
        assert b"\r\n" in archive.read(crlf_name)
        assert archive.read(crlf_name) == (bundle / crlf_name).read_bytes()


@pytest.mark.parametrize("damage,message", [
    ("traversal", "unsafe or duplicate scorer payload path"),
    ("extra", "missing or extra payload"),
    ("tamper", "scorer payload changed"),
])
def test_local_bundle_rejects_unsafe_extra_and_changed_bytes(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, damage: str, message: str) -> None:
    root = local_root(tmp_path)
    bundle = root / stage.LOCAL_BUNDLE
    if damage == "traversal":
        manifest_path = bundle / "bundle_manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"][0]["name"] = "../outside.py"
        manifest_path.write_bytes((json.dumps(manifest, sort_keys=True) + "\n").encode())
        monkeypatch.setattr(stage, "MANIFEST_SHA", stage.sha(manifest_path))
    elif damage == "extra":
        (bundle / "extra.py").write_bytes(b"pass\n")
    else:
        path = bundle / "current_official" / "metrics.py"
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    with pytest.raises(ValueError, match=message):
        stage.pack_checked_bundle(bundle)


@pytest.mark.parametrize("damage,message", [
    ("traversal", "unsafe stage ZIP paths"),
    ("extra", "remote ZIP payload set mismatch"),
    ("tamper", "config.json"),
])
def test_generated_stage_rejects_zip_damage_before_intent(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, damage: str, message: str) -> None:
    payload, _ = stage.pack_checked_bundle(ROOT / stage.LOCAL_BUNDLE)
    code, run, _ = remote_paths(monkeypatch, tmp_path)
    if damage == "traversal":
        payload = rewrite_zip(payload, extra="../outside.py")
    elif damage == "extra":
        payload = rewrite_zip(payload, extra="extra.py")
    else:
        payload = rewrite_zip(payload, changed="config.json")
    source = stage.remote_stage_program(payload, "a" * 64)
    with pytest.raises(AssertionError, match=message):
        exec(compile(source, "<generated-exp209-stage>", "exec"), {})
    assert not code.exists() and not run.exists()
    assert not Path(stage.STAGE_INTENT).exists()


def test_stage_and_launch_write_durable_intents_once_without_ssh(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = local_root(tmp_path)
    _, hashes = stage.pack_checked_bundle(root / stage.LOCAL_BUNDLE)
    stage_intent = root / stage.LOCAL_INTENT
    stage_receipt = root / stage.LOCAL_RECEIPT
    launch_intent = root / launch.LOCAL_INTENT
    launch_receipt = root / launch.LOCAL_RECEIPT
    calls: list[str] = []

    def fake_stage_ssh(_host: str, program: str, timeout: int = 180) -> dict:
        calls.append("stage" if len(calls) == 0 else "readback")
        assert timeout == 180
        assert stage_intent.is_file() and not stage_receipt.exists()
        assert json.loads(stage_intent.read_text())["remote_stage"] == "UNATTEMPTED"
        compile(program, "<remote-stage-or-readback>", "exec")
        if len(calls) == 1:
            return {"status": "STAGED_EXP209_SCORER_V1_NO_RUN", "code_dir": stage.CODE_DIR,
                    "run_root": stage.RUN_ROOT, "file_hashes": hashes, "file_count": 15,
                    "remote_stage_intent_sha256": "e" * 64,
                    "labels_read": False, "metric_executed": False}
        return {"status": "PASS_EXP209_SCORER_REMOTE_SHA_READBACK",
                "file_hashes": hashes, "bundle_manifest_sha256": stage.MANIFEST_SHA,
                "config_sha256": stage.CONFIG_SHA,
                "remote_stage_intent_sha256": "e" * 64,
                "remote_stage_complete_sha256": "b" * 64,
                "run_absent": True, "labels_read": False, "metric_executed": False}

    monkeypatch.setattr(stage, "ssh_python", fake_stage_ssh)
    staged = stage.stage(root, "forbidden-host", stage.MANIFEST_SHA, stage.CONFIG_SHA)
    assert calls == ["stage", "readback"]
    assert staged["status"] == "PASS_EXP209_SCORER_V1_STAGED_NO_RUN"
    assert staged["local_stage_intent_sha256"] == stage.sha(stage_intent)
    assert stage_receipt.is_file()
    with pytest.raises(ValueError, match="already attempted"):
        stage.stage(root, "forbidden-host", stage.MANIFEST_SHA, stage.CONFIG_SHA)
    assert calls == ["stage", "readback"]

    stage_receipt_sha = stage.sha(stage_receipt)
    supervisor_sha = stage.sha(ROOT / launch.SUPERVISOR_SOURCE)
    # The handoff fixture copies the sealed bundle; the separate supervisor is local code.
    (root / "scripts").mkdir()
    shutil.copyfile(ROOT / launch.SUPERVISOR_SOURCE, root / launch.SUPERVISOR_SOURCE)

    def fake_launch_ssh(_host: str, program: str, timeout: int = 180) -> dict:
        calls.append("launch")
        assert timeout == 600
        assert launch_intent.is_file() and not launch_receipt.exists()
        assert json.loads(launch_intent.read_text())["remote_action"] == "UNATTEMPTED"
        compile(program, "<remote-launch>", "exec")
        return {"status": "STARTED_EXP209_SCORER_V1_CPU_SUPERVISOR",
                "control_dir": launch.CONTROL, "run_root": launch.RUN_ROOT,
                "bundle_manifest_sha256": launch.MANIFEST_SHA,
                "config_sha256": launch.CONFIG_SHA, "supervisor_sha256": supervisor_sha,
                "supervisor_pid": 1201, "supervisor_start_tick": 301,
                "worker_pid": 1202, "worker_start_tick": 302,
                "launcher_geff_opened": False,
                "launcher_target_metric_executed": False, "gpu_used": False,
                "preflight": {"status": "PASS_EXP209_SCORER_CURRENT_ENV_SYNTHETIC_NO_GEFF"}}

    monkeypatch.setattr(stage, "ssh_python", fake_launch_ssh)
    launched = launch.launch(root, "forbidden-host", launch.MANIFEST_SHA,
                             launch.CONFIG_SHA, stage_receipt_sha)
    assert calls == ["stage", "readback", "launch"]
    assert launched["local_launch_intent_sha256"] == stage.sha(launch_intent)
    assert launched["local_stage_receipt_sha256"] == stage_receipt_sha
    assert launched["worker_resources"] == {"cpu_count": 8,
                                            "memory_bytes": 32 * 1024**3,
                                            "wall_timeout_seconds": 8 * 60 * 60}
    assert launch_receipt.is_file()
    with pytest.raises(ValueError, match="already attempted"):
        launch.launch(root, "forbidden-host", launch.MANIFEST_SHA,
                      launch.CONFIG_SHA, stage_receipt_sha)
    assert calls == ["stage", "readback", "launch"]


def test_ambiguous_stage_ssh_keeps_intent_and_refuses_retry(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = local_root(tmp_path)
    intent = root / stage.LOCAL_INTENT
    receipt = root / stage.LOCAL_RECEIPT
    calls = 0

    def uncertain(_host: str, _program: str, timeout: int = 180) -> dict:
        nonlocal calls
        calls += 1
        assert intent.is_file() and not receipt.exists()
        raise TimeoutError("ambiguous SSH stage reply")

    monkeypatch.setattr(stage, "ssh_python", uncertain)
    with pytest.raises(TimeoutError, match="ambiguous SSH"):
        stage.stage(root, "forbidden-host", stage.MANIFEST_SHA, stage.CONFIG_SHA)
    assert intent.is_file() and not receipt.exists()
    with pytest.raises(ValueError, match="already attempted"):
        stage.stage(root, "forbidden-host", stage.MANIFEST_SHA, stage.CONFIG_SHA)
    assert calls == 1


def test_stage_requires_independent_remote_readback_match(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = local_root(tmp_path)
    _, hashes = stage.pack_checked_bundle(root / stage.LOCAL_BUNDLE)
    calls = 0

    def remote(_host: str, _program: str, timeout: int = 180) -> dict:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"status": "STAGED_EXP209_SCORER_V1_NO_RUN", "code_dir": stage.CODE_DIR,
                    "run_root": stage.RUN_ROOT, "file_hashes": hashes, "file_count": 15,
                    "remote_stage_intent_sha256": "e" * 64,
                    "labels_read": False, "metric_executed": False}
        bad = dict(hashes)
        bad["current_official/metrics.py"] = "0" * 64
        return {"status": "PASS_EXP209_SCORER_REMOTE_SHA_READBACK",
                "file_hashes": bad, "bundle_manifest_sha256": stage.MANIFEST_SHA,
                "config_sha256": stage.CONFIG_SHA,
                "remote_stage_intent_sha256": "e" * 64, "run_absent": True,
                "labels_read": False, "metric_executed": False}

    monkeypatch.setattr(stage, "ssh_python", remote)
    with pytest.raises(ValueError, match="post-stage remote SHA readback mismatch"):
        stage.stage(root, "forbidden-host", stage.MANIFEST_SHA, stage.CONFIG_SHA)
    assert calls == 2 and (root / stage.LOCAL_INTENT).is_file()
    assert not (root / stage.LOCAL_RECEIPT).exists()


def seed_stage_receipt(root: Path) -> str:
    _, hashes = stage.pack_checked_bundle(root / stage.LOCAL_BUNDLE)
    path = root / stage.LOCAL_RECEIPT
    stage.write_once_durable(path, {
        "status": "PASS_EXP209_SCORER_V1_STAGED_NO_RUN",
        "code_dir": stage.CODE_DIR, "run_root": stage.RUN_ROOT,
        "file_hashes": hashes, "bundle_manifest_sha256": stage.MANIFEST_SHA,
        "config_sha256": stage.CONFIG_SHA,
        "remote_stage_intent_sha256": "e" * 64,
        "remote_stage_complete_sha256": "b" * 64,
        "labels_read": False, "metric_executed": False,
        "remote_run_created": False,
    })
    (root / "scripts").mkdir()
    shutil.copyfile(ROOT / launch.SUPERVISOR_SOURCE, root / launch.SUPERVISOR_SOURCE)
    return stage.sha(path)


def test_launch_stage_receipt_sha_gate_and_ambiguous_ssh(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = local_root(tmp_path)
    receipt_sha = seed_stage_receipt(root)
    intent = root / launch.LOCAL_INTENT
    receipt = root / launch.LOCAL_RECEIPT
    calls = 0

    def uncertain(_host: str, program: str, timeout: int = 180) -> dict:
        nonlocal calls
        calls += 1
        assert timeout == 600 and intent.is_file() and not receipt.exists()
        compile(program, "<remote-launch>", "exec")
        raise TimeoutError("ambiguous SSH launch reply")

    monkeypatch.setattr(stage, "ssh_python", uncertain)
    with pytest.raises(ValueError, match="root-reviewed stage receipt SHA required"):
        launch.launch(root, "forbidden-host", launch.MANIFEST_SHA,
                      launch.CONFIG_SHA, "0" * 64)
    assert not intent.exists() and calls == 0
    with pytest.raises(TimeoutError, match="ambiguous SSH"):
        launch.launch(root, "forbidden-host", launch.MANIFEST_SHA,
                      launch.CONFIG_SHA, receipt_sha)
    assert intent.is_file() and not receipt.exists()
    with pytest.raises(ValueError, match="already attempted"):
        launch.launch(root, "forbidden-host", launch.MANIFEST_SHA,
                      launch.CONFIG_SHA, receipt_sha)
    assert calls == 1


def test_generated_programs_compile_and_bounded_preflight_audit() -> None:
    payload, hashes = stage.pack_checked_bundle(ROOT / stage.LOCAL_BUNDLE)
    stage_source = stage.remote_stage_program(payload, "a" * 64)
    readback_source = stage.remote_readback_program("a" * 64)
    preflight_source = launch.preflight_source()
    launch_source = launch.remote_launch_program(hashes, "b" * 64, "c" * 64,
                                                 "d" * 64,
                                                 (ROOT / launch.SUPERVISOR_SOURCE).read_bytes())
    for name, source in (("stage", stage_source), ("readback", readback_source),
                         ("preflight", preflight_source), ("launch", launch_source)):
        compile(source, f"<exp209-{name}>", "exec")
    compile((ROOT / launch.SUPERVISOR_SOURCE).read_bytes(), "<exp209-supervisor>", "exec")
    assert "os.O_EXCL" in stage_source and "os.fsync" in stage_source
    assert "run_absent':True" in readback_source
    assert "sys.addaudithook(audit)" in preflight_source
    assert "runtime_gate(config" in preflight_source
    assert "target_metric_executed':False" in preflight_source
    assert "timeout=240,check=True" in launch_source
    assert "range(150)" in launch_source and "time.sleep(0.2)" in launch_source
    assert "CUDA_VISIBLE_DEVICES':'','" in launch_source
    assert "assert not run.exists() and not control.exists()" in launch_source
    assert launch_source.index("assert not run.exists() and not control.exists()") < launch_source.index("preflight=subprocess.run")
    assert launch_source.index("preflight=subprocess.run") < launch_source.index("control.mkdir")
    assert supervisor.CPU_COUNT == 8
    assert supervisor.MEMORY_BYTES == 32 * 1024**3
    assert supervisor.WALL_SECONDS == 8 * 60 * 60
    supervisor_source = (ROOT / launch.SUPERVISOR_SOURCE).read_text(encoding="utf-8")
    assert "resource.setrlimit(resource.RLIMIT_AS" in supervisor_source
    assert '"CUDA_VISIBLE_DEVICES": ""' in supervisor_source

    # Run only the preflight audit callback, never runtime_gate or a metric.
    tree = ast.parse(preflight_source)
    audit = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "audit")
    namespace = {"os": os, "pathlib": __import__("pathlib")}
    exec(compile(ast.Module(body=[audit], type_ignores=[]), "<audit-only>", "exec"), namespace)
    namespace["audit"]("open", ("/data/movie.zarr/0",))
    with pytest.raises(PermissionError, match="forbids GEFF"):
        namespace["audit"]("open", ("/data/movie.GEFF/nodes",))


@pytest.mark.parametrize("occupied", ["output", "control"])
def test_generated_launch_refuses_occupied_output_or_control_before_preflight(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, occupied: str) -> None:
    code, run, control = remote_paths(monkeypatch, tmp_path)
    code.mkdir()
    (run if occupied == "output" else control).mkdir()
    source = launch.remote_launch_program({}, "b" * 64, "c" * 64,
                                          "d" * 64, b"# supervisor\n")
    with pytest.raises(AssertionError, match="namespace already exists"):
        exec(compile(source, "<generated-exp209-launch>", "exec"), {})
    assert not (control / "launch_intent.json").exists()
    assert not (control / "supervisor.py").exists()
