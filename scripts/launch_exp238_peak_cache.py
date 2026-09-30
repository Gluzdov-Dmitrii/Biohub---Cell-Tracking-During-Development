"""Fair one-shot EXP238 A100 launch. Default is local review only.

--execute is reserved for a later root decision after code-stage review. A failed
or ambiguous request keeps its intent/lease for explicit diagnosis; no blind retry.
"""

import argparse
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from stage_exp238_peak_cache import ROOT, REPORTS, atomic_json, local_preflight, sha


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PROJECT = "biohub-cell-tracking-during-development"


def launch_config(plan: dict, manifest_sha256: str, plan_sha256: str) -> dict:
    cohort = plan["cohort"]
    namespace = Path(plan["code"]).name
    assert namespace == Path(plan["run"]).name
    return {"experiment": "EXP238", "cohort": cohort,
            "lease_id": "exp238-" + cohort + "-peak-cache-v1-20260927",
            "token": namespace, "code": plan["code"], "run": plan["run"],
            "max_seconds": 3600 if cohort == "source44" else 7200,
            "cpu_affinity": "0-7", "script": "run_exp238_peak_cache.py",
            "arguments": [plan["code"] + "/exp238_plan.json", "--plan-sha256",
                          plan_sha256, "--manifest-sha256", manifest_sha256]}


def remote_launch_preflight(plan: dict, stage: dict) -> dict:
    source = '''import hashlib,json,pathlib
p=json.loads(PLAN);s=json.loads(STAGE)
code=pathlib.Path(p['code']);run=pathlib.Path(p['run'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not run.exists()
assert sha(code/'code_manifest.json')==s['manifest_sha256']
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'exp238_plan.json')==s['plan_sha256']
assert sha(code/'exp238_parent_plan.json')==p['parent_plan_sha256']
assert sha(code/'horaz/src/src/engine.py')==p['patched_engine_sha256']
assert sha(code/'horaz/src/src/detection.py')==p['patched_detection_sha256']
assert sha(code/'run_exp238_peak_cache.py')==p['runner_sha256']
parent=pathlib.Path(p['parent_run'])
assert sha(parent/'output/status.json')==p['parent_status_sha256']
assert sha(pathlib.Path(p['checkpoint']))==p['checkpoint_sha256']
for row in p['movies']:
 csv=parent/'output'/('graph__'+row['dataset']+'.csv')
 assert sha(csv)==row['graph_csv_sha256'] and sha(csv.with_suffix('.json'))==row['graph_receipt_sha256']
print(json.dumps({'status':'PASS_EXP238_LAUNCH_PREFLIGHT_NO_LABELS','movies':len(p['movies']),
 'run_absent':True,'labels_read':False}))
'''.replace("PLAN", repr(json.dumps(plan, sort_keys=True))).replace(
        "STAGE", repr(json.dumps(stage, sort_keys=True)))
    return ssh("nsu-a100", "python3 -", source)


def release_if_no_run(config: dict, prefix: Path) -> dict:
    """Release only a confirmed prelaunch reservation; preserve ambiguous runs."""
    source = '''import json,pathlib
run=pathlib.Path(RUN)
print(json.dumps({'run_exists':run.exists()}))
'''.replace("RUN", repr(config["run"]))
    observed = ssh(config["alias"], "python3 -", source)
    assert set(observed) == {"run_exists"} and isinstance(observed["run_exists"], bool)
    if observed["run_exists"]:
        return {"status": "STOPPED_AMBIGUOUS_RUN_EXISTS_RETAIN_LEASE", "observation": observed}
    released = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "release",
                                               "--id", config["lease_id"],
                                               "--token", config["token"],
                                               "--verified-stopped"]))
    receipt = {"status": "RELEASED_CONFIRMED_NO_RUN_AFTER_PRELAUNCH_FAILURE",
               "observation": observed, "queue": released, "config": config}
    atomic_json(prefix.with_name(prefix.name + "_prelaunch_release.json"), receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("source44", "source6"), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan, local = local_preflight(args.cohort)
    stage_path = REPORTS / ("exp238_" + args.cohort + "_peak_cache_stage_20260927.json")
    if not args.execute:
        print(json.dumps({"status": "EXP238_LOCAL_LAUNCH_REVIEW_ONLY", "cohort": args.cohort,
                          "stage_receipt_present": stage_path.exists(),
                          "plan_sha256": local["plan_sha256"], "gpu_request": False},
                         sort_keys=True))
        return
    stage = json.loads(stage_path.read_text())
    assert stage["status"] == "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS"
    assert stage["cohort"] == args.cohort and stage["run_started"] is False
    assert stage["local"]["plan_sha256"] == local["plan_sha256"]
    assert stage["stage"]["plan_sha256"] == local["plan_sha256"]
    config = launch_config(plan, stage["stage"]["manifest_sha256"], local["plan_sha256"])
    prefix = REPORTS / ("exp238_" + args.cohort + "_peak_cache_launch_20260927")
    assert not prefix.with_name(prefix.name + "_intent.json").exists()
    assert not prefix.with_name(prefix.name + "_reservation.json").exists()
    assert not prefix.with_name(prefix.name + "_partial.json").exists()
    assert not prefix.with_suffix(".json").exists()
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    assert not any(item["id"] == config["lease_id"] for item in queue["requests"])
    assert not any(item["state"].startswith("WAITING") and item["project"] != PROJECT
                   for item in queue["requests"]), "Foreign project waiting; defer"
    preflight = remote_launch_preflight(plan, stage["stage"])
    assert preflight["status"] == "PASS_EXP238_LAUNCH_PREFLIGHT_NO_LABELS"
    assert preflight["movies"] == len(plan["movies"])
    atomic_json(prefix.with_name(prefix.name + "_intent.json"),
                {"status": "INTENT_EXP238_A100_REQUEST", "config": config,
                 "stage_receipt_sha256": sha(stage_path), "preflight": preflight})
    request = ["python3", QUEUE, "request", "--id", config["lease_id"],
               "--owner", "biohub-agent", "--token", config["token"],
               "--project", PROJECT, "--run-path", config["run"],
               "--pool", "a100", "--count", "1", "--cpu", "8",
               "--ram-gib", "32", "--disk-gib", "4", "--minutes",
               "65" if args.cohort == "source44" else "130"]
    lease = queue_request(request, config["lease_id"], config["token"])
    atomic_json(prefix.with_name(prefix.name + "_reservation.json"),
                {"lease": lease, "config": config})
    assert lease["state"] == "RESERVED" and len(lease["gpus"]) == 1
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    remote = '''import hashlib,json,pathlib,subprocess
c=json.loads(CONFIG);run=pathlib.Path(c['run']);code=pathlib.Path(c['code'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not run.exists() and sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/'exp238_plan.json')==PLAN_SHA
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
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
    except Exception:
        # A lost SSH reply can hide a live worker. Probe once; retain the lease
        # whenever run creation is observed or the probe itself is uncertain.
        release_if_no_run(config, prefix)
        raise
    atomic_json(prefix.with_name(prefix.name + "_partial.json"),
                {"lease": lease, "launch": launched, "config": config})
    control = '''import json,pathlib,subprocess
c=json.loads(CONFIG);run=pathlib.Path(c['run'])
with (run/'controller.log').open('w') as out:
 process=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(run/'config.json')],
                          stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':process.pid}))
'''.replace("CONFIG", repr(json.dumps(config, sort_keys=True)))
    controller = ssh("nsu-quadro", "python3 -", control)
    receipt = {"status": "LAUNCHED_EXP238_SOURCE_PEAK_CACHE", "cohort": args.cohort,
               "lease": lease, "launch": launched, "control": controller,
               "config": config, "source_labels_read": False, "target_data_opened": False}
    atomic_json(prefix.with_suffix(".json"), receipt)
    print(json.dumps({"status": receipt["status"], "cohort": args.cohort,
                      "gpu": config["gpu"], "run": config["run"]}, sort_keys=True))


if __name__ == "__main__":
    main()
