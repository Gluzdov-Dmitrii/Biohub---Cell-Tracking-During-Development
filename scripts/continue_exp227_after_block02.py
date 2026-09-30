"""One finite handoff: released epoch10 training -> eight no-label source graphs."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

from monitor_exp213_job import QUEUE, ssh


ROOT = Path(__file__).resolve().parents[1]
RUN = ("/home/scientists/gluz_d_s/kaggle/projects/"
       "biohub-cell-tracking-during-development/runs/exp227_horaz_source_block02_20260927")
LEASE = "exp227-horaz-source-block02-20260927"
RECEIPT = ROOT / "reports/exp227_source10_handoff_20260927.json"
PREPARE = ROOT / "scripts/prepare_exp227_source_graph10.py"
LAUNCH = ROOT / "scripts/launch_exp227_remote.py"
CONFIG = ROOT / "reports/exp227_source_graph10_config_20260927.json"


def save(value):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(RECEIPT)


def probe():
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    matching = [row for row in queue["requests"] if row["id"] == LEASE]
    assert len(matching) == 1
    lease = matching[0]
    assert lease["run_path"] == RUN
    source = '''import json,pathlib
run=pathlib.Path(RUN)
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
history=read('output/fold1/history.json') or []
result=read('output/result.json');ex=read('exit.json');complete=read('supervision/complete.json')
print(json.dumps({'epochs':len(history),'last_epoch':history[-1]['epoch'] if history else None,
 'result_status':result.get('status') if result else None,
 'completed_epochs':result.get('completed_epochs') if result else None,
 'target_data_opened':result.get('target_data_opened') if result else None,
 'exit':ex,'complete_status':complete.get('status') if complete else None,
 'checkpoint10_exists':(run/'output/fold1/epoch_010.pt').is_file()}))
'''.replace("RUN", repr(RUN))
    observed = ssh("nsu-a100", "python3 -", source)
    return lease, observed


def run_step(name, args, result):
    step = subprocess.run(args, text=True, capture_output=True, timeout=180,
                          cwd=ROOT)
    log_path = ROOT / f"reports/exp227_source10_handoff_{name}_20260927.log"
    log_path.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    result[name + "_log"] = str(log_path)
    result[name + "_returncode"] = step.returncode
    save(result)
    if step.returncode:
        raise RuntimeError(f"{name} returned {step.returncode}; see {log_path}")


def main():
    assert not RECEIPT.exists(), "Existing handoff must be reconciled, never restarted blindly"
    assert not CONFIG.exists(), "Source graph config already exists; reconcile"
    result = {"status": "WAITING_FOR_EXP227_BLOCK02_RELEASE",
              "lease_id": LEASE, "training_run": RUN,
              "source_labels_opened": False, "target_labels_opened": False,
              "started": time.time()}
    save(result)
    deadline = time.monotonic() + 7200
    consecutive_errors = 0
    try:
        while time.monotonic() < deadline:
            try:
                lease, observed = probe()
                consecutive_errors = 0
            except Exception as exc:
                consecutive_errors += 1
                result["last_observation_error"] = repr(exc)
                result["consecutive_observation_errors"] = consecutive_errors
                save(result)
                if consecutive_errors >= 5:
                    raise RuntimeError("Five consecutive observation failures") from exc
                time.sleep(90)
                continue
            state = lease["state"]
            if state in ("CANCELLED", "FAILED"):
                raise RuntimeError(f"Training lease ended in {state}")
            if observed["exit"] is not None:
                exit_record = observed["exit"]
                if exit_record["returncode"] != 0 or exit_record["hard_timeout"] is not False:
                    raise RuntimeError("EXP227 training worker failed or timed out")
            if observed["result_status"] is not None and observed["result_status"] != "PASS_FULL_SOURCE_BLOCK_10_OF_50":
                raise RuntimeError(f"EXP227 training result failed: {observed['result_status']}")
            if state == "RELEASED" and observed["complete_status"] == "RELEASED_AFTER_VERIFIED_EXIT":
                assert observed["exit"] is not None
                assert observed["result_status"] == "PASS_FULL_SOURCE_BLOCK_10_OF_50"
                assert observed["completed_epochs"] == observed["epochs"] == observed["last_epoch"] == 10
                assert observed["target_data_opened"] is False
                assert observed["checkpoint10_exists"] is True
                result["training_release"] = {"queue_state": state, "observed": observed}
                result["status"] = "TRAINING_RELEASED_PREPARING_SOURCE10"
                save(result)
                run_step("prepare", [sys.executable, str(PREPARE)], result)
                assert CONFIG.is_file()
                result["status"] = "SOURCE10_STAGED_LAUNCHING"
                save(result)
                run_step("launch", [sys.executable, str(LAUNCH), str(CONFIG)], result)
                launch_receipt = CONFIG.with_name(CONFIG.stem + "_launch.json")
                assert launch_receipt.is_file()
                result["source10_launch_receipt"] = str(launch_receipt)
                result["status"] = "PASS_EXP227_SOURCE10_NO_LABEL_INFERENCE_LAUNCHED"
                return
            snapshot = {"queue_state": state, "epochs": observed["epochs"],
                        "complete_status": observed["complete_status"]}
            if result.get("last_observed") != snapshot:
                result["last_observed"] = snapshot
                save(result)
            time.sleep(90)
        result["status"] = "WAIT_TIMEOUT_EXP227_JOB_NOT_ASSUMED_TERMINAL"
    except BaseException as exc:
        result["status"] = "STOPPED_EXP227_SOURCE10_HANDOFF"
        result["error"] = repr(exc)
        raise
    finally:
        result["finished_or_stopped"] = time.time()
        save(result)


if __name__ == "__main__":
    main()
