"""Finite local EXP227 source20 -> EXP234 recovery and scorer handoff.

The existing recovery and scorer controllers own all chunk, queue, graph, and
label gates. This starter only releases them after the source20 handoff passes.
An existing receipt or partial startup is terminal and requires reconciliation.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import psutil

import continue_exp227_after_block03 as source20
import continue_exp234_after_target_rollout as scorer
import recover_exp234_target_rollout_v2 as recovery


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp234_source20_release_starter_20260927.json"
SOURCE_HANDOFF_PID = 25908
SOURCE_WAIT_SECONDS = 48 * 3600
SOURCE_POLL_SECONDS = 120
CHILD_RECEIPT_SECONDS = 900
CHILD_POLL_SECONDS = 2
RECOVERY_SCRIPT = ROOT / "scripts/recover_exp234_target_rollout_v2.py"
SCORER_SCRIPT = ROOT / "scripts/continue_exp234_after_target_rollout.py"
SOURCE_ACTIVE = {
    "WAITING_FOR_EXP227_BLOCK03_RELEASE",
    "TRAINING_RELEASED_PREPARING_SOURCE20_GRAPHS",
    "SOURCE20_GRAPHS_STAGED_LAUNCHING",
    "WAITING_FOR_SOURCE20_GRAPH_RELEASE",
    "SOURCE20_NO_LABEL_GRAPHS_RELEASED_AUDITING",
    "SOURCE20_SCORER_STAGED_LAUNCHING",
    "WAITING_FOR_SOURCE20_OFFICIAL_SCORE",
    "SOURCE20_OFFICIAL_SCORER_EXITED_VERIFYING",
}
SOURCE_PASS = "PASS_EXP227_SOURCE20_OFFICIAL_HANDOFF"


class TerminalAnomaly(RuntimeError):
    """State that must be reconciled before another local start."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def child_files(kind):
    stem = "exp234_target_recovery_v2_20260927" if kind == "recovery" else (
        "exp234_target_score_handoff_20260927")
    return (ROOT / f"reports/{stem}.stdout.log",
            ROOT / f"reports/{stem}.stderr.log")


def assert_no_existing_children():
    paths = [recovery.RECEIPT, scorer.RECEIPT, scorer.RELEASE,
             scorer.SCORE_PREPARE, scorer.SCORE_LAUNCH, scorer.SCORE_VERIFIED,
             *child_files("recovery"), *child_files("scorer")]
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise TerminalAnomaly("Existing EXP234 recovery/scorer artifact: " + ", ".join(existing))


def source_receipt():
    if not source20.RECEIPT.is_file():
        raise TerminalAnomaly("Existing EXP227 source20 handoff receipt is absent")
    observed = read_json(source20.RECEIPT)
    status = observed.get("status")
    if status not in SOURCE_ACTIVE | {SOURCE_PASS}:
        raise TerminalAnomaly(f"EXP227 source20 handoff is not a valid active/PASS state: {status}")
    if observed.get("target_labels_opened") is not False:
        raise TerminalAnomaly("EXP227 source20 handoff target-label guard failed")
    if observed.get("source_labels_opened_before_inference") is not False:
        raise TerminalAnomaly("EXP227 source20 handoff graph-before-label guard failed")
    if observed.get("training_run") != source20.TRAIN_RUN or (
            observed.get("source_graph_run") != source20.GRAPH_RUN or
            observed.get("source_score_run") != source20.SCORE_RUN):
        raise TerminalAnomaly("EXP227 source20 handoff run identity changed")
    return observed


def source_process_create_time():
    process = psutil.Process(SOURCE_HANDOFF_PID)
    if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
        raise TerminalAnomaly("EXP227 source20 handoff PID is not running")
    if process.cwd().casefold() != str(ROOT).casefold():
        raise TerminalAnomaly("EXP227 source20 handoff PID has unexpected cwd")
    if not any(Path(arg).name == "continue_exp227_after_block03.py"
               for arg in process.cmdline()):
        raise TerminalAnomaly("EXP227 source20 handoff PID has unexpected command")
    return process.create_time()


def wait_source(state):
    deadline = time.monotonic() + SOURCE_WAIT_SECONDS
    source_create_time = None
    while time.monotonic() < deadline:
        observed = source_receipt()
        if observed["status"] == SOURCE_PASS:
            if "finished_or_stopped" not in observed or "error" in observed:
                raise TerminalAnomaly("EXP227 source20 PASS receipt is incomplete")
            return observed
        try:
            create_time = source_process_create_time()
        except (psutil.NoSuchProcess, TerminalAnomaly) as exc:
            # The process can finish between the receipt read and PID probe.
            if source_receipt()["status"] == SOURCE_PASS:
                continue
            raise TerminalAnomaly("EXP227 source20 handoff stopped before PASS") from exc
        if source_create_time is None:
            source_create_time = create_time
            state["source_handoff_pid"] = SOURCE_HANDOFF_PID
            state["source_handoff_process_create_time"] = create_time
            save(state)
        elif abs(create_time - source_create_time) >= 2:
            raise TerminalAnomaly("EXP227 source20 handoff PID was reused")
        time.sleep(SOURCE_POLL_SECONDS)
    raise TimeoutError("EXP227 source20 handoff did not PASS within 48h")


def verify_source_graph_release(observed):
    """Check the handoff's sealed audit and a fresh queue/remote release view."""
    embedded = observed.get("graph_release_or_exit")
    if not isinstance(embedded, list) or len(embedded) != 2 or (
            source20.check_graph(*embedded) is not True):
        raise TerminalAnomaly("EXP227 source20 handoff lacks a verified graph release")
    if observed.get("source_score_receipt") != str(source20.SCORE_VERIFIED):
        raise TerminalAnomaly("EXP227 source20 score receipt path changed")
    verified = read_json(source20.SCORE_VERIFIED)
    if (verified.get("status") != "VERIFIED_EXP227_SOURCE20_OFFICIAL" or
            verified.get("rows") != 8 or
            verified.get("source_labels_read") is not True or
            verified.get("target_labels_read") is not False or
            not math.isfinite(verified["source_score"])):
        raise TerminalAnomaly("EXP227 source20 official score receipt is invalid")
    config = read_json(source20.GRAPH_CONFIG)
    if config.get("run") != source20.GRAPH_RUN:
        raise TerminalAnomaly("EXP227 source20 graph config run changed")
    lease = source20.queue_lease(source20.GRAPH_LEASE, source20.GRAPH_RUN)
    remote = source20.probe_gpu_run(source20.GRAPH_RUN, config["alias"])
    if source20.check_graph(lease, remote) is not True:
        raise TerminalAnomaly("EXP227 source20 graph is not independently released")
    return {"handoff_receipt_sha256": sha(source20.RECEIPT),
            "source_score_receipt_sha256": sha(source20.SCORE_VERIFIED),
            "graph_lease_state": lease["state"],
            "graph_status": remote["status"], "graph_movies": len(remote["movies"])}


def recovery_receipt_gate(observed, pid):
    status = observed.get("status", "")
    if not status.startswith("WAITING_FOR_") and status != (
            "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"):
        raise TerminalAnomaly(f"EXP234 recovery stopped/unknown during startup: {status}")
    if observed.get("pid") != pid or observed.get("target_labels_read") is not False or (
            observed.get("kaggle_post") is not False or
            observed.get("original_coordinator_sha256") != sha(recovery.ORIGINAL)):
        raise TerminalAnomaly("EXP234 recovery receipt identity/label gate failed")
    completed = observed.get("completed", [])
    if len(completed) < 5 or completed[:5] != read_json(recovery.ORIGINAL)["completed"]:
        raise TerminalAnomaly("EXP234 recovery lost the five accepted chunks")
    return status


def scorer_receipt_gate(observed, _pid):
    status = observed.get("status", "")
    valid = status == "WAITING_FOR_EXP234_TARGET175_RECOVERY_NO_LABEL_RELEASE" or (
        status.startswith("EXP234_TARGET175_RELEASED_") or
        status.startswith("EXP234_OFFICIAL_") or
        status.startswith("WAITING_FOR_EXP234_OFFICIAL_") or
        status == "PASS_EXP234_TARGET175_OFFICIAL_SCORE_HANDOFF")
    if not valid:
        raise TerminalAnomaly(f"EXP234 scorer handoff stopped/unknown during startup: {status}")
    if (observed.get("coordinator_receipt") != str(recovery.RECEIPT) or
            observed.get("target_labels_opened_before_graph_gate") is not False or
            observed.get("kaggle_post") is not False):
        raise TerminalAnomaly("EXP234 scorer handoff receipt identity/label gate failed")
    return status


def start_controller(kind, script, receipt, gate, state):
    if receipt.exists():
        raise TerminalAnomaly(f"EXP234 {kind} already has a receipt")
    stdout_path, stderr_path = child_files(kind)
    state[f"{kind}_start_attempted"] = True
    state["status"] = f"STARTING_EXP234_{kind.upper()}_ONCE"
    save(state)
    with stdout_path.open("x") as out, stderr_path.open("x") as err:
        process = subprocess.Popen([sys.executable, str(script)], cwd=ROOT,
                                   stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                   close_fds=True,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    state[f"{kind}_pid"] = process.pid
    state[f"{kind}_stdout"] = str(stdout_path)
    state[f"{kind}_stderr"] = str(stderr_path)
    save(state)
    deadline = time.monotonic() + CHILD_RECEIPT_SECONDS
    while time.monotonic() < deadline:
        if receipt.is_file():
            child = read_json(receipt)
            status = gate(child, process.pid)
            exit_code = process.poll()
            if exit_code is not None and (exit_code != 0 or not status.startswith("PASS_")):
                raise TerminalAnomaly(f"EXP234 {kind} exited during startup: {exit_code}")
            state[f"{kind}_receipt"] = str(receipt)
            state[f"{kind}_receipt_status"] = status
            state[f"{kind}_receipt_sha256"] = sha(receipt)
            save(state)
            return
        exit_code = process.poll()
        if exit_code is not None:
            raise TerminalAnomaly(f"EXP234 {kind} exited before receipt creation: {exit_code}")
        time.sleep(CHILD_POLL_SECONDS)
    raise TerminalAnomaly(f"EXP234 {kind} started but receipt absent after 15m; reconcile PID")


def main():
    if RECEIPT.exists():
        raise TerminalAnomaly("Existing starter receipt: reconcile, never restart")
    source_receipt()  # Absent or STOPPED prerequisite is terminal before claim.
    assert_no_existing_children()
    state = {"status": "WAITING_FOR_EXP227_SOURCE20_OFFICIAL_HANDOFF",
             "started": time.time(), "source_handoff_receipt": str(source20.RECEIPT),
             "source_handoff_expected_pid": SOURCE_HANDOFF_PID,
             "target_labels_opened_before_graph_gate": False, "kaggle_post": False,
             "recovery_start_attempted": False, "scorer_start_attempted": False}
    claim(state)
    try:
        observed = wait_source(state)
        state["source20_release_gate"] = verify_source_graph_release(observed)
        state["status"] = "EXP227_SOURCE20_RELEASED_RECHECKING_EXP234_PREFIX"
        save(state)
        assert_no_existing_children()
        original, _, _, prepared = recovery.original_prefix()
        state["original_coordinator_sha256"] = sha(recovery.ORIGINAL)
        state["accepted_chunks"] = len(original["completed"])
        state["target_code_manifest_sha256"] = prepared["stage"]["manifest_sha256"]
        save(state)
        assert_no_existing_children()
        start_controller("recovery", RECOVERY_SCRIPT, recovery.RECEIPT,
                         recovery_receipt_gate, state)
        if not recovery.RECEIPT.is_file():
            raise TerminalAnomaly("EXP234 recovery receipt disappeared before scorer start")
        if scorer.RECEIPT.exists() or any(path.exists() for path in (
                scorer.RELEASE, scorer.SCORE_PREPARE, scorer.SCORE_LAUNCH,
                scorer.SCORE_VERIFIED, *child_files("scorer"))):
            raise TerminalAnomaly("EXP234 scorer partial startup exists")
        start_controller("scorer", SCORER_SCRIPT, scorer.RECEIPT,
                         scorer_receipt_gate, state)
        state["status"] = "PASS_EXP234_SOURCE20_RELEASE_CONTROLLERS_STARTED"
    except BaseException as exc:
        state["status"] = "STOPPED_EXP234_SOURCE20_RELEASE_STARTER"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


if __name__ == "__main__":
    main()
