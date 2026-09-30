"""Lease an idle A100 for eight no-label EXP227 epoch20 source graphs."""
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from prepare_exp227_source_graph20 import CODE, TRAIN_RUN, REMOTE, RUN


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "reports/exp227_source_graph20_config_20260927.json"
PREPARE = ROOT / "reports/exp227_source_graph20_prepare_20260927.json"
PARENT_CONFIG = ROOT / "reports/exp227_source_block03_config_20260927.json"


def main():
    prepared = json.loads(PREPARE.read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS"
    assert prepared["target_labels_read"] is False
    assert prepared["movies"] == 8
    config = json.loads(CONFIG.read_text())
    assert config["experiment"] == "EXP227" and config["max_seconds"] == 3600
    assert config["code"] == CODE == prepared["stage"]["code"]
    assert config["run"] == RUN
    assert config["script"] == "run_exp227_source_graph20.py"
    assert config["arguments"] == [CODE + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert not CONFIG.with_name(CONFIG.stem + "_launch.json").exists()
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    parent_config = json.loads(PARENT_CONFIG.read_text())
    parents = [row for row in state["requests"] if row["id"] == parent_config["lease_id"]]
    assert len(parents) == 1 and parents[0]["state"] == "RELEASED"
    assert parents[0]["run_path"] == TRAIN_RUN
    assert not any(row["state"].startswith("WAITING") and
                   row["project"] != "biohub-cell-tracking-during-development"
                   for row in state["requests"]), "Other project waiting; defer"
    assert not any(row["id"] == config["lease_id"] for row in state["requests"])
    args = ["python3", QUEUE, "request", "--id", config["lease_id"], "--owner", "biohub-agent",
            "--token", config["token"], "--project", "biohub-cell-tracking-during-development",
            "--run-path", RUN, "--pool", "a100", "--count", "1", "--cpu", "8",
            "--ram-gib", "32", "--disk-gib", "4", "--minutes", "70"]
    lease = queue_request(args, config["lease_id"], config["token"])
    CONFIG.with_name(CONFIG.stem + "_reservation.json").write_text(
        json.dumps({"lease": lease, "config": config}, indent=2) + "\n")
    assert lease["state"] == "RESERVED" and len(lease["gpus"]) == 1
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    CONFIG.write_text(json.dumps(config, indent=2) + "\n")
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
        # A lost SSH reply after run creation might hide a live worker.
        inspected = ssh(config["alias"], "python3 -",
                        "import json,pathlib\nprint(json.dumps({'run_exists':pathlib.Path(" +
                        repr(RUN) + ").exists()}))\n")
        if not inspected["run_exists"]:
            released = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "release",
                                                      "--id", config["lease_id"],
                                                      "--token", config["token"],
                                                      "--verified-stopped"]))
            CONFIG.with_name(CONFIG.stem + "_prelaunch_release.json").write_text(
                json.dumps({"status": "RELEASED_AFTER_REJECTED_PRELAUNCH",
                            "queue": released}, indent=2) + "\n")
        raise
    CONFIG.with_name(CONFIG.stem + "_partial_launch.json").write_text(
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
    CONFIG.with_name(CONFIG.stem + "_launch.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "EXP227_SOURCE_GRAPH20_LAUNCHED",
                      "gpu": config["gpu"], "run": RUN,
                      "wrapper_pid": launched["wrapper"],
                      "controller_pid": controller["controller_pid"]}))


if __name__ == "__main__":
    main()
