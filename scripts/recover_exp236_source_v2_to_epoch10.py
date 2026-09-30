"""Recover EXP236 after the stopped controller's Windows plan-newline check.

Default invocation is read-only. ``--launch`` is required to claim a fresh
controller receipt and continue the already staged block02 through epoch10.
The original stopped controller and all of its receipts remain untouched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

import continue_exp236_source_v2_to_epoch10 as chain
from monitor_exp213_job import ssh
from prepare_exp236_source_resume_v2 import paths
from run_exp236_source_resume_v2 import SOURCE_DUPLICATE_MAP_SHA


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = chain.RECEIPT
ORIGINAL_SCRIPT = ROOT / "scripts/continue_exp236_source_v2_to_epoch10.py"
RECEIPT = ROOT / "reports/exp236_source_v2_epoch10_recovery_20260927.json"
PROJECT = chain.PROJECT


class Reconcile(RuntimeError):
    """An observed claim or artifact requires review before any launch."""


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
    assert original["status"] == "STOPPED_EXP236_SOURCE_V2_CONTINUATION"
    assert original["source_run"] == paths(1)[1] and original["final_epoch"] == 10
    assert original["target_data_opened"] is False
    assert original["finished_or_stopped"] >= original["started"]
    assert original["error"] == "AssertionError()"
    assert original["prepare_block02_returncode"] == 0
    assert "launch_block02_returncode" not in original
    assert "block02_launch_sha256" not in original
    log = ROOT / "reports/exp236_source_v2_to_epoch10_prepare_block02_20260927.log"
    assert Path(original["prepare_block02_log"]).resolve() == log.resolve()
    assert "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS" in log.read_text()
    if live_original_pids():
        raise Reconcile("Original EXP236 continuation process is still alive")
    observed = chain.block_probe(1)
    assert chain.block_released(1, observed)
    assert observed == original["block01_release_verified"]
    audited = chain.audit_block(1)
    assert audited == original["block01_audit"]
    return original, sha(ORIGINAL), audited


def unused_artifacts(block):
    files = chain.local_paths(block)
    for name in ("launch", "reservation", "partial", "prelaunch_release"):
        if files[name].exists():
            raise Reconcile(f"Block{block:02d} has existing {name} artifact")
    return files


def local_stage_gate(block, parent_audit):
    files = unused_artifacts(block)
    prepared, config, plan, _ = chain.local_block(block, launched=False)
    assert prepared["parent_prepare_sha256"] == sha(chain.local_paths(block - 1)["prepare"])
    assert prepared["preflight"]["checkpoint_sha256"] == parent_audit["checkpoint_sha256"]
    assert prepared["preflight"]["history_sha256"] == parent_audit["history_sha256"]
    assert prepared["preflight"]["result_sha256"] == parent_audit["result_sha256"]
    assert prepared["preflight"]["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    for name in ("checkpoint", "history", "result"):
        assert plan[f"parent_{name}_sha256"] == parent_audit[f"{name}_sha256"]
    assert plan["parent_plan_sha256"] == parent_audit["plan_sha256"]
    assert plan["parent_code_manifest_sha256"] == parent_audit["manifest_sha256"]
    code, run = paths(block)
    assert config == {
        "experiment": "EXP236",
        "lease_id": f"exp236-horaz-source6bba-block{block:02d}-v2-20260927",
        "token": f"exp236_horaz_source6bba_block{block:02d}_v2_20260927",
        "code": code, "run": run, "max_seconds": 10800,
        "cpu_affinity": "0-7", "script": "run_exp236_source_resume_v2.py",
        "arguments": [code + "/plan.json", "--plan-sha256",
                      prepared["stage"]["plan_sha256"]],
    }
    runner = ROOT / "scripts/run_exp236_source_resume_v2.py"
    assert hashlib.sha256(runner.read_text().encode()).hexdigest() == (
        prepared["stage"]["runner_sha256"])
    return files, prepared, config, plan


def remote_stage_gate(block, prepared):
    code, run = paths(block)
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
assert sha(code/'run_exp236_source_resume_v2.py')==@@RUNNER_SHA@@
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@MAP_SHA@@
print(json.dumps({'status':'PASS_EXP236_RECOVERY_STAGE_GATE',
 'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'run_absent':True}))
'''.replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"])).replace(
        "@@RUNNER_SHA@@", repr(prepared["stage"]["runner_sha256"])).replace(
        "@@MAP_SHA@@", repr(SOURCE_DUPLICATE_MAP_SHA))
    observed = ssh("nsu-a100", "python3 -", source)
    assert observed == {
        "status": "PASS_EXP236_RECOVERY_STAGE_GATE",
        "manifest_sha256": prepared["stage"]["manifest_sha256"],
        "plan_sha256": prepared["stage"]["plan_sha256"],
        "run_absent": True,
    }
    return observed


def downstream_absent():
    for block in (3, 4):
        if any(path.exists() for path in chain.local_paths(block).values()):
            raise Reconcile(f"Block{block:02d} already has local artifacts")
    source = '''import json,pathlib
paths=@@PATHS@@
print(json.dumps({'absent':all(not pathlib.Path(path).exists() for path in paths)}))
'''.replace("@@PATHS@@", repr([path for block in (3, 4) for path in paths(block)]))
    if ssh("nsu-a100", "python3 -", source) != {"absent": True}:
        raise Reconcile("Block03 or block04 has remote code/run artifacts")


def queue_gate(parent_block, child_block):
    queue = chain.queue_status()
    parent = chain.lease_for(queue, parent_block)
    if parent["state"] != "RELEASED":
        raise Reconcile(f"Block{parent_block:02d} lease is no longer RELEASED")
    _, run = paths(child_block)
    lease_id = f"exp236-horaz-source6bba-block{child_block:02d}-v2-20260927"
    if any(row["id"] == lease_id or row["run_path"] == run for row in queue["requests"]):
        raise Reconcile(f"Block{child_block:02d} already has a queue claim")
    return queue


def stage_gate(block, parent_audit):
    files, prepared, config, _ = local_stage_gate(block, parent_audit)
    remote = remote_stage_gate(block, prepared)
    queue_gate(block - 1, block)
    return {"block": block, "prepare_sha256": sha(files["prepare"]),
            "local_plan_raw_sha256": sha(files["plan"]),
            "staged_plan_sha256": prepared["stage"]["plan_sha256"],
            "manifest_sha256": remote["manifest_sha256"],
            "run_absent": remote["run_absent"], "lease_id": config["lease_id"]}


def preflight():
    if RECEIPT.exists():
        raise Reconcile("Existing recovery receipt must be reconciled")
    _, original_sha, audited = original_gate()
    downstream_absent()
    stage = stage_gate(2, audited)
    return {"status": "PASS_EXP236_SOURCE_V2_RECOVERY_PREFLIGHT",
            "original_receipt_sha256": original_sha, "block01_audit": audited,
            "block02_stage": stage, "target_data_opened": False}


def fair_probe(parent_block, child_block):
    queue = queue_gate(parent_block, child_block)
    requests = queue["requests"]
    waiting = sorted(row["id"] for row in requests
                     if row["state"].startswith("WAITING") and
                     (row["project"] != PROJECT or row["pool"] == "a100"))
    pool = queue["pools"]["a100"]
    active = [row for row in requests if row["pool"] == "a100" and
              row["state"] in ("RUNNING", "RESERVED")]
    occupied = {gpu for row in active for gpu in row.get("gpus", [])}
    free = sorted(set(pool["gpus"]) - occupied)
    capacity = (pool["cpu"] - sum(row["cpu"] for row in active) >= 8 and
                pool["ram_gib"] - sum(row["ram_gib"] for row in active) >= 32)
    idle = []
    if not waiting and free and capacity:
        source = '''import json,subprocess
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                              '--format=csv,noheader'],text=True)
lines={line.strip() for line in busy.splitlines() if line.strip()}
assert all(line.startswith('GPU-') for line in lines)
print(json.dumps({'busy':sorted(lines)}))
'''
        busy = ssh("nsu-a100", "python3 -", source)["busy"]
        idle = sorted(set(free) - set(busy))
    return {"waiting": waiting, "queue_free": free, "idle": idle,
            "capacity": capacity, "ready": not waiting and bool(idle) and capacity}


def wait_for(name, seconds, probe, check, state):
    deadline = time.monotonic() + seconds
    errors = 0
    while time.monotonic() < deadline:
        try:
            observed = probe()
            errors = 0
        except Reconcile:
            raise
        except Exception as exc:
            errors += 1
            state[name + "_observation_error"] = repr(exc)
            state[name + "_observation_failures"] = errors
            save(state)
            if errors >= 5:
                raise RuntimeError(f"Five consecutive {name} observation failures") from exc
            time.sleep(chain.INTERVAL_SECONDS)
            continue
        if check(observed):
            state[name + "_verified"] = observed
            save(state)
            return observed
        compact = json.dumps(observed, sort_keys=True)
        if state.get(name + "_last_snapshot") != compact:
            state[name + "_last_snapshot"] = compact
            save(state)
        time.sleep(chain.INTERVAL_SECONDS)
    raise TimeoutError(f"{name} did not verify within {seconds}s")


def step(name, script, args, timeout, state):
    log = ROOT / f"reports/exp236_source_v2_epoch10_recovery_{name}_20260927.log"
    if log.exists():
        raise Reconcile(f"Existing {name} step log must be reconciled")
    state[name + "_attempted"] = True
    save(state)
    try:
        completed = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args],
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
    state = {"status": "WAITING_FOR_FAIR_EXP236_BLOCK02_V2_RESOURCE",
             "started": time.time(), "pid": os.getpid(),
             "original_receipt_sha256": prepared["original_receipt_sha256"],
             "block01_audit": prepared["block01_audit"],
             "block02_stage": prepared["block02_stage"],
             "target_data_opened": False}
    claim(state)
    try:
        parent_audit = prepared["block01_audit"]
        for block in (2, 3, 4):
            parent = block - 1
            if block > 2:
                state["status"] = f"PREPARING_EXP236_BLOCK{block:02d}_V2"
                save(state)
                step(f"prepare_block{block:02d}", "prepare_exp236_source_resume_v2.py",
                     ["--parent-block", str(parent)], 900, state)
            evidence = stage_gate(block, parent_audit)
            state[f"block{block:02d}_stage"] = evidence
            state["status"] = f"WAITING_FOR_FAIR_EXP236_BLOCK{block:02d}_V2_RESOURCE"
            save(state)
            wait_for(f"block{block:02d}_resource", chain.RESOURCE_WAIT_SECONDS,
                     lambda p=parent, b=block: fair_probe(p, b),
                     lambda observed: observed["ready"], state)
            assert sha(ORIGINAL) == prepared["original_receipt_sha256"]
            assert stage_gate(block, parent_audit) == evidence
            if not fair_probe(parent, block)["ready"]:
                raise Reconcile("Fair physical A100 changed before launch")
            state["status"] = f"LAUNCHING_EXP236_BLOCK{block:02d}_V2"
            save(state)
            step(f"launch_block{block:02d}", "launch_exp236_source_resume_v2.py",
                 ["--block", str(block)], 300, state)
            chain.local_block(block, launched=True)
            state[f"block{block:02d}_launch_sha256"] = sha(chain.local_paths(block)["launch"])
            state["status"] = f"WAITING_FOR_EXP236_BLOCK{block:02d}_V2_RELEASE"
            save(state)
            wait_for(f"block{block:02d}_release", chain.BLOCK_RUN_WAIT_SECONDS,
                     lambda b=block: chain.block_probe(b),
                     lambda observed, b=block: chain.block_released(b, observed), state)
            state["status"] = f"AUDITING_EXP236_BLOCK{block:02d}_V2"
            save(state)
            audited = chain.audit_block(block, parent_audit)
            state[f"block{block:02d}_audit"] = audited
            save(state)
            parent_audit = audited
        state["status"] = "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
        state["final_audit"] = parent_audit
    except BaseException as exc:
        state["status"] = "STOPPED_EXP236_SOURCE_V2_RECOVERY"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch", action="store_true",
                        help="claim a fresh receipt and continue training when fair")
    args = parser.parse_args()
    prepared = preflight()
    if not args.launch:
        print(json.dumps(prepared))
        return
    run(prepared)


if __name__ == "__main__":
    main()
