"""Launch one bounded EXP234 source-selection job on a leased A100."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh


ROOT = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def main():
    path = Path(sys.argv[1])
    config = json.loads(path.read_text())
    assert config["experiment"] == "EXP234" and config["pool"] == "a100"
    assert config["max_seconds"] <= 10800
    assert config["code"].startswith(ROOT + "/code/exp234_")
    assert config["run"].startswith(ROOT + "/runs/exp234_")
    assert config["script"] == "run_exp234_source_threshold.py"
    assert config["arguments"][1] == "--plan-sha256"
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    assert not any(r["id"] == config["lease_id"] for r in state["requests"]), "Existing lease: reconcile"
    assert not any(r["state"].startswith("WAITING") and
                   r["project"] != "biohub-cell-tracking-during-development"
                   for r in state["requests"]), "Other project is waiting"
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
config=r/'config.json';config.write_text(json.dumps(c,indent=2)+'\\n')
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
assert c['gpu'] not in busy,'Allocated GPU physically busy'
records={}
for name,cmd in [('wrapper',[ROOT+'/envs/prepost/py3.11-stdlib-v1/bin/python',c['code']+'/exp214_inference_job.py',str(config)]),
                 ('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(config)])]:
 with (r/(name+'.log')).open('w') as out:
  proc=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=proc.pid
print(json.dumps(records))
'''.replace("CONFIG", repr(config)).replace("ROOT", repr(ROOT))
    launch = ssh("nsu-a100", "python3 -", launch_source)
    partial = {"lease": lease, "launch": launch, "config": config}
    path.with_name(path.stem + "_partial_launch.json").write_text(json.dumps(partial, indent=2) + "\n")
    # The A100 run directory is local to ngpu01. The queue mutates only via
    # nsu-quadro, so use the existing verified Windows-side monitor.
    monitor_receipt = path.with_name(path.stem + "_monitor.json")
    monitor_out = path.with_name(path.stem + "_monitor.log")
    monitor_err = path.with_name(path.stem + "_monitor.err")
    with monitor_out.open("a") as out, monitor_err.open("a") as err:
        monitor = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("monitor_exp213_job.py")),
             "--config", str(path.resolve()), "--receipt", str(monitor_receipt.resolve())],
            stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    receipt = {**partial, "monitor_pid": monitor.pid,
               "monitor_receipt": str(monitor_receipt)}
    path.with_name(path.stem + "_launch.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "LAUNCHED_EXP234_SOURCE", "lease": lease["id"],
                      "host": lease["host"], "gpu": config["gpu"],
                      "run": config["run"], "wrapper": launch["wrapper"],
                      "monitor_pid": monitor.pid}))


if __name__ == "__main__":
    main()
