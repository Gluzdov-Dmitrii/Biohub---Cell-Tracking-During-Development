"""EXP238 source6 fair attempt1 with a distinct queue identity.

Default is local review. --execute performs one readiness check and either
defers without an intent/queue request or requests once. It never retries an
ambiguous request, changes sealed code/plan, or opens labels/target images.
"""

import argparse
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from stage_exp238_peak_cache import REPORTS, atomic_json, local_preflight, sha
from launch_exp238_peak_cache import (
    PROJECT, REMOTE, launch_config, release_if_no_run, remote_launch_preflight,
)


NEW_LEASE_ID = "exp238-source6-peak-cache-v1a01-20260927"
OLD_LEASE_ID = "exp238-source6-peak-cache-v1-20260927"
SOURCE44_LEASE_ID = "exp238-source44-peak-cache-v1-20260927"
ATTEMPT0_RECEIPT = REPORTS / "exp238_source6_peak_cache_attempt0_wait_20260927.json"
ATTEMPT0_RECEIPT_SHA = "2d62c76ef2915a86334f42219d1471c3caaa38205581a249704f05fe41c800f5"
STAGE = REPORTS / "exp238_source6_peak_cache_stage_20260927.json"
STAGE_SHA = "50aad2cabfa71c12ce28a701e9a69e960be5800ea3182d13da149508df0d07cf"
PREFIX = REPORTS / "exp238_source6_peak_cache_launch_a01_20260927"


def artifact(name: str) -> Path:
    return PREFIX.with_name(PREFIX.name + "_" + name + ".json")


def fresh_attempt() -> None:
    for name in ("intent", "reservation", "partial", "launch", "wait", "failure",
                 "prelaunch_release"):
        assert not artifact(name).exists(), f"Attempt1 already has {name}; reconcile, do not retry"


def local_gate() -> tuple[dict, dict, dict]:
    plan, local = local_preflight("source6")
    assert sha(ATTEMPT0_RECEIPT) == ATTEMPT0_RECEIPT_SHA
    attempt0 = json.loads(ATTEMPT0_RECEIPT.read_text())
    assert attempt0["status"] == "WAITING_RESOURCE_CANCELLED_UNLAUNCHED_EXP238_SOURCE6_ATTEMPT0"
    assert attempt0["lease"]["id"] == OLD_LEASE_ID
    assert attempt0["lease"]["state"] == "CANCELLED"
    assert attempt0["lease"]["gpus"] == [] and attempt0["lease"]["process"] is None
    assert all(not row["run_exists"] and row["matched_processes"] == []
               for row in attempt0["remote_probes"])
    assert sha(STAGE) == STAGE_SHA
    stage = json.loads(STAGE.read_text())
    assert stage["status"] == "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS"
    assert stage["cohort"] == "source6" and stage["run_started"] is False
    assert stage["stage"]["plan_sha256"] == local["plan_sha256"]
    assert stage["stage"]["runner_sha256"] == plan["runner_sha256"]
    fresh_attempt()
    return plan, local, stage


def read_queue() -> dict:
    return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))


def physical_busy() -> set[str]:
    source = '''import json,subprocess
raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                             '--format=csv,noheader'],text=True)
lines=[line.strip() for line in raw.splitlines() if line.strip()]
assert all(line.startswith('GPU-') for line in lines),lines
print(json.dumps({'busy_gpu_uuids':sorted(set(lines))}))
'''
    return set(ssh("nsu-a100", "python3 -", source)["busy_gpu_uuids"])


def fair_capacity(queue: dict, busy: set[str] | None = None) -> dict:
    rows = queue["requests"]
    old = [row for row in rows if row["id"] == OLD_LEASE_ID]
    source44 = [row for row in rows if row["id"] == SOURCE44_LEASE_ID]
    assert len(old) == len(source44) == 1
    assert old[0]["state"] == "CANCELLED" and old[0]["gpus"] == []
    assert old[0]["process"] is None
    assert not any(row["id"] == NEW_LEASE_ID for row in rows)
    if source44[0]["state"] != "RELEASED":
        return {"ready": False, "reason": "SOURCE44_NOT_RELEASED",
                "source44_state": source44[0]["state"]}
    foreign_waiting = [row["id"] for row in rows
                       if row["project"] != PROJECT and row["state"].startswith("WAITING")]
    if foreign_waiting:
        return {"ready": False, "reason": "FOREIGN_WAITING",
                "foreign_waiting": foreign_waiting}
    pool = set(queue["pools"]["a100"]["gpus"])
    allocated = {gpu for row in rows
                 if row["pool"] == "a100" and row["state"] in ("RESERVED", "RUNNING")
                 for gpu in row.get("gpus", [])}
    free_queue = pool - allocated
    if not free_queue:
        return {"ready": False, "reason": "NO_QUEUE_FREE_A100", "queue_free": 0}
    if busy is None:
        return {"ready": False, "reason": "PHYSICAL_GPU_STATUS_UNCHECKED",
                "queue_free": len(free_queue)}
    idle = free_queue - busy
    return {"ready": bool(idle),
            "reason": "FAIR_A100_READY" if idle else "NO_PHYSICALLY_IDLE_QUEUE_FREE_A100",
            "queue_free": len(free_queue), "idle_gpu_uuids": sorted(idle)}


def confirm_waiting_cancelled(plan: dict, config: dict, error: str) -> dict:
    queue = read_queue()
    rows = [row for row in queue["requests"] if row["id"] == NEW_LEASE_ID]
    assert len(rows) == 1
    lease = rows[0]
    assert lease["state"] == "CANCELLED" and lease["gpus"] == []
    assert lease["process"] is None and lease["run_path"] == plan["run"]
    source = '''import json,pathlib
print(json.dumps({'run_exists':pathlib.Path(RUN).exists()}))
'''.replace("RUN", repr(plan["run"]))
    observed = ssh("nsu-a100", "python3 -", source)
    assert observed == {"run_exists": False}
    receipt = {"status": "WAITING_RESOURCE_CANCELLED_UNLAUNCHED_EXP238_SOURCE6_ATTEMPT1",
               "error": error, "lease": lease, "run_absent": True,
               "config": config, "source_labels_read": False,
               "target_data_opened": False, "remote_mutation": False}
    atomic_json(artifact("wait"), receipt)
    return receipt


def launch_once(plan: dict, local: dict, stage: dict, capacity: dict) -> dict:
    fresh_attempt()
    preflight = remote_launch_preflight(plan, stage["stage"])
    assert preflight["status"] == "PASS_EXP238_LAUNCH_PREFLIGHT_NO_LABELS"
    assert preflight["movies"] == 11 and preflight["run_absent"] is True
    config = launch_config(plan, stage["stage"]["manifest_sha256"], local["plan_sha256"])
    config["lease_id"] = NEW_LEASE_ID
    assert config["run"] == plan["run"] and config["code"] == plan["code"]
    assert config["token"] == Path(plan["code"]).name
    atomic_json(artifact("intent"),
                {"status": "INTENT_EXP238_SOURCE6_A01_A100_REQUEST",
                 "config": config, "stage_receipt_sha256": STAGE_SHA,
                 "attempt0_receipt_sha256": ATTEMPT0_RECEIPT_SHA,
                 "local_plan_sha256": local["plan_sha256"],
                 "fair_capacity": capacity, "preflight": preflight})
    request = ["python3", QUEUE, "request", "--id", NEW_LEASE_ID,
               "--owner", "biohub-agent", "--token", config["token"],
               "--project", PROJECT, "--run-path", config["run"],
               "--pool", "a100", "--count", "1", "--cpu", "8",
               "--ram-gib", "32", "--disk-gib", "4", "--minutes", "130"]
    try:
        lease = queue_request(request, NEW_LEASE_ID, config["token"])
    except RuntimeError as exc:
        if "Queue returned WAITING_RESOURCE; cancelled unlaunched request" in str(exc):
            return confirm_waiting_cancelled(plan, config, str(exc))
        atomic_json(artifact("failure"), {"status": "STOPPED_UNCERTAIN_QUEUE_REQUEST_A01",
                                          "error": str(exc), "config": config})
        raise
    atomic_json(artifact("reservation"), {"lease": lease, "config": config})
    assert lease["state"] == "RESERVED" and len(lease["gpus"]) == 1
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    remote = '''import hashlib,json,pathlib,subprocess
c=json.loads(CONFIG);run=pathlib.Path(c['run']);code=pathlib.Path(c['code'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not run.exists() and sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/'exp238_plan.json')==PLAN_SHA
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                              '--format=csv,noheader'],text=True)
assert c['gpu'] not in busy.splitlines(),'Reserved GPU has a compute process'
run.mkdir()
cfg=run/'config.json';cfg.write_text(json.dumps(c,indent=2)+'\\n')
records={}
for name,command in [('wrapper',[PYTHON,c['code']+'/exp227_job.py',str(cfg)]),
                     ('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(cfg)])]:
 with (run/(name+'.log')).open('w') as out:
  process=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=process.pid
print(json.dumps(records))
'''.replace("CONFIG", repr(json.dumps(config, sort_keys=True))).replace(
        "MANIFEST_SHA", repr(stage["stage"]["manifest_sha256"])).replace(
        "PLAN_SHA", repr(local["plan_sha256"])).replace(
        "PYTHON", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"))
    try:
        launched = ssh(config["alias"], "python3 -", remote)
    except Exception as exc:
        try:
            release = release_if_no_run(config, PREFIX)
        except Exception as probe_exc:
            release = {"status": "UNOBSERVABLE_RUN_RETAIN_LEASE", "error": str(probe_exc)}
        atomic_json(artifact("failure"), {"status": "STOPPED_AFTER_RESERVED_A01",
                                          "error": str(exc), "reconciliation": release,
                                          "config": config})
        raise
    atomic_json(artifact("partial"), {"lease": lease, "launch": launched, "config": config})
    control = '''import json,pathlib,subprocess
c=json.loads(CONFIG);run=pathlib.Path(c['run'])
with (run/'controller.log').open('w') as out:
 process=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(run/'config.json')],
                          stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':process.pid}))
'''.replace("CONFIG", repr(json.dumps(config, sort_keys=True)))
    try:
        controller = ssh("nsu-quadro", "python3 -", control)
    except Exception as exc:
        atomic_json(artifact("failure"), {"status": "STOPPED_CONTROLLER_UNCERTAIN_A01",
                                          "error": str(exc), "config": config})
        raise
    receipt = {"status": "LAUNCHED_EXP238_SOURCE6_PEAK_CACHE_A01", "cohort": "source6",
               "lease": lease, "launch": launched, "control": controller,
               "config": config, "source_labels_read": False, "target_data_opened": False}
    atomic_json(artifact("launch"), receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan, local, stage = local_gate()
    if not args.execute:
        print(json.dumps({"status": "EXP238_SOURCE6_A01_LOCAL_REVIEW_ONLY",
                          "new_lease_id": NEW_LEASE_ID,
                          "same_code": plan["code"], "same_run": plan["run"],
                          "plan_sha256": local["plan_sha256"], "gpu_request": False},
                         sort_keys=True))
        return
    queue = read_queue()
    preliminary = fair_capacity(queue)
    if preliminary["reason"] not in ("PHYSICAL_GPU_STATUS_UNCHECKED",):
        print(json.dumps({"status": "DEFER_EXP238_SOURCE6_A01_NO_QUEUE_REQUEST",
                          "capacity": preliminary}, sort_keys=True))
        return
    capacity = fair_capacity(queue, physical_busy())
    if not capacity["ready"]:
        print(json.dumps({"status": "DEFER_EXP238_SOURCE6_A01_NO_QUEUE_REQUEST",
                          "capacity": capacity}, sort_keys=True))
        return
    result = launch_once(plan, local, stage, capacity)
    print(json.dumps({"status": result["status"], "lease_id": NEW_LEASE_ID,
                      "run": plan["run"]}, sort_keys=True))


if __name__ == "__main__":
    main()
