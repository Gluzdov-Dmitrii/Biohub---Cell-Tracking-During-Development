"""Launch one frozen EXP234 target chunk after both source choices are sealed."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh
from prepare_exp234_target_rollout_v2 import local_freeze


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = Path(sys.argv[1])
    config = json.loads(path.read_text())
    assert config["experiment"] == "EXP234_TARGET_CHUNK"
    assert config["pool"] == "a100" and config["max_seconds"] <= 10800
    assert config["code"] == REMOTE + "/code/exp234_target_rollout_v2_20260927"
    assert config["run"].startswith(REMOTE + "/runs/exp234_target_")
    assert config["script"] == "run_exp234_target_chunk.py"
    assert config["arguments"][1] == "--plan-sha256"
    assignment, choices = local_freeze()
    prepared = json.loads((ROOT / "reports/exp234_target_prepare_v2_20260927.json").read_text())
    assert prepared["status"] == "PREPARED_EXP234_TARGET175_NO_LABELS"
    assert prepared["assignment_sha256"] == sha(ROOT / "reports/exp234_target_chunk_assignment_20260926.json")
    assert prepared["chunks"] == {"44b6": 8, "6bba": 4}
    assert prepared["target_labels_read"] is False
    for source in ("44b6", "6bba"):
        assert prepared["source_choices"][source] == {
            "selected_threshold": choices[source]["selected_threshold"],
            "result_sha256": choices[source]["result_sha256"],
            "gate_sha256": choices[source]["gate_sha256"]}
    stem = path.stem
    source = "44b6" if "_44b6_" in stem else "6bba"
    index = int(stem.split("_chunk")[1].split("_")[0])
    assert 0 <= index < (8 if source == "44b6" else 4)
    assert config["arguments"][0] == config["code"] + f"/{source}_chunk{index:02d}_plan.json"
    assert config["run"] == REMOTE + f"/runs/exp234_target_{source}_chunk{index:02d}_v2_20260927"
    assert len(assignment["directions"][source]["chunks"][index]) in (14, 15)

    preflight = '''import hashlib,json,pathlib
c=CONFIG; code=pathlib.Path(c['code']);run=pathlib.Path(c['run'])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not run.exists()
assert sha(code/'code_manifest.json')==MANIFEST_SHA
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
plan=pathlib.Path(c['arguments'][0]);assert sha(plan)==c['arguments'][2]
p=json.loads(plan.read_text())
assert p['selected_threshold']==THRESHOLD and p['source_embryo']==EMBRYO
assert p['output']==str(run/'output')
assert sha(p['source_selection_result'])==SELECTION_SHA
assert sha(p['assignment'])==ASSIGNMENT_SHA
assert sha(p['bundle'])==p['bundle_sha256']
print(json.dumps({'status':'PASS_EXP234_TARGET_LAUNCH_PREFLIGHT','plan_sha256':sha(plan)}))
'''.replace("CONFIG", repr(config)).replace("MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "THRESHOLD", repr(choices[source]["selected_threshold"])).replace("EMBRYO", repr(source)).replace(
        "SELECTION_SHA", repr(choices[source]["result_sha256"])).replace(
        "ASSIGNMENT_SHA", repr(prepared["assignment_sha256"]))
    remote_gate = ssh("nsu-a100", "python3 -", preflight)
    assert remote_gate["status"] == "PASS_EXP234_TARGET_LAUNCH_PREFLIGHT"
    assert remote_gate["plan_sha256"] == config["arguments"][2]

    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    assert not any(r["id"] == config["lease_id"] for r in state["requests"]), "Existing lease: reconcile"
    assert not any(r["state"].startswith("WAITING") and
                   r["project"] != "biohub-cell-tracking-during-development"
                   for r in state["requests"]), "Other project is waiting"
    assert not any(r["state"] in ("RUNNING", "RESERVED") and
                   r["id"].startswith("exp234-target-" + source + "-")
                   for r in state["requests"]), "Same-source target chunk already active"
    resources = config["resources"]
    args = ["python3", QUEUE, "request", "--id", config["lease_id"],
            "--owner", "biohub-agent", "--token", config["token"],
            "--project", "biohub-cell-tracking-during-development",
            "--run-path", config["run"], "--pool", "a100", "--count", "1",
            "--cpu", str(resources["cpu"]), "--ram-gib", str(resources["ram_gib"]),
            "--disk-gib", str(resources["disk_growth_gib"]),
            "--minutes", str(config["max_seconds"] // 60 + 10)]
    lease = queue_request(args, config["lease_id"], config["token"])
    assert lease["state"] == "RESERVED" and lease["alias"] == "nsu-a100"
    config["gpu"] = lease["gpus"][0]
    config["alias"] = lease["alias"]
    path.write_text(json.dumps(config, indent=2) + "\n")
    launch_source = '''import json,pathlib,subprocess
c=CONFIG;r=pathlib.Path(c['run']);assert not r.exists();r.mkdir()
conf=r/'config.json';conf.write_text(json.dumps(c,indent=2)+'\\n')
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
assert c['gpu'] not in busy,'Allocated GPU physically busy'
records={}
for name,cmd in [('wrapper',[ROOT+'/envs/prepost/py3.11-stdlib-v1/bin/python',c['code']+'/exp214_inference_job.py',str(conf)]),
                 ('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(conf)])]:
 with (r/(name+'.log')).open('w') as out:
  proc=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=proc.pid
print(json.dumps(records))
'''.replace("CONFIG", repr(config)).replace("ROOT", repr(REMOTE))
    launch = ssh("nsu-a100", "python3 -", launch_source)
    partial = {"lease": lease, "launch": launch, "config": config,
               "preflight": remote_gate}
    path.with_name(path.stem + "_partial_launch.json").write_text(json.dumps(partial, indent=2) + "\n")
    monitor_receipt = path.with_name(path.stem + "_monitor.json")
    with path.with_name(path.stem + "_monitor.log").open("a") as out, \
            path.with_name(path.stem + "_monitor.err").open("a") as err:
        monitor = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("monitor_exp213_job.py")),
             "--config", str(path.resolve()), "--receipt", str(monitor_receipt.resolve())],
            stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    receipt = {**partial, "monitor_pid": monitor.pid, "monitor_receipt": str(monitor_receipt)}
    path.with_name(path.stem + "_launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "LAUNCHED_EXP234_TARGET_CHUNK", "source": source,
                      "chunk": index, "lease": lease["id"], "gpu": config["gpu"],
                      "monitor_pid": monitor.pid}))


if __name__ == "__main__":
    main()
