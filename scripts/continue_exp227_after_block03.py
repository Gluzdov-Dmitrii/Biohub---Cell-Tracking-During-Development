"""Finite block03 -> source20 graphs -> official source8 score handoff."""
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import time

from monitor_exp213_job import QUEUE, ssh
from run_exp227_source_graph20 import INNER_IDS, REMOTE, TRAIN_RUN, RUN as GRAPH_RUN


ROOT = Path(__file__).resolve().parents[1]
TRAIN_LEASE = "exp227-horaz-source-block03-20260927"
GRAPH_LEASE = "exp227-source-graph20-v1-20260927"
SCORE_RUN = REMOTE + "/runs/exp227_source_graph20_official_v1_20260927"
RECEIPT = ROOT / "reports/exp227_source20_handoff_20260927.json"
GRAPH_PREPARE = ROOT / "scripts/prepare_exp227_source_graph20.py"
GRAPH_LAUNCH = ROOT / "scripts/launch_exp227_source_graph20.py"
GRAPH_CONFIG = ROOT / "reports/exp227_source_graph20_config_20260927.json"
GRAPH_PREPARED = ROOT / "reports/exp227_source_graph20_prepare_20260927.json"
GRAPH_LAUNCHED = ROOT / "reports/exp227_source_graph20_config_20260927_launch.json"
SCORE_PREPARE = ROOT / "scripts/prepare_exp227_source_graph20_scorer.py"
SCORE_LAUNCH = ROOT / "scripts/launch_exp227_source_graph20_scorer.py"
SCORE_VERIFY = ROOT / "scripts/verify_exp227_source_graph20_scorer.py"
SCORE_PREPARED = ROOT / "reports/exp227_source_graph20_scorer_prepare_20260927.json"
SCORE_LAUNCHED = ROOT / "reports/exp227_source_graph20_scorer_launch_20260927.json"
SCORE_VERIFIED = ROOT / "reports/exp227_source_graph20_score_20260927.json"


def save(value):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(RECEIPT)


def queue_lease(lease_id, expected_run):
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    matching = [row for row in queue["requests"] if row["id"] == lease_id]
    assert len(matching) == 1, f"Expected one queue lease for {lease_id}"
    lease = matching[0]
    assert lease["run_path"] == expected_run
    return lease


def probe_gpu_run(run, alias):
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
history=read('output/fold1/history.json') if @@TRAIN@@ else None
result=read('output/result.json') if @@TRAIN@@ else None
status=read('output/status.json') if not @@TRAIN@@ else None
ex=read('exit.json');complete=read('supervision/complete.json')
control=read('supervision/control.json')
print(json.dumps({'epochs':len(history) if history else None,
 'last_epoch':history[-1]['epoch'] if history else None,
 'result_status':result.get('status') if result else None,
 'completed_epochs':result.get('completed_epochs') if result else None,
 'target_data_opened':result.get('target_data_opened') if result else None,
 'status':status.get('status') if status else None,
 'movies':status.get('movies') if status else None,
 'records':len(status['records']) if status else None,
 'source_labels_read':status.get('source_labels_read') if status else None,
 'target_labels_read':status.get('target_labels_read') if status else None,
 'exit':ex,'complete_status':complete.get('status') if complete else None,
 'control_state':control.get('queue',{}).get('state') if control else None,
 'checkpoint20_exists':(run/'output/fold1/epoch_020.pt').is_file() if @@TRAIN@@ else None,
 'output_names':sorted(p.name for p in (run/'output').iterdir()) if (run/'output').is_dir() and not @@TRAIN@@ else None}))
'''.replace("@@RUN@@", repr(run)).replace("@@TRAIN@@", str(run == TRAIN_RUN))
    return ssh(alias, "python3 -", source)


def probe_score():
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
ex=read('exit.json');result=read('output/result.json')
print(json.dumps({'exit':ex,'result_status':result.get('status') if result else None,
 'rows':len(result['rows']) if result else None,
 'source_score':result.get('summary',{}).get('score') if result else None}))
'''.replace("@@RUN@@", repr(SCORE_RUN))
    return ssh("nsu-quadro", "python3 -", source)


def check_training(lease, observed):
    if lease["state"] in ("CANCELLED", "FAILED"):
        raise RuntimeError(f"Training lease ended in {lease['state']}")
    ex = observed["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["hard_timeout"] is not False):
        raise RuntimeError("EXP227 block03 worker failed or timed out")
    if observed["result_status"] is not None and observed["result_status"] != "PASS_FULL_SOURCE_BLOCK_20_OF_50":
        raise RuntimeError(f"EXP227 block03 result failed: {observed['result_status']}")
    if lease["state"] == "RELEASED":
        assert observed["complete_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert observed["control_state"] == "RELEASED"
        assert ex is not None and ex["returncode"] == 0
        assert observed["result_status"] == "PASS_FULL_SOURCE_BLOCK_20_OF_50"
        assert observed["completed_epochs"] == observed["epochs"] == observed["last_epoch"] == 20
        assert observed["target_data_opened"] is False
        assert observed["checkpoint20_exists"] is True
        return True
    return False


def check_graph(lease, observed):
    if lease["state"] in ("CANCELLED", "FAILED"):
        raise RuntimeError(f"Source20 graph lease ended in {lease['state']}")
    ex = observed["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["hard_timeout"] is not False):
        raise RuntimeError("Source20 graph worker failed or timed out")
    if observed["status"] is not None and observed["status"] != "PASS_EXP227_SOURCE_GRAPH20_NO_LABELS":
        raise RuntimeError(f"Source20 graph result failed: {observed['status']}")
    if lease["state"] == "RELEASED":
        assert observed["complete_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert observed["control_state"] == "RELEASED"
        assert ex is not None and ex["returncode"] == 0
        assert observed["status"] == "PASS_EXP227_SOURCE_GRAPH20_NO_LABELS"
        assert observed["source_labels_read"] is False and observed["target_labels_read"] is False
        assert observed["movies"] == list(INNER_IDS) and observed["records"] == 8
        expected = {"status.json"} | {"graph__" + name + suffix
                                      for name in INNER_IDS for suffix in (".csv", ".json")}
        assert set(observed["output_names"]) == expected
        return True
    return False


def check_score(observed):
    ex = observed["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["timeout"] is not False):
        raise RuntimeError("Source20 official scorer failed or timed out")
    if observed["result_status"] is not None and observed["result_status"] != "PASS_EXP227_SOURCE_GRAPH20_OFFICIAL":
        raise RuntimeError(f"Source20 official score failed: {observed['result_status']}")
    if ex is not None:
        assert observed["result_status"] == "PASS_EXP227_SOURCE_GRAPH20_OFFICIAL"
        assert observed["rows"] == 8 and math.isfinite(observed["source_score"])
        return True
    return False


def wait_for(name, seconds, interval, probe, check, result):
    deadline = time.monotonic() + seconds
    errors = 0
    while time.monotonic() < deadline:
        try:
            state = probe()
            errors = 0
            result.pop("last_observation_error", None)
        except Exception as exc:
            errors += 1
            result["last_observation_error"] = repr(exc)
            result["consecutive_observation_errors"] = errors
            save(result)
            if errors >= 5:
                raise RuntimeError(f"Five consecutive {name} observation failures") from exc
            time.sleep(interval)
            continue
        if check(state):
            result[name + "_release_or_exit"] = state
            save(result)
            return state
        snapshot = json.dumps(state, sort_keys=True)
        if result.get(name + "_last_snapshot") != snapshot:
            result[name + "_last_snapshot"] = snapshot
            save(result)
        time.sleep(interval)
    raise TimeoutError(f"{name} did not reach a verified terminal state within {seconds}s")


def run_step(name, script, result):
    step = subprocess.run([sys.executable, str(script)], text=True, capture_output=True,
                          timeout=180, cwd=ROOT)
    log_path = ROOT / f"reports/exp227_source20_handoff_{name}_20260927.log"
    log_path.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    result[name + "_log"] = str(log_path)
    result[name + "_returncode"] = step.returncode
    save(result)
    if step.returncode:
        raise RuntimeError(f"{name} returned {step.returncode}; see {log_path}")


def main():
    assert not RECEIPT.exists(), "Existing handoff must be reconciled, never restarted blindly"
    assert not any(path.exists() for path in (GRAPH_CONFIG, GRAPH_PREPARED, GRAPH_LAUNCHED,
                                                SCORE_PREPARED, SCORE_LAUNCHED, SCORE_VERIFIED))
    result = {"status": "WAITING_FOR_EXP227_BLOCK03_RELEASE",
              "training_run": TRAIN_RUN, "source_graph_run": GRAPH_RUN,
              "source_score_run": SCORE_RUN, "source_labels_opened_before_inference": False,
              "target_labels_opened": False, "started": time.time()}
    save(result)
    try:
        wait_for("training", 24000, 90,
                 lambda: (queue_lease(TRAIN_LEASE, TRAIN_RUN),
                          probe_gpu_run(TRAIN_RUN, "nsu-a100")),
                 lambda state: check_training(*state), result)
        result["status"] = "TRAINING_RELEASED_PREPARING_SOURCE20_GRAPHS"
        save(result)
        run_step("prepare_graph", GRAPH_PREPARE, result)
        assert GRAPH_CONFIG.is_file() and GRAPH_PREPARED.is_file()
        result["status"] = "SOURCE20_GRAPHS_STAGED_LAUNCHING"
        save(result)
        run_step("launch_graph", GRAPH_LAUNCH, result)
        assert GRAPH_LAUNCHED.is_file()
        result["status"] = "WAITING_FOR_SOURCE20_GRAPH_RELEASE"
        save(result)
        wait_for("graph", 5400, 90,
                 lambda: (queue_lease(GRAPH_LEASE, GRAPH_RUN),
                          probe_gpu_run(GRAPH_RUN,
                                        json.loads(GRAPH_CONFIG.read_text())["alias"])),
                 lambda state: check_graph(*state), result)
        result["status"] = "SOURCE20_NO_LABEL_GRAPHS_RELEASED_AUDITING"
        save(result)
        run_step("prepare_score", SCORE_PREPARE, result)
        assert SCORE_PREPARED.is_file()
        result["status"] = "SOURCE20_SCORER_STAGED_LAUNCHING"
        save(result)
        run_step("launch_score", SCORE_LAUNCH, result)
        assert SCORE_LAUNCHED.is_file()
        result["status"] = "WAITING_FOR_SOURCE20_OFFICIAL_SCORE"
        save(result)
        wait_for("score", 2700, 90, probe_score, check_score, result)
        result["status"] = "SOURCE20_OFFICIAL_SCORER_EXITED_VERIFYING"
        save(result)
        run_step("verify_score", SCORE_VERIFY, result)
        assert SCORE_VERIFIED.is_file()
        verified = json.loads(SCORE_VERIFIED.read_text())
        assert verified["status"] == "VERIFIED_EXP227_SOURCE20_OFFICIAL"
        assert verified["source_labels_read"] is True and verified["target_labels_read"] is False
        result["source_score_receipt"] = str(SCORE_VERIFIED)
        result["status"] = "PASS_EXP227_SOURCE20_OFFICIAL_HANDOFF"
    except BaseException as exc:
        result["status"] = "STOPPED_EXP227_SOURCE20_HANDOFF"
        result["error"] = repr(exc)
        raise
    finally:
        result["finished_or_stopped"] = time.time()
        save(result)


if __name__ == "__main__":
    main()
