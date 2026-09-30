"""Fair, one-shot A100 launcher for one staged EXP227 target image chunk.

This file is inert until launch_index is called after source-only selection,
local bundle preparation and immutable stage review.
"""
import hashlib
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from prepare_exp227_target_chunk0_local import ROOT, fair_idle_a100, paths, sha
from stage_exp227_target_chunk import stage_paths


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def launch_paths(index):
    prefix = f"exp227_target6bba_chunk{index:02d}"
    return {"reservation": ROOT / f"reports/{prefix}_reservation_20260927.json",
            "partial": ROOT / f"reports/{prefix}_partial_launch_20260927.json",
            "launch": ROOT / f"reports/{prefix}_launch_20260927.json",
            "prelaunch_release": ROOT / f"reports/{prefix}_prelaunch_release_20260927.json"}


def local_gate(index):
    destination = paths(index)
    staged_paths = stage_paths(index)
    output = launch_paths(index)
    assert not any(path.exists() for path in output.values()), "Existing launch artifact requires reconciliation"
    stage = json.loads(staged_paths["stage"].read_text())
    config = json.loads(staged_paths["config"].read_text())
    prepared = json.loads(destination["receipt"].read_text())
    assert stage["status"] == "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS"
    assert stage["chunk_index"] == index and prepared["chunk_index"] == index
    assert stage["code"] == config["code"] == destination["code"]
    assert stage["run"] == config["run"] == destination["run"]
    assert stage["lease_id"] == config["lease_id"] == destination["lease_id"]
    assert stage["selection_sha256"] == prepared["selection_sha256"]
    assert stage["checkpoint_sha256"] == prepared["checkpoint_sha256"]
    assert stage["plan_sha256"] == prepared["plan_sha256"]
    assert stage["movies"] == prepared["movies"]
    assert stage["local_prepare_sha256"] == sha(destination["receipt"])
    assert stage["remote_run_created"] is False and stage["gpu_claimed"] is False
    assert stage["target_labels_read"] is False and prepared["target_labels_read"] is False
    assert config["experiment"] == "EXP227_TARGET6BBA_CHUNK"
    assert config["chunk_index"] == index and config["pool"] == "a100"
    assert config["token"] == destination["token"]
    assert config["script"] == "run_exp227_target_chunk.py"
    assert config["arguments"] == [destination["code"] + "/plan.json", "--plan-sha256",
                                   stage["plan_sha256"]]
    assert config["max_seconds"] == 10800 and config["resources"] == {
        "cpu": 8, "ram_gib": 32, "disk_growth_gib": 4}
    return stage, config


def preflight_source(stage, config):
    return '''import hashlib,json,pathlib
c=CONFIG;code=pathlib.Path(c['code']);run=pathlib.Path(c['run'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not run.exists()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 p=(code/name).resolve();assert p.is_relative_to(code.resolve()) and sha(p)==digest,name
assert sha(code/'plan.json')==PLAN_SHA
plan=json.loads((code/'plan.json').read_text())
assert plan['experiment']=='EXP227_TARGET6BBA_CHUNK' and plan['chunk_index']==c['chunk_index']
assert plan['code']==c['code'] and plan['output']==str(run/'output')
assert plan['movies']==MOVIES and all(name.startswith('6bba_') for name in plan['movies'])
assert sha(code/'selection.json')==SELECTION_SHA
assert sha(code/'assignment.json')==ASSIGNMENT_SHA
assert sha(pathlib.Path(plan['checkpoint']))==CHECKPOINT_SHA
assert plan['checkpoint_sha256']==CHECKPOINT_SHA
print(json.dumps({'status':'PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT',
                  'manifest_sha256':sha(code/'code_manifest.json'),
                  'plan_sha256':sha(code/'plan.json'),
                  'run_absent':True}))
'''.replace("CONFIG", repr(config)).replace("MANIFEST_SHA", repr(stage["manifest_sha256"])).replace(
        "PLAN_SHA", repr(stage["plan_sha256"])).replace(
        "MOVIES", repr(stage["movies"])).replace(
        "SELECTION_SHA", repr(stage["selection_sha256"])).replace(
        "ASSIGNMENT_SHA", repr("9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4")).replace(
        "CHECKPOINT_SHA", repr(stage["checkpoint_sha256"]))


PHYSICAL_IDLE_SOURCE = '''import json,subprocess
all_gpus=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True)
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
all_ids=[line.strip() for line in all_gpus.splitlines() if line.strip()]
busy_ids=[line.strip() for line in busy.splitlines() if line.strip()]
assert len(all_ids)==len(set(all_ids)) and all_ids
print(json.dumps({'all_gpus':all_ids,'busy_gpus':busy_ids,
                  'idle_gpus':sorted(set(all_ids)-set(busy_ids))}))
'''


def launch_source(config, stage):
    return '''import hashlib,json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run']);code=pathlib.Path(c['code'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/'plan.json')==PLAN_SHA
assert not run.exists()
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
assert c['gpu'] not in busy.splitlines(),'Reserved GPU has a compute process'
run.mkdir();cfg=run/'config.json';cfg.write_text(json.dumps(c,indent=2)+'\\n')
records={}
for name,args in [('wrapper',[PYTHON,c['code']+'/exp227_job.py',str(cfg)]),
                  ('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(cfg)])]:
 with (run/(name+'.log')).open('w') as out:
  process=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=process.pid
print(json.dumps(records))
'''.replace("CONFIG", repr(config)).replace("PYTHON", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python")).replace(
        "MANIFEST_SHA", repr(stage["manifest_sha256"])).replace("PLAN_SHA", repr(stage["plan_sha256"]))


def controller_source(config):
    return '''import json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run'])
with (run/'controller.log').open('w') as out:
 process=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(run/'config.json')],
                          stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':process.pid}))
'''.replace("CONFIG", repr(config))


def summarize_queue(state):
    return [{key: row.get(key) for key in ("id", "state", "project", "gpus", "run_path")}
            for row in state["requests"]]


def release_if_no_run(config, receipt_path, reason, alias="nsu-a100"):
    """Release a rejected reservation only after proving no run directory exists."""
    inspected = ssh(alias, "python3 -",
                    "import json,pathlib\nprint(json.dumps({'run_exists':pathlib.Path(" +
                    repr(config["run"]) + ").exists()}))\n")
    assert inspected["run_exists"] is False, "Remote run exists; preserve lease for reconciliation"
    released = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "release",
        "--id", config["lease_id"], "--token", config["token"], "--verified-stopped"]))
    assert released["state"] == "RELEASED" and released["id"] == config["lease_id"]
    receipt_path.write_text(json.dumps({"status": "RELEASED_AFTER_REJECTED_PRELAUNCH",
        "reason": reason, "queue": released}, indent=2) + "\n")
    return released


def launch_index(index):
    destination = paths(index)
    output = launch_paths(index)
    stage, config = local_gate(index)
    remote_gate = ssh("nsu-a100", "python3 -", preflight_source(stage, config))
    assert remote_gate == {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                           "manifest_sha256": stage["manifest_sha256"],
                           "plan_sha256": stage["plan_sha256"], "run_absent": True}
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    physical = ssh("nsu-a100", "python3 -", PHYSICAL_IDLE_SOURCE)
    assert set(physical["idle_gpus"]) == set(physical["all_gpus"]) - set(physical["busy_gpus"])
    selected_idle = fair_idle_a100(state, physical["idle_gpus"], config["lease_id"])
    assert not any(row["state"] in ("RUNNING", "RESERVED") and
                   row["id"].startswith("exp227-target6bba-chunk")
                   for row in state["requests"]), "Another EXP227 target chunk is active"
    fair_proof = {"queue_preclaim": summarize_queue(state), "physical_preclaim": physical,
                  "first_fair_idle_gpu": selected_idle}
    resources = config["resources"]
    args = ["python3", QUEUE, "request", "--id", config["lease_id"],
            "--owner", "biohub-agent", "--token", config["token"],
            "--project", "biohub-cell-tracking-during-development",
            "--run-path", config["run"], "--pool", "a100", "--count", "1",
            "--cpu", str(resources["cpu"]), "--ram-gib", str(resources["ram_gib"]),
            "--disk-gib", str(resources["disk_growth_gib"]),
            "--minutes", str(config["max_seconds"] // 60 + 10)]
    try:
        lease = queue_request(args, config["lease_id"], config["token"])
    except Exception as error:
        output["reservation"].write_text(json.dumps({
            "status": "AMBIGUOUS_QUEUE_REQUEST_STOP", "error": repr(error),
            "config": config, "fair_proof": fair_proof}, indent=2) + "\n")
        raise
    output["reservation"].write_text(json.dumps({"status": "RESERVED_EXP227_TARGET_CHUNK",
        "lease": lease, "config": config, "fair_proof": fair_proof}, indent=2) + "\n")
    assert lease["state"] == "RESERVED" and lease["id"] == config["lease_id"]
    assert lease["alias"] == "nsu-a100" and lease["run_path"] == config["run"]
    assert lease["owner"] == "biohub-agent" and lease["token"] == config["token"]
    assert lease["project"] == "biohub-cell-tracking-during-development"
    assert len(lease["gpus"]) == 1
    if (lease["gpus"][0] not in physical["idle_gpus"] or
            any(row["state"] in ("RUNNING", "RESERVED") and
                lease["gpus"][0] in row.get("gpus", []) for row in state["requests"])):
        release_if_no_run(config, output["prelaunch_release"],
                          "Allocated GPU was not queue-free and physically idle")
        raise AssertionError("Allocated GPU failed fair physical-idle gate")
    assigned = {**config, "gpu": lease["gpus"][0], "alias": lease["alias"]}
    try:
        launched = ssh(assigned["alias"], "python3 -", launch_source(assigned, stage))
    except Exception:
        release_if_no_run(config, output["prelaunch_release"],
                          "Remote launch rejected before run creation", alias=assigned["alias"])
        raise
    partial = {"status": "PARTIAL_EXP227_TARGET_CHUNK_LAUNCH", "chunk_index": index,
               "lease_id": config["lease_id"], "lease": lease, "config": assigned,
               "launch": launched, "fair_proof": fair_proof,
               "remote_preflight": remote_gate,
               "code": config["code"], "run": config["run"],
               "manifest_sha256": stage["manifest_sha256"],
               "plan_sha256": stage["plan_sha256"], "target_labels_read": False}
    output["partial"].write_text(json.dumps(partial, indent=2) + "\n")
    control = ssh("nsu-quadro", "python3 -", controller_source(assigned))
    assert isinstance(control["controller_pid"], int) and control["controller_pid"] > 0
    receipt = {**partial, "status": "LAUNCHED_EXP227_TARGET6BBA_CHUNK", "control": control}
    output["launch"].write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "chunk_index": index,
                      "lease_id": config["lease_id"], "gpu": assigned["gpu"]}))
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    launch_index(parser.parse_args().index)
