"""Lease one fair, idle A100 for EXP236 v2 source11 no-label epoch10 graphs."""
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from prepare_exp236_source_graph10_v2 import (
    CODE, CONFIG_PATH, CONTROLLER_RECEIPT, PREPARE_PATH, ROOT, RUN, TRAIN_RUN,
    PLAN_PATH, REMOTE, sha,
)
from run_exp236_source_graph10_v2 import DUPLICATE_MAP_SHA, INNER_IDS, validate


PARENT_CONFIG = ROOT / "reports/exp236_source_block04_v2_config_20260927.json"


def main():
    prepared = json.loads(PREPARE_PATH.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS"
    assert prepared["source_labels_read"] is False
    assert prepared["target_labels_read"] is False and prepared["target_data_opened"] is False
    assert prepared["movies"] == len(INNER_IDS) == 11
    assert prepared["controller_receipt_sha256"] == sha(CONTROLLER_RECEIPT)
    assert prepared["training_chain"][-1]["run"] == TRAIN_RUN
    plan = json.loads(PLAN_PATH.read_text())
    validate(plan)
    assert prepared["training_chain"] == plan["training_chain"]
    assert sha(PLAN_PATH) == prepared["stage"]["plan_sha256"]
    config = json.loads(CONFIG_PATH.read_text())
    assert config["experiment"] == "EXP236" and config["max_seconds"] == 7200
    assert config["code"] == CODE == prepared["stage"]["code"]
    assert config["run"] == RUN and config["script"] == "run_exp236_source_graph10_v2.py"
    assert config["arguments"] == [CODE + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert not CONFIG_PATH.with_name(CONFIG_PATH.stem + "_launch.json").exists()
    assert not CONFIG_PATH.with_name(CONFIG_PATH.stem + "_reservation.json").exists()
    parent_config = json.loads(PARENT_CONFIG.read_text())
    assert parent_config["code"] == prepared["training_chain"][-1]["code"]
    assert parent_config["run"] == TRAIN_RUN
    assert parent_config["lease_id"] == "exp236-horaz-source6bba-block04-v2-20260927"
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    parents = [row for row in state["requests"] if row["id"] == parent_config["lease_id"]]
    assert len(parents) == 1 and parents[0]["state"] == "RELEASED"
    assert parents[0]["run_path"] == TRAIN_RUN
    assert not any(row["state"].startswith("WAITING") and
                   row["project"] != "biohub-cell-tracking-during-development"
                   for row in state["requests"]), "Other project waiting; defer"
    assert not any(row["id"] == config["lease_id"] for row in state["requests"])
    stage_check = '''import hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@PLAN_SHA@@
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@DUPLICATE_MAP_SHA@@
assert not run.exists()
print(json.dumps({'status':'PASS_EXP236_SOURCE_GRAPH10_V2_STAGE_RECHECK'}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(prepared["stage"]["plan_sha256"])).replace(
        "@@DUPLICATE_MAP_SHA@@", repr(DUPLICATE_MAP_SHA))
    assert ssh("nsu-a100", "python3 -", stage_check)["status"] == (
        "PASS_EXP236_SOURCE_GRAPH10_V2_STAGE_RECHECK")
    args = ["python3", QUEUE, "request", "--id", config["lease_id"], "--owner", "biohub-agent",
            "--token", config["token"], "--project", "biohub-cell-tracking-during-development",
            "--run-path", RUN, "--pool", "a100", "--count", "1", "--cpu", "8",
            "--ram-gib", "32", "--disk-gib", "4", "--minutes", "130"]
    lease = queue_request(args, config["lease_id"], config["token"])
    CONFIG_PATH.with_name(CONFIG_PATH.stem + "_reservation.json").write_text(
        json.dumps({"lease": lease, "config": config}, indent=2) + "\n")
    assert lease["state"] == "RESERVED" and len(lease["gpus"]) == 1
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    source = '''import hashlib,json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run']);code=pathlib.Path(c['code'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/'plan.json')==PLAN_SHA
assert not run.exists()
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
assert c['gpu'] not in busy.splitlines(), 'Reserved GPU has a compute process'
run.mkdir();cfg=run/'config.json';cfg.write_text(json.dumps(c,indent=2))
records={}
for name,args in [('wrapper',[PYTHON,c['code']+'/exp227_job.py',str(cfg)]),
                  ('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(cfg)])]:
 with (run/(name+'.log')).open('w') as out:
  process=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=process.pid
print(json.dumps(records))
'''.replace("CONFIG", repr(config)).replace(
        "PYTHON", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python")).replace(
        "MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PLAN_SHA", repr(prepared["stage"]["plan_sha256"]))
    try:
        launched = ssh(config["alias"], "python3 -", source)
    except Exception:
        # Lost SSH output after mkdir could hide a live worker: retain that lease.
        inspected = ssh(config["alias"], "python3 -",
                        "import json,pathlib\nprint(json.dumps({'run_exists':pathlib.Path(" +
                        repr(RUN) + ").exists()}))\n")
        if not inspected["run_exists"]:
            released = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "release",
                                                      "--id", config["lease_id"],
                                                      "--token", config["token"],
                                                      "--verified-stopped"]))
            CONFIG_PATH.with_name(CONFIG_PATH.stem + "_prelaunch_release.json").write_text(
                json.dumps({"status": "RELEASED_AFTER_REJECTED_PRELAUNCH",
                            "queue": released}, indent=2) + "\n")
        raise
    CONFIG_PATH.with_name(CONFIG_PATH.stem + "_partial_launch.json").write_text(
        json.dumps({"lease": lease, "launch": launched, "config": config}, indent=2) + "\n")
    control = '''import json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run'])
with (run/'controller.log').open('w') as out:
 process=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(run/'config.json')],
                          stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':process.pid}))
'''.replace("CONFIG", repr(config))
    controller = ssh("nsu-quadro", "python3 -", control)
    receipt = {"lease": lease, "launch": launched, "control": controller,
               "config": config}
    CONFIG_PATH.with_name(CONFIG_PATH.stem + "_launch.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "EXP236_SOURCE_GRAPH10_V2_LAUNCHED",
                      "gpu": config["gpu"], "run": RUN,
                      "wrapper_pid": launched["wrapper"],
                      "controller_pid": controller["controller_pid"]}))


if __name__ == "__main__":
    main()
