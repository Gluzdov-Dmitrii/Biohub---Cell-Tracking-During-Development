"""Finite no-label EXP234 target rollout; stop on the first failed chunk."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import psutil

from monitor_exp213_job import ssh
from prepare_exp234_target_rollout_v2 import local_freeze


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp234_target_rollout_v2_20260927"
RECEIPT = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
SEQUENCE = [("6bba", i) for i in range(4)] + [("44b6", i) for i in range(8)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(result):
    RECEIPT.write_text(json.dumps(result, indent=2) + "\n")


def check_release(source, index, assignment, choices):
    token = f"{source}_chunk{index:02d}"
    config_path = ROOT / f"reports/exp234_target_{token}_config_v2_20260927.json"
    config = json.loads(config_path.read_text())
    assert config["code"] == CODE and config["script"] == "run_exp234_target_chunk.py"
    assert config["run"] == REMOTE + f"/runs/exp234_target_{token}_v2_20260927"
    assert config["arguments"] == [CODE + f"/{token}_plan.json", "--plan-sha256",
                                   config["arguments"][2]]
    monitor_path = config_path.with_name(config_path.stem + "_monitor.json")
    monitor = json.loads(monitor_path.read_text())
    assert monitor["monitor_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert monitor["queue"]["state"] == "RELEASED"
    assert monitor["queue"]["id"] == config["lease_id"]
    assert monitor["exit"]["returncode"] == 0
    assert monitor["exit"]["hard_timeout"] is False
    assert monitor["identity_alive"] is False and monitor["group_alive"] is False
    assert monitor["gpu_pids"] == []
    assert monitor["launch"]["config"] == config
    status = monitor["status"]
    assert status["status"] == "PASS_EXP234_TARGET_CHUNK_NO_LABELS"
    assert status["source_embryo"] == source and status["chunk_index"] == index
    assert status["selected_threshold"] == choices[source]["selected_threshold"]
    assert status["source_selection_result_sha256"] == choices[source]["result_sha256"]
    assert status["plan_sha256"] == config["arguments"][2]
    assert status["movies"] == assignment["directions"][source]["chunks"][index]
    assert status["target_labels_read"] is False
    remote_source = '''import hashlib,json,pathlib
run=pathlib.Path(RUN);code=pathlib.Path(CODE)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((run/'output/status.json').read_text())
assert status==STATUS
assert json.loads((run/'exit.json').read_text())==EXIT
assert sha(run/'output/submission.csv')==status['csv_sha256']
assert sha(run/'output/inference_receipt.json')==status['receipt_sha256']
assert sha(code/'code_manifest.json')==MANIFEST_SHA
assert sha(code/PLAN_NAME)==status['plan_sha256']
print(json.dumps({'status':'PASS_EXP234_REMOTE_CHUNK_AUDIT','csv_sha256':status['csv_sha256'],
                  'receipt_sha256':status['receipt_sha256']}))
'''.replace("RUN", repr(config["run"])).replace("CODE", repr(CODE)).replace(
        "STATUS", repr(status)).replace("EXIT", repr(monitor["exit"])).replace(
        "MANIFEST_SHA", repr("0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4")).replace(
        "PLAN_NAME", repr(token + "_plan.json"))
    remote = ssh("nsu-a100", "python3 -", remote_source)
    assert remote["status"] == "PASS_EXP234_REMOTE_CHUNK_AUDIT"
    return {"source": source, "chunk": index, "movies": len(status["movies"]),
            "monitor_sha256": sha(monitor_path), "plan_sha256": status["plan_sha256"],
            "csv_sha256": remote["csv_sha256"], "receipt_sha256": remote["receipt_sha256"]}


def main():
    assert not RECEIPT.exists(), "Existing coordinator receipt: reconcile, never restart blindly"
    assignment, choices = local_freeze()
    prepared = json.loads((ROOT / "reports/exp234_target_prepare_v2_20260927.json").read_text())
    assert prepared["status"] == "PREPARED_EXP234_TARGET175_NO_LABELS"
    assert prepared["stage"]["manifest_sha256"] == "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4"
    assert prepared["assignment_sha256"] == sha(ROOT / "reports/exp234_target_chunk_assignment_20260926.json")
    result = {"status": "RUNNING_EXP234_TARGET_NO_LABEL_ROLLOUT", "started": time.time(),
              "code_manifest_sha256": prepared["stage"]["manifest_sha256"],
              "source_choices": prepared["source_choices"], "completed": [],
              "target_labels_read": False}
    save(result)
    try:
        for offset, (source, index) in enumerate(SEQUENCE):
            token = f"{source}_chunk{index:02d}"
            config_path = ROOT / f"reports/exp234_target_{token}_config_v2_20260927.json"
            launch_path = config_path.with_name(config_path.stem + "_launch.json")
            if offset == 0:
                assert launch_path.exists(), "First chunk must already be launched and inspected"
            else:
                assert not launch_path.exists(), "Unexpected prelaunched chunk: reconcile"
                launch = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/launch_exp234_target_chunk_v2.py"),
                     str(config_path)], text=True, capture_output=True, timeout=120)
                log = config_path.with_name(config_path.stem + "_coordinator_launch.log")
                log.write_text(launch.stdout + "\n--- stderr ---\n" + launch.stderr)
                if launch.returncode:
                    raise RuntimeError(f"Target {token} launch failed; see {log}")
            launched = json.loads(launch_path.read_text())
            monitor_pid = launched["monitor_pid"]
            monitor_path = config_path.with_name(config_path.stem + "_monitor.json")
            if not monitor_path.exists() or json.loads(monitor_path.read_text()).get("monitor_status") != "RELEASED_AFTER_VERIFIED_EXIT":
                try:
                    psutil.Process(monitor_pid).wait(timeout=11400)
                except psutil.NoSuchProcess:
                    pass
            record = check_release(source, index, assignment, choices)
            result["completed"].append(record)
            result["last_verified"] = time.time()
            save(result)
            print(json.dumps({"verified": token, "movies": record["movies"],
                              "completed_chunks": len(result["completed"])}), flush=True)
        assert len(result["completed"]) == 12
        assert sum(item["movies"] for item in result["completed"]) == 175
        result["status"] = "PASS_EXP234_TARGET175_NO_LABELS_RELEASED"
    except BaseException as exc:
        result["status"] = "STOPPED_EXP234_TARGET_ROLLOUT"
        result["error"] = repr(exc)
        raise
    finally:
        result["finished_or_stopped"] = time.time()
        save(result)


if __name__ == "__main__":
    main()
