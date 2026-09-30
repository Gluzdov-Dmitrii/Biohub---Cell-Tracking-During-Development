"""Finite, restart-safe EXP227 source44 -> target6bba no-label rollout.

This module only coordinates separately guarded prepare, stage, launch and
read-only post-run gates. Importing it does not contact the cluster. A phase
intent is durable before each side effect; an uncertain phase is never retried.
No target GEFF label or target scorer is opened here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import time


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
PREREG = ROOT / "reports/EXP227_SOURCE44_TARGET6BBA_PREREG_20260927.md"
SELECTION = ROOT / "reports/exp227_source_checkpoint_selection_20260927.json"
RECEIPT = ROOT / "reports/exp227_target6bba_eight_chunk_coordinator_20260927.json"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
DATASET = re.compile(r"6bba_[0-9a-f]{8}\Z")
RUN_PREFIX = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


class ReconciliationNeeded(RuntimeError):
    """A prior side effect may have happened; a blind retry is forbidden."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest_object(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def hex64(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def frozen_inputs(assignment_path=ASSIGNMENT, prereg_path=PREREG, selection_path=SELECTION):
    """Fail before any receipt or remote action if source selection is not sealed."""
    from prepare_exp227_target_chunk0_local import validate_selection

    require(sha(assignment_path) == ASSIGNMENT_SHA, "Frozen assignment bytes changed")
    assignment = json.loads(Path(assignment_path).read_text())
    require(assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS", "Assignment status")
    require(assignment["thresholds_selected"] is False and assignment["target_labels_read"] is False,
            "Assignment accessed target labels or thresholds")
    direction = assignment["directions"]["44b6"]
    chunks = direction["chunks"]
    require(direction["target_embryo"] == "6bba" and direction["movie_count"] == 116,
            "Wrong target cohort")
    require(len(chunks) == 8 and [len(chunk) for chunk in chunks] == [15] * 4 + [14] * 4,
            "Wrong frozen chunk sizes")
    names = [name for chunk in chunks for name in chunk]
    require(len(names) == len(set(names)) == 116 and all(DATASET.fullmatch(name) for name in names),
            "Target IDs missing, duplicated or malformed")
    prereg_sha = sha(prereg_path)
    selection_sha = sha(selection_path)
    selection = json.loads(Path(selection_path).read_text())
    validate_selection(selection, prereg_sha)
    require(hex64(selection["checkpoint_sha256"]), "Selected checkpoint SHA missing")
    return {"assignment_sha256": ASSIGNMENT_SHA, "prereg_sha256": prereg_sha,
            "selection_sha256": selection_sha, "checkpoint_sha256": selection["checkpoint_sha256"],
            "selected_epoch": selection["selected_epoch"], "chunks": chunks}


def _seal(state):
    body = dict(state)
    body.pop("state_sha256", None)
    state["state_sha256"] = digest_object(body)
    return state


def _read_state(path):
    state = json.loads(Path(path).read_text())
    digest = state.get("state_sha256")
    require(hex64(digest) and digest == digest_object({k: v for k, v in state.items()
                                                       if k != "state_sha256"}),
            "Coordinator receipt integrity mismatch")
    return state


def _save(path, state, *, create=False):
    path = Path(path)
    state["updated_unix"] = time.time()
    data = json.dumps(_seal(state), indent=2) + "\n"
    if create:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return
    temporary = path.with_name(path.name + f".partial.{os.getpid()}.{time.time_ns()}")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _validate_prepare(result, index, frozen):
    require(result["status"] == "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY", "Prepare status")
    require(result["chunk_index"] == index and result["movies"] == frozen["chunks"][index],
            "Prepare changed frozen assignment")
    for key in ("selection_sha256", "checkpoint_sha256"):
        require(result[key] == frozen[key], "Prepare changed " + key)
    require(result["assignment_sha256"] == frozen["assignment_sha256"] and
            result["prereg_sha256"] == frozen["prereg_sha256"] and
            result["selected_epoch"] == frozen["selected_epoch"], "Prepare changed frozen inputs")
    require(hex64(result["plan_sha256"]), "Prepare plan SHA missing")
    require(result.get("target_labels_read") is False, "Prepare target-label assertion missing")
    require(result["remote_stage_created"] is False and result["remote_run_created"] is False and
            result["gpu_claimed"] is False, "Prepare unexpectedly mutated remote state")
    require(Path(result["bundle"]).is_dir(), "Local prepare bundle missing")


def _validate_stage(result, index, frozen, prepared):
    require(result["status"] == "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS", "Stage status")
    require(result["chunk_index"] == index, "Stage chunk index")
    for key in ("plan_sha256", "selection_sha256", "checkpoint_sha256"):
        require(result[key] == prepared[key], "Stage changed " + key)
    require(result["movies"] == frozen["chunks"][index], "Stage movies changed")
    require(result["lease_id"] == prepared["lease_id"], "Stage lease ID changed")
    require(hex64(result["manifest_sha256"]), "Stage manifest SHA missing")
    suffix = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
    require(result["code"] == RUN_PREFIX + "/code/" + suffix, "Unexpected target code path")
    require(result["run"] == RUN_PREFIX + "/runs/" + suffix, "Unexpected target run path")
    require(isinstance(result["lease_id"], str) and result["lease_id"], "Stage lease ID missing")
    require(result.get("target_labels_read") is False, "Stage target-label assertion missing")
    require(result["remote_run_created"] is False and result["gpu_claimed"] is False,
            "Stage unexpectedly launched")


def _validate_launch(result, index, stage):
    require(result["status"] == "LAUNCHED_EXP227_TARGET6BBA_CHUNK", "Launch status")
    require(result["chunk_index"] == index, "Launch chunk index")
    for key in ("code", "run", "manifest_sha256", "plan_sha256", "lease_id"):
        require(result[key] == stage[key], "Launch changed " + key)
    for key in ("lease", "config", "launch", "control"):
        require(result.get(key), "Launch missing " + key + " evidence")
    require(result.get("target_labels_read") is False, "Launch target-label assertion missing")
    lease, config, proof = result["lease"], result["config"], result["fair_proof"]
    require(lease["state"] == "RESERVED" and lease["id"] == stage["lease_id"] and
            lease["run_path"] == stage["run"] and lease["alias"] == "nsu-a100" and
            lease["owner"] == "biohub-agent" and
            lease["project"] == "biohub-cell-tracking-during-development", "Launch lease identity")
    require(lease["token"] == config["token"] and
            config["lease_id"] == stage["lease_id"] and config["gpu"] in lease["gpus"] and
            len(lease["gpus"]) == 1 and config["pool"] == "a100", "Launch GPU/token identity")
    physical = proof["physical_preclaim"]
    idle = set(physical["idle_gpus"])
    require(idle == set(physical["all_gpus"]) - set(physical["busy_gpus"]),
            "Invalid physical GPU idle evidence")
    require(lease["gpus"][0] in idle and proof["first_fair_idle_gpu"] in idle,
            "Assigned GPU was not physically idle")
    requests = proof["queue_preclaim"]
    require(not any(row["state"].startswith("WAITING") and
                    row["project"] != "biohub-cell-tracking-during-development" for row in requests),
            "Earlier foreign WAITING queue claim")
    require(not any(row["state"] in ("RESERVED", "RUNNING") and
                    lease["gpus"][0] in (row.get("gpus") or []) for row in requests),
            "Assigned GPU was occupied in preclaim queue")
    require(not any(row["id"] == stage["lease_id"] for row in requests),
            "Target lease existed before claim")


def _validate_postrun(result, index, frozen, stage):
    require(result["status"] == "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS", "Post-run status")
    require(result["chunk_index"] == index and result["movies"] == frozen["chunks"][index],
            "Post-run movies changed")
    for key in ("manifest_sha256", "plan_sha256", "checkpoint_sha256"):
        require(result[key] == stage[key], "Post-run changed " + key)
    for key in ("status_sha256", "exit_sha256", "supervision_sha256", "control_sha256"):
        require(hex64(result[key]), "Post-run missing " + key)
    hashes = result["graph_hashes"]
    require(len(hashes) == len(frozen["chunks"][index]), "Post-run graph count")
    require([row["dataset"] for row in hashes] == frozen["chunks"][index], "Post-run graph order")
    require(all(hex64(row["csv_sha256"]) and hex64(row["receipt_sha256"]) for row in hashes),
            "Post-run graph hash missing")
    require(result["target_labels_read"] is False and result["queue_state_in_control"] == "RELEASED",
            "Post-run label/release assertion")


def _completion_ready(snapshot, run):
    exit_record = snapshot.get("exit")
    complete = snapshot.get("complete")
    control = snapshot.get("control")
    if exit_record is not None:
        require(exit_record.get("returncode") == 0 and exit_record.get("hard_timeout") is False,
                "Target process failed or timed out")
    if complete is not None:
        require(exit_record is not None and complete.get("exit") == exit_record and
                complete.get("status") == "RELEASED_AFTER_VERIFIED_EXIT", "Bad supervision completion")
    if control is not None:
        queue = control.get("queue", {})
        require(queue.get("run_path") == run, "Bad queue control run path")
        if control.get("action") == "heartbeat":
            require(queue.get("state") in ("RESERVED", "RUNNING") and complete is None,
                    "Bad queue control heartbeat")
            return False
        require(control.get("action") == "release" and queue.get("state") == "RELEASED" and
                exit_record is not None, "Bad queue control release")
    if complete is not None:
        require(control is not None and control.get("action") == "release",
                "Completion lacks queue release")
    return exit_record is not None and complete is not None and control is not None


def _fair_a100_available(snapshot, lease_id):
    """Read-only precheck; the launcher independently repeats it before claim."""
    queue = snapshot["queue"]
    physical = snapshot["physical"]
    requests = queue["requests"]
    all_gpus = physical["all_gpus"]
    busy_gpus = physical["busy_gpus"]
    idle_gpus = physical["idle_gpus"]
    require(len(all_gpus) == len(set(all_gpus)) and all_gpus,
            "Malformed physical A100 inventory")
    require(set(idle_gpus) == set(all_gpus) - set(busy_gpus),
            "Inconsistent physical A100 idle snapshot")
    require(not any(row["id"] == lease_id for row in requests),
            "Existing target lease requires reconciliation")
    if any(row["state"].startswith("WAITING") and
           row["project"] != "biohub-cell-tracking-during-development" for row in requests):
        return None, "FOREIGN_WAITING"
    occupied = {gpu for row in requests if row["state"] in ("RESERVED", "RUNNING")
                for gpu in (row.get("gpus") or [])}
    available = sorted(set(idle_gpus) - occupied)
    if not available:
        return None, "NO_FAIR_IDLE_A100"
    return available[0], "FAIR_IDLE_A100_AVAILABLE"


class DefaultOps:
    """All cluster access is lazy and happens only when the CLI is run."""

    def prepare(self, index):
        from prepare_exp227_target_chunk0_local import paths, prepare_index
        destination = paths(index)
        if destination["bundle"].exists() or destination["receipt"].exists():
            require(destination["bundle"].is_dir() and destination["receipt"].is_file(),
                    "Partial existing local prepare requires reconciliation")
            # Chunk00 can already be prepared before the coordinator starts.
            # This replays the complete local bundle/selection/assignment audit
            # without creating or changing any file. An existing stage blocks it.
            from stage_exp227_target_chunk import local_gate
            prepared, *_ = local_gate(index)
            return prepared
        return prepare_index(index)

    def stage(self, index):
        from stage_exp227_target_chunk import stage_index
        return stage_index(index)

    def launch(self, index):
        from launch_exp227_target_chunk import launch_index
        return launch_index(index)

    def completion(self, run):
        from monitor_exp213_job import ssh
        source = ("import json\nfrom pathlib import Path\n"
                  f"r=Path({run!r})\n"
                  "def read(name):\n p=r/name\n return json.loads(p.read_text()) if p.exists() else None\n"
                  "print(json.dumps({'exit':read('exit.json'),"
                  "'complete':read('supervision/complete.json'),"
                  "'control':read('supervision/control.json')}))\n")
        return ssh("nsu-quadro", "python3 -", source)

    def postrun(self, stage):
        from monitor_exp213_job import ssh
        command = shlex.join(["python3", stage["code"] + "/verify_exp227_target_chunk0.py",
                                "--code", stage["code"], "--run", stage["run"],
                                "--manifest-sha256", stage["manifest_sha256"],
                                "--plan-sha256", stage["plan_sha256"]])
        return ssh("nsu-quadro", command)

    def queue_status(self):
        from monitor_exp213_job import QUEUE, ssh
        return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))

    def prelaunch_fair(self):
        from launch_exp227_target_chunk import PHYSICAL_IDLE_SOURCE
        from monitor_exp213_job import ssh
        return {"queue": self.queue_status(),
                "physical": ssh("nsu-a100", "python3 -", PHYSICAL_IDLE_SOURCE)}


def _phase(path, state, chunk, phase, index, call, validate):
    item = chunk.get(phase)
    if item is None:
        item = {"intent_unix": time.time(), "chunk_index": index}
        chunk[phase] = item
        _save(path, state)
        result = call(index)
        item["result"] = result
        _save(path, state)
    elif "result" not in item:
        raise ReconciliationNeeded(f"Chunk {index} {phase} intent has no result; inspect remote/local state")
    if not item.get("validated", False):
        validate(item["result"])
        item["validated"] = True
        _save(path, state)
    return item["result"]


def _run_locked(*, receipt=RECEIPT, ops=None, resume=False, wait_seconds=14400,
                fair_wait_seconds=14400, poll_seconds=90,
                assignment=ASSIGNMENT, prereg=PREREG, selection=SELECTION, sleeper=time.sleep,
                monotonic=time.monotonic):
    """Run eight chunks in order; an existing receipt needs explicit resume.

    Resume skips validated side effects. A side effect with an intent but no
    result requires manual reconciliation, and no later chunk is touched.
    """
    require(wait_seconds >= 0 and fair_wait_seconds >= 0 and poll_seconds >= 60,
            "Finite waits and >=60s polling required")
    frozen = frozen_inputs(assignment, prereg, selection)
    receipt = Path(receipt)
    if receipt.exists():
        state = _read_state(receipt)
        require(state["frozen"] == frozen, "Frozen inputs differ from coordinator receipt")
        if state["status"] == "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED":
            return state
        if not resume:
            raise ReconciliationNeeded("Existing coordinator receipt; use --resume after review")
        if state["status"] == "STOPPED_NEEDS_RECONCILIATION":
            raise ReconciliationNeeded("Stopped anomaly requires explicit reconciliation")
    else:
        state = {"status": "ACTIVE_NO_TARGET_LABELS", "frozen": frozen,
                 "chunks": [{} for _ in range(8)], "target_labels_read": False,
                 "target_score_computed": False}
        _save(receipt, state, create=True)
    ops = ops or DefaultOps()
    try:
        for index, chunk in enumerate(state["chunks"]):
            prepared = _phase(receipt, state, chunk, "prepare", index, ops.prepare,
                              lambda result: _validate_prepare(result, index, frozen))
            stage = _phase(receipt, state, chunk, "stage", index, ops.stage,
                           lambda result: _validate_stage(result, index, frozen, prepared))
            if "launch" not in chunk:
                fair_deadline = monotonic() + fair_wait_seconds
                while True:
                    fair_snapshot = ops.prelaunch_fair()
                    fair_gpu, fair_reason = _fair_a100_available(fair_snapshot, stage["lease_id"])
                    if fair_gpu is not None:
                        chunk["fair_prelaunch"] = {"gpu": fair_gpu,
                                                   "snapshot_sha256": digest_object(fair_snapshot),
                                                   "checked_unix": time.time()}
                        state["status"] = "ACTIVE_NO_TARGET_LABELS"
                        state.pop("waiting_chunk_index", None)
                        state.pop("wait_reason", None)
                        state.pop("last_fair_snapshot_sha256", None)
                        _save(receipt, state)
                        break
                    remaining = fair_deadline - monotonic()
                    if remaining < poll_seconds:
                        if remaining > 0:
                            sleeper(remaining)  # No second read before the >=60s poll interval.
                        state["status"] = "WAITING_FOR_FAIR_A100_NO_NEW_LAUNCH"
                        state["waiting_chunk_index"] = index
                        state["wait_reason"] = fair_reason
                        state["last_fair_snapshot_sha256"] = digest_object(fair_snapshot)
                        _save(receipt, state)
                        return state
                    sleeper(poll_seconds)
            _phase(receipt, state, chunk, "launch", index, ops.launch,
                   lambda result: _validate_launch(result, index, stage))
            if "postrun" in chunk:
                require(chunk["postrun"].get("validated") is True, "Unverified post-run receipt")
                _validate_postrun(chunk["postrun"]["gate"], index, frozen, stage)
                continue
            deadline = monotonic() + wait_seconds
            while True:
                snapshot = ops.completion(stage["run"])
                if _completion_ready(snapshot, stage["run"]):
                    break
                if monotonic() >= deadline:
                    state["status"] = "WAITING_FOR_RELEASE_NO_NEW_LAUNCH"
                    state["waiting_chunk_index"] = index
                    _save(receipt, state)
                    return state
                sleeper(min(poll_seconds, max(0, deadline - monotonic())))
            gate = ops.postrun(stage)
            _validate_postrun(gate, index, frozen, stage)
            queue_state = ops.queue_status()  # Fresh live read after all graph/exit hashes.
            from verify_exp227_target_chunk0 import live_release
            row = live_release(queue_state, stage["lease_id"], stage["run"])
            require(row["id"] == stage["lease_id"], "Live lease ID changed")
            chunk["postrun"] = {"validated": True, "gate": gate, "queue_row": row,
                                "queue_snapshot_sha256": digest_object(queue_state),
                                "live_release_checked_unix": time.time()}
            state["status"] = "ACTIVE_NO_TARGET_LABELS"
            state.pop("waiting_chunk_index", None)
            _save(receipt, state)
        hashes = [row for chunk in state["chunks"] for row in chunk["postrun"]["gate"]["graph_hashes"]]
        require(len(hashes) == 116 and [row["dataset"] for row in hashes] ==
                [name for group in frozen["chunks"] for name in group], "Final 116-graph assignment mismatch")
        require(len({row["dataset"] for row in hashes}) == 116, "Duplicate final graph ID")
        state["status"] = "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED"
        state["movie_count"] = 116
        state["graph_count"] = 116
        state["all_leases_released"] = True
        state["target_labels_read"] = False
        state["target_score_computed"] = False
        state["separate_guarded_scorer_may_be_prepared"] = True
        _save(receipt, state)
        return state
    except Exception as error:
        state["status"] = "STOPPED_NEEDS_RECONCILIATION"
        state["error"] = {"type": type(error).__name__, "message": str(error)}
        _save(receipt, state)
        raise


def run(*, receipt=RECEIPT, ops=None, resume=False, wait_seconds=14400,
        fair_wait_seconds=14400, poll_seconds=90,
        assignment=ASSIGNMENT, prereg=PREREG, selection=SELECTION, sleeper=time.sleep,
        monotonic=time.monotonic):
    """Acquire a one-process lock before any coordinator receipt or cluster work."""
    receipt = Path(receipt)
    lock = receipt.with_name(receipt.name + ".lock")
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps({"pid": os.getpid(), "created_unix": time.time()}) + "\n")
    except FileExistsError as error:
        raise ReconciliationNeeded("Coordinator lock exists; inspect the running process before recovery") from error
    try:
        return _run_locked(receipt=receipt, ops=ops, resume=resume, wait_seconds=wait_seconds,
                           fair_wait_seconds=fair_wait_seconds,
                           poll_seconds=poll_seconds, assignment=assignment, prereg=prereg,
                           selection=selection, sleeper=sleeper, monotonic=monotonic)
    finally:
        lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="Continue only already-validated phases")
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    parser.add_argument("--wait-seconds", type=int, default=14400)
    parser.add_argument("--fair-wait-seconds", type=int, default=14400)
    parser.add_argument("--poll-seconds", type=int, default=90)
    args = parser.parse_args()
    result = run(receipt=args.receipt, resume=args.resume, wait_seconds=args.wait_seconds,
                 fair_wait_seconds=args.fair_wait_seconds,
                 poll_seconds=args.poll_seconds)
    print(json.dumps({"status": result["status"],
                      "verified_chunks": sum("postrun" in row for row in result["chunks"]),
                      "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
