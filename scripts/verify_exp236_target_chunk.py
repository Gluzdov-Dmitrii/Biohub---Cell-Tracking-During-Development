"""Read-only graph, hash, process and release gate for one EXP236 target chunk.

Invoke on the shared remote filesystem only after a separate guarded launch.
It never opens GEFF labels or computes a target metric.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

from run_exp223_inference import verify_csv
from run_exp236_target_chunk import COLUMNS, image_shape, no_labels_guard, validate_plan


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def live_release(queue_state, lease_id, run):
    """Require a fresh shared-queue snapshot as well as the run's control file."""
    matches = [row for row in queue_state["requests"] if row["id"] == lease_id]
    assert len(matches) == 1 and matches[0]["state"] == "RELEASED"
    assert matches[0]["run_path"] == str(run)
    return matches[0]


def gate(code, run, manifest_sha, plan_sha):
    code = Path(code)
    run = Path(run)
    assert sha(code / "code_manifest.json") == manifest_sha
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest, name
    assert sha(code / "plan.json") == plan_sha
    plan = json.loads((code / "plan.json").read_text())
    validate_plan(plan)
    sys.addaudithook(no_labels_guard(plan["data_root"], plan["movies"]))
    assert Path(plan["code"]).resolve() == code.resolve()
    assert Path(plan["output"]).resolve() == (run / "output").resolve()
    assert sha(plan["checkpoint"]) == plan["checkpoint_sha256"]
    exit_record = json.loads((run / "exit.json").read_text())
    supervision = json.loads((run / "supervision/complete.json").read_text())
    control = json.loads((run / "supervision/control.json").read_text())
    assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
    assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert supervision["exit"] == exit_record
    assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
    assert Path(control["queue"]["run_path"]).resolve() == run.resolve()
    output = run / "output"
    expected = {"status.json"} | {"graph__" + name + suffix for name in plan["movies"]
                                  for suffix in (".csv", ".json")}
    assert {path.name for path in output.iterdir()} == expected
    status_path = output / "status.json"
    status = json.loads(status_path.read_text())
    assert status["status"] == f"PASS_EXP236_TARGET44B6_CHUNK{plan['chunk_index']:02d}_NO_LABELS"
    assert status["target_labels_read"] is False
    assert status["source_embryo"] == "6bba" and status["target_embryo"] == "44b6"
    assert status["chunk_index"] == plan["chunk_index"] and status["movies"] == plan["movies"]
    assert status["assignment_sha256"] == plan["assignment_sha256"]
    assert status["source_handoff_sha256"] == plan["source_handoff_sha256"]
    assert status["checkpoint_sha256"] == plan["checkpoint_sha256"]
    assert status["plan_sha256"] == plan_sha
    assert len(status["records"]) == len(plan["movies"]) and len(plan["movies"]) in (14, 15)
    hashes = []
    for name, record in zip(plan["movies"], status["records"]):
        csv_path = output / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        shape = image_shape(Path(plan["data_root"]) / (name + ".zarr"))
        assert record["dataset"] == name and record["shape"] == shape
        assert record["checkpoint_sha256"] == plan["checkpoint_sha256"]
        assert record["plan_sha256"] == plan_sha
        assert Path(record["csv"]).resolve() == csv_path.resolve()
        assert sha(csv_path) == record["csv_sha256"]
        assert json.loads(receipt_path.read_text()) == record
        with csv_path.open(newline="") as handle:
            assert next(csv.reader(handle)) == COLUMNS
        counts = verify_csv(csv_path, {"shape": shape, "dataset": name})
        assert counts == {"nodes": record["nodes"], "edges": record["edges"]}
        hashes.append({"dataset": name, "csv_sha256": record["csv_sha256"],
                       "receipt_sha256": sha(receipt_path)})
    return {"status": "PASS_EXP236_TARGET44B6_CHUNK_POSTRUN_NO_LABELS",
            "chunk_index": plan["chunk_index"],
            "movies": list(plan["movies"]), "graph_hashes": hashes,
            "manifest_sha256": manifest_sha, "plan_sha256": plan_sha,
            "checkpoint_sha256": plan["checkpoint_sha256"],
            "status_sha256": sha(status_path), "exit_sha256": sha(run / "exit.json"),
            "supervision_sha256": sha(run / "supervision/complete.json"),
            "control_sha256": sha(run / "supervision/control.json"),
            "queue_state_in_control": "RELEASED", "target_labels_read": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(gate(args.code, args.run, args.manifest_sha256, args.plan_sha256)))


if __name__ == "__main__":
    main()
