"""Local-only gates for EXP236 block01 v2 duplicate-window exclusion."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import exp236_duplicate_frame_safeguard as safeguard  # noqa: E402
import launch_exp236_source_block01_v2 as launch  # noqa: E402
import prepare_exp236_source_block01_v2 as prepare  # noqa: E402
from run_exp236_source_block01_v2 import validate  # noqa: E402


def sha(body):
    return hashlib.sha256(body).hexdigest()


def source_cohort():
    manifest = json.loads(
        (ROOT / "work/exp236_source6bba_20260927/source6bba_manifest.json").read_text()
    )
    return manifest, {
        "status": "PASS_EXP236_SOURCE6BBA_V2_PREFLIGHT",
        "bundle_sha256": manifest["source_bundle_sha256"],
        "training_plan_sha256": manifest["training_plan_sha256"],
        "train": [row["dataset_id"] for row in manifest["train"]],
        "inner_validation": [row["dataset_id"] for row in manifest["inner_validation"]],
    }


def parent_failure():
    return {
        "code_manifest_sha256": prepare.V1_CODE_MANIFEST_SHA256,
        "plan_sha256": prepare.V1_PLAN_SHA256,
        "result": {
            "status": "FAILED_EXP236_SOURCE_BLOCK01",
            "error": prepare.V1_ERROR,
            "plan_sha256": prepare.V1_PLAN_SHA256,
            "target_data_opened": False,
        },
        "exit": {"returncode": 1, "hard_timeout": False},
        "supervision": {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit_matches": True},
        "control": {"action": "release", "queue_state": "RELEASED",
                    "queue_id": prepare.V1_LEASE_ID, "queue_run_path": prepare.V1_RUN},
    }


def parent_queue():
    return {"requests": [{"id": prepare.V1_LEASE_ID,
                           "state": "RELEASED", "run_path": prepare.V1_RUN}]}


def test_full_source_audits_are_pinned_and_record_all_removed_windows():
    audits = prepare.verify_source_audits()
    assert audits["movies_scanned"] == 126
    assert audits["effective_duplicate_pairs"] == audits["raw_duplicate_pairs"] == 927
    assert audits["inconsistent_sampled_pairs"] == 43
    assert audits["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert audits["removed_sampled_windows_by_split"] == {"train": 809,
                                                           "inner_validation": 101}
    assert {39, 82, 87, 95} <= set(audits["duplicate_starts"]["6bba_7f87b3d8"])


def test_window_filter_excludes_crossing_pairs_and_keeps_other_windows():
    starts = frozenset({1, 3})
    assert safeguard.window_crosses_duplicate(1, 2, starts)
    assert safeguard.window_crosses_duplicate(0, 3, starts)
    assert not safeguard.window_crosses_duplicate(0, 2, starts)
    assert not safeguard.window_crosses_duplicate(2, 2, starts)


def test_loader_view_scan_matches_pinned_pair_map_and_fails_closed(tmp_path, monkeypatch):
    frames = np.zeros((4, 2, 4, 4), dtype=np.uint16)
    frames[1] = 1
    frames[2] = 1
    frames[3] = 2
    pair_map = tmp_path / safeguard.PAIR_MAP_NAME
    document = {"source_embryo": "6bba", "loader_view": "float32_zarr_downsample_1_4_4",
                "window_size": 2, "source_dataset_ids": ["6bba_test"],
                "duplicate_starts": {"6bba_test": [1]}}
    pair_map.write_text(json.dumps(document))
    monkeypatch.setattr(safeguard, "__file__", str(tmp_path / "exp236_duplicate_frame_safeguard.py"))
    monkeypatch.setattr(safeguard, "zarr", SimpleNamespace(open=lambda *_args, **_kwargs: {"0": frames}))
    assert safeguard.source_duplicate_starts("6bba_test", "unused.zarr", 4,
                                             (1, 4, 4)) == frozenset({1})
    document["duplicate_starts"]["6bba_test"] = [2]
    pair_map.write_text(json.dumps(document))
    with pytest.raises(AssertionError, match="pair map mismatch"):
        safeguard.source_duplicate_starts("6bba_test", "unused.zarr", 4, (1, 4, 4))
    with pytest.raises(AssertionError):
        safeguard.source_duplicate_starts("44b6_test", "unused.zarr", 4, (1, 4, 4))


def test_patched_horaz_loader_filters_windows_and_retains_runtime_assert(tmp_path, monkeypatch):
    original = (ROOT / "outputs/research/exp223_horaz0_package_20260921/selected/src/src/datasets.py").read_bytes()
    patched = safeguard.patch_horaz_datasets(original)
    path = tmp_path / "datasets.py"
    path.write_bytes(patched)
    sys.path.insert(0, str(ROOT / "outputs/research/exp223_horaz0_package_20260921/selected/src/src"))
    spec = importlib.util.spec_from_file_location("exp236_v2_datasets_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    frames = np.zeros((4, 2, 4, 4), dtype=np.uint16)
    frames[1] = 1
    frames[2] = 1
    frames[3] = 2
    monkeypatch.setattr(module, "read_zarr_metadata", lambda _path: ((4, 2, 4, 4), 0.0, 2.0))
    coords = np.zeros((4, 3), dtype=np.float32)
    coords[2, 0] = 1.0  # The repeated t1/t2 images have divergent source labels.
    graph = module.TrainingGraph(
        node_ids=np.arange(4, dtype=np.int64),
        times=np.arange(4, dtype=np.int16),
        coords=coords,
        edges=np.array([[0, 1], [1, 2], [2, 3]], dtype=np.int64),
    )
    monkeypatch.setattr(module, "read_training_graph", lambda _path: graph)
    monkeypatch.setattr(module, "source_duplicate_starts", lambda *_args: frozenset({1}))
    monkeypatch.setattr(module, "zarr", SimpleNamespace(open=lambda *_args, **_kwargs: {"0": frames}))
    record = {"dataset_id": "6bba_test", "zarr_path": "unused.zarr", "geff_path": "unused.geff"}
    metadata, windows = module.load_video_windows(record, 2, (1, 4, 4), None)
    assert [window.time_start for window in windows] == [0, 2]
    dataset = module.FrameWindowDataset([(metadata, windows)], max_nodes=1, augment=False)
    assert len(dataset) == 2
    dataset[0]
    dataset[1]
    with pytest.raises(AssertionError, match="Consecutive duplicate frames"):
        module.assert_no_consecutive_duplicate_frames(torch.ones((2, 2, 1, 1)),
                                                      "6bba_test", 1)


def test_v2_payload_keeps_cohort_recipe_and_pins_code_plan_and_pair_map():
    old_manifest, source = source_cohort()
    audits = prepare.verify_source_audits()
    manifest_body, plan_body, files = prepare.build_payload(source, audits)
    plan = json.loads(plan_body)
    pair_map = json.loads(files["horaz/src/src/exp236_source_duplicate_pairs.json"])
    hashes = json.loads(files["code_manifest.json"])
    assert json.loads(manifest_body) == old_manifest
    assert plan["train"] == old_manifest["train"]
    assert plan["inner_validation"] == old_manifest["inner_validation"]
    assert plan["fold"] == 0 and plan["block_end_epoch"] == 3
    assert plan["planned_epochs"] == 50 and plan["resume"] is False
    assert plan["source_duplicate_policy"] == "exclude_all_effective_duplicate_windows_v2"
    assert plan["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert plan["removed_sampled_windows_by_split"] == {"train": 809,
                                                         "inner_validation": 101}
    assert pair_map["duplicate_starts"] == audits["duplicate_starts"]
    assert plan["source_duplicate_map_sha256"] == sha(
        files["horaz/src/src/exp236_source_duplicate_pairs.json"])
    validate(plan)
    assert sha(manifest_body) == prepare.SOURCE_MANIFEST_SHA256
    assert sha(plan_body) == prepare.PLAN_SHA256
    assert sha(files["code_manifest.json"]) == prepare.CODE_MANIFEST_SHA256
    assert hashes == {name: sha(body) for name, body in sorted(files.items())
                      if name != "code_manifest.json"}
    assert b"seed=3406" in files["run_exp236_source_block01_v2.py"]
    assert b"cfg.epochs = 3" in files["run_exp236_source_block01_v2.py"]
    patched = files["horaz/src/src/datasets.py"]
    assert b"window_crosses_duplicate" in patched
    assert b"assert_no_consecutive_duplicate_frames(images, metadata.dataset_id, time_start)" in patched
    assert "run_exp236_source_block01_v2.py" in files["exp227_job.py"].decode()
    for name, body in files.items():
        if name.endswith(".py"):
            ast.parse(body.decode(), filename=name)


def test_v1_failure_and_released_queue_gate_rejects_changed_evidence():
    parent, queue = parent_failure(), parent_queue()
    assert prepare.validate_parent_failure(parent, queue)["status"] == "PASS_EXP236_V1_FAILED_AND_RELEASED"
    parent["result"]["error"] = "different failure"
    with pytest.raises(AssertionError):
        prepare.validate_parent_failure(parent, queue)
    parent["result"]["error"] = prepare.V1_ERROR
    queue["requests"][0]["state"] = "RUNNING"
    with pytest.raises(AssertionError):
        prepare.validate_parent_failure(parent, queue)


def test_prepare_generated_remote_scripts_are_parseable_without_staging(tmp_path, monkeypatch):
    _, source = source_cohort()
    audits = prepare.verify_source_audits()
    manifest_body, plan_body, files = prepare.build_payload(source, audits)
    monkeypatch.setattr(prepare, "WORK", tmp_path / "work")
    monkeypatch.setattr(prepare, "PREPARE_RECEIPT", tmp_path / "prepare.json")
    monkeypatch.setattr(prepare, "CONFIG_RECEIPT", tmp_path / "config.json")
    calls = []

    def fake_ssh(host, command, script=None):
        calls.append((host, command))
        if script is not None:
            ast.parse(script)
        if len(calls) == 1:
            return parent_failure()
        if len(calls) == 2:
            return parent_queue()
        if len(calls) == 3:
            return source
        if len(calls) == 4:
            return {"status": "STAGED_EXP236_SOURCE6BBA_BLOCK01_V2",
                    "code": prepare.CODE,
                    "manifest_sha256": sha(files["code_manifest.json"]),
                    "plan_sha256": sha(plan_body),
                    "source_manifest_sha256": sha(manifest_body)}
        raise AssertionError("Unexpected remote call")

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    prepare.main()
    assert len(calls) == 4
    config = json.loads(prepare.CONFIG_RECEIPT.read_text())
    receipt = json.loads(prepare.PREPARE_RECEIPT.read_text())
    assert config["script"] == "run_exp236_source_block01_v2.py"
    assert receipt["parent_failure"]["error"] == prepare.V1_ERROR
    assert receipt["source_duplicate_audits"]["effective_duplicate_pairs"] == 927
    assert (prepare.WORK / "plan.json").read_bytes() == plan_body


def test_launcher_releases_lease_after_rejected_prelaunch(tmp_path, monkeypatch):
    config_path = tmp_path / "exp236_source_block01_v2_config_20260927.json"
    prepare_path = tmp_path / "exp236_source_block01_v2_prepare_20260927.json"
    config = {"experiment": "EXP236",
              "lease_id": "exp236-horaz-source6bba-block01-v2-20260927",
              "token": "exp236_horaz_source6bba_block01_v2_20260927",
              "code": prepare.CODE, "run": prepare.RUN, "max_seconds": 10800,
              "cpu_affinity": "0-7", "script": "run_exp236_source_block01_v2.py",
              "arguments": [prepare.CODE + "/plan.json", "--plan-sha256", "abc"]}
    audit_summary = {key: value for key, value in prepare.verify_source_audits().items()
                     if key != "duplicate_starts"}
    prepared = {"status": "PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS",
                "source_duplicate_policy": "exclude_all_effective_duplicate_windows_v2",
                "source_duplicate_audits": audit_summary,
                "parent_failure": prepare.validate_parent_failure(parent_failure(), parent_queue()),
                "target_data_opened": False,
                "stage": {"status": "STAGED_EXP236_SOURCE6BBA_BLOCK01_V2",
                          "code": prepare.CODE, "plan_sha256": "abc", "manifest_sha256": "def"}}
    config_path.write_text(json.dumps(config))
    prepare_path.write_text(json.dumps(prepared))
    monkeypatch.setattr(launch, "CONFIG", config_path)
    monkeypatch.setattr(launch, "PREPARE", prepare_path)
    calls = []

    def fake_ssh(host, command, source=None):
        calls.append((host, command))
        if host == "nsu-quadro" and " status" in command:
            return parent_queue()
        if host == "nsu-a100" and command == "python3 -":
            if "nvidia-smi" in source:
                ast.parse(source)
                raise RuntimeError("GPU occupied before run directory creation")
            return {"run_exists": False}
        if host == "nsu-quadro" and " release" in command:
            return {"state": "RELEASED"}
        raise AssertionError((host, command))

    monkeypatch.setattr(launch, "ssh", fake_ssh)
    monkeypatch.setattr(
        launch, "queue_request",
        lambda _args, _lease_id, _token: {
            "state": "RESERVED", "gpus": ["GPU-occupied"], "alias": "nsu-a100"},
    )
    with pytest.raises(RuntimeError, match="GPU occupied"):
        launch.main()
    released = json.loads(config_path.with_name(config_path.stem + "_prelaunch_release.json").read_text())
    assert released["status"] == "RELEASED_AFTER_REJECTED_PRELAUNCH"
    assert released["queue"]["state"] == "RELEASED"
    assert any(host == "nsu-quadro" and " release" in command for host, command in calls)
    assert not config_path.with_name(config_path.stem + "_partial_launch.json").exists()


def test_launcher_blocks_mismatched_audit_before_remote_queue(tmp_path, monkeypatch):
    prepare_path = tmp_path / "prepare.json"
    prepare_path.write_text(json.dumps({
        "status": "PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS",
        "target_data_opened": False,
        "source_duplicate_policy": "exclude_all_effective_duplicate_windows_v2",
        "stage": {"status": "STAGED_EXP236_SOURCE6BBA_BLOCK01_V2"},
        "source_duplicate_audits": {"effective_sha256": "wrong"},
    }))
    monkeypatch.setattr(launch, "PREPARE", prepare_path)
    monkeypatch.setattr(launch, "ssh", lambda *_args, **_kwargs: pytest.fail("remote call before audit gate"))
    with pytest.raises(AssertionError):
        launch.main()
