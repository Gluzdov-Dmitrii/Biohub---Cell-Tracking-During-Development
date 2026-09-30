"""Focused local-only contracts for the frozen EXP238 peak side channel."""

import ast
import importlib.util
import json
from pathlib import Path
import sys
import types

import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from exp238_patch_horaz import patch_detection, patch_engine
from run_exp238_peak_cache import PeakCollector, PEAK_DTYPE, require_graph_replay, validate_plan
import stage_exp238_peak_cache as stage
import launch_exp238_peak_cache as launch

BUNDLE = ROOT / "work/exp238_source_peak_cache_local_20260927"


def test_exact_pinned_patch_preserves_original_detection_call():
    original_engine = (BUNDLE / "base/engine.py").read_bytes()
    original_detection = (BUNDLE / "base/detection.py").read_bytes()
    patched_engine = patch_engine(original_engine)
    patched_detection = patch_detection(original_detection)
    assert patched_engine == (BUNDLE / "patched/engine.py").read_bytes()
    assert patched_detection == (BUNDLE / "patched/detection.py").read_bytes()
    old_tree = ast.parse(original_engine)
    new_tree = ast.parse(patched_engine)
    assert len(old_tree.body) == len(new_tree.body)
    assert original_engine.count(b"coords = detect_cells(") == patched_engine.count(b"coords = detect_cells(")
    old = original_detection.decode()
    new = patched_detection.decode()
    start = old.index("def detect_cells(")
    end = old.index("\n\ndef _flip(")
    assert old[start:end] == new[new.index("def detect_cells("):new.index("\n\n# EXP238 side channel")]


def test_hook_is_after_branch_and_seen_frame_guard_before_original_detection():
    tree = ast.parse((BUNDLE / "patched/engine.py").read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "emit_exp238_selected_peaks"]
    assert len(calls) == 1
    loops = [node for node in ast.walk(tree) if isinstance(node, ast.For)
             and isinstance(node.target, ast.Tuple)
             and [elt.id for elt in node.target.elts if isinstance(elt, ast.Name)] == ["frame_index", "time"]]
    chosen = [loop for loop in loops if loop.lineno < calls[0].lineno < loop.end_lineno]
    assert len(chosen) == 1
    body = chosen[0].body
    assert isinstance(body[0], ast.If) and isinstance(body[0].body[0], ast.Continue)
    assert isinstance(body[1], ast.Expr) and body[1].value.func.id == "emit_exp238_selected_peaks"
    assert isinstance(body[2], ast.Assign) and body[2].value.func.id == "detect_cells"
    assert body[1].lineno < body[2].lineno
    assert ast.unparse(calls[0].args[0]) == "detection_logits[frame_index][0]"


def load_patched_detection(monkeypatch):
    models = types.ModuleType("models")
    tracker = types.ModuleType("models.tracker")
    tracker.TrackerModel = object
    tracker.position_features = lambda *args: None
    monkeypatch.setitem(sys.modules, "models", models)
    monkeypatch.setitem(sys.modules, "models.tracker", tracker)
    path = BUNDLE / "patched/detection.py"
    spec = importlib.util.spec_from_file_location("detection", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "detection", module)
    spec.loader.exec_module(module)
    return module


def test_hook_module_identity_and_peak_score_pairing(monkeypatch):
    detection = load_patched_detection(monkeypatch)
    from detection import emit_exp238_selected_peaks
    assert emit_exp238_selected_peaks.__globals__ is detection.__dict__
    logits = torch.full((1, 2, 3, 3), -20.0)
    logits[0, 0, 1, 1] = torch.logit(torch.tensor(0.2))
    logits[0, 1, 2, 2] = torch.logit(torch.tensor(0.99))
    received = []
    detection.EXP238_PEAK_HOOK = lambda *args: received.append(args)
    emit_exp238_selected_peaks(logits, 7, 0.96875, (1, 3, 3), False, (1, 4, 4), 1.0, True)
    assert len(received) == 1
    time_index, coords, scores, metadata = received[0]
    assert time_index == 7
    assert coords.tolist() == [[0, 1, 1], [1, 2, 2]]
    np.testing.assert_allclose(scores, [0.2, 0.99], rtol=0, atol=1e-6)
    assert metadata["downsample_zyx"] == [1, 4, 4]
    assert metadata["pool_kernel_zyx"] == [1, 3, 3]
    assert metadata["selected_threshold"] == 0.96875
    assert detection.detect_cells(logits, 7, 0.96875, (1, 3, 3)).tolist() == [[7, 1, 2, 2]]
    detection.EXP238_PEAK_HOOK = None


def test_peak_cap_fails_without_truncation(monkeypatch):
    detection = load_patched_detection(monkeypatch)
    logits = torch.full((1, 2, 3, 3), -20.0)
    logits[0, 0, 1, 1] = 1.0
    logits[0, 1, 2, 2] = 2.0
    detection.EXP238_PEAK_HOOK = lambda *args: None
    detection.EXP238_MAX_PEAKS_PER_FRAME = 1
    with pytest.raises(RuntimeError, match="cap exceeded"):
        detection.emit_exp238_selected_peaks(logits, 0, 0.96875, (1, 3, 3),
                                             False, (1, 4, 4), 1.0, True)


def test_collector_keeps_low_resolution_coordinates_and_guards_order():
    collector = PeakCollector("44b6_example", [100, 64, 256, 256])
    metadata = {"floor": 0.075, "downsample_zyx": [1, 4, 4],
                "logit_shape_zyx": [64, 64, 64], "pool_kernel_zyx": [3, 3, 3],
                "selected_threshold": 0.96875, "adaptive_mode": False,
                "tta": True, "gamma": 1.0}
    collector.add(0, np.asarray([[2, 10, 11]], dtype=np.uint16),
                  np.asarray([0.2], dtype=np.float32), metadata)
    assert collector.parts[0].dtype == PEAK_DTYPE
    assert collector.parts[0][0].tolist() == (0, 2, 10, 11, pytest.approx(0.2))
    with pytest.raises(AssertionError):
        collector.add(0, np.empty((0, 3), dtype=np.uint16),
                      np.empty((0,), dtype=np.float32), metadata)


def test_exact_graph_hash_gate_precedes_peak_save(tmp_path):
    csv_path = tmp_path / "graph.csv"
    csv_path.write_bytes(b"sealed graph bytes\n")
    expected = stage.sha(csv_path)
    assert require_graph_replay(csv_path, expected) == expected
    with pytest.raises(RuntimeError, match="replay mismatch"):
        require_graph_replay(csv_path, "0" * 64)
    tree = ast.parse((SCRIPTS / "run_exp238_peak_cache.py").read_text())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assert next(node.lineno for node in ast.walk(main) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == "require_graph_replay") < (
                    next(node.lineno for node in ast.walk(main) if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Attribute) and node.func.attr == "save"))


def test_local_plans_and_dry_runs_are_nonmutating(monkeypatch, capsys):
    for cohort, count in (("source44", 8), ("source6", 11)):
        plan, local = stage.local_preflight(cohort)
        validate_plan(plan)
        assert len(plan["movies"]) == count
        assert local["plan_sha256"] == stage.sha(BUNDLE / cohort / "exp238_plan.json")
        assert all(row["dataset"].startswith(plan["source_embryo"] + "_")
                   for row in plan["movies"])
    monkeypatch.setattr(stage, "ssh", lambda *args, **kwargs: pytest.fail("dry-run called SSH"))
    monkeypatch.setattr(launch, "ssh", lambda *args, **kwargs: pytest.fail("dry-run called SSH"))
    monkeypatch.setattr(sys, "argv", ["stage", "--cohort", "source44"])
    stage.main()
    assert json.loads(capsys.readouterr().out)["remote_stage"] is False
    monkeypatch.setattr(sys, "argv", ["launch", "--cohort", "source6"])
    launch.main()
    assert json.loads(capsys.readouterr().out)["gpu_request"] is False


def test_stage_and_launch_remote_templates_parse_without_execution(monkeypatch):
    plan, local = stage.local_preflight("source44")
    captured = []

    def capture(alias, command, source):
        assert command == "python3 -" and alias == "nsu-a100"
        ast.parse(source)
        captured.append(source)
        return {"status": "CAPTURED"}

    monkeypatch.setattr(stage, "ssh", capture)
    stage.remote_preflight(plan)
    stage.stage_remote(plan, "source44")
    monkeypatch.setattr(launch, "ssh", capture)
    launch.remote_launch_preflight(plan, {"manifest_sha256": "a" * 64,
                                          "plan_sha256": local["plan_sha256"]})
    assert len(captured) == 3
    assert "shutil.copytree(parent,code)" in captured[1]
    assert "run_exp238_peak_cache.py" in captured[1]


def test_launch_contract_includes_hashes_and_fair_a100_request():
    plan, local = stage.local_preflight("source6")
    config = launch.launch_config(plan, "a" * 64, local["plan_sha256"])
    assert config["script"] == "run_exp238_peak_cache.py"
    assert config["arguments"][-2:] == ["--manifest-sha256", "a" * 64]
    assert config["cpu_affinity"] == "0-7" and config["max_seconds"] == 7200
    text = (SCRIPTS / "launch_exp238_peak_cache.py").read_text()
    assert "WAITING" in text and "queue_request" in text and "nvidia-smi" in text


def test_failed_prelaunch_releases_only_when_run_confirmed_absent(monkeypatch, tmp_path):
    plan, local = stage.local_preflight("source6")
    config = launch.launch_config(plan, "a" * 64, local["plan_sha256"])
    config.update({"gpu": "GPU-test", "alias": "nsu-a100"})
    calls = []

    def absent(alias, command, source=None):
        calls.append((alias, command))
        if alias == "nsu-a100":
            ast.parse(source)
            return {"run_exists": False}
        assert alias == "nsu-quadro" and "--verified-stopped" in command
        return {"state": "RELEASED"}

    monkeypatch.setattr(launch, "ssh", absent)
    prefix = tmp_path / "exp238_launch"
    result = launch.release_if_no_run(config, prefix)
    assert result["status"] == "RELEASED_CONFIRMED_NO_RUN_AFTER_PRELAUNCH_FAILURE"
    assert len(calls) == 2
    assert prefix.with_name(prefix.name + "_prelaunch_release.json").exists()

    def exists(alias, command, source=None):
        assert alias == "nsu-a100"
        return {"run_exists": True}

    monkeypatch.setattr(launch, "ssh", exists)
    result = launch.release_if_no_run(config, tmp_path / "other_launch")
    assert result["status"] == "STOPPED_AMBIGUOUS_RUN_EXISTS_RETAIN_LEASE"
    assert not (tmp_path / "other_launch_prelaunch_release.json").exists()


def test_uncertain_prelaunch_probe_never_releases(monkeypatch, tmp_path):
    plan, local = stage.local_preflight("source44")
    config = launch.launch_config(plan, "a" * 64, local["plan_sha256"])
    config.update({"gpu": "GPU-test", "alias": "nsu-a100"})
    aliases = []

    def fail_probe(alias, command, source=None):
        aliases.append(alias)
        raise TimeoutError("SSH observation unavailable")

    monkeypatch.setattr(launch, "ssh", fail_probe)
    with pytest.raises(TimeoutError):
        launch.release_if_no_run(config, tmp_path / "uncertain")
    assert aliases == ["nsu-a100"]
    assert not list(tmp_path.glob("*release*"))
