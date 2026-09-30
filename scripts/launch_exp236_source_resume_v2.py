"""Lease one A100 for a verified v2 EXP236 source-only continuation block."""
import argparse
import json
from pathlib import Path
import shlex

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from prepare_exp236_source_block01_v2 import verify_source_audits
from run_exp236_source_resume_v2 import SOURCE_DUPLICATE_MAP_SHA


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--block", type=int, choices=(2, 3, 4), required=True)
    block = parser.parse_args().block
    stem = f"exp236_source_block{block:02d}_v2"
    config_path = ROOT / f"reports/{stem}_config_20260927.json"
    prepare_path = ROOT / f"reports/{stem}_prepare_20260927.json"
    prepared = json.loads(prepare_path.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS"
    assert prepared["target_data_opened"] is False
    assert prepared["parent_block"] == block - 1 and prepared["next_block"] == block
    assert prepared["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    audits = verify_source_audits()
    assert prepared["source_duplicate_audits"] == {
        key: value for key, value in audits.items() if key != "duplicate_starts"
    }
    assert prepared["preflight"]["status"] == "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT"
    assert prepared["preflight"]["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert prepared["stage"]["status"] == "STAGED_EXP236_SOURCE_RESUME_V2"
    assert prepared["stage"]["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    config = json.loads(config_path.read_text())
    assert config["experiment"] == "EXP236" and config["max_seconds"] == 10800
    assert config["code"] == prepared["stage"]["code"]
    assert config["code"] == REMOTE + f"/code/exp236_horaz_source6bba_block{block:02d}_v2_20260927"
    assert config["run"] == REMOTE + f"/runs/exp236_horaz_source6bba_block{block:02d}_v2_20260927"
    assert config["lease_id"] == f"exp236-horaz-source6bba-block{block:02d}-v2-20260927"
    assert config["token"] == f"exp236_horaz_source6bba_block{block:02d}_v2_20260927"
    assert config["script"] == "run_exp236_source_resume_v2.py"
    assert config["arguments"] == [config["code"] + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert not config_path.with_name(config_path.stem + "_launch.json").exists()
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    parent = json.loads((ROOT / f"reports/exp236_source_block{block-1:02d}_v2_config_20260927.json").read_text())
    parents = [row for row in state["requests"] if row["id"] == parent["lease_id"]]
    assert len(parents) == 1 and parents[0]["state"] == "RELEASED"
    assert parents[0]["run_path"] == parent["run"]
    assert not any(row["state"].startswith("WAITING") and
                   row["project"] != "biohub-cell-tracking-during-development"
                   for row in state["requests"]), "Other project waiting; defer"
    assert not any(row["id"] == config["lease_id"] for row in state["requests"])
    args = ["python3", QUEUE, "request", "--id", config["lease_id"], "--owner", "biohub-agent",
            "--token", config["token"], "--project", "biohub-cell-tracking-during-development",
            "--run-path", config["run"], "--pool", "a100", "--count", "1", "--cpu", "8",
            "--ram-gib", "32", "--disk-gib", "4", "--minutes", "190"]
    lease = queue_request(args, config["lease_id"], config["token"])
    config_path.with_name(config_path.stem + "_reservation.json").write_text(
        json.dumps({"lease": lease, "config": config}, indent=2) + "\n")
    assert lease["state"] == "RESERVED"
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    source = '''import hashlib,json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run']);code=pathlib.Path(c['code'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/'plan.json')==PLAN_SHA
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==DUPLICATE_MAP_SHA
assert not run.exists()
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
assert c['gpu'] not in busy
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
        "PLAN_SHA", repr(prepared["stage"]["plan_sha256"])).replace(
        "DUPLICATE_MAP_SHA", repr(SOURCE_DUPLICATE_MAP_SHA))
    try:
        launched = ssh(config["alias"], "python3 -", source)
    except Exception:
        inspected = ssh(config["alias"], "python3 -",
                        "import json,pathlib\nprint(json.dumps({'run_exists':pathlib.Path(" +
                        repr(config["run"]) + ").exists()}))\n")
        if not inspected["run_exists"]:
            released = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "release",
                                                      "--id", config["lease_id"],
                                                      "--token", config["token"],
                                                      "--verified-stopped"]))
            config_path.with_name(config_path.stem + "_prelaunch_release.json").write_text(
                json.dumps({"status": "RELEASED_AFTER_REJECTED_PRELAUNCH",
                            "queue": released}, indent=2) + "\n")
        raise
    config_path.with_name(config_path.stem + "_partial_launch.json").write_text(
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
               "config": config, "source_duplicate_audits": prepared["source_duplicate_audits"],
               "source_duplicate_map_sha256": SOURCE_DUPLICATE_MAP_SHA}
    config_path.with_name(config_path.stem + "_launch.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "EXP236_SOURCE_RESUME_V2_LAUNCHED", "block": block,
                      "gpu": config["gpu"], "run": config["run"],
                      "wrapper_pid": launched["wrapper"],
                      "controller_pid": controller["controller_pid"]}))


if __name__ == "__main__":
    main()
