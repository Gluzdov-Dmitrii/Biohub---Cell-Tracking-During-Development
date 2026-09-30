"""Finite EXP236 v2 source6bba handoff: released epochs 3 -> 6 -> 9 -> 10.

Start only after the separately authorized block01 v2 launch. This controller
never starts block01, scores graphs, reads target data, or submits to Kaggle.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

from monitor_exp213_job import QUEUE, ssh
from prepare_exp236_source_resume_v2 import SCHEDULE, paths
from run_exp236_source_resume_v2 import (
    REMOTE, SOURCE_BUNDLE_SHA, SOURCE_DUPLICATE_MAP_SHA, SOURCE_MANIFEST_SHA,
)
from prepare_exp236_source_block01_v2 import (
    CODE_MANIFEST_SHA256 as BLOCK01_MANIFEST_SHA,
    PLAN_SHA256 as BLOCK01_PLAN_SHA,
)


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp236_source_v2_to_epoch10_20260927.json"
EPOCHS = {1: 3, 2: 6, 3: 9, 4: 10}
INTERVAL_SECONDS = 120
BLOCK01_LAUNCH_WAIT_SECONDS = 43200
RESOURCE_WAIT_SECONDS = 21600
BLOCK_RUN_WAIT_SECONDS = 14400
PROJECT = "biohub-cell-tracking-during-development"


class TerminalAnomaly(RuntimeError):
    """Observed state that needs reconciliation, not another poll."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def staged_plan_sha(path, block):
    """Hash the bytes written by the Linux stage, not Windows newline expansion.

    Block01's frozen local plan was transferred byte-for-byte. Resume plans
    were staged from ``plan_text`` on Linux, then written locally with
    ``Path.write_text``; that second write expands LF to CRLF on Windows.
    """
    raw = Path(path).read_bytes()
    if block == 1:
        return hashlib.sha256(raw).hexdigest()
    canonical = raw.replace(b"\r\n", b"\n")
    assert b"\r" not in canonical, "Resume plan contains an unexpected CR byte"
    return hashlib.sha256(canonical).hexdigest()


def local_paths(block):
    stem = f"exp236_source_block{block:02d}_v2"
    config = ROOT / f"reports/{stem}_config_20260927.json"
    return {"config": config,
            "prepare": ROOT / f"reports/{stem}_prepare_20260927.json",
            "plan": (ROOT / "work/exp236_source6bba_v2_20260927/plan.json" if block == 1
                     else ROOT / f"reports/{stem}_plan_20260927.json"),
            "launch": config.with_name(config.stem + "_launch.json"),
            "reservation": config.with_name(config.stem + "_reservation.json"),
            "partial": config.with_name(config.stem + "_partial_launch.json"),
            "prelaunch_release": config.with_name(config.stem + "_prelaunch_release.json")}


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def queue_status():
    return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))


def lease_for(queue, block):
    _, run = paths(block)
    lease_id = f"exp236-horaz-source6bba-block{block:02d}-v2-20260927"
    matching = [row for row in queue["requests"] if row["id"] == lease_id]
    if len(matching) != 1:
        raise TerminalAnomaly(f"Expected one lease for block{block:02d}")
    lease = matching[0]
    if lease["run_path"] != run or lease["pool"] != "a100":
        raise TerminalAnomaly(f"Block{block:02d} queue lease changed identity")
    return lease


def local_block(block, launched):
    files = local_paths(block)
    prepared = json.loads(files["prepare"].read_text())
    config = json.loads(files["config"].read_text())
    code, run = paths(block)
    assert prepared["status"] == ("PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS"
                                  if block == 1 else
                                  "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS")
    assert prepared["target_data_opened"] is False
    assert prepared["stage"]["status"] == ("STAGED_EXP236_SOURCE6BBA_BLOCK01_V2"
                                           if block == 1 else "STAGED_EXP236_SOURCE_RESUME_V2")
    assert prepared["stage"]["code"] == code
    assert config["experiment"] == "EXP236" and config["code"] == code and config["run"] == run
    assert config["lease_id"] == f"exp236-horaz-source6bba-block{block:02d}-v2-20260927"
    assert config["arguments"] == [code + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert staged_plan_sha(files["plan"], block) == prepared["stage"]["plan_sha256"]
    plan = json.loads(files["plan"].read_text())
    assert plan["experiment"] == "EXP236" and plan["block_end_epoch"] == EPOCHS[block]
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    assert plan["fold"] == 0 and plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert plan["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert len(plan["train"]) == 115 and len(plan["inner_validation"]) == 11
    assert plan["data_root"] == REMOTE + "/data/exp213_source_view_20260912"
    assert all(row["dataset_id"].startswith("6bba_") and
               row["zarr_path"] == plan["data_root"] + "/" + row["dataset_id"] + ".zarr" and
               row["geff_path"] == plan["data_root"] + "/" + row["dataset_id"] + ".geff"
               for row in plan["train"] + plan["inner_validation"])
    if block == 1:
        assert prepared["stage"]["manifest_sha256"] == BLOCK01_MANIFEST_SHA
        assert prepared["stage"]["plan_sha256"] == BLOCK01_PLAN_SHA
    else:
        assert prepared["parent_block"] == block - 1 and prepared["next_block"] == block
        assert prepared["preflight"]["status"] == "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT"
        assert prepared["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    if launched:
        launch = json.loads(files["launch"].read_text())
        assert launch["config"] == config
        assert launch["lease"]["id"] == config["lease_id"]
        assert launch["lease"]["state"] == "RESERVED"
        assert launch["source_duplicate_audits"] == prepared["source_duplicate_audits"]
        assert config["alias"] == launch["lease"]["alias"]
        return prepared, config, plan, launch
    return prepared, config, plan, None


def wait_for(name, seconds, probe, check, state):
    deadline = time.monotonic() + seconds
    errors = 0
    while time.monotonic() < deadline:
        try:
            observed = probe()
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
                raise RuntimeError(f"Five consecutive {name} observation failures") from exc
            time.sleep(INTERVAL_SECONDS)
            continue
        if check(observed):
            state[name + "_verified"] = observed
            save(state)
            return observed
        compact = json.dumps(observed, sort_keys=True)
        if state.get(name + "_last_snapshot") != compact:
            state[name + "_last_snapshot"] = compact
            save(state)
        time.sleep(INTERVAL_SECONDS)
    raise TimeoutError(f"{name} did not reach its verified state within {seconds}s")


def block01_launch_probe():
    files = local_paths(1)
    if files["prelaunch_release"].exists():
        raise TerminalAnomaly("Block01 prelaunch was rejected")
    if not files["launch"].is_file():
        for name in ("reservation", "partial"):
            if files[name].exists() and time.time() - files[name].stat().st_mtime > 900:
                raise TerminalAnomaly(f"Block01 has a stale {name} without a launch receipt")
        return {"launch_receipt": False,
                "reservation": files["reservation"].exists(),
                "partial": files["partial"].exists()}
    try:
        prepared, config, _, _ = local_block(1, launched=True)
    except Exception as exc:
        raise TerminalAnomaly("Block01 launch receipt or config failed local validation") from exc
    return {"launch_receipt": True, "lease_id": config["lease_id"],
            "run": config["run"], "prepare_sha256": sha(files["prepare"]),
            "launch_sha256": sha(files["launch"]),
            "manifest_sha256": prepared["stage"]["manifest_sha256"]}


def run_probe(block, alias):
    _, run = paths(block)
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
history=read('output/fold0/history.json')
result=read('output/result.json');ex=read('exit.json')
complete=read('supervision/complete.json');control=read('supervision/control.json')
print(json.dumps({'epochs':len(history) if history else None,
 'last_epoch':history[-1]['epoch'] if history else None,
 'result_status':result.get('status') if result else None,
 'completed_epochs':result.get('completed_epochs') if result else None,
 'target_data_opened':result.get('target_data_opened') if result else None,
 'exit':ex,'complete_status':complete.get('status') if complete else None,
 'supervision_exit_matches':complete.get('exit')==ex if complete and ex else None,
 'control_state':control.get('queue',{}).get('state') if control else None,
 'control_run_matches':pathlib.Path(control['queue']['run_path']).resolve()==run.resolve() if control else None}))
'''.replace("@@RUN@@", repr(run))
    return ssh(alias, "python3 -", source)


def block_probe(block):
    try:
        _, config, _, _ = local_block(block, launched=True)
    except Exception as exc:
        raise TerminalAnomaly(f"Block{block:02d} local launch evidence changed") from exc
    queue = queue_status()
    lease = lease_for(queue, block)
    if lease["alias"] != config["alias"]:
        raise TerminalAnomaly(f"Block{block:02d} queue alias differs from launch receipt")
    return {"queue_state": lease["state"], "remote": run_probe(block, config["alias"])}


def block_released(block, observed):
    lease_state = observed["queue_state"]
    remote = observed["remote"]
    if lease_state not in ("RESERVED", "RUNNING", "RELEASED"):
        raise RuntimeError(f"Block{block:02d} lease entered {lease_state}")
    ex = remote["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["hard_timeout"] is not False):
        raise RuntimeError(f"Block{block:02d} worker failed or timed out")
    status = remote["result_status"]
    allowed_running = ("RUNNING_EXP236_SOURCE_BLOCK01" if block == 1
                       else "RUNNING_EXP236_SOURCE_RESUME")
    expected = f"PASS_EXP236_SOURCE_BLOCK_{EPOCHS[block]}_OF_50"
    if status is not None and status not in (allowed_running, expected):
        raise RuntimeError(f"Block{block:02d} result anomaly: {status}")
    if remote["target_data_opened"] not in (None, False):
        raise RuntimeError(f"Block{block:02d} opened or attempted target data")
    if lease_state == "RELEASED":
        assert ex is not None and ex["returncode"] == 0
        assert remote["complete_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert remote["supervision_exit_matches"] is True
        assert remote["control_state"] == "RELEASED" and remote["control_run_matches"] is True
        assert status == expected and remote["completed_epochs"] == EPOCHS[block]
        assert remote["epochs"] == remote["last_epoch"] == EPOCHS[block]
        assert remote["target_data_opened"] is False
        return True
    return False


def audit_block(block, parent_audit=None):
    prepared, config, plan, _ = local_block(block, launched=True)
    if parent_audit is not None:
        assert plan["parent_completed_epochs"] == EPOCHS[block - 1]
        assert plan["parent_checkpoint_sha256"] == parent_audit["checkpoint_sha256"]
        assert plan["parent_history_sha256"] == parent_audit["history_sha256"]
        assert plan["parent_result_sha256"] == parent_audit["result_sha256"]
        assert plan["parent_plan_sha256"] == parent_audit["plan_sha256"]
        assert plan["parent_code_manifest_sha256"] == parent_audit["manifest_sha256"]
    code, run = paths(block)
    source = '''import hashlib,json,math,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@PLAN_SHA@@
assert sha(code/'source6bba_manifest.json')==@@SOURCE_MANIFEST_SHA@@
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@DUPLICATE_MAP_SHA@@
plan=json.loads((code/'plan.json').read_text())
assert plan['experiment']=='EXP236' and plan['block_end_epoch']==@@END@@
assert plan['source_embryo']=='6bba' and plan['target_embryo']=='44b6' and plan['fold']==0
assert plan['source_bundle_sha256']==@@SOURCE_BUNDLE_SHA@@
assert plan['data_root']==@@DATA_ROOT@@
assert plan['source_duplicate_policy']=='exclude_all_effective_duplicate_windows_v2'
assert plan['source_duplicate_map_sha256']==@@DUPLICATE_MAP_SHA@@
assert plan['excluded_pairs_by_split']=={'train':824,'inner_validation':103}
assert plan['removed_sampled_windows_by_split']=={'train':809,'inner_validation':101}
assert len(plan['train'])==115 and len(plan['inner_validation'])==11
ids={row['dataset_id'] for row in plan['train']+plan['inner_validation']}
assert len(ids)==126 and all(name.startswith('6bba_') for name in ids)
assert all(row['zarr_path']==plan['data_root']+'/'+row['dataset_id']+'.zarr' and
           row['geff_path']==plan['data_root']+'/'+row['dataset_id']+'.geff'
           for row in plan['train']+plan['inner_validation'])
config=json.loads((run/'config.json').read_text())
assert config['code']==str(code) and config['run']==str(run)
result_path=run/'output/result.json';result=json.loads(result_path.read_text())
assert result['status']=='PASS_EXP236_SOURCE_BLOCK_@@END@@_OF_50'
assert result['completed_epochs']==@@END@@ and result['planned_epochs']==50
assert result['target_data_opened'] is False and result['denied_accesses']==[]
assert result['opened_datasets']==sorted(ids)
assert result['checkpoint_reload']=='PASS_weights_only'
assert result['source_duplicate_policy']==plan['source_duplicate_policy']
assert result['source_duplicate_map_sha256']==@@DUPLICATE_MAP_SHA@@
assert result['excluded_pairs_by_split']==plan['excluded_pairs_by_split']
assert result['removed_sampled_windows_by_split']==plan['removed_sampled_windows_by_split']
history_path=run/'output/fold0/history.json';history=json.loads(history_path.read_text())
assert [row['epoch'] for row in history]==list(range(1,@@END@@+1))
assert result['history']==history
assert all(math.isfinite(v) for row in history for v in row.values() if isinstance(v,(int,float)))
checkpoint=run/'output/fold0/last.pt'
assert sha(checkpoint)==result['checkpoint_sha256']
ex=json.loads((run/'exit.json').read_text())
complete=json.loads((run/'supervision/complete.json').read_text())
control=json.loads((run/'supervision/control.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert complete['status']=='RELEASED_AFTER_VERIFIED_EXIT' and complete['exit']==ex
assert control['action']=='release' and control['queue']['state']=='RELEASED'
assert pathlib.Path(control['queue']['run_path']).resolve()==run.resolve()
print(json.dumps({'status':'PASS_EXP236_SOURCE_V2_BLOCK_AUDIT','block':@@BLOCK@@,
 'completed_epochs':@@END@@,'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'checkpoint_sha256':sha(checkpoint),
 'history_sha256':sha(history_path),'result_sha256':sha(result_path),
 'exit_sha256':sha(run/'exit.json'),'target_data_opened':False}))
'''.replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"])).replace(
        "@@SOURCE_MANIFEST_SHA@@", repr(SOURCE_MANIFEST_SHA)).replace(
        "@@SOURCE_BUNDLE_SHA@@", repr(SOURCE_BUNDLE_SHA)).replace(
        "@@DUPLICATE_MAP_SHA@@", repr(SOURCE_DUPLICATE_MAP_SHA)).replace(
        "@@DATA_ROOT@@", repr(REMOTE + "/data/exp213_source_view_20260912")).replace(
        "@@END@@", str(EPOCHS[block])).replace("@@BLOCK@@", str(block))
    audited = ssh(config["alias"], "python3 -", source)
    assert audited["status"] == "PASS_EXP236_SOURCE_V2_BLOCK_AUDIT"
    assert audited["block"] == block and audited["completed_epochs"] == EPOCHS[block]
    assert audited["manifest_sha256"] == prepared["stage"]["manifest_sha256"]
    assert audited["plan_sha256"] == prepared["stage"]["plan_sha256"]
    assert audited["target_data_opened"] is False
    return audited


def resource_probe(parent_block, child_block):
    queue = queue_status()
    parent = lease_for(queue, parent_block)
    if parent["state"] != "RELEASED":
        raise TerminalAnomaly(f"Parent block{parent_block:02d} release changed")
    child_id = f"exp236-horaz-source6bba-block{child_block:02d}-v2-20260927"
    if any(row["id"] == child_id for row in queue["requests"]):
        raise TerminalAnomaly(f"Child block{child_block:02d} already has a queue request")
    waiting = [row["id"] for row in queue["requests"]
               if row["project"] != PROJECT and row["state"].startswith("WAITING")]
    active_gpus = {gpu for row in queue["requests"]
                   if row["pool"] == "a100" and row["state"] in ("RUNNING", "RESERVED")
                   for gpu in row.get("gpus", [])}
    free = [gpu for gpu in queue["pools"]["a100"]["gpus"] if gpu not in active_gpus]
    return {"other_projects_waiting": waiting, "free_queue_gpu_count": len(free)}


def run_step(name, args, timeout, state):
    log_path = ROOT / f"reports/exp236_source_v2_to_epoch10_{name}_20260927.log"
    try:
        step = subprocess.run([sys.executable, *args], cwd=ROOT, text=True,
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log_path.write_text(out + "\n--- stderr ---\n" + err)
        state[name + "_log"] = str(log_path)
        state[name + "_timeout"] = True
        save(state)
        raise RuntimeError(f"{name} exceeded {timeout}s; reconcile {log_path}") from exc
    log_path.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    state[name + "_log"] = str(log_path)
    state[name + "_returncode"] = step.returncode
    save(state)
    if step.returncode:
        raise RuntimeError(f"{name} returned {step.returncode}; reconcile {log_path}")


def main():
    assert SCHEDULE == {1: (3, 4, 6), 2: (6, 7, 9), 3: (9, 10, 10)}
    assert not RECEIPT.exists(), "Existing controller receipt must be reconciled, never restarted blindly"
    for block in (2, 3, 4):
        assert not any(path.exists() for path in local_paths(block).values()), (
            f"Block{block:02d} already has local artifacts; reconcile before controller start")
    local_block(1, launched=False)
    state = {"status": "WAITING_FOR_EXP236_BLOCK01_V2_LAUNCH",
             "source_run": paths(1)[1], "final_epoch": 10,
             "target_data_opened": False, "started": time.time()}
    claim(state)
    try:
        wait_for("block01_launch", BLOCK01_LAUNCH_WAIT_SECONDS, block01_launch_probe,
                 lambda observed: observed["launch_receipt"], state)
        parent_audit = None
        for block in (1, 2, 3, 4):
            state["status"] = f"WAITING_FOR_EXP236_BLOCK{block:02d}_V2_RELEASE"
            save(state)
            wait_for(f"block{block:02d}_release", BLOCK_RUN_WAIT_SECONDS,
                     lambda block=block: block_probe(block),
                     lambda observed, block=block: block_released(block, observed), state)
            state["status"] = f"AUDITING_EXP236_BLOCK{block:02d}_V2"
            save(state)
            audited = audit_block(block, parent_audit)
            state[f"block{block:02d}_audit"] = audited
            save(state)
            parent_audit = audited
            if block == 4:
                break
            child = block + 1
            state["status"] = f"PREPARING_EXP236_BLOCK{child:02d}_V2"
            save(state)
            run_step(f"prepare_block{child:02d}",
                     [str(ROOT / "scripts/prepare_exp236_source_resume_v2.py"),
                      "--parent-block", str(block)], 900, state)
            child_files = local_paths(child)
            prepared, config, plan, _ = local_block(child, launched=False)
            assert plan["parent_checkpoint_sha256"] == audited["checkpoint_sha256"]
            assert plan["parent_history_sha256"] == audited["history_sha256"]
            assert plan["parent_result_sha256"] == audited["result_sha256"]
            state[f"block{child:02d}_prepare_sha256"] = sha(child_files["prepare"])
            state[f"block{child:02d}_plan_sha256"] = prepared["stage"]["plan_sha256"]
            save(state)
            state["status"] = f"WAITING_FOR_FAIR_EXP236_BLOCK{child:02d}_V2_RESOURCE"
            save(state)
            wait_for(f"block{child:02d}_resource", RESOURCE_WAIT_SECONDS,
                     lambda block=block, child=child: resource_probe(block, child),
                     lambda observed: not observed["other_projects_waiting"] and
                                      observed["free_queue_gpu_count"] > 0, state)
            state["status"] = f"LAUNCHING_EXP236_BLOCK{child:02d}_V2"
            save(state)
            run_step(f"launch_block{child:02d}",
                     [str(ROOT / "scripts/launch_exp236_source_resume_v2.py"),
                      "--block", str(child)], 300, state)
            local_block(child, launched=True)
            state[f"block{child:02d}_launch_sha256"] = sha(child_files["launch"])
            save(state)
        state["status"] = "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
        state["final_audit"] = parent_audit
    except BaseException as exc:
        state["status"] = "STOPPED_EXP236_SOURCE_V2_CONTINUATION"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


if __name__ == "__main__":
    main()
