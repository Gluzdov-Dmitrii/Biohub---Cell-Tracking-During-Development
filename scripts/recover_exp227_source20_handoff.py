"""One-shot recovery for a fair-queue stop before EXP227 source20 graph launch.

The original handoff and its receipt remain untouched. This controller only
accepts its terminal, prelaunch fairness failure and never retries a launch.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import psutil

import continue_exp227_after_block03 as handoff
from monitor_exp213_job import QUEUE, ssh
from prepare_exp227_source_graph20 import (
    CODE, REMOTE, RUN, SOURCE_MANIFEST_SHA, TRAIN_CODE, TRAIN_MANIFEST_SHA,
    TRAIN_PLAN_SHA, TRAIN_RUN,
)
from run_exp227_source_graph20 import INNER_IDS, validate


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp227_source20_fair_recovery_20260927.json"
HANDOFF = handoff.RECEIPT
HANDOFF_SCRIPT = ROOT / "scripts/continue_exp227_after_block03.py"
GRAPH_PREPARED = handoff.GRAPH_PREPARED
GRAPH_CONFIG = handoff.GRAPH_CONFIG
GRAPH_PLAN = ROOT / "reports/exp227_source_graph20_plan_20260927.json"
GRAPH_LAUNCHED = handoff.GRAPH_LAUNCHED
SCORE_PREPARED = handoff.SCORE_PREPARED
SCORE_LAUNCHED = handoff.SCORE_LAUNCHED
SCORE_VERIFIED = handoff.SCORE_VERIFIED
GRAPH_LAUNCH = handoff.GRAPH_LAUNCH
SCORE_PREPARE = handoff.SCORE_PREPARE
SCORE_LAUNCH = handoff.SCORE_LAUNCH
SCORE_VERIFY = handoff.SCORE_VERIFY
GRAPH_LEASE = handoff.GRAPH_LEASE
TRAIN_LEASE = handoff.TRAIN_LEASE
SCORE_RUN = handoff.SCORE_RUN
PROJECT = "biohub-cell-tracking-during-development"
INTERVAL_SECONDS = 120
MAX_WAIT_SECONDS = 48 * 3600


class Reconcile(RuntimeError):
    """A claim or artifact may exist; a human must reconcile it before reuse."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def live_handoff_pids():
    found = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        try:
            args = process.info["cmdline"] or []
            if any(Path(arg.strip('"')).name == HANDOFF_SCRIPT.name for arg in args):
                found.append(process.info["pid"])
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    return found


def original_gate():
    original = json.loads(HANDOFF.read_text())
    assert original["status"] == "STOPPED_EXP227_SOURCE20_HANDOFF"
    assert original["training_run"] == TRAIN_RUN
    assert original["source_graph_run"] == RUN and original["source_score_run"] == SCORE_RUN
    assert original["source_labels_opened_before_inference"] is False
    assert original["target_labels_opened"] is False
    assert original["finished_or_stopped"] >= original["started"]
    assert original["prepare_graph_returncode"] == 0
    assert original["launch_graph_returncode"] != 0
    assert "launch_graph returned" in original["error"]
    expected_log = ROOT / "reports/exp227_source20_handoff_launch_graph_20260927.log"
    assert Path(original["launch_graph_log"]).resolve() == expected_log.resolve()
    failure = expected_log.read_text()
    assert ("Other project waiting; defer" in failure or
            "Queue returned WAITING_RESOURCE" in failure), "Not the registered fair-resource stop"
    previous = original["training_release_or_exit"]
    assert len(previous) == 2 and previous[0]["id"] == TRAIN_LEASE
    assert previous[0]["run_path"] == TRAIN_RUN
    assert handoff.check_training(*previous)
    if live_handoff_pids():
        raise Reconcile("Original source20 handoff process is still alive")
    return original, sha(HANDOFF)


def local_artifact_gate():
    for suffix in ("_reservation.json", "_partial_launch.json", "_prelaunch_release.json",
                   "_launch.json"):
        if GRAPH_CONFIG.with_name(GRAPH_CONFIG.stem + suffix).exists():
            raise Reconcile("Graph reservation or launch artifact exists: " + suffix)
    if any(path.exists() for path in (SCORE_PREPARED, SCORE_LAUNCHED, SCORE_VERIFIED)):
        raise Reconcile("Source scorer already has an artifact")
    prepared = json.loads(GRAPH_PREPARED.read_text())
    plan = json.loads(GRAPH_PLAN.read_text())
    config = json.loads(GRAPH_CONFIG.read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS"
    assert prepared["target_labels_read"] is False and prepared["movies"] == 8
    assert prepared["preflight"]["status"] == "PASS_EXP227_SOURCE20_PARENT_PREFLIGHT"
    assert [row["dataset"] for row in prepared["preflight"]["movies"]] == list(INNER_IDS)
    assert prepared["preflight"]["movies"] == plan["movies"]
    validate(plan)
    assert plan["checkpoint_sha256"] == prepared["preflight"]["checkpoint_sha256"]
    assert plan["training_result_sha256"] == prepared["preflight"]["training_result_sha256"]
    assert plan["training_history_sha256"] == prepared["preflight"]["training_history_sha256"]
    stage = prepared["stage"]
    assert stage["status"] == "STAGED_EXP227_SOURCE_GRAPH20" and stage["code"] == CODE
    assert stage["plan_sha256"] == sha(GRAPH_PLAN)
    assert stage["runner_sha256"] == sha(ROOT / "scripts/run_exp227_source_graph20.py")
    expected = {"experiment": "EXP227", "lease_id": GRAPH_LEASE,
                "token": "exp227_source_graph20_v1_20260927", "code": CODE, "run": RUN,
                "max_seconds": 3600, "cpu_affinity": "0-7",
                "script": "run_exp227_source_graph20.py",
                "arguments": [CODE + "/plan.json", "--plan-sha256", stage["plan_sha256"]]}
    assert config == expected, "Graph launcher config changed from prepared contract"
    return prepared, plan, config


def queue_status():
    return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))


def queue_gate(state, config):
    matches = [row for row in state["requests"] if row["id"] == TRAIN_LEASE]
    assert len(matches) == 1 and matches[0]["state"] == "RELEASED"
    assert matches[0]["run_path"] == TRAIN_RUN
    if any(row["id"] == GRAPH_LEASE or row["run_path"] == RUN for row in state["requests"]):
        raise Reconcile("Graph lease or queue claim exists in any state")
    pool = state["pools"]["a100"]
    allocated = {gpu for row in state["requests"]
                 if row["pool"] == "a100" and row["state"] in ("RUNNING", "RESERVED")
                 for gpu in row["gpus"]}
    free = set(pool["gpus"]) - allocated
    waiting = sorted(row["id"] for row in state["requests"]
                     if row["state"].startswith("WAITING") and
                     (row["project"] != PROJECT or row["pool"] == "a100"))
    active = [row for row in state["requests"]
              if row["pool"] == "a100" and row["state"] in ("RUNNING", "RESERVED")]
    enough = (pool["cpu"] - sum(row["cpu"] for row in active) >= 8 and
              pool["ram_gib"] - sum(row["ram_gib"] for row in active) >= 32)
    return {"foreign_or_a100_waiting": waiting, "queue_free": sorted(free),
            "resources_available": enough, "ready_for_physical_probe": not waiting and bool(free) and enough}


def remote_gate(prepared, plan):
    source = '''import hashlib,json,pathlib
train_code=pathlib.Path(@@TRAIN_CODE@@);train_run=pathlib.Path(@@TRAIN_RUN@@)
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
score_code=pathlib.Path(@@SCORE_CODE@@);score_run=pathlib.Path(@@SCORE_RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(train_code/'code_manifest.json')==@@TRAIN_MANIFEST_SHA@@
for name,digest in json.loads((train_code/'code_manifest.json').read_text()).items():
 path=(train_code/name).resolve();assert path.is_relative_to(train_code.resolve()) and sha(path)==digest,name
assert sha(train_code/'plan.json')==@@TRAIN_PLAN_SHA@@
ex=json.loads((train_run/'exit.json').read_text())
sup=json.loads((train_run/'supervision/complete.json').read_text())
ctl=json.loads((train_run/'supervision/control.json').read_text())
result_path=train_run/'output/result.json';result=json.loads(result_path.read_text())
history_path=train_run/'output/fold1/history.json';history=json.loads(history_path.read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and sup['exit']==ex
assert ctl['action']=='release' and ctl['queue']['state']=='RELEASED'
assert pathlib.Path(ctl['queue']['run_path'])==train_run
assert result['status']=='PASS_FULL_SOURCE_BLOCK_20_OF_50'
assert result['target_data_opened'] is False and not result['denied_accesses']
assert result['completed_epochs']==20 and result['planned_epochs']==50
assert result['checkpoint_reload']=='PASS_weights_only' and result['plan_sha256']==@@TRAIN_PLAN_SHA@@
assert sha(train_run/'output/contract.json')==@@TRAIN_PLAN_SHA@@
assert [row['epoch'] for row in history]==list(range(1,21)) and result['history']==history
assert sha(train_run/'output/fold1/last.pt')==result['checkpoint_sha256']
assert sha(train_run/'output/fold1/epoch_020.pt')==result['periodic_checkpoint_sha256']==@@CHECKPOINT_SHA@@
assert sha(result_path)==@@RESULT_SHA@@ and sha(history_path)==@@HISTORY_SHA@@
assert sha(train_code/'source44_manifest.json')==@@SOURCE_MANIFEST_SHA@@
manifest=json.loads((train_code/'source44_manifest.json').read_text())
assert len(manifest['train'])==63
assert [row['dataset_id'] for row in manifest['inner_validation']]==@@INNER_IDS@@
assert set(result['opened_datasets'])=={row['dataset_id'] for row in manifest['train']}|set(@@INNER_IDS@@)
assert sha(code/'code_manifest.json')==@@GRAPH_MANIFEST_SHA@@
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@GRAPH_PLAN_SHA@@
assert sha(code/'run_exp227_source_graph20.py')==@@RUNNER_SHA@@
assert sha(code/'run_exp223_inference.py')==@@HELPER_SHA@@
assert not run.exists() and not score_code.exists() and not score_run.exists()
print(json.dumps({'status':'PASS_EXP227_SOURCE20_FAIR_RECOVERY_REMOTE_GATE',
 'checkpoint_sha256':sha(train_run/'output/fold1/epoch_020.pt'),
 'training_result_sha256':sha(result_path),'training_history_sha256':sha(history_path),
 'graph_manifest_sha256':sha(code/'code_manifest.json'),'graph_plan_sha256':sha(code/'plan.json'),
 'graph_run_absent':True,'score_run_absent':True}))
'''.replace("@@TRAIN_CODE@@", repr(TRAIN_CODE)).replace("@@TRAIN_RUN@@", repr(TRAIN_RUN)).replace(
        "@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@SCORE_CODE@@", repr(REMOTE + "/code/exp227_source_graph20_scorer_v1_20260927")).replace(
        "@@SCORE_RUN@@", repr(SCORE_RUN)).replace("@@TRAIN_MANIFEST_SHA@@", repr(TRAIN_MANIFEST_SHA)).replace(
        "@@TRAIN_PLAN_SHA@@", repr(TRAIN_PLAN_SHA)).replace("@@SOURCE_MANIFEST_SHA@@", repr(SOURCE_MANIFEST_SHA)).replace(
        "@@CHECKPOINT_SHA@@", repr(plan["checkpoint_sha256"])).replace(
        "@@RESULT_SHA@@", repr(plan["training_result_sha256"])).replace(
        "@@HISTORY_SHA@@", repr(plan["training_history_sha256"])).replace(
        "@@INNER_IDS@@", repr(list(INNER_IDS))).replace(
        "@@GRAPH_MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@GRAPH_PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"])).replace(
        "@@RUNNER_SHA@@", repr(prepared["stage"]["runner_sha256"])).replace(
        "@@HELPER_SHA@@", repr(sha(ROOT / "scripts/run_exp223_inference.py")))
    observed = ssh("nsu-a100", "python3 -", source)
    assert observed["status"] == "PASS_EXP227_SOURCE20_FAIR_RECOVERY_REMOTE_GATE"
    assert observed["checkpoint_sha256"] == plan["checkpoint_sha256"]
    assert observed["training_result_sha256"] == plan["training_result_sha256"]
    assert observed["training_history_sha256"] == plan["training_history_sha256"]
    assert observed["graph_manifest_sha256"] == prepared["stage"]["manifest_sha256"]
    assert observed["graph_plan_sha256"] == prepared["stage"]["plan_sha256"]
    assert observed["graph_run_absent"] is True and observed["score_run_absent"] is True
    return observed


def remote_run_absent():
    source = '''import json,pathlib
print(json.dumps({'graph_run_absent':not pathlib.Path(@@GRAPH_RUN@@).exists(),
 'score_run_absent':not pathlib.Path(@@SCORE_RUN@@).exists(),
 'score_code_absent':not pathlib.Path(@@SCORE_CODE@@).exists()}))
'''.replace("@@GRAPH_RUN@@", repr(RUN)).replace("@@SCORE_RUN@@", repr(SCORE_RUN)).replace(
        "@@SCORE_CODE@@", repr(REMOTE + "/code/exp227_source_graph20_scorer_v1_20260927"))
    found = ssh("nsu-a100", "python3 -", source)
    if found != {"graph_run_absent": True, "score_run_absent": True, "score_code_absent": True}:
        raise Reconcile("Graph or scorer remote artifact already exists")


def physical_idle(free):
    source = '''import json,subprocess
raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                             '--format=csv,noheader'],text=True)
lines=[line.strip() for line in raw.splitlines() if line.strip()]
assert all(line.startswith('GPU-') for line in lines),lines
print(json.dumps({'busy_gpu_uuids':sorted(set(lines))}))
'''
    observed = ssh("nsu-a100", "python3 -", source)
    busy = observed["busy_gpu_uuids"]
    assert isinstance(busy, list) and all(isinstance(item, str) and item.startswith("GPU-") for item in busy)
    return sorted(set(free) - set(busy))


def fair_observation(config):
    local_artifact_gate()
    remote_run_absent()
    queue = queue_status()
    available = queue_gate(queue, config)
    idle = physical_idle(available["queue_free"]) if available["ready_for_physical_probe"] else []
    available["physically_idle"] = idle
    return available


def wait_fair(config, state, deadline):
    while time.monotonic() < deadline:
        assert sha(HANDOFF) == state["original_handoff_sha256"], "Original handoff receipt changed"
        if live_handoff_pids():
            raise Reconcile("Original handoff restarted while recovery waited")
        observed = fair_observation(config)
        if state.get("last_resource_observation") != observed:
            state["last_resource_observation"] = observed
            save(state)
        if observed["physically_idle"]:
            return observed
        time.sleep(min(INTERVAL_SECONDS, max(0, deadline - time.monotonic())))
    raise TimeoutError("No fair, physically idle A100 within 48-hour recovery bound")


def run_step(name, script, state, timeout=300):
    log = ROOT / f"reports/exp227_source20_fair_recovery_{name}_20260927.log"
    assert not log.exists(), "Existing recovery step log: reconcile"
    state[name + "_attempted"] = True
    state["status"] = "INVOKING_" + name.upper() + "_ONCE"
    save(state)
    try:
        step = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True,
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log.write_text(out + "\n--- stderr ---\n" + err)
        state[name + "_log"] = str(log)
        state[name + "_timeout"] = True
        save(state)
        raise Reconcile(name + " timed out; launched state may be ambiguous") from exc
    log.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    state[name + "_log"] = str(log)
    state[name + "_returncode"] = step.returncode
    save(state)
    if step.returncode:
        raise Reconcile(f"{name} returned {step.returncode}; no retry")


def graph_launch_readback(prepared, expected):
    launched = json.loads(GRAPH_LAUNCHED.read_text())
    config = json.loads(GRAPH_CONFIG.read_text())
    reservation = json.loads(GRAPH_CONFIG.with_name(
        GRAPH_CONFIG.stem + "_reservation.json").read_text())
    partial = json.loads(GRAPH_CONFIG.with_name(
        GRAPH_CONFIG.stem + "_partial_launch.json").read_text())
    assert set(config) == set(expected) | {"gpu", "alias"}
    assert all(config[key] == value for key, value in expected.items())
    assert launched["config"] == config
    assert reservation == {"lease": launched["lease"], "config": expected}
    assert partial == {"lease": launched["lease"], "launch": launched["launch"],
                       "config": config}
    assert launched["lease"]["state"] == "RESERVED"
    assert launched["lease"]["gpus"] == [config["gpu"]]
    assert launched["lease"]["alias"] == config["alias"]
    assert launched["lease"]["id"] == GRAPH_LEASE
    assert launched["lease"]["run_path"] == RUN
    assert launched["lease"]["token"] == config["token"]
    assert all(isinstance(launched["launch"][name], int) and launched["launch"][name] > 0
               for name in ("wrapper", "observe"))
    assert isinstance(launched["control"]["controller_pid"], int)
    lease = handoff.queue_lease(GRAPH_LEASE, RUN)
    assert lease["token"] == config["token"] and lease["state"] in ("RESERVED", "RUNNING", "RELEASED")
    assert lease["gpus"] == [config["gpu"]]
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
print(json.dumps({'run_exists':run.is_dir(),
 'config_matches':json.loads((run/'config.json').read_text())==@@CONFIG@@ if (run/'config.json').is_file() else False}))
'''.replace("@@RUN@@", repr(RUN)).replace("@@CONFIG@@", repr(config))
    observed = ssh(config["alias"], "python3 -", source)
    assert observed == {"run_exists": True, "config_matches": True}
    assert prepared["stage"]["plan_sha256"] == config["arguments"][2]
    return {"lease": lease, "gpu": config["gpu"], "run": observed,
            "launch_receipt_sha256": sha(GRAPH_LAUNCHED)}


def graph_probe():
    config = json.loads(GRAPH_CONFIG.read_text())
    queue = queue_status()
    matches = [row for row in queue["requests"] if row["id"] == GRAPH_LEASE or
               row["run_path"] == RUN]
    if len(matches) != 1 or matches[0]["id"] != GRAPH_LEASE:
        raise Reconcile("Graph queue lease or run claim is ambiguous")
    lease = matches[0]
    if (lease["run_path"] != RUN or lease["token"] != config["token"] or
            lease["gpus"] != [config["gpu"]] or lease["alias"] != config["alias"]):
        raise Reconcile("Graph queue lease identity changed")
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
print(json.dumps({'run_exists':run.is_dir()}))
'''.replace("@@RUN@@", repr(RUN))
    if ssh(config["alias"], "python3 -", source) != {"run_exists": True}:
        raise Reconcile("Graph remote run disappeared or became ambiguous")
    return lease, handoff.probe_gpu_run(RUN, config["alias"])


def score_probe():
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
print(json.dumps({'run_exists':run.is_dir()}))
'''.replace("@@RUN@@", repr(SCORE_RUN))
    if ssh("nsu-quadro", "python3 -", source) != {"run_exists": True}:
        raise Reconcile("Source scorer remote run disappeared or became ambiguous")
    return handoff.probe_score()


def wait_verified(name, seconds, interval, probe, check, state):
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
            state[name + "_consecutive_observation_errors"] = errors
            save(state)
            if errors >= 5:
                raise Reconcile("Five consecutive " + name + " observation failures") from exc
            time.sleep(interval)
            continue
        if check(observed):
            state[name + "_verified"] = observed
            save(state)
            return
        snapshot = json.dumps(observed, sort_keys=True)
        if state.get(name + "_last_snapshot") != snapshot:
            state[name + "_last_snapshot"] = snapshot
            save(state)
        time.sleep(interval)
    raise TimeoutError(name + " did not verify before its finite deadline")


def main():
    original, original_sha = original_gate()
    prepared, plan, config = local_artifact_gate()
    queue_gate(queue_status(), config)
    remote_gate(prepared, plan)
    state = {"status": "WAITING_FOR_FAIR_A100_FOR_EXP227_SOURCE20_GRAPHS",
             "pid": os.getpid(), "process_create_time": psutil.Process(os.getpid()).create_time(),
             "started": time.time(), "original_handoff_sha256": original_sha,
             "original_status": original["status"], "training_run": TRAIN_RUN,
             "source_graph_run": RUN, "source_score_run": SCORE_RUN,
             "target_data_opened": False, "target_labels_opened": False,
             "source_labels_opened_before_inference": False, "kaggle_post": False,
             "graph_launch_attempted": False, "score_launch_attempted": False}
    claim(state)
    try:
        deadline = time.monotonic() + MAX_WAIT_SECONDS
        wait_fair(config, state, deadline)
        assert sha(HANDOFF) == original_sha
        original_gate()
        prepared, plan, config = local_artifact_gate()
        available = queue_gate(queue_status(), config)
        remote_gate(prepared, plan)
        assert available["ready_for_physical_probe"]
        assert physical_idle(available["queue_free"]), "No physically idle fair A100 at launch gate"
        run_step("graph_launch", GRAPH_LAUNCH, state)
        assert GRAPH_LAUNCHED.is_file(), "Graph launcher succeeded without a receipt"
        state["graph_launch_readback"] = graph_launch_readback(prepared, config)
        state["status"] = "WAITING_FOR_EXP227_SOURCE20_GRAPH_RELEASE"
        save(state)
        wait_verified("graph", 5400, 90, graph_probe,
                      lambda pair: handoff.check_graph(*pair), state)
        state["status"] = "SOURCE20_GRAPHS_RELEASED_PREPARING_SCORER"
        save(state)
        run_step("score_prepare", SCORE_PREPARE, state)
        assert SCORE_PREPARED.is_file()
        state["status"] = "SOURCE20_SCORER_STAGED_LAUNCHING"
        save(state)
        run_step("score_launch", SCORE_LAUNCH, state)
        assert SCORE_LAUNCHED.is_file()
        state["status"] = "WAITING_FOR_SOURCE20_OFFICIAL_SCORE"
        save(state)
        wait_verified("score", 2700, 90, score_probe, handoff.check_score, state)
        state["status"] = "SOURCE20_OFFICIAL_SCORER_EXITED_VERIFYING"
        save(state)
        run_step("score_verify", SCORE_VERIFY, state)
        verified = json.loads(SCORE_VERIFIED.read_text())
        assert verified["status"] == "VERIFIED_EXP227_SOURCE20_OFFICIAL"
        assert verified["source_labels_read"] is True and verified["target_labels_read"] is False
        assert verified["rows"] == 8 and math.isfinite(verified["source_score"])
        assert sha(HANDOFF) == original_sha, "Original handoff receipt changed"
        state["source_score_receipt"] = str(SCORE_VERIFIED)
        state["source_score_receipt_sha256"] = sha(SCORE_VERIFIED)
        state["status"] = "PASS_EXP227_SOURCE20_OFFICIAL_FAIR_RECOVERY"
    except BaseException as exc:
        state["status"] = "STOPPED_EXP227_SOURCE20_FAIR_RECOVERY"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


if __name__ == "__main__":
    main()
