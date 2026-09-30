"""Finite EXP234 target graph release -> one official175 CPU score handoff.

This controller only waits for the already-running no-label coordinator. It never
starts or changes target inference and stops after a verified official score.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import psutil

from finish_exp234_target_rollout_v2 import SEQUENCE, check_release
from monitor_exp213_job import ssh
from prepare_exp234_target_rollout_v2 import local_freeze


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
COORDINATOR = ROOT / "reports/exp234_target_recovery_v2_20260927.json"
TARGET_PREPARE = ROOT / "reports/exp234_target_prepare_v2_20260927.json"
RECEIPT = ROOT / "reports/exp234_target_score_handoff_20260927.json"
RELEASE = ROOT / "reports/exp234_target_release_manifest_v2_20260927.json"
SCORE_PREPARE = ROOT / "reports/exp234_target_official_scorer_prepare_20260927.json"
SCORE_LAUNCH = ROOT / "reports/exp234_target_official_scorer_launch_20260927.json"
SCORE_VERIFIED = ROOT / "reports/exp234_target_official_score_20260927.json"
PREPARE_SCRIPT = ROOT / "scripts/prepare_exp234_target_official_scorer.py"
LAUNCH_SCRIPT = ROOT / "scripts/launch_exp234_target_official_scorer.py"
VERIFY_SCRIPT = ROOT / "scripts/verify_exp234_target_official_scorer.py"
SCORE_RUN = ("/home/scientists/gluz_d_s/kaggle/projects/"
             "biohub-cell-tracking-during-development/runs/"
             "exp234_target_official_score175_20260927")
COORDINATOR_WAIT_SECONDS = 50 * 3600
SCORE_WAIT_SECONDS = 4400
SCORE_POLL_SECONDS = 90


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(value):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(RECEIPT)


def wait_coordinator():
    """Use an OS process wait, then require the separate recovery receipt."""
    initial = json.loads(COORDINATOR.read_text())
    assert (initial["status"].startswith("WAITING_FOR_") or
            initial["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED")
    assert initial["target_labels_read"] is False
    try:
        process = psutil.Process(initial["pid"])
    except psutil.NoSuchProcess:
        process = None
    if process is not None:
        assert abs(process.create_time() - initial["process_create_time"]) < 2, (
            "Coordinator PID reused")
        assert process.cwd().lower() == str(ROOT).lower()
        assert any(Path(arg).name == "recover_exp234_target_rollout_v2.py"
                   for arg in process.cmdline()), "Unexpected coordinator process"
        try:
            code = process.wait(timeout=COORDINATOR_WAIT_SECONDS)
        except psutil.NoSuchProcess:
            code = None
        if code is not None and code != 0:
            raise RuntimeError(f"EXP234 coordinator exited {code}")
    final = json.loads(COORDINATOR.read_text())
    assert final["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    assert final["target_labels_read"] is False
    assert "error" not in final
    assert len(final["completed"]) == 12
    assert sum(item["movies"] for item in final["completed"]) == 175
    assert "finished_or_stopped" in final
    return final


def verify_coordinator(final):
    """Repeat the exact coordinator release and remote hash audit before scoring."""
    original = json.loads(ORIGINAL.read_text())
    assert original["status"] == "STOPPED_EXP234_TARGET_ROLLOUT"
    assert original["target_labels_read"] is False
    assert len(original["completed"]) == 5
    assert final["original_coordinator_sha256"] == sha(ORIGINAL)
    assert final["completed"][:5] == original["completed"]
    assignment, choices = local_freeze()
    prepared = json.loads(TARGET_PREPARE.read_text())
    assert prepared["status"] == "PREPARED_EXP234_TARGET175_NO_LABELS"
    assert prepared["target_labels_read"] is False
    assert prepared["stage"]["manifest_sha256"] == (
        "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4")
    assert prepared["assignment_sha256"] == sha(
        ROOT / "reports/exp234_target_chunk_assignment_20260926.json")
    assert final["code_manifest_sha256"] == prepared["stage"]["manifest_sha256"]
    selected = {source: {key: choices[source][key] for key in (
        "selected_threshold", "result_sha256", "gate_sha256")}
        for source in ("44b6", "6bba")}
    assert final["source_choices"] == prepared["source_choices"] == selected
    assert len(SEQUENCE) == 12 and len(final["completed"]) == 12
    checked = []
    for (source, index), item in zip(SEQUENCE, final["completed"]):
        assert item["source"] == source and item["chunk"] == index
        assert item["plan_sha256"] == prepared["stage"]["plan_sha256"][
            f"{source}_chunk{index:02d}_plan.json"]
        expected = check_release(source, index, assignment, choices)
        assert item == expected, f"Coordinator release/hash mismatch for {source} chunk{index:02d}"
        checked.append(expected)
    assert sum(item["movies"] for item in checked) == 175
    return {"chunks": len(checked), "movies": 175,
            "original_coordinator_sha256": sha(ORIGINAL),
            "coordinator_sha256": sha(COORDINATOR)}


def run_step(name, script, result):
    completed = subprocess.run([sys.executable, str(script)], cwd=ROOT, text=True,
                               capture_output=True, timeout=180)
    log_path = ROOT / f"reports/exp234_target_score_handoff_{name}_20260927.log"
    log_path.write_text(completed.stdout + "\n--- stderr ---\n" + completed.stderr)
    result[name + "_log"] = str(log_path)
    result[name + "_returncode"] = completed.returncode
    save(result)
    if completed.returncode:
        raise RuntimeError(f"{name} returned {completed.returncode}; see {log_path}")


def probe_score_exit():
    source = '''import json,pathlib
run=pathlib.Path(@@RUN@@)
path=run/'exit.json'
ex=json.loads(path.read_text()) if path.is_file() else None
print(json.dumps({'exit':ex}))
'''.replace("@@RUN@@", repr(SCORE_RUN))
    return ssh("nsu-quadro", "python3 -", source)


def check_score_exit(observed):
    ex = observed["exit"]
    if ex is None:
        return False
    if ex["returncode"] != 0 or ex["timeout"] is not False:
        raise RuntimeError("EXP234 official scorer failed or timed out")
    return True


def wait_score_exit(result):
    deadline = time.monotonic() + SCORE_WAIT_SECONDS
    errors = 0
    while time.monotonic() < deadline:
        try:
            observed = probe_score_exit()
            errors = 0
            result.pop("last_observation_error", None)
        except Exception as exc:
            errors += 1
            result["last_observation_error"] = repr(exc)
            result["consecutive_observation_errors"] = errors
            save(result)
            if errors >= 5:
                raise RuntimeError("Five consecutive scorer observation failures") from exc
            time.sleep(SCORE_POLL_SECONDS)
            continue
        if check_score_exit(observed):
            result["score_exit"] = observed["exit"]
            save(result)
            return
        time.sleep(SCORE_POLL_SECONDS)
    raise TimeoutError("EXP234 official scorer did not exit within observation bound")


def main():
    assert not RECEIPT.exists(), "Existing handoff must be reconciled, never restarted blindly"
    assert not any(path.exists() for path in (RELEASE, SCORE_PREPARE, SCORE_LAUNCH,
                                                SCORE_VERIFIED)), "Existing scorer state: reconcile"
    result = {"status": "WAITING_FOR_EXP234_TARGET175_RECOVERY_NO_LABEL_RELEASE",
              "coordinator_receipt": str(COORDINATOR),
              "target_labels_opened_before_graph_gate": False,
              "kaggle_post": False, "started": time.time()}
    save(result)
    try:
        final = wait_coordinator()
        result["status"] = "EXP234_TARGET175_RELEASED_RECHECKING_HASHES"
        save(result)
        result["release_audit"] = verify_coordinator(final)
        result["status"] = "EXP234_TARGET175_RELEASED_PREPARING_SCORER"
        save(result)
        run_step("prepare_score", PREPARE_SCRIPT, result)
        assert RELEASE.is_file() and SCORE_PREPARE.is_file()
        prepared = json.loads(SCORE_PREPARE.read_text())
        assert prepared["status"] == "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS"
        assert prepared["coordinator_receipt_sha256"] == result["release_audit"]["coordinator_sha256"]
        result["status"] = "EXP234_OFFICIAL_SCORER_STAGED_LAUNCHING"
        save(result)
        run_step("launch_score", LAUNCH_SCRIPT, result)
        assert SCORE_LAUNCH.is_file()
        launched = json.loads(SCORE_LAUNCH.read_text())
        assert launched["status"] == "EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED"
        assert launched["run"] == SCORE_RUN
        result["status"] = "WAITING_FOR_EXP234_OFFICIAL_SCORE_EXIT"
        save(result)
        wait_score_exit(result)
        result["status"] = "EXP234_OFFICIAL_SCORER_EXITED_VERIFYING"
        save(result)
        run_step("verify_score", VERIFY_SCRIPT, result)
        assert SCORE_VERIFIED.is_file()
        verified = json.loads(SCORE_VERIFIED.read_text())
        assert verified["status"] == "VERIFIED_EXP234_TARGET175_OFFICIAL"
        assert verified["rows"] == 175 and verified["baseline_replay"] == "PASS_1e-12"
        assert math.isfinite(verified["official_score"])
        assert verified["coordinator_receipt_sha256"] == result["release_audit"]["coordinator_sha256"]
        result["score_receipt"] = str(SCORE_VERIFIED)
        result["official_score"] = verified["official_score"]
        result["status"] = "PASS_EXP234_TARGET175_OFFICIAL_SCORE_HANDOFF"
    except BaseException as exc:
        result["status"] = "STOPPED_EXP234_TARGET175_SCORE_HANDOFF"
        result["error"] = repr(exc)
        raise
    finally:
        result["finished_or_stopped"] = time.time()
        save(result)


if __name__ == "__main__":
    main()
