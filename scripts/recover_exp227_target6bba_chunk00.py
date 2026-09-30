"""Audit the stopped EXP227 chunk00 and prepare a separate resume receipt.

The default invocation is read-only. --write-receipt creates a new local
coordinator receipt after the same fresh remote checks. Neither mode starts a
run, claims a GPU, reads target labels, or scores target graphs. The original
STOPPED_NEEDS_RECONCILIATION receipt is never edited.
"""
import argparse
import copy
import json
from pathlib import Path
import time

import coordinate_exp227_target6bba as coord
from launch_exp227_target_chunk import launch_paths
from monitor_exp213_job import probe, releasable
from prepare_exp227_target_chunk0_local import paths
from stage_exp227_target_chunk import stage_paths
from verify_exp227_target_chunk0 import live_release


SOURCE = coord.RECEIPT
RECOVERED = coord.ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"


def stopped_state(source=SOURCE):
    source = Path(source)
    coord.require(not source.with_name(source.name + ".lock").exists(),
                  "Original coordinator lock exists")
    source_sha = coord.sha(source)
    state = coord._read_state(source)
    coord.require(state["status"] == "STOPPED_NEEDS_RECONCILIATION" and
                  state.get("error") == {"type": "ValueError", "message": "Bad queue control release"},
                  "Unexpected stop reason")
    coord.require(state["frozen"] == coord.frozen_inputs(), "Frozen source/assignment changed")
    coord.require(len(state["chunks"]) == 8 and all(not chunk for chunk in state["chunks"][1:]),
                  "Later chunk was touched")
    chunk = state["chunks"][0]
    coord.require(set(chunk) == {"prepare", "stage", "fair_prelaunch", "launch"},
                  "Unexpected chunk00 phase")
    for phase in ("prepare", "stage", "launch"):
        coord.require(chunk[phase].get("validated") is True and "result" in chunk[phase],
                      "Unvalidated chunk00 " + phase)
    prepared = chunk["prepare"]["result"]
    stage = chunk["stage"]["result"]
    launch = chunk["launch"]["result"]
    coord._validate_prepare(prepared, 0, state["frozen"])
    coord._validate_stage(stage, 0, state["frozen"], prepared)
    coord._validate_launch(launch, 0, stage)
    for phase, path in (("prepare", paths(0)["receipt"]),
                        ("stage", stage_paths(0)["stage"]),
                        ("launch", launch_paths(0)["launch"])):
        coord.require(json.loads(path.read_text()) == chunk[phase]["result"],
                      "Local " + phase + " receipt differs from stopped coordinator")
    return state, source_sha, stage, launch


def audit(*, source=SOURCE, ops=None, process_probe=probe):
    """Fresh remote graph, process, supervisor and queue checks; no mutation."""
    state, source_sha, stage, launch = stopped_state(source)
    ops = ops or coord.DefaultOps()
    completion = ops.completion(stage["run"])
    coord.require(coord._completion_ready(completion, stage["run"]),
                  "Chunk00 supervision is not complete")
    control_row = completion["control"]["queue"]
    config = launch["config"]
    lease = launch["lease"]
    for key in ("id", "owner", "token", "project", "run_path", "pool"):
        coord.require(control_row.get(key) == lease[key], "Control changed lease " + key)
    gate = ops.postrun(stage)
    coord._validate_postrun(gate, 0, state["frozen"], stage)
    queue_state = ops.queue_status()
    row = live_release(queue_state, stage["lease_id"], stage["run"])
    for key in ("id", "owner", "token", "project", "run_path", "pool"):
        coord.require(row.get(key) == lease[key], "Live queue changed lease " + key)
    coord.require(row.get("gpus") == [] and row.get("process") == control_row.get("process"),
                  "Released lease still has GPUs or process identity changed")
    process = process_probe(config)
    coord.require(process["exit"] == completion["exit"] and releasable(process),
                  "Process identity/group or assigned GPU still active")
    coord.require(process["launch"]["pid"] == row["process"]["pid"] and
                  process["launch"]["start"] == row["process"]["start"] and
                  process["status"]["status"] == "PASS_EXP227_TARGET6BBA_CHUNK00_NO_LABELS",
                  "Live process or output status changed")
    evidence = {"source_receipt": str(source), "source_sha256": source_sha,
                "source_state_sha256": state["state_sha256"],
                "status": "PASS_EXP227_TARGET6BBA_CHUNK00_RECONCILIATION_NO_LABELS",
                "chunk_index": 0, "movie_count": len(gate["graph_hashes"]),
                "graph_hashes_sha256": coord.digest_object(gate["graph_hashes"]),
                "manifest_sha256": gate["manifest_sha256"],
                "plan_sha256": gate["plan_sha256"],
                "checkpoint_sha256": gate["checkpoint_sha256"],
                "status_sha256": gate["status_sha256"],
                "exit_sha256": gate["exit_sha256"],
                "supervision_sha256": gate["supervision_sha256"],
                "control_sha256": gate["control_sha256"],
                "queue_snapshot_sha256": coord.digest_object(queue_state),
                "queue_lease_id": row["id"], "queue_state": row["state"],
                "identity_alive": process["identity_alive"],
                "group_alive": process["group_alive"],
                "assigned_gpu_pids": process["gpu_pids"],
                "target_labels_read": False, "target_score_computed": False}
    postrun = {"validated": True, "gate": gate, "queue_row": row,
               "queue_snapshot_sha256": evidence["queue_snapshot_sha256"],
               "live_release_checked_unix": time.time()}
    return state, evidence, postrun


def write_recovered(*, source=SOURCE, recovered=RECOVERED,
                    ops=None, process_probe=probe):
    """Create only a new sealed local receipt; a later separate command resumes."""
    recovered = Path(recovered)
    coord.require(not recovered.exists() and
                  not recovered.with_name(recovered.name + ".lock").exists(),
                  "Recovery receipt or lock already exists")
    state, evidence, postrun = audit(source=source, ops=ops, process_probe=process_probe)
    coord.require(coord.sha(source) == evidence["source_sha256"],
                  "Original stopped receipt changed during audit")
    successor = copy.deepcopy(state)
    successor["status"] = "ACTIVE_NO_TARGET_LABELS"
    successor.pop("error")
    successor["chunks"][0]["postrun"] = postrun
    successor["recovery"] = evidence
    coord._save(recovered, successor, create=True)
    return {**evidence, "recovered_receipt": str(recovered),
            "recovered_receipt_sha256": coord.sha(recovered)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true",
                        help="Create a separate local receipt after all read-only gates")
    args = parser.parse_args()
    result = (write_recovered() if args.write_receipt else audit()[1])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
