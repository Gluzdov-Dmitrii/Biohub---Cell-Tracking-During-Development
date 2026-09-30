"""Finite EXP236 v2 epoch10 -> source6bba inner11 graph/score handoff.

Start once against the existing training controller. The graph runner has no
label access; the guarded scorer may read source6bba labels only after the
eleven graph hashes, worker exit and queue release have been verified.
"""
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import time

from monitor_exp213_job import QUEUE, ssh
from prepare_exp236_source_graph10_v2 import (
    CONFIG_PATH as GRAPH_CONFIG, CONTROLLER_RECEIPT as TRAIN_CONTROLLER,
    PLAN_PATH as GRAPH_PLAN,
    PREPARE_PATH as GRAPH_PREPARED, verify_parent_chain,
)
from run_exp236_source_graph10_v2 import INNER_IDS, RUN as GRAPH_RUN, TRAIN_RUN
from prepare_exp236_source_graph10_scorer import RUN as SCORE_RUN


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp236_source10_handoff_20260927.json"
GRAPH_LEASE = "exp236-source-graph10-v2-20260927"
GRAPH_LAUNCHED = GRAPH_CONFIG.with_name(GRAPH_CONFIG.stem + "_launch.json")
GRAPH_RESERVATION = GRAPH_CONFIG.with_name(GRAPH_CONFIG.stem + "_reservation.json")
GRAPH_PARTIAL = GRAPH_CONFIG.with_name(GRAPH_CONFIG.stem + "_partial_launch.json")
GRAPH_PRELAUNCH_RELEASE = GRAPH_CONFIG.with_name(GRAPH_CONFIG.stem + "_prelaunch_release.json")
SCORE_PREPARED = ROOT / "reports/exp236_source_graph10_scorer_prepare_20260927.json"
SCORE_LAUNCHED = ROOT / "reports/exp236_source_graph10_scorer_launch_20260927.json"
SCORE_VERIFIED = ROOT / "reports/exp236_source_graph10_score_20260927.json"
INTERVAL_SECONDS = 120
PROJECT = "biohub-cell-tracking-during-development"


class TerminalAnomaly(RuntimeError):
    """An observed failure that must stop this one-shot controller."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(state):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(RECEIPT)


def claim(state):
    with RECEIPT.open("x") as handle:
        handle.write(json.dumps(state, indent=2) + "\n")


def queue_status():
    return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))


def lease_for(queue, lease_id, run):
    matching = [row for row in queue["requests"] if row["id"] == lease_id]
    if len(matching) != 1:
        raise TerminalAnomaly(f"Expected one lease for {lease_id}")
    lease = matching[0]
    if lease["run_path"] != run or lease["pool"] != "a100":
        raise TerminalAnomaly(f"Changed lease identity for {lease_id}")
    return lease


def controller_probe():
    controller = json.loads(TRAIN_CONTROLLER.read_text())
    status = controller["status"]
    if status.startswith("STOPPED_"):
        raise TerminalAnomaly(f"EXP236 training controller stopped: {controller.get('error')}")
    if status == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED":
        try:
            chain, receipt_sha = verify_parent_chain()
            assert len(chain) == 4
            assert [row["completed_epochs"] for row in chain] == [3, 6, 9, 10]
            assert chain[-1]["run"] == TRAIN_RUN
            assert controller["final_audit"] == {
                key: value for key, value in chain[-1].items() if key not in ("code", "run")
            }
        except (AssertionError, KeyError, ValueError) as exc:
            raise TerminalAnomaly("EXP236 epoch10 chain failed release/hash audit") from exc
        return {"status": status, "controller_sha256": receipt_sha,
                "checkpoint_sha256": chain[-1]["checkpoint_sha256"],
                "training_result_sha256": chain[-1]["result_sha256"]}
    if not (status.startswith(("WAITING_FOR_", "AUDITING_", "PREPARING_", "LAUNCHING_"))
            and "EXP236" in status):
        raise TerminalAnomaly(f"Unknown EXP236 controller state: {status}")
    return {"status": status}


def controller_released(observed):
    return observed["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"


def physical_busy():
    source = '''import json,subprocess
raw=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid',
                             '--format=csv,noheader'],text=True)
lines=[line.strip() for line in raw.splitlines() if line.strip()]
assert all(line.startswith('GPU-') for line in lines),lines
print(json.dumps({'busy_gpu_uuids':sorted(set(lines))}))
'''
    return set(ssh("nsu-a100", "python3 -", source)["busy_gpu_uuids"])


def resource_probe():
    if any(path.exists() for path in (GRAPH_RESERVATION, GRAPH_PARTIAL,
                                      GRAPH_PRELAUNCH_RELEASE, GRAPH_LAUNCHED)):
        raise TerminalAnomaly("EXP236 graph launch artifact appeared while waiting")
    queue = queue_status()
    parent_id = "exp236-horaz-source6bba-block04-v2-20260927"
    if lease_for(queue, parent_id, TRAIN_RUN)["state"] != "RELEASED":
        raise TerminalAnomaly("EXP236 block04 release changed")
    if any(row["id"] == GRAPH_LEASE for row in queue["requests"]):
        raise TerminalAnomaly("EXP236 graph lease already exists")
    waiting = [row["id"] for row in queue["requests"]
               if row["project"] != PROJECT and row["state"].startswith("WAITING")]
    pool = set(queue["pools"]["a100"]["gpus"])
    allocated = {gpu for row in queue["requests"]
                 if row["pool"] == "a100" and row["state"] in ("RUNNING", "RESERVED")
                 for gpu in row.get("gpus", [])}
    free = pool - allocated
    if waiting or not free:
        return {"foreign_waiting": waiting, "queue_free": len(free), "idle_free": 0}
    return {"foreign_waiting": [], "queue_free": len(free),
            "idle_free": len(free - physical_busy())}


def resource_ready(observed):
    return not observed["foreign_waiting"] and observed["idle_free"] > 0


def graph_probe():
    prepared = json.loads(GRAPH_PREPARED.read_text())
    config = json.loads(GRAPH_CONFIG.read_text())
    launch = json.loads(GRAPH_LAUNCHED.read_text())
    if prepared["status"] != "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS":
        raise TerminalAnomaly("Changed EXP236 graph preparation")
    if prepared["controller_receipt_sha256"] != sha(TRAIN_CONTROLLER):
        raise TerminalAnomaly("Changed EXP236 training controller receipt")
    if sha(GRAPH_PLAN) != prepared["stage"]["plan_sha256"]:
        raise TerminalAnomaly("Changed EXP236 graph plan")
    if launch["config"] != config or launch["lease"]["id"] != GRAPH_LEASE:
        raise TerminalAnomaly("Changed EXP236 graph launch receipt")
    queue = queue_status()
    lease = lease_for(queue, GRAPH_LEASE, GRAPH_RUN)
    if lease["alias"] != config["alias"]:
        raise TerminalAnomaly("EXP236 graph lease alias changed")
    source = '''import hashlib,json,pathlib
run=pathlib.Path(@@RUN@@)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
status=read('output/status.json');ex=read('exit.json')
complete=read('supervision/complete.json');control=read('supervision/control.json')
audit_error=None;hashes=[]
if status is not None:
 try:
  for row in status['records']:
   name=row['dataset'];csv=run/'output'/('graph__'+name+'.csv')
   receipt=csv.with_suffix('.json')
   assert pathlib.Path(row['csv']).resolve()==csv.resolve()
   assert sha(csv)==row['csv_sha256']
   assert json.loads(receipt.read_text())==row
   hashes.append({'dataset':name,'csv_sha256':sha(csv),'receipt_sha256':sha(receipt)})
 except Exception as err:audit_error=repr(err)
print(json.dumps({'status':status.get('status') if status else None,
 'movies':status.get('movies') if status else None,
 'records':[row.get('dataset') for row in status['records']] if status else None,
 'checkpoint_sha256':status.get('checkpoint_sha256') if status else None,
 'plan_sha256':status.get('plan_sha256') if status else None,
 'source_labels_read':status.get('source_labels_read') if status else None,
 'target_labels_read':status.get('target_labels_read') if status else None,
 'target_data_opened':status.get('target_data_opened') if status else None,
 'output_names':sorted(p.name for p in (run/'output').iterdir()) if (run/'output').is_dir() else None,
 'hashes':hashes,'audit_error':audit_error,'exit':ex,
 'complete_status':complete.get('status') if complete else None,
 'supervision_exit_matches':complete.get('exit')==ex if complete and ex else None,
 'control_state':control.get('queue',{}).get('state') if control else None,
 'control_run_matches':pathlib.Path(control['queue']['run_path']).resolve()==run.resolve() if control else None}))
'''.replace("@@RUN@@", repr(GRAPH_RUN))
    return {"lease_state": lease["state"],
            "remote": ssh(config["alias"], "python3 -", source),
            "checkpoint_sha256": prepared["preflight"]["checkpoint_sha256"],
            "plan_sha256": prepared["stage"]["plan_sha256"]}


def graph_released(observed):
    state = observed["lease_state"]
    remote = observed["remote"]
    if state not in ("RESERVED", "RUNNING", "RELEASED"):
        raise TerminalAnomaly(f"EXP236 graph lease entered {state}")
    ex = remote["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["hard_timeout"] is not False):
        raise TerminalAnomaly("EXP236 graph worker failed or timed out")
    if remote["status"] is not None and remote["status"] != "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS":
        raise TerminalAnomaly(f"EXP236 graph status: {remote['status']}")
    if remote["audit_error"] is not None:
        raise TerminalAnomaly(f"EXP236 graph hash audit: {remote['audit_error']}")
    for key in ("source_labels_read", "target_labels_read", "target_data_opened"):
        if remote[key] not in (None, False):
            raise TerminalAnomaly(f"EXP236 graph attempted forbidden access: {key}")
    if state == "RELEASED":
        assert ex is not None and ex["returncode"] == 0
        assert remote["complete_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert remote["supervision_exit_matches"] is True
        assert remote["control_state"] == "RELEASED" and remote["control_run_matches"] is True
        assert remote["status"] == "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS"
        assert remote["movies"] == remote["records"] == [*INNER_IDS]
        assert [row["dataset"] for row in remote["hashes"]] == [*INNER_IDS]
        assert remote["checkpoint_sha256"] == observed["checkpoint_sha256"]
        assert remote["plan_sha256"] == observed["plan_sha256"]
        assert all(remote[key] is False for key in
                   ("source_labels_read", "target_labels_read", "target_data_opened"))
        expected = {"status.json"} | {"graph__" + name + suffix
                                      for name in INNER_IDS for suffix in (".csv", ".json")}
        assert set(remote["output_names"]) == expected
        return True
    return False


def score_probe():
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
def read(name):
 path=run/name;return json.loads(path.read_text()) if path.is_file() else None
ex=read('exit.json');result=read('output/result.json');gate=read('output/no_metric_gate.json')
print(json.dumps({'exit':ex,'result_status':result.get('status') if result else None,
 'rows':[row.get('dataset') for row in result['rows']] if result else None,
 'source_score':result.get('summary',{}).get('score') if result else None,
 'source_labels_read':result.get('source_labels_read') if result else None,
 'target_labels_read':result.get('target_labels_read') if result else None,
 'target_data_opened':result.get('target_data_opened') if result else None,
 'gate_status':gate.get('status') if gate else None}))
'''.replace("@@RUN@@", repr(SCORE_RUN))
    return ssh("nsu-quadro", "python3 -", source)


def score_exited(observed):
    ex = observed["exit"]
    if ex is not None and (ex["returncode"] != 0 or ex["timeout"] is not False):
        raise TerminalAnomaly("EXP236 official source scorer failed or timed out")
    if observed["result_status"] is not None and observed["result_status"] != (
            "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL"):
        raise TerminalAnomaly(f"EXP236 source score status: {observed['result_status']}")
    if observed["target_labels_read"] not in (None, False) or observed["target_data_opened"] not in (None, False):
        raise TerminalAnomaly("EXP236 scorer attempted target data")
    if ex is not None:
        assert observed["result_status"] == "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL"
        assert observed["rows"] == [*INNER_IDS]
        assert observed["source_labels_read"] is True
        assert observed["target_labels_read"] is False and observed["target_data_opened"] is False
        assert observed["gate_status"] == "PASS_EXP236_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS"
        assert isinstance(observed["source_score"], (int, float))
        assert math.isfinite(observed["source_score"])
        return True
    return False


def wait_for(name, seconds, probe, check, state):
    deadline = time.monotonic() + seconds
    errors = 0
    while time.monotonic() < deadline:
        try:
            observed = probe()
            errors = 0
            state.pop("last_observation_error", None)
        except TerminalAnomaly:
            raise
        except Exception as exc:
            errors += 1
            state["last_observation_error"] = repr(exc)
            state["consecutive_observation_errors"] = errors
            save(state)
            if errors >= 5:
                raise RuntimeError(f"Five consecutive {name} observation failures") from exc
            time.sleep(INTERVAL_SECONDS)
            continue
        if check(observed):
            state[name + "_verified"] = observed
            save(state)
            return observed
        snapshot = json.dumps(observed, sort_keys=True)
        if state.get(name + "_last_snapshot") != snapshot:
            state[name + "_last_snapshot"] = snapshot
            save(state)
        time.sleep(INTERVAL_SECONDS)
    raise TimeoutError(f"{name} did not reach its verified state within {seconds}s")


def run_step(name, script, timeout, state):
    log_path = ROOT / f"reports/exp236_source10_handoff_{name}_20260927.log"
    try:
        step = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True,
                              capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log_path.write_text(out + "\n--- stderr ---\n" + err)
        state[name + "_log"] = str(log_path)
        state[name + "_timeout"] = True
        save(state)
        raise RuntimeError(f"{name} exceeded {timeout}s; reconcile {log_path}") from exc
    log_path.write_text(step.stdout + "\n--- stderr ---\n" + step.stderr)
    state[name + "_log"] = str(log_path)
    state[name + "_returncode"] = step.returncode
    save(state)
    if step.returncode:
        raise RuntimeError(f"{name} returned {step.returncode}; reconcile {log_path}")


def main():
    assert TRAIN_CONTROLLER.is_file(), "Existing EXP236 training controller receipt required"
    assert not RECEIPT.exists(), "Existing handoff receipt must be reconciled, never restarted"
    assert not any(path.exists() for path in (
        GRAPH_PLAN, GRAPH_CONFIG, GRAPH_PREPARED, GRAPH_LAUNCHED,
        GRAPH_RESERVATION, GRAPH_PARTIAL, GRAPH_PRELAUNCH_RELEASE,
        SCORE_PREPARED, SCORE_LAUNCHED, SCORE_VERIFIED,
    )), "Existing graph/scorer artifact must be reconciled before handoff"
    state = {"status": "WAITING_FOR_EXP236_EPOCH10_V2_RELEASE",
             "training_run": TRAIN_RUN, "source_graph_run": GRAPH_RUN,
             "source_score_run": SCORE_RUN, "source_labels_opened_before_graphs": False,
             "target_data_opened": False, "started": time.time()}
    claim(state)
    try:
        parent = wait_for("training", 172800, controller_probe, controller_released, state)
        state["training_controller_sha256"] = parent["controller_sha256"]
        state["status"] = "EXP236_EPOCH10_RELEASED_PREPARING_SOURCE11_GRAPHS"
        save(state)
        run_step("prepare_graph", ROOT / "scripts/prepare_exp236_source_graph10_v2.py", 900, state)
        assert GRAPH_PLAN.is_file() and GRAPH_CONFIG.is_file() and GRAPH_PREPARED.is_file()
        prepared = json.loads(GRAPH_PREPARED.read_text())
        assert prepared["controller_receipt_sha256"] == parent["controller_sha256"]
        assert prepared["preflight"]["checkpoint_sha256"] == parent["checkpoint_sha256"]
        state["status"] = "WAITING_FOR_FAIR_EXP236_SOURCE11_GRAPH_RESOURCE"
        save(state)
        wait_for("graph_resource", 86400, resource_probe, resource_ready, state)
        state["status"] = "EXP236_SOURCE11_GRAPHS_STAGED_LAUNCHING"
        save(state)
        run_step("launch_graph", ROOT / "scripts/launch_exp236_source_graph10_v2.py", 300, state)
        assert GRAPH_LAUNCHED.is_file()
        state["status"] = "WAITING_FOR_EXP236_SOURCE11_GRAPH_RELEASE"
        save(state)
        wait_for("graph", 9000, graph_probe, graph_released, state)
        state["status"] = "EXP236_SOURCE11_NO_LABEL_GRAPHS_RELEASED_AUDITING"
        save(state)
        run_step("prepare_score", ROOT / "scripts/prepare_exp236_source_graph10_scorer.py", 900, state)
        assert SCORE_PREPARED.is_file()
        prepared_score = json.loads(SCORE_PREPARED.read_text())
        assert prepared_score["preflight"]["status"] == "PASS_EXP236_SOURCE10_SCORER_PREFLIGHT"
        assert [row["dataset"] for row in prepared_score["preflight"]["hashes"]] == [*INNER_IDS]
        state["status"] = "EXP236_SOURCE11_SCORER_STAGED_LAUNCHING"
        save(state)
        run_step("launch_score", ROOT / "scripts/launch_exp236_source_graph10_scorer.py", 300, state)
        assert SCORE_LAUNCHED.is_file()
        state["status"] = "WAITING_FOR_EXP236_SOURCE11_OFFICIAL_SCORE"
        save(state)
        wait_for("score", 2700, score_probe, score_exited, state)
        state["status"] = "EXP236_SOURCE11_OFFICIAL_SCORER_EXITED_VERIFYING"
        save(state)
        run_step("verify_score", ROOT / "scripts/verify_exp236_source_graph10_scorer.py", 300, state)
        assert SCORE_VERIFIED.is_file()
        verified = json.loads(SCORE_VERIFIED.read_text())
        assert verified["status"] == "VERIFIED_EXP236_SOURCE10_OFFICIAL"
        assert verified["rows"] == 11 and math.isfinite(verified["source_score"])
        assert verified["source_labels_read"] is True and verified["target_labels_read"] is False
        state["source_score_receipt"] = str(SCORE_VERIFIED)
        state["source_score_receipt_sha256"] = sha(SCORE_VERIFIED)
        state["status"] = "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF"
    except BaseException as exc:
        state["status"] = "STOPPED_EXP236_SOURCE11_HANDOFF"
        state["error"] = repr(exc)
        raise
    finally:
        state["finished_or_stopped"] = time.time()
        save(state)


if __name__ == "__main__":
    main()
