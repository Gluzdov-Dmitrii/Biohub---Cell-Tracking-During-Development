"""Wait fairly for one EXP236 v2 block01 launch, then hand off to epoch10.

This finite local starter invokes the existing immutable block01 launcher once.
It never retries an ambiguous reservation or run, reads target data, or submits.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import continue_exp236_source_v2_to_epoch10 as continuation
from monitor_exp213_job import ssh
from prepare_exp236_source_block01_v2 import (
    CODE_MANIFEST_SHA256, PLAN_SHA256, SOURCE_MANIFEST_SHA256,
    verify_source_audits,
)
from run_exp236_source_resume_v2 import SOURCE_DUPLICATE_MAP_SHA


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp236_block01_v2_fair_starter_20260927.json"
LOADER_SMOKE = ROOT / "reports/exp236_v2_loader_cpu_smoke_20260927.json"
LOADER_SMOKE_SHA = "fb7cbd61afd898af2700d5c7f5ace6b2705d805bd9b1e7bb580930b53f1f94fb"
LAUNCH_SCRIPT = ROOT / "scripts/launch_exp236_source_block01_v2.py"
CONTROLLER_SCRIPT = ROOT / "scripts/continue_exp236_source_v2_to_epoch10.py"
INTERVAL_SECONDS = 120
MAX_WAIT_SECONDS = 48 * 3600
PROJECT = "biohub-cell-tracking-during-development"


class TerminalAnomaly(RuntimeError):
    """An observed state requiring manual reconciliation."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def assert_fresh():
    files = continuation.local_paths(1)
    if any(files[name].exists() for name in ("reservation", "partial", "prelaunch_release", "launch")):
        raise TerminalAnomaly("Block01 already has a reservation or launch artifact")
    if continuation.RECEIPT.exists():
        raise TerminalAnomaly("Continuation controller already has a receipt")
    for block in (2, 3, 4):
        if any(path.exists() for path in continuation.local_paths(block).values()):
            raise TerminalAnomaly(f"Block{block:02d} artifact exists before block01 launch")


def local_stage_gate():
    prepared, config, plan, _ = continuation.local_block(1, launched=False)
    assert prepared["preflight"]["status"] == "PASS_EXP236_SOURCE6BBA_V2_PREFLIGHT"
    assert prepared["stage"]["manifest_sha256"] == CODE_MANIFEST_SHA256
    assert prepared["stage"]["plan_sha256"] == PLAN_SHA256
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA256
    assert plan["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert prepared["source_duplicate_policy"] == "exclude_all_effective_duplicate_windows_v2"
    audits = verify_source_audits()
    assert prepared["source_duplicate_audits"] == {
        key: value for key, value in audits.items() if key != "duplicate_starts"
    }
    assert sha(LOADER_SMOKE) == LOADER_SMOKE_SHA
    smoke = json.loads(LOADER_SMOKE.read_text())
    assert smoke["status"] == "PASS_EXP236_V2_ALL126_SOURCE_LOADER_CPU"
    assert smoke["manifest_sha256"] == CODE_MANIFEST_SHA256
    assert smoke["plan_sha256"] == PLAN_SHA256
    assert smoke["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert smoke["target_data_opened"] is False
    assert config["max_seconds"] == 10800 and config["script"] == "run_exp236_source_block01_v2.py"
    return prepared, config


def physical_busy():
    source = '''import json,subprocess
raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                             '--format=csv,noheader'],text=True)
lines=[line.strip() for line in raw.splitlines() if line.strip()]
assert all(line.startswith('GPU-') for line in lines),lines
print(json.dumps({'busy_gpu_uuids':sorted(set(lines))}))
'''
    result = ssh("nsu-a100", "python3 -", source)
    return set(result["busy_gpu_uuids"])


def fair_capacity():
    queue = continuation.queue_status()
    files = continuation.local_paths(1)
    if any(files[name].exists() for name in ("reservation", "partial", "prelaunch_release", "launch")):
        raise TerminalAnomaly("Block01 artifact appeared while waiting; reconcile")
    block01_id = "exp236-horaz-source6bba-block01-v2-20260927"
    if any(row["id"] == block01_id for row in queue["requests"]):
        raise TerminalAnomaly("Block01 already has a queue request")
    waiting = [row["id"] for row in queue["requests"]
               if row["project"] != PROJECT and row["state"].startswith("WAITING")]
    pool = set(queue["pools"]["a100"]["gpus"])
    allocated = {gpu for row in queue["requests"]
                 if row["pool"] == "a100" and row["state"] in ("RESERVED", "RUNNING")
                 for gpu in row.get("gpus", [])}
    free_queue = pool - allocated
    if waiting or not free_queue:
        return {"foreign_waiting": waiting, "queue_free": len(free_queue),
                "physically_idle_queue_free": 0}
    idle = free_queue - physical_busy()
    return {"foreign_waiting": [], "queue_free": len(free_queue),
            "physically_idle_queue_free": len(idle)}


def remote_stage_gate(prepared, config):
    code = config["code"]
    run = config["run"]
    source = '''import hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@PLAN_SHA@@
assert sha(code/'source6bba_manifest.json')==@@SOURCE_MANIFEST_SHA@@
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@DUPLICATE_MAP_SHA@@
assert not run.exists()
print(json.dumps({'status':'PASS_EXP236_V2_BLOCK01_STARTER_STAGE_GATE',
 'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'run_exists':False}))
'''.replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"])).replace(
        "@@SOURCE_MANIFEST_SHA@@", repr(SOURCE_MANIFEST_SHA256)).replace(
        "@@DUPLICATE_MAP_SHA@@", repr(SOURCE_DUPLICATE_MAP_SHA))
    gate = ssh("nsu-a100", "python3 -", source)
    assert gate["status"] == "PASS_EXP236_V2_BLOCK01_STARTER_STAGE_GATE"
    assert gate["manifest_sha256"] == CODE_MANIFEST_SHA256
    assert gate["plan_sha256"] == PLAN_SHA256 and gate["run_exists"] is False
    return gate


def launch_once(state):
    assert_fresh()
    log_path = ROOT / "reports/exp236_block01_v2_fair_starter_launch_20260927.log"
    state["status"] = "INVOKING_EXP236_BLOCK01_V2_LAUNCH_ONCE"
    state["launch_attempted"] = True
    save(state)
    try:
        step = subprocess.run([sys.executable, str(LAUNCH_SCRIPT)], cwd=ROOT,
                              text=True, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log_path.write_text(out + "\n--- stderr ---\n" + err)
        state["launch_log"] = str(log_path)
        state["launch_timeout"] = True
        save(state)
        raise TerminalAnomaly("Block01 launcher timed out; reservation/run state is ambiguous") from exc
    log_path.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    state["launch_log"] = str(log_path)
    state["launch_returncode"] = step.returncode
    save(state)
    if step.returncode:
        raise TerminalAnomaly(f"Block01 launcher returned {step.returncode}; no retry")


def launch_readback():
    prepared, config, _, launch = continuation.local_block(1, launched=True)
    queue = continuation.queue_status()
    lease = continuation.lease_for(queue, 1)
    assert lease["owner"] == "biohub-agent" and lease["project"] == PROJECT
    assert lease["token"] == config["token"]
    assert lease["state"] in ("RESERVED", "RUNNING", "RELEASED")
    assert lease["alias"] == config["alias"] and config["gpu"] in launch["lease"]["gpus"]
    if lease["state"] != "RELEASED":
        assert config["gpu"] in lease["gpus"] and lease["gpus"] == launch["lease"]["gpus"]
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@);code=pathlib.Path(@@CODE@@)
config=json.loads((run/'config.json').read_text())
assert config==@@CONFIG@@
def live(pid,required):
 proc=pathlib.Path('/proc')/str(pid)
 if not proc.exists():return False
 stat=(proc/'stat').read_text();state=stat[stat.rfind(')')+2:].split()[0]
 cmd=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
 return state!='Z' and all(item in cmd for item in required)
ex=json.loads((run/'exit.json').read_text()) if (run/'exit.json').is_file() else None
print(json.dumps({'run_exists':True,'exit':ex,
 'wrapper_live':live(@@WRAPPER_PID@@,[str(code/'exp227_job.py'),str(run/'config.json')]),
 'observer_live':live(@@OBSERVER_PID@@,[str(code/'exp223_supervisor.py'),'observe'])}))
'''.replace("@@RUN@@", repr(config["run"])).replace("@@CODE@@", repr(config["code"])).replace(
        "@@CONFIG@@", repr(config)).replace(
        "@@WRAPPER_PID@@", str(launch["launch"]["wrapper"])).replace(
        "@@OBSERVER_PID@@", str(launch["launch"]["observe"]))
    observed = ssh(config["alias"], "python3 -", source)
    assert observed["run_exists"] is True
    controller_source = '''import json,pathlib
proc=pathlib.Path('/proc')/str(@@CONTROLLER_PID@@)
live=False
if proc.exists():
 stat=(proc/'stat').read_text();state=stat[stat.rfind(')')+2:].split()[0]
 cmd=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
 live=state!='Z' and @@SCRIPT@@ in cmd and 'control' in cmd and @@CONFIG_PATH@@ in cmd
print(json.dumps({'controller_live':live}))
'''.replace("@@CONTROLLER_PID@@", str(launch["control"]["controller_pid"])).replace(
        "@@SCRIPT@@", repr(config["code"] + "/exp223_supervisor.py")).replace(
        "@@CONFIG_PATH@@", repr(config["run"] + "/config.json"))
    controller = ssh("nsu-quadro", "python3 -", controller_source)
    observed["controller_live"] = controller["controller_live"]
    ex = observed["exit"]
    if ex is None:
        assert observed["wrapper_live"] and observed["observer_live"] and observed["controller_live"]
        assert lease["state"] in ("RESERVED", "RUNNING")
    else:
        assert ex["returncode"] == 0 and ex["hard_timeout"] is False
        assert lease["state"] == "RELEASED"
    return {"queue_state": lease["state"], "gpu": config["gpu"],
            "run": config["run"], "worker": observed,
            "launch_receipt_sha256": sha(continuation.local_paths(1)["launch"]),
            "prepare_receipt_sha256": sha(continuation.local_paths(1)["prepare"]),
            "manifest_sha256": prepared["stage"]["manifest_sha256"]}


def reconcile_failed_launch():
    files = continuation.local_paths(1)
    queue = continuation.queue_status()
    lease_id = "exp236-horaz-source6bba-block01-v2-20260927"
    matching = [row for row in queue["requests"] if row["id"] == lease_id]
    _, run = continuation.paths(1)
    remote = ssh("nsu-a100", "python3 -",
                 "import json,pathlib\nprint(json.dumps({'run_exists':pathlib.Path(" +
                 repr(run) + ").exists()}))\n")
    return {"queue_lease_states": [row["state"] for row in matching],
            "run_exists": remote["run_exists"],
            "reservation_receipt": files["reservation"].exists(),
            "partial_launch_receipt": files["partial"].exists(),
            "launch_receipt": files["launch"].exists(),
            "prelaunch_release_receipt": files["prelaunch_release"].exists()}


def start_continuation(state):
    assert not continuation.RECEIPT.exists()
    stdout_path = ROOT / "reports/exp236_source_v2_to_epoch10_20260927.stdout.log"
    stderr_path = ROOT / "reports/exp236_source_v2_to_epoch10_20260927.stderr.log"
    state["status"] = "STARTING_EXP236_V2_EPOCH10_CONTINUATION"
    save(state)
    with stdout_path.open("x") as out, stderr_path.open("x") as err:
        process = subprocess.Popen([sys.executable, str(CONTROLLER_SCRIPT)], cwd=ROOT,
                                   stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                   close_fds=True,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    state["continuation_pid"] = process.pid
    state["continuation_stdout"] = str(stdout_path)
    state["continuation_stderr"] = str(stderr_path)
    save(state)
    for _ in range(15):
        if continuation.RECEIPT.exists():
            child = json.loads(continuation.RECEIPT.read_text())
            if child["status"].startswith("STOPPED"):
                raise TerminalAnomaly("Continuation controller stopped during handoff")
            if process.poll() is not None:
                raise TerminalAnomaly("Continuation controller exited during handoff")
            return {"pid": process.pid, "receipt": str(continuation.RECEIPT),
                    "status": child["status"]}
        if process.poll() is not None:
            raise TerminalAnomaly("Continuation controller exited before receipt creation")
        time.sleep(1)
    raise TerminalAnomaly("Continuation process started but receipt did not appear in 15s")


def main():
    assert not RECEIPT.exists(), "Existing starter receipt must be reconciled, never restarted"
    assert_fresh()
    prepared, config = local_stage_gate()
    state = {"status": "WAITING_FOR_FAIR_EXP236_BLOCK01_V2_RESOURCE",
             "started": time.time(), "deadline_seconds": MAX_WAIT_SECONDS,
             "block01_run": config["run"], "source_only": True,
             "target_data_opened": False, "launch_attempted": False,
             "prepare_receipt_sha256": sha(continuation.local_paths(1)["prepare"])}
    claim(state)
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    errors = 0
    try:
        while time.monotonic() < deadline:
            try:
                capacity = fair_capacity()
                errors = 0
                state.pop("last_observation_error", None)
            except TerminalAnomaly:
                raise
            except Exception as exc:
                errors += 1
                state["last_observation_error"] = repr(exc)
                state["consecutive_observation_errors"] = errors
                save(state)
                if errors >= 5:
                    raise RuntimeError("Five consecutive fair-resource observation failures") from exc
                time.sleep(INTERVAL_SECONDS)
                continue
            if state.get("last_capacity") != capacity:
                state["last_capacity"] = capacity
                save(state)
            if capacity["foreign_waiting"] or not capacity["physically_idle_queue_free"]:
                time.sleep(INTERVAL_SECONDS)
                continue
            assert_fresh()
            prepared_now, config_now = local_stage_gate()
            if sha(continuation.local_paths(1)["prepare"]) != state["prepare_receipt_sha256"]:
                raise TerminalAnomaly("Block01 prepared receipt changed while waiting")
            assert prepared_now == prepared and config_now == config
            state["remote_stage_gate"] = remote_stage_gate(prepared_now, config_now)
            save(state)
            capacity = fair_capacity()
            if capacity["foreign_waiting"] or not capacity["physically_idle_queue_free"]:
                state["last_capacity"] = capacity
                save(state)
                time.sleep(INTERVAL_SECONDS)
                continue
            launch_once(state)
            state["status"] = "VERIFYING_EXP236_BLOCK01_V2_LAUNCH"
            save(state)
            state["launch_readback"] = launch_readback()
            save(state)
            state["handoff"] = start_continuation(state)
            state["status"] = "PASS_EXP236_BLOCK01_V2_FAIR_STARTER_HANDOFF"
            return
        raise TimeoutError("No fair physically idle A100 within 48h")
    except BaseException as exc:
        state["status"] = "STOPPED_EXP236_BLOCK01_V2_FAIR_STARTER"
        state["error"] = repr(exc)
        if state["launch_attempted"]:
            try:
                state["launch_failure_reconciliation"] = reconcile_failed_launch()
            except Exception as inspect_exc:
                state["launch_failure_reconciliation_error"] = repr(inspect_exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


if __name__ == "__main__":
    main()
