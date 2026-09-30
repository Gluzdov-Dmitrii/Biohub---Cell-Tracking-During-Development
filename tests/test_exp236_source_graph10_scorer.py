"""Synthetic no-label gates for the epoch-10 source6bba scorer."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_exp236_source_graph10_scorer as prepare
import launch_exp236_source_graph10_scorer as launch
import verify_exp236_source_graph10_scorer as verify
import score_exp236_source_graph10 as score
from score_exp236_source_graph10 import EXPECTED_MOVIES, gate


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path, monkeypatch):
    code, run = tmp_path / "inference_code", tmp_path / "inference_run"
    output = run / "output"
    code.mkdir()
    output.mkdir(parents=True)
    train_run = tmp_path / "training_run"
    checkpoint = train_run / "output/fold0/last.pt"
    checkpoint_sha = put(checkpoint, "sealed weights")
    source = {"train": [{"dataset_id": f"6bba_train{i:03d}"} for i in range(115)],
              "inner_validation": [{"dataset_id": name} for name in EXPECTED_MOVIES]}
    source_sha = put(code / "source6bba_manifest.json", source)
    duplicate_sha = put(code / "horaz/src/src/exp236_source_duplicate_pairs.json", "sealed map")
    history_sha = put(train_run / "output/fold0/history.json", [{"epoch": i} for i in range(1, 11)])
    result_sha = put(train_run / "output/result.json",
                     {"status": "PASS_EXP236_SOURCE_BLOCK_10_OF_50",
                      "completed_epochs": 10, "target_data_opened": False,
                      "source_duplicate_map_sha256": duplicate_sha})
    monkeypatch.setattr(score, "SOURCE_MANIFEST_SHA", source_sha)
    monkeypatch.setattr(score, "SOURCE_DUPLICATE_MAP_SHA", duplicate_sha)
    monkeypatch.setattr(score, "TRAIN_RUN", str(train_run))
    data_dir = tmp_path / "data/exp213_source_view_20260912"
    movies = [{"dataset": name, "zarr": str(data_dir / (name + ".zarr")),
               "shape": [2, 1, 1, 1]} for name in EXPECTED_MOVIES]
    plan = {"experiment": "EXP236_SOURCE_GRAPH10", "source_embryo": "6bba",
            "target_embryo": "44b6", "fold": 0, "checkpoint_epoch": 10,
            "source_manifest_sha256": source_sha, "checkpoint": str(checkpoint),
            "source_bundle_sha256": score.SOURCE_BUNDLE_SHA,
            "source_duplicate_map_sha256": duplicate_sha,
            "source_duplicate_policy": "exclude_all_effective_duplicate_windows_v2",
            "excluded_pairs_by_split": {"train": 824, "inner_validation": 103},
            "removed_sampled_windows_by_split": {"train": 809, "inner_validation": 101},
            "training_run": str(train_run),
            "training_result_sha256": result_sha,
            "training_history_sha256": history_sha,
            "checkpoint_sha256": checkpoint_sha, "code": str(code),
            "output": str(output), "movies": movies}
    plan_sha = put(code / "plan.json", plan)
    manifest_sha = put(code / "code_manifest.json",
                       {"plan.json": plan_sha, "source6bba_manifest.json": source_sha,
                        "horaz/src/src/exp236_source_duplicate_pairs.json": duplicate_sha})
    exit_record = {"returncode": 0, "hard_timeout": False}
    exit_sha = put(run / "exit.json", exit_record)
    put(run / "supervision/complete.json",
        {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record})
    put(run / "supervision/control.json",
        {"action": "release", "queue": {"state": "RELEASED", "run_path": str(run)}})
    records, hashes = [], []
    for name in EXPECTED_MOVIES:
        csv_path = output / ("graph__" + name + ".csv")
        csv_sha = put(csv_path,
            "id,dataset,row_type,node_id,t,z,y,x,source_id,target_id\n"
            f"0,{name},node,1,0,0,0,0,-1,-1\n"
            f"1,{name},node,2,1,0,0,0,-1,-1\n"
            f"2,{name},edge,-1,-1,-1,-1,-1,1,2\n")
        record = {"dataset": name, "shape": [2, 1, 1, 1], "nodes": 2, "edges": 1,
                  "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
                  "csv": str(csv_path), "csv_sha256": csv_sha}
        receipt_sha = put(csv_path.with_suffix(".json"), record)
        records.append(record)
        hashes.append({"dataset": name, "csv_sha256": csv_sha,
                       "receipt_sha256": receipt_sha})
    status_sha = put(output / "status.json",
        {"status": "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS", "source_embryo": "6bba",
         "source_labels_read": False, "target_labels_read": False,
         "target_data_opened": False,
         "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
         "movies": list(EXPECTED_MOVIES), "records": records})
    config = {"inference_code": str(code), "inference_manifest_sha256": manifest_sha,
              "plan_sha256": plan_sha, "checkpoint_sha256": checkpoint_sha,
              "inference_run": str(run), "inference_exit_sha256": exit_sha,
              "inference_status_sha256": status_sha, "inference_graph_hashes": hashes,
              "data_dir": str(data_dir)}
    return config, source_sha, duplicate_sha, str(train_run)


def test_all_eleven_sealed_graphs_pass_before_labels(tmp_path, monkeypatch):
    config, _, _, _ = fixture(tmp_path, monkeypatch)
    plan, graphs, receipt = gate(config)
    assert [row["dataset"] for row in plan["movies"]] == list(EXPECTED_MOVIES)
    assert list(graphs) == list(EXPECTED_MOVIES)
    assert receipt["hashes"] == config["inference_graph_hashes"]


def test_source_only_guard_rejects_target_and_other_label_roots(tmp_path):
    guard = score.source_only_guard(tmp_path)
    guard("open", (tmp_path / (EXPECTED_MOVIES[0] + ".geff") / "nodes.json",))
    for path in (tmp_path / "44b6_forbidden.geff" / "nodes.json",
                 tmp_path / "6bba_other.geff" / "nodes.json",
                 tmp_path / "6bba_other.zarr" / "0/zarr.json"):
        with pytest.raises(PermissionError):
            guard("open", (path,))


@pytest.mark.parametrize("change", (
    "source_labels", "target_labels", "target_data", "release", "csv", "receipt",
    "duplicate_map", "checkpoint", "training_result", "wrong_movie",
))
def test_incomplete_or_changed_inference_blocks_labels(tmp_path, monkeypatch, change):
    config, _, _, _ = fixture(tmp_path, monkeypatch)
    run = Path(config["inference_run"])
    if change in ("source_labels", "target_labels", "target_data"):
        path = run / "output/status.json"
        status = json.loads(path.read_text())
        field = {"source_labels": "source_labels_read", "target_labels": "target_labels_read",
                 "target_data": "target_data_opened"}[change]
        status[field] = True
        put(path, status)
        config["inference_status_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif change == "release":
        path = run / "supervision/control.json"
        control = json.loads(path.read_text())
        control["queue"]["state"] = "RUNNING"
        put(path, control)
    elif change == "csv":
        csv_path = run / "output" / ("graph__" + EXPECTED_MOVIES[0] + ".csv")
        put(csv_path, csv_path.read_text().replace(",1,0,0,0,-1,-1", ",1,0,0,1,-1,-1"))
    elif change == "receipt":
        path = run / "output" / ("graph__" + EXPECTED_MOVIES[0] + ".json")
        receipt = json.loads(path.read_text())
        receipt["nodes"] = 3
        put(path, receipt)
    elif change == "duplicate_map":
        put(Path(config["inference_code"]) / "horaz/src/src/exp236_source_duplicate_pairs.json",
            "changed map")
    elif change == "checkpoint":
        put(Path(config["inference_code"]).parent / "training_run/output/fold0/last.pt",
            "changed checkpoint")
    elif change == "training_result":
        put(Path(config["inference_code"]).parent / "training_run/output/result.json",
            {"status": "PASS_EXP236_SOURCE_BLOCK_10_OF_50",
             "completed_epochs": 10, "target_data_opened": True,
             "source_duplicate_map_sha256": config["checkpoint_sha256"]})
    else:
        status_path = run / "output/status.json"
        status = json.loads(status_path.read_text())
        status["movies"][0] = "44b6_forbidden"
        put(status_path, status)
        config["inference_status_sha256"] = hashlib.sha256(status_path.read_bytes()).hexdigest()
    with pytest.raises(AssertionError):
        gate(config)


@pytest.mark.parametrize("change", (
    "complete", "csv", "release", "source_labels", "target_data", "duplicate_map",
))
def test_prepare_preflight_validates_graphs_without_staging(tmp_path, monkeypatch, change):
    config, source_sha, duplicate_sha, train_run = fixture(tmp_path, monkeypatch)
    inference_run = Path(config["inference_run"])
    if change == "csv":
        csv_path = inference_run / "output" / ("graph__" + EXPECTED_MOVIES[0] + ".csv")
        put(csv_path, csv_path.read_text() + f"3,{EXPECTED_MOVIES[0]},edge,-1,-1,-1,-1,-1,1,2\n")
    elif change == "release":
        control_path = inference_run / "supervision/control.json"
        control = json.loads(control_path.read_text())
        control["queue"]["state"] = "RUNNING"
        put(control_path, control)
    elif change == "source_labels":
        status_path = inference_run / "output/status.json"
        status = json.loads(status_path.read_text())
        status["source_labels_read"] = True
        put(status_path, status)
    elif change == "target_data":
        status_path = inference_run / "output/status.json"
        status = json.loads(status_path.read_text())
        status["target_data_opened"] = True
        put(status_path, status)
    elif change == "duplicate_map":
        put(Path(config["inference_code"]) / "horaz/src/src/exp236_source_duplicate_pairs.json",
            "changed map")
    reports = tmp_path / "reports"
    reports.mkdir()
    prepared = {"status": "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS",
                "target_labels_read": False, "source_labels_read": False,
                "target_data_opened": False,
                "movies": 11,
                "stage": {"manifest_sha256": config["inference_manifest_sha256"],
                          "plan_sha256": config["plan_sha256"],
                          "status": "STAGED_EXP236_SOURCE_GRAPH10_V2",
                          "code": config["inference_code"],
                          "duplicate_map_sha256": duplicate_sha},
                "preflight": {"checkpoint_sha256": config["checkpoint_sha256"]}}
    put(reports / "exp236_source_graph10_v2_prepare_20260927.json", prepared)
    plan_text = (Path(config["inference_code"]) / "plan.json").read_text()
    put(reports / "exp236_source_graph10_v2_plan_20260927.json", plan_text)
    lease_id = "exp236-source-graph10-v2-20260927"
    put(reports / "exp236_source_graph10_v2_config_20260927.json",
        {"experiment": "EXP236", "lease_id": lease_id,
         "script": "run_exp236_source_graph10_v2.py",
         "code": config["inference_code"], "run": config["inference_run"],
         "arguments": [config["inference_code"] + "/plan.json", "--plan-sha256",
                       config["plan_sha256"]]})
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "REMOTE", str(tmp_path))
    monkeypatch.setattr(prepare, "INFERENCE_CODE", config["inference_code"])
    monkeypatch.setattr(prepare, "INFERENCE_RUN", config["inference_run"])
    monkeypatch.setattr(prepare, "CODE", str(tmp_path / "unused_scorer_code"))
    monkeypatch.setattr(prepare, "RUN", str(tmp_path / "unused_scorer_run"))
    monkeypatch.setattr(prepare, "SOURCE_MANIFEST_SHA", source_sha)
    monkeypatch.setattr(prepare, "SOURCE_DUPLICATE_MAP_SHA", duplicate_sha)
    monkeypatch.setattr(prepare, "SOURCE_BUNDLE_SHA", score.SOURCE_BUNDLE_SHA)
    monkeypatch.setattr(prepare, "TRAIN_RUN", train_run)
    workspace = Path(__file__).resolve().parents[1]
    for name in ("score_exp236_source_graph10.py", "score_exp214_paired.py",
                 "score_exp223_official.py"):
        put(tmp_path / "scripts" / name, (workspace / "scripts" / name).read_text())
    pin_name = "exp223_official_score_config_v2_20260922.json"
    put(reports / pin_name, (workspace / "reports" / pin_name).read_text())

    class StopBeforeStage(Exception):
        pass

    seen = {}
    def fake_ssh(_host, _command, source=None):
        if source is None:
            return {"requests": [{"id": lease_id, "state": "RELEASED",
                                  "run_path": config["inference_run"]}]}
        if _host == "nsu-quadro":
            ast.parse(source)
            seen["stage_compiled"] = True
            raise StopBeforeStage
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exec(compile(source, "<generated scorer preflight>", "exec"), {})
        seen.update(json.loads(buffer.getvalue().strip()))
        return seen

    monkeypatch.setattr(prepare, "ssh", fake_ssh)
    if change == "complete":
        with pytest.raises(StopBeforeStage):
            prepare.main()
        assert seen["status"] == "PASS_EXP236_SOURCE10_SCORER_PREFLIGHT"
        assert seen["hashes"] == config["inference_graph_hashes"]
        assert seen["stage_compiled"] is True
    else:
        with pytest.raises(AssertionError):
            prepare.main()
        assert "stage_compiled" not in seen


def test_launch_and_readback_templates_compile_without_remote_calls(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    code, run = "/remote/scorer_code", "/remote/scorer_run"
    put(reports / "exp236_source_graph10_v2_prepare_20260927.json", {"status": "inference prepared"})
    prepared = {"status": "PREPARED_EXP236_SOURCE10_OFFICIAL_SCORER_NO_LABELS",
                "source_labels_read": False, "target_labels_read": False,
                "target_data_opened": False,
                "inference_prepare_sha256": hashlib.sha256(
                    (reports / "exp236_source_graph10_v2_prepare_20260927.json").read_bytes()).hexdigest(),
                "stage": {"code": code, "manifest_sha256": "a" * 64,
                          "score_config_sha256": "b" * 64},
                "config": {"experiment": "EXP236_SOURCE_GRAPH10_OFFICIAL",
                           "source_manifest_sha256": "c" * 64,
                           "source_duplicate_map_sha256": "d" * 64,
                           "output": run + "/output"}}
    put(reports / "exp236_source_graph10_scorer_prepare_20260927.json", prepared)
    put(reports / "exp236_source_graph10_scorer_launch_20260927.json",
        {"status": "EXP236_SOURCE10_OFFICIAL_SCORER_LAUNCHED",
         "run": run, "score_config_sha256": "b" * 64})

    class StopBeforeRemote(Exception):
        pass

    def capture(_host, _command, source):
        ast.parse(source)
        raise StopBeforeRemote

    monkeypatch.setattr(launch, "ROOT", tmp_path)
    monkeypatch.setattr(launch, "CODE", code)
    monkeypatch.setattr(launch, "RUN", run)
    monkeypatch.setattr(launch, "ssh", capture)
    # Launch requires its local receipt absent, so inspect before installing it.
    (reports / "exp236_source_graph10_scorer_launch_20260927.json").unlink()
    with pytest.raises(StopBeforeRemote):
        launch.main()
    put(reports / "exp236_source_graph10_scorer_launch_20260927.json",
        {"status": "EXP236_SOURCE10_OFFICIAL_SCORER_LAUNCHED",
         "run": run, "score_config_sha256": "b" * 64})
    monkeypatch.setattr(verify, "PREPARE", reports / "exp236_source_graph10_scorer_prepare_20260927.json")
    monkeypatch.setattr(verify, "LAUNCH", reports / "exp236_source_graph10_scorer_launch_20260927.json")
    monkeypatch.setattr(verify, "RECEIPT", reports / "exp236_source_graph10_score_20260927.json")
    monkeypatch.setattr(verify, "ssh", capture)
    with pytest.raises(StopBeforeRemote):
        verify.main()
