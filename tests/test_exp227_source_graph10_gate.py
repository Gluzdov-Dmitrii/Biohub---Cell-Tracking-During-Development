"""Source labels stay closed until all eight EXP227 graphs and release gates pass."""
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from score_exp227_source_graph10 import gate


def write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, data):
    return write(path, json.dumps(data) + "\n")


def fixture(tmp_path):
    code, run = tmp_path / "code", tmp_path / "run"
    code.mkdir()
    output = run / "output"
    output.mkdir(parents=True)
    checkpoint = tmp_path / "epoch_010.pt"
    checkpoint_sha = write(checkpoint, "fixed checkpoint")
    names = [f"44b6_{i:08d}" for i in range(8)]
    movies = [{"dataset": name, "shape": [2, 1, 1, 1]} for name in names]
    plan = {"experiment": "EXP227_SOURCE_GRAPH10", "source_embryo": "44b6",
            "checkpoint_epoch": 10, "checkpoint": str(checkpoint),
            "checkpoint_sha256": checkpoint_sha, "output": str(output), "movies": movies}
    plan_sha = put(code / "plan.json", plan)
    manifest_sha = put(code / "code_manifest.json", {"plan.json": plan_sha})
    exit_record = {"returncode": 0, "hard_timeout": False}
    exit_sha = put(run / "exit.json", exit_record)
    put(run / "supervision/complete.json",
        {"status": "RELEASED_AFTER_VERIFIED_EXIT", "exit": exit_record})
    put(run / "supervision/control.json",
        {"action": "release", "queue": {"state": "RELEASED", "run_path": str(run)}})
    records = []
    for name in names:
        csv_path = output / ("graph__" + name + ".csv")
        csv_sha = write(csv_path,
            "id,dataset,row_type,node_id,t,z,y,x,source_id,target_id\n"
            f"0,{name},node,1,0,0,0,0,-1,-1\n"
            f"1,{name},node,2,1,0,0,0,-1,-1\n"
            f"2,{name},edge,-1,-1,-1,-1,-1,1,2\n")
        record = {"dataset": name, "shape": [2, 1, 1, 1],
                  "checkpoint_sha256": checkpoint_sha, "plan_sha256": plan_sha,
                  "csv": str(csv_path), "csv_sha256": csv_sha}
        put(csv_path.with_suffix(".json"), record)
        records.append(record)
    status_sha = put(output / "status.json",
        {"status": "PASS_EXP227_SOURCE_GRAPH10_NO_LABELS",
         "target_labels_read": False, "checkpoint_sha256": checkpoint_sha,
         "plan_sha256": plan_sha, "movies": names, "records": records})
    return {"inference_code": str(code), "inference_manifest_sha256": manifest_sha,
            "plan_sha256": plan_sha, "checkpoint_sha256": checkpoint_sha,
            "inference_run": str(run), "inference_exit_sha256": exit_sha,
            "inference_status_sha256": status_sha}


def test_complete_graphs_and_release_pass(tmp_path):
    config = fixture(tmp_path)
    plan, graphs, receipt = gate(config)
    assert len(plan["movies"]) == len(graphs) == 8
    assert receipt["status"] == "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"


@pytest.mark.parametrize("change", ("running_lease", "missing_receipt", "extra_output"))
def test_incomplete_or_changed_outputs_block_labels(tmp_path, change):
    config = fixture(tmp_path)
    run = Path(config["inference_run"])
    if change == "running_lease":
        path = run / "supervision/control.json"
        state = json.loads(path.read_text())
        state["queue"]["state"] = "RUNNING"
        put(path, state)
    elif change == "missing_receipt":
        (run / "output/graph__44b6_00000000.json").unlink()
    else:
        write(run / "output/extra.csv", "unexpected")
    with pytest.raises((AssertionError, FileNotFoundError)):
        gate(config)
