"""Synthetic no-label gates for the epoch-20 source scorer."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_exp227_source_graph20_scorer as prepare
import launch_exp227_source_graph20_scorer as launch
import verify_exp227_source_graph20_scorer as verify
from score_exp227_source_graph20 import EXPECTED_MOVIES, gate


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value) + "\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    code, run = tmp_path / "inference_code", tmp_path / "inference_run"
    output = run / "output"
    code.mkdir()
    output.mkdir(parents=True)
    checkpoint = tmp_path / "epoch_020.pt"
    checkpoint_sha = put(checkpoint, "sealed weights")
    source = {"inner_validation": [{"dataset_id": name} for name in EXPECTED_MOVIES]}
    source_sha = put(code / "source44_manifest.json", source)
    data_dir = tmp_path / "data/exp213_source_view_20260912"
    movies = [{"dataset": name, "zarr": str(data_dir / (name + ".zarr")),
               "shape": [2, 1, 1, 1]} for name in EXPECTED_MOVIES]
    plan = {"experiment": "EXP227_SOURCE_GRAPH20", "source_embryo": "44b6",
            "target_embryo": "6bba", "fold": 1, "checkpoint_epoch": 20,
            "source_manifest_sha256": source_sha, "checkpoint": str(checkpoint),
            "checkpoint_sha256": checkpoint_sha, "code": str(code),
            "output": str(output), "movies": movies}
    plan_sha = put(code / "plan.json", plan)
    manifest_sha = put(code / "code_manifest.json",
                       {"plan.json": plan_sha, "source44_manifest.json": source_sha})
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
        {"status": "PASS_EXP227_SOURCE_GRAPH20_NO_LABELS", "source_embryo": "44b6",
         "source_labels_read": False, "target_labels_read": False,
         "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
         "movies": list(EXPECTED_MOVIES), "records": records})
    config = {"inference_code": str(code), "inference_manifest_sha256": manifest_sha,
              "plan_sha256": plan_sha, "checkpoint_sha256": checkpoint_sha,
              "inference_run": str(run), "inference_exit_sha256": exit_sha,
              "inference_status_sha256": status_sha, "inference_graph_hashes": hashes,
              "data_dir": str(data_dir)}
    return config, source_sha


def test_all_eight_sealed_graphs_pass_before_labels(tmp_path):
    config, _ = fixture(tmp_path)
    plan, graphs, receipt = gate(config)
    assert [row["dataset"] for row in plan["movies"]] == list(EXPECTED_MOVIES)
    assert list(graphs) == list(EXPECTED_MOVIES)
    assert receipt["hashes"] == config["inference_graph_hashes"]


@pytest.mark.parametrize("change", ("source_labels", "target_labels", "release", "csv", "receipt"))
def test_incomplete_or_changed_inference_blocks_labels(tmp_path, change):
    config, _ = fixture(tmp_path)
    run = Path(config["inference_run"])
    if change in ("source_labels", "target_labels"):
        path = run / "output/status.json"
        status = json.loads(path.read_text())
        status["source_labels_read" if change == "source_labels" else "target_labels_read"] = True
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
    else:
        path = run / "output" / ("graph__" + EXPECTED_MOVIES[0] + ".json")
        receipt = json.loads(path.read_text())
        receipt["nodes"] = 3
        put(path, receipt)
    with pytest.raises(AssertionError):
        gate(config)


@pytest.mark.parametrize("change", ("complete", "csv", "release", "source_labels"))
def test_prepare_preflight_validates_graphs_without_staging(tmp_path, monkeypatch, change):
    config, source_sha = fixture(tmp_path)
    inference_run = Path(config["inference_run"])
    if change == "csv":
        csv_path = inference_run / "output" / ("graph__" + EXPECTED_MOVIES[0] + ".csv")
        put(csv_path, csv_path.read_text() + "3,44b6_996155de,edge,-1,-1,-1,-1,-1,1,2\n")
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
    reports = tmp_path / "reports"
    reports.mkdir()
    prepared = {"status": "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS",
                "target_labels_read": False,
                "stage": {"manifest_sha256": config["inference_manifest_sha256"],
                          "plan_sha256": config["plan_sha256"]},
                "preflight": {"checkpoint_sha256": config["checkpoint_sha256"]}}
    put(reports / "exp227_source_graph20_prepare_20260927.json", prepared)
    plan_text = (Path(config["inference_code"]) / "plan.json").read_text()
    put(reports / "exp227_source_graph20_plan_20260927.json", plan_text)
    lease_id = "exp227-source-graph20-v1-20260927"
    put(reports / "exp227_source_graph20_config_20260927.json",
        {"experiment": "EXP227", "lease_id": lease_id,
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
    workspace = Path(__file__).resolve().parents[1]
    for name in ("score_exp227_source_graph20.py", "score_exp214_paired.py",
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
        assert seen["status"] == "PASS_EXP227_SOURCE20_SCORER_PREFLIGHT"
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
    put(reports / "exp227_source_graph20_prepare_20260927.json", {"status": "inference prepared"})
    prepared = {"status": "PREPARED_EXP227_SOURCE20_OFFICIAL_SCORER_NO_LABELS",
                "source_labels_read": False, "target_labels_read": False,
                "inference_prepare_sha256": hashlib.sha256(
                    (reports / "exp227_source_graph20_prepare_20260927.json").read_bytes()).hexdigest(),
                "stage": {"code": code, "manifest_sha256": "a" * 64,
                          "score_config_sha256": "b" * 64},
                "config": {"experiment": "EXP227_SOURCE_GRAPH20_OFFICIAL",
                           "output": run + "/output"}}
    put(reports / "exp227_source_graph20_scorer_prepare_20260927.json", prepared)
    put(reports / "exp227_source_graph20_scorer_launch_20260927.json",
        {"status": "EXP227_SOURCE20_OFFICIAL_SCORER_LAUNCHED",
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
    (reports / "exp227_source_graph20_scorer_launch_20260927.json").unlink()
    with pytest.raises(StopBeforeRemote):
        launch.main()
    put(reports / "exp227_source_graph20_scorer_launch_20260927.json",
        {"status": "EXP227_SOURCE20_OFFICIAL_SCORER_LAUNCHED",
         "run": run, "score_config_sha256": "b" * 64})
    monkeypatch.setattr(verify, "PREPARE", reports / "exp227_source_graph20_scorer_prepare_20260927.json")
    monkeypatch.setattr(verify, "LAUNCH", reports / "exp227_source_graph20_scorer_launch_20260927.json")
    monkeypatch.setattr(verify, "RECEIPT", reports / "exp227_source_graph20_score_20260927.json")
    monkeypatch.setattr(verify, "ssh", capture)
    with pytest.raises(StopBeforeRemote):
        verify.main()
