"""Resume only EXP234's seven unlaunched target chunks after queue fairness clears."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import psutil

from finish_exp234_target_rollout_v2 import CODE, ROOT, SEQUENCE, check_release
from monitor_exp213_job import QUEUE, ssh
from prepare_exp234_target_rollout_v2 import local_freeze


ORIGINAL = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
RECEIPT = ROOT / "reports/exp234_target_recovery_v2_20260927.json"
TARGET_PREPARE = ROOT / "reports/exp234_target_prepare_v2_20260927.json"
FIRST_UNLAUNCHED = 5
POLL_SECONDS = 120
TOTAL_SECONDS = 48 * 3600
PROJECT = "biohub-cell-tracking-during-development"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(value):
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(RECEIPT)


def config_path(source, index):
    return ROOT / f"reports/exp234_target_{source}_chunk{index:02d}_config_v2_20260927.json"


def assert_unlaunched(source, index):
    path = config_path(source, index)
    config = json.loads(path.read_text())
    assert config["code"] == CODE
    assert config["script"] == "run_exp234_target_chunk.py"
    assert config["run"].endswith(f"/runs/exp234_target_{source}_chunk{index:02d}_v2_20260927")
    assert config["arguments"][:2] == [CODE + f"/{source}_chunk{index:02d}_plan.json",
                                       "--plan-sha256"]
    assert not any(path.with_name(path.stem + suffix).exists() for suffix in (
        "_launch.json", "_partial_launch.json", "_monitor.json")), "Chunk already launched: reconcile"
    return config


def original_prefix():
    """Pin the stopped receipt and re-run each of its five remote release audits."""
    original = json.loads(ORIGINAL.read_text())
    assert original["status"] == "STOPPED_EXP234_TARGET_ROLLOUT"
    assert original["target_labels_read"] is False
    assert len(original["completed"]) == FIRST_UNLAUNCHED
    assert sum(item["movies"] for item in original["completed"]) == 74
    assert "44b6_chunk01 launch failed" in original["error"]
    failure_log = config_path("44b6", 1).with_name(
        "exp234_target_44b6_chunk01_config_v2_20260927_coordinator_launch.log")
    assert "AssertionError: Other project is waiting" in failure_log.read_text()
    assert "finished_or_stopped" in original
    assignment, choices = local_freeze()
    prepared = json.loads(TARGET_PREPARE.read_text())
    assert prepared["status"] == "PREPARED_EXP234_TARGET175_NO_LABELS"
    assert prepared["target_labels_read"] is False
    assert prepared["stage"]["manifest_sha256"] == (
        "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4")
    assert prepared["assignment_sha256"] == sha(
        ROOT / "reports/exp234_target_chunk_assignment_20260926.json")
    assert original["code_manifest_sha256"] == prepared["stage"]["manifest_sha256"]
    selected = {source: {key: choices[source][key] for key in (
        "selected_threshold", "result_sha256", "gate_sha256")}
        for source in ("44b6", "6bba")}
    assert original["source_choices"] == prepared["source_choices"] == selected
    for (source, index), item in zip(SEQUENCE[:FIRST_UNLAUNCHED], original["completed"]):
        assert item["source"] == source and item["chunk"] == index
        assert item["plan_sha256"] == prepared["stage"]["plan_sha256"][
            f"{source}_chunk{index:02d}_plan.json"]
        assert item == check_release(source, index, assignment, choices)
    for source, index in SEQUENCE[FIRST_UNLAUNCHED:]:
        assert_unlaunched(source, index)
    return original, assignment, choices, prepared


def queue_status():
    return ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))


def fair_resource_available(state, config):
    """Follow the launcher's foreign-waiter rule and require free pool capacity."""
    requests = state["requests"]
    assert not any(row["id"] == config["lease_id"] for row in requests), "Existing lease: reconcile"
    if any(row["state"].startswith("WAITING") and row["project"] != PROJECT
           for row in requests):
        return False
    pool = state["pools"]["a100"]
    active = [row for row in requests if row["pool"] == "a100"
              and row["state"] in ("RUNNING", "RESERVED")]
    occupied = {gpu for row in active for gpu in row["gpus"]}
    if not set(pool["gpus"]) - occupied:
        return False
    required = config["resources"]
    if pool["cpu"] - sum(row["cpu"] for row in active) < required["cpu"]:
        return False
    if pool["ram_gib"] - sum(row["ram_gib"] for row in active) < required["ram_gib"]:
        return False
    return True


def remote_run_absent_and_gpu_idle(config, state):
    pool = state["pools"]["a100"]
    occupied = {gpu for row in state["requests"] if row["pool"] == "a100"
                and row["state"] in ("RUNNING", "RESERVED") for gpu in row["gpus"]}
    candidates = sorted(set(pool["gpus"]) - occupied)
    source = '''import json,pathlib,subprocess
run=pathlib.Path(@@RUN@@)
busy=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
print(json.dumps({'run_absent':not run.exists(),
                  'idle_candidates':[gpu for gpu in @@CANDIDATES@@ if gpu not in busy]}))
'''.replace("@@RUN@@", repr(config["run"])).replace("@@CANDIDATES@@", repr(candidates))
    observed = ssh("nsu-a100", "python3 -", source)
    assert observed["run_absent"] is True, "Existing remote chunk run: reconcile"
    return bool(observed["idle_candidates"])


def wait_fair(config, result, deadline):
    errors = 0
    while time.monotonic() < deadline:
        try:
            state = queue_status()
            errors = 0
            result.pop("last_observation_error", None)
        except Exception as exc:
            errors += 1
            result["last_observation_error"] = repr(exc)
            result["consecutive_observation_errors"] = errors
            save(result)
            if errors >= 5:
                raise RuntimeError("Five consecutive queue/resource observations failed") from exc
            time.sleep(POLL_SECONDS)
            continue
        ready = fair_resource_available(state, config)
        if ready:
            ready = remote_run_absent_and_gpu_idle(config, state)
        if ready:
            return
        snapshot = {"foreign_waiting": sorted(row["id"] for row in state["requests"]
                                               if row["state"].startswith("WAITING")
                                               and row["project"] != PROJECT),
                    "a100_active": sorted(row["id"] for row in state["requests"]
                                          if row["pool"] == "a100" and
                                          row["state"] in ("RUNNING", "RESERVED"))}
        if result.get("last_queue_snapshot") != snapshot:
            result["last_queue_snapshot"] = snapshot
            save(result)
        time.sleep(POLL_SECONDS)
    raise TimeoutError("Fair A100 capacity did not become available within recovery bound")


def launch_one(source, index, config, result):
    path = config_path(source, index)
    token = f"{source}_chunk{index:02d}"
    attempts = result.setdefault("launch_attempts", {})
    attempts[token] = attempts.get(token, 0) + 1
    attempt = attempts[token]
    save(result)
    log = ROOT / f"reports/exp234_target_recovery_{token}_launch_attempt{attempt:02d}_20260927.log"
    assert not log.exists(), "Existing recovery launch log: reconcile"
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/launch_exp234_target_chunk_v2.py"),
                                str(path)], cwd=ROOT, text=True, capture_output=True, timeout=180)
    log.write_text(completed.stdout + "\n--- stderr ---\n" + completed.stderr)
    result["last_launch_log"] = str(log)
    result["last_launch_returncode"] = completed.returncode
    save(result)
    if completed.returncode:
        # Only a fresh queue race is retryable, and only before any reservation/run.
        fairness = "AssertionError: Other project is waiting" in completed.stderr
        if fairness:
            assert_unlaunched(source, index)
            state = queue_status()
            assert not any(row["id"] == config["lease_id"] for row in state["requests"]), (
                "Lease exists after rejected launch")
            source_code = '''import json,pathlib
print(json.dumps({'run_absent':not pathlib.Path(@@RUN@@).exists()}))
'''.replace("@@RUN@@", repr(config["run"]))
            assert ssh("nsu-a100", "python3 -", source_code)["run_absent"] is True
            return False
        raise RuntimeError(f"Target {token} launch failed; see {log}")
    assert path.with_name(path.stem + "_launch.json").is_file()
    return True


def wait_and_verify_chunk(source, index, assignment, choices):
    path = config_path(source, index)
    launched = json.loads(path.with_name(path.stem + "_launch.json").read_text())
    monitor = path.with_name(path.stem + "_monitor.json")
    if not monitor.exists() or json.loads(monitor.read_text()).get("monitor_status") != "RELEASED_AFTER_VERIFIED_EXIT":
        try:
            process = psutil.Process(launched["monitor_pid"])
            command = process.cmdline()
            assert any(Path(arg).name == "monitor_exp213_job.py" for arg in command)
            assert str(path.resolve()) in command
            process.wait(timeout=11400)
        except psutil.NoSuchProcess:
            pass
    return check_release(source, index, assignment, choices)


def main():
    assert not RECEIPT.exists(), "Existing recovery receipt must be reconciled"
    original, assignment, choices, prepared = original_prefix()
    result = {"status": "WAITING_FOR_FAIR_A100_FOR_EXP234_TARGET_RECOVERY",
              "pid": os.getpid(), "process_create_time": psutil.Process(os.getpid()).create_time(),
              "started": time.time(),
              "original_coordinator_sha256": sha(ORIGINAL),
              "code_manifest_sha256": prepared["stage"]["manifest_sha256"],
              "source_choices": original["source_choices"],
              "completed": list(original["completed"]),
              "target_labels_read": False, "kaggle_post": False}
    save(result)
    deadline = time.monotonic() + TOTAL_SECONDS
    try:
        for source, index in SEQUENCE[FIRST_UNLAUNCHED:]:
            token = f"{source}_chunk{index:02d}"
            config = assert_unlaunched(source, index)
            result["status"] = "WAITING_FOR_FAIR_A100_FOR_" + token.upper()
            save(result)
            while True:
                wait_fair(config, result, deadline)
                if launch_one(source, index, config, result):
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError("EXP234 target recovery expired after a queue race")
                time.sleep(POLL_SECONDS)
            result["status"] = "WAITING_FOR_EXP234_TARGET_" + token.upper() + "_RELEASE"
            save(result)
            record = wait_and_verify_chunk(source, index, assignment, choices)
            result["completed"].append(record)
            result["last_verified"] = time.time()
            save(result)
        assert len(result["completed"]) == len(SEQUENCE) == 12
        assert sum(item["movies"] for item in result["completed"]) == 175
        assert result["completed"][:FIRST_UNLAUNCHED] == original["completed"]
        assert sha(ORIGINAL) == result["original_coordinator_sha256"]
        result["status"] = "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    except BaseException as exc:
        result["status"] = "STOPPED_EXP234_TARGET_RECOVERY"
        result["error"] = repr(exc)
        raise
    finally:
        result["finished_or_stopped"] = time.time()
        save(result)


if __name__ == "__main__":
    main()
