"""One-shot source11 graph/scorer handoff after EXP236 epoch10 recovery.

Default invocation audits only. ``--launch`` claims a new receipt and waits
for the recovery controller's exact epoch10 release before staging any graph.
The original stopped handoff receipt is never changed or restarted.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

import continue_exp236_after_epoch10_to_source_score as handoff
from monitor_exp213_job import ssh
from prepare_exp236_source_graph10_v2 import (
    CONTROLLER_RECEIPT as TRAIN_RECOVERY, ORIGINAL_CONTROLLER_RECEIPT,
    verify_parent_chain,
)
from prepare_exp236_source_graph10_scorer import CODE as SCORE_CODE
from run_exp236_source_graph10_v2 import CODE as GRAPH_CODE, INNER_IDS


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = handoff.RECEIPT
ORIGINAL_SCRIPT = ROOT / "scripts/continue_exp236_after_epoch10_to_source_score.py"
RECEIPT = ROOT / "reports/exp236_source11_handoff_recovery_20260927.json"


class Reconcile(RuntimeError):
    """An existing claim or artifact needs review before continuation."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def live_original_pids():
    pids = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if any(Path(arg.strip('"')).name == ORIGINAL_SCRIPT.name for arg in args):
                pids.append(process.info["pid"])
        except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
            continue
    return pids


def original_gate():
    original = json.loads(ORIGINAL.read_text())
    assert original["status"] == "STOPPED_EXP236_SOURCE11_HANDOFF"
    assert original["training_run"] == handoff.TRAIN_RUN
    assert original["source_graph_run"] == handoff.GRAPH_RUN
    assert original["source_score_run"] == handoff.SCORE_RUN
    assert original["source_labels_opened_before_graphs"] is False
    assert original["target_data_opened"] is False
    assert original["finished_or_stopped"] >= original["started"]
    assert original["error"] == (
        "TerminalAnomaly('EXP236 training controller stopped: AssertionError()')")
    assert "prepare_graph_returncode" not in original
    assert "launch_graph_returncode" not in original
    assert "prepare_score_returncode" not in original
    assert "launch_score_returncode" not in original
    if live_original_pids():
        raise Reconcile("Original EXP236 source11 handoff process is still alive")
    return sha(ORIGINAL)


def no_local_stage_artifacts():
    for path in (
        handoff.GRAPH_PLAN, handoff.GRAPH_CONFIG, handoff.GRAPH_PREPARED,
        handoff.GRAPH_LAUNCHED, handoff.GRAPH_RESERVATION, handoff.GRAPH_PARTIAL,
        handoff.GRAPH_PRELAUNCH_RELEASE, handoff.SCORE_PREPARED,
        handoff.SCORE_LAUNCHED, handoff.SCORE_VERIFIED,
    ):
        if path.exists():
            raise Reconcile(f"Graph or scorer artifact already exists: {path.name}")


def remote_absent():
    source = '''import json,pathlib
paths=@@PATHS@@
print(json.dumps({'absent':all(not pathlib.Path(path).exists() for path in paths)}))
'''.replace("@@PATHS@@", repr([GRAPH_CODE, handoff.GRAPH_RUN]))
    if ssh("nsu-a100", "python3 -", source) != {"absent": True}:
        raise Reconcile("EXP236 source11 remote graph code or run exists")
    score_source = '''import json,pathlib
paths=@@PATHS@@
print(json.dumps({'absent':all(not pathlib.Path(path).exists() for path in paths)}))
'''.replace("@@PATHS@@", repr([SCORE_CODE, handoff.SCORE_RUN]))
    if ssh("nsu-quadro", "python3 -", score_source) != {"absent": True}:
        raise Reconcile("EXP236 source11 remote scorer code or run exists")


def graph_queue_absent(queue=None):
    queue = handoff.queue_status() if queue is None else queue
    if any(row["id"] == handoff.GRAPH_LEASE or
           row["run_path"] == handoff.GRAPH_RUN for row in queue["requests"]):
        raise Reconcile("EXP236 source11 graph queue claim already exists")
    return queue


def fair_graph_probe():
    if any(path.exists() for path in (handoff.GRAPH_RESERVATION,
                                      handoff.GRAPH_PARTIAL,
                                      handoff.GRAPH_PRELAUNCH_RELEASE,
                                      handoff.GRAPH_LAUNCHED)):
        raise Reconcile("Graph launch artifact appeared while waiting")
    queue = graph_queue_absent()
    parent_id = "exp236-horaz-source6bba-block04-v2-20260927"
    if handoff.lease_for(queue, parent_id, handoff.TRAIN_RUN)["state"] != "RELEASED":
        raise Reconcile("EXP236 block04 release changed")
    requests = queue["requests"]
    waiting = sorted(row["id"] for row in requests
                     if row["state"].startswith("WAITING") and
                     (row["project"] != handoff.PROJECT or row["pool"] == "a100"))
    pool = queue["pools"]["a100"]
    active = [row for row in requests if row["pool"] == "a100" and
              row["state"] in ("RUNNING", "RESERVED")]
    occupied = {gpu for row in active for gpu in row.get("gpus", [])}
    free = sorted(set(pool["gpus"]) - occupied)
    capacity = (pool["cpu"] - sum(row["cpu"] for row in active) >= 8 and
                pool["ram_gib"] - sum(row["ram_gib"] for row in active) >= 32)
    idle = sorted(set(free) - handoff.physical_busy()) if not waiting and free and capacity else []
    return {"waiting": waiting, "queue_free": free, "idle": idle,
            "capacity": capacity, "ready": not waiting and bool(idle) and capacity}


def recovery_receipt_gate():
    recovery = json.loads(TRAIN_RECOVERY.read_text())
    assert recovery["original_receipt_sha256"] == sha(ORIGINAL_CONTROLLER_RECEIPT)
    assert recovery["target_data_opened"] is False
    assert recovery["block01_audit"]["completed_epochs"] == 3
    status = recovery["status"]
    if status.startswith("STOPPED_"):
        raise Reconcile(f"EXP236 training recovery stopped: {recovery.get('error')}")
    if status == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED":
        chain, receipt_sha = verify_parent_chain()
        assert len(chain) == 4
        assert [row["completed_epochs"] for row in chain] == [3, 6, 9, 10]
        assert chain[-1]["run"] == handoff.TRAIN_RUN
        assert recovery["final_audit"] == {
            key: value for key, value in chain[-1].items() if key not in ("code", "run")
        }
        return {"status": status, "controller_sha256": receipt_sha,
                "checkpoint_sha256": chain[-1]["checkpoint_sha256"],
                "training_result_sha256": chain[-1]["result_sha256"]}
    if not (status.startswith(("WAITING_FOR_", "PREPARING_", "LAUNCHING_", "AUDITING_"))
            and "EXP236" in status and "error" not in recovery):
        raise Reconcile(f"Unexpected EXP236 training recovery state: {status}")
    return {"status": status}


def preflight():
    if RECEIPT.exists():
        raise Reconcile("Existing source11 recovery receipt must be reconciled")
    original_sha = original_gate()
    no_local_stage_artifacts()
    remote_absent()
    graph_queue_absent()
    training = recovery_receipt_gate()
    return {"status": "PASS_EXP236_SOURCE11_RECOVERY_PREFLIGHT",
            "original_handoff_sha256": original_sha,
            "training_recovery_status": training["status"],
            "training_run": handoff.TRAIN_RUN,
            "source_graph_run": handoff.GRAPH_RUN,
            "source_score_run": handoff.SCORE_RUN,
            "source_labels_opened_before_graphs": False,
            "target_data_opened": False}


def graph_stage_gate(parent):
    if sha(ORIGINAL) != parent["original_handoff_sha256"]:
        raise Reconcile("Original source11 handoff receipt changed")
    if sha(TRAIN_RECOVERY) != parent["training_controller_sha256"]:
        raise Reconcile("Completed EXP236 training recovery receipt changed")
    for path in (handoff.GRAPH_LAUNCHED, handoff.GRAPH_RESERVATION,
                 handoff.GRAPH_PARTIAL, handoff.GRAPH_PRELAUNCH_RELEASE,
                 handoff.SCORE_PREPARED, handoff.SCORE_LAUNCHED,
                 handoff.SCORE_VERIFIED):
        if path.exists():
            raise Reconcile(f"Graph or scorer launch artifact exists: {path.name}")
    score_stage_absent()
    prepared = json.loads(handoff.GRAPH_PREPARED.read_text())
    config = json.loads(handoff.GRAPH_CONFIG.read_text())
    plan = json.loads(handoff.GRAPH_PLAN.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS"
    assert prepared["movies"] == len(INNER_IDS) == 11
    assert prepared["source_labels_read"] is False
    assert prepared["target_labels_read"] is False and prepared["target_data_opened"] is False
    assert prepared["controller_receipt_sha256"] == parent["training_controller_sha256"]
    assert prepared["preflight"]["checkpoint_sha256"] == parent["checkpoint_sha256"]
    assert sha(handoff.GRAPH_PLAN) == prepared["stage"]["plan_sha256"]
    assert plan["training_chain"] == prepared["training_chain"]
    assert [row["dataset"] for row in plan["movies"]] == list(INNER_IDS)
    assert config == {"experiment": "EXP236", "lease_id": handoff.GRAPH_LEASE,
                      "token": "exp236_source_graph10_v2_20260927",
                      "code": GRAPH_CODE, "run": handoff.GRAPH_RUN,
                      "max_seconds": 7200, "cpu_affinity": "0-7",
                      "script": "run_exp236_source_graph10_v2.py",
                      "arguments": [GRAPH_CODE + "/plan.json", "--plan-sha256",
                                    prepared["stage"]["plan_sha256"]]}
    graph_queue_absent()
    source = '''import hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert code.is_dir() and not run.exists()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve()
 assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@PLAN_SHA@@
print(json.dumps({'status':'PASS_EXP236_SOURCE11_RECOVERY_STAGE_GATE',
 'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'graph_run_absent':True}))
'''.replace("@@CODE@@", repr(GRAPH_CODE)).replace(
        "@@RUN@@", repr(handoff.GRAPH_RUN)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"]))
    remote = ssh("nsu-a100", "python3 -", source)
    assert remote == {"status": "PASS_EXP236_SOURCE11_RECOVERY_STAGE_GATE",
                      "manifest_sha256": prepared["stage"]["manifest_sha256"],
                      "plan_sha256": prepared["stage"]["plan_sha256"],
                      "graph_run_absent": True}
    return {"graph_prepare_sha256": sha(handoff.GRAPH_PREPARED),
            "graph_plan_sha256": remote["plan_sha256"],
            "graph_manifest_sha256": remote["manifest_sha256"],
            "graph_run_absent": True}


def score_stage_absent():
    for path in (handoff.SCORE_PREPARED, handoff.SCORE_LAUNCHED,
                 handoff.SCORE_VERIFIED):
        if path.exists():
            raise Reconcile(f"Source scorer artifact already exists: {path.name}")
    source = '''import json,pathlib
print(json.dumps({'absent':not pathlib.Path(@@CODE@@).exists() and
                            not pathlib.Path(@@RUN@@).exists()}))
'''.replace("@@CODE@@", repr(SCORE_CODE)).replace(
        "@@RUN@@", repr(handoff.SCORE_RUN))
    if ssh("nsu-quadro", "python3 -", source) != {"absent": True}:
        raise Reconcile("Source scorer code or run already exists")


def score_launch_gate():
    if handoff.SCORE_LAUNCHED.exists() or handoff.SCORE_VERIFIED.exists():
        raise Reconcile("Source scorer launch or verified receipt already exists")
    prepared = json.loads(handoff.SCORE_PREPARED.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE10_OFFICIAL_SCORER_NO_LABELS"
    assert prepared["source_labels_read"] is False
    assert prepared["target_labels_read"] is False and prepared["target_data_opened"] is False
    assert prepared["inference_prepare_sha256"] == sha(handoff.GRAPH_PREPARED)
    assert prepared["preflight"]["status"] == "PASS_EXP236_SOURCE10_SCORER_PREFLIGHT"
    assert [row["dataset"] for row in prepared["preflight"]["hashes"]] == list(INNER_IDS)
    source = '''import hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert code.is_dir() and not run.exists()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve()
 assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
print(json.dumps({'status':'PASS_EXP236_SOURCE11_SCORE_STAGE_GATE'}))
'''.replace("@@CODE@@", repr(SCORE_CODE)).replace(
        "@@RUN@@", repr(handoff.SCORE_RUN)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(prepared["stage"]["score_config_sha256"]))
    assert ssh("nsu-quadro", "python3 -", source) == {
        "status": "PASS_EXP236_SOURCE11_SCORE_STAGE_GATE"}
    return sha(handoff.SCORE_PREPARED)


def wait_for(name, seconds, probe, check, state):
    deadline = time.monotonic() + seconds
    errors = 0
    while time.monotonic() < deadline:
        try:
            observed = probe()
            errors = 0
        except (Reconcile, handoff.TerminalAnomaly):
            raise
        except Exception as exc:
            errors += 1
            state[name + "_observation_error"] = repr(exc)
            state[name + "_observation_failures"] = errors
            save(state)
            if errors >= 5:
                raise RuntimeError(f"Five consecutive {name} observation failures") from exc
            time.sleep(handoff.INTERVAL_SECONDS)
            continue
        if check(observed):
            state[name + "_verified"] = observed
            save(state)
            return observed
        compact = json.dumps(observed, sort_keys=True)
        if state.get(name + "_last_snapshot") != compact:
            state[name + "_last_snapshot"] = compact
            save(state)
        time.sleep(handoff.INTERVAL_SECONDS)
    raise TimeoutError(f"{name} did not verify within {seconds}s")


def step(name, script, timeout, state):
    log = ROOT / f"reports/exp236_source11_handoff_recovery_{name}_20260927.log"
    if log.exists():
        raise Reconcile(f"Existing {name} step log must be reconciled")
    state[name + "_attempted"] = True
    save(state)
    try:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script)],
                                   cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log.write_text(out + "\n--- stderr ---\n" + err)
        state[name + "_log"] = str(log)
        state[name + "_timeout"] = True
        save(state)
        raise RuntimeError(f"{name} timed out; reconcile {log}") from exc
    log.write_text(completed.stdout + "\n--- stderr ---\n" + completed.stderr)
    state[name + "_log"] = str(log)
    state[name + "_returncode"] = completed.returncode
    save(state)
    if completed.returncode:
        raise RuntimeError(f"{name} returned {completed.returncode}; reconcile {log}")


def run(prepared):
    state = {"status": "WAITING_FOR_EXP236_RECOVERED_EPOCH10_RELEASE",
             "started": time.time(), "pid": os.getpid(),
             "original_handoff_sha256": prepared["original_handoff_sha256"],
             "training_run": handoff.TRAIN_RUN,
             "source_graph_run": handoff.GRAPH_RUN,
             "source_score_run": handoff.SCORE_RUN,
             "source_labels_opened_before_graphs": False,
             "target_data_opened": False}
    claim(state)
    try:
        parent = wait_for("training", 172800, recovery_receipt_gate,
                          lambda observed: observed["status"] ==
                          "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED", state)
        state["training_controller_sha256"] = parent["controller_sha256"]
        state["status"] = "EXP236_RECOVERED_EPOCH10_PREPARING_SOURCE11_GRAPHS"
        save(state)
        assert sha(ORIGINAL) == prepared["original_handoff_sha256"]
        no_local_stage_artifacts()
        remote_absent()
        graph_queue_absent()
        step("prepare_graph", "prepare_exp236_source_graph10_v2.py", 900, state)
        graph_parent = {**parent,
                        "original_handoff_sha256": prepared["original_handoff_sha256"],
                        "training_controller_sha256": parent["controller_sha256"]}
        staged = graph_stage_gate(graph_parent)
        state["graph_stage"] = staged
        state["status"] = "WAITING_FOR_FAIR_EXP236_SOURCE11_GRAPH_RESOURCE"
        save(state)
        wait_for("graph_resource", 86400, fair_graph_probe,
                 lambda observed: observed["ready"], state)
        assert graph_stage_gate(graph_parent) == staged
        if not fair_graph_probe()["ready"]:
            raise Reconcile("Fair physical A100 changed before graph launch")
        state["status"] = "EXP236_SOURCE11_GRAPHS_STAGED_LAUNCHING"
        save(state)
        step("launch_graph", "launch_exp236_source_graph10_v2.py", 300, state)
        assert handoff.GRAPH_LAUNCHED.is_file()
        state["graph_launch_sha256"] = sha(handoff.GRAPH_LAUNCHED)
        state["status"] = "WAITING_FOR_EXP236_SOURCE11_GRAPH_RELEASE"
        save(state)
        wait_for("graph", 9000, handoff.graph_probe, handoff.graph_released, state)
        state["status"] = "EXP236_SOURCE11_NO_LABEL_GRAPHS_RELEASED_AUDITING"
        save(state)
        assert sha(TRAIN_RECOVERY) == parent["controller_sha256"]
        assert handoff.graph_released(handoff.graph_probe())
        score_stage_absent()
        step("prepare_score", "prepare_exp236_source_graph10_scorer.py", 900, state)
        state["score_prepare_sha256"] = score_launch_gate()
        state["status"] = "EXP236_SOURCE11_SCORER_STAGED_LAUNCHING"
        save(state)
        assert score_launch_gate() == state["score_prepare_sha256"]
        step("launch_score", "launch_exp236_source_graph10_scorer.py", 300, state)
        assert handoff.SCORE_LAUNCHED.is_file()
        state["status"] = "WAITING_FOR_EXP236_SOURCE11_OFFICIAL_SCORE"
        save(state)
        wait_for("score", 2700, handoff.score_probe, handoff.score_exited, state)
        state["status"] = "EXP236_SOURCE11_OFFICIAL_SCORER_EXITED_VERIFYING"
        save(state)
        step("verify_score", "verify_exp236_source_graph10_scorer.py", 300, state)
        assert handoff.SCORE_VERIFIED.is_file()
        verified = json.loads(handoff.SCORE_VERIFIED.read_text())
        assert verified["status"] == "VERIFIED_EXP236_SOURCE10_OFFICIAL"
        assert verified["rows"] == 11 and math.isfinite(verified["source_score"])
        assert verified["source_labels_read"] is True and verified["target_labels_read"] is False
        state["source_score_receipt"] = str(handoff.SCORE_VERIFIED)
        state["source_score_receipt_sha256"] = sha(handoff.SCORE_VERIFIED)
        state["status"] = "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF"
    except BaseException as exc:
        state["status"] = "STOPPED_EXP236_SOURCE11_HANDOFF_RECOVERY"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true",
                        help="claim new receipt and wait for epoch10 before graph/scorer stages")
    args = parser.parse_args()
    prepared = preflight()
    if not args.launch:
        print(json.dumps(prepared))
        return
    run(prepared)


if __name__ == "__main__":
    main()
