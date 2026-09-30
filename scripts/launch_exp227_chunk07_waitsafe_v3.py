"""Reviewed-only EXP227 chunk07 v3 fair launch with durable wait outcomes.

Each invocation is one attempt. A race that returns WAITING_RESOURCE is
cancelled by queue_request, then independently checked for no run/worker/GPU,
and recorded as a nonfatal wait. Retry with the next attempt number, which
uses a fresh lease ID while retaining the immutable v3 code and run paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex

import coordinate_exp227_target6bba as coord
from launch_exp221_job import queue_request
from launch_exp227_target_chunk import (
    PHYSICAL_IDLE_SOURCE, controller_source, launch_source,
    preflight_source, release_if_no_run,
)
from monitor_exp213_job import QUEUE, ssh
from prepare_exp227_chunk07_waitsafe_v3 import validate_actual_runner


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_stage_20260927.json"
CONFIG = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_config_20260927.json"
LOCAL = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_local_prepare_20260927.json"
AUDIT = ROOT / "reports/exp227_target6bba_chunk07_v2_failed_reconciliation_20260927.json"
SOURCE = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
EXPECTED_LOCAL_SHA = "9bae3cfe842e9772aadf07bce8572fc84802ed54af0a84838fad450dfa24e0d8"
EXPECTED_AUDIT_SHA = "5c777467215e6fe4f984cdcf4920070d07a2f704c819144b1cd4896af0981796"
EXPECTED_STOPPED_SHA = "8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths(attempt: int) -> dict[str, Path]:
    assert isinstance(attempt, int) and 0 <= attempt <= 99
    base = ROOT / f"reports/exp227_target6bba_chunk07_waitsafe_v3_attempt{attempt:02d}_20260927"
    return {name: base.with_name(base.name + "_" + name + ".json")
            for name in ("intent", "reservation", "partial", "result", "prelaunch_release")}


def attempt_lease(base: str, attempt: int) -> str:
    assert base == "exp227-target6bba-chunk07-v3-20260927"
    assert 0 <= attempt <= 99
    return base if attempt == 0 else base.replace("-v3-", f"-v3a{attempt:02d}-")


def local_gate(attempt: int) -> tuple[dict, dict]:
    output = paths(attempt)
    assert not any(p.exists() for p in output.values()), "Existing attempt needs reconciliation"
    assert sha(LOCAL) == EXPECTED_LOCAL_SHA and sha(AUDIT) == EXPECTED_AUDIT_SHA
    local = json.loads(LOCAL.read_text())
    audit = json.loads(AUDIT.read_text())
    assert local["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY"
    assert audit["status"] == "RECONCILED_EXP227_CHUNK07_V2_FAILED_BEFORE_GRAPHS"
    assert local["failed_v2_reconciliation_sha256"] == sha(AUDIT)
    assert sha(SOURCE) == audit["source_stopped_sha256"] == EXPECTED_STOPPED_SHA
    assert audit["queue_row"]["state"] == "RELEASED"
    assert audit["remote"]["output_exists"] is False and audit["remote"]["graph_files"] == []
    stage = json.loads(STAGE.read_text())
    base_config = json.loads(CONFIG.read_text())
    assert stage["status"] == "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS"
    assert stage["chunk_index"] == base_config["chunk_index"] == 7
    assert stage["source_stopped_sha256"] == audit["source_stopped_sha256"]
    assert stage["local_prepare_sha256"] == sha(LOCAL)
    assert stage["failed_v2_reconciliation_sha256"] == sha(AUDIT)
    assert stage["runner_contract"] == local["actual_runner_contract"]
    for key in ("code", "run", "lease_id", "token"):
        assert stage[key] == base_config[key] == local["identity"][key]
    assert stage["plan_sha256"] == local["plan_sha256"]
    assert stage["checkpoint_sha256"] == local["checkpoint_sha256"]
    assert stage["selection_sha256"] == local["selection_sha256"]
    assert stage["assignment_sha256"] == local["assignment_sha256"]
    assert stage["movies"] == local["movies"] and len(stage["movies"]) == 14
    bundle = Path(local["bundle"])
    manifest_path = bundle / "local_bundle_manifest.json"
    assert sha(manifest_path) == local["bundle_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    assert set(p.name for p in bundle.iterdir()) == set(manifest) | {"local_bundle_manifest.json"}
    assert all(sha(bundle / name) == digest for name, digest in manifest.items())
    assert manifest["run_exp227_target_chunk.py"] == local["runner_sha256"]
    assert validate_actual_runner(bundle, json.loads((bundle / "plan.json").read_text())) == local["actual_runner_contract"]
    assert stage["remote_run_created"] is False and stage["gpu_claimed"] is False
    assert stage["target_labels_read"] is False and stage["kaggle_post"] is False
    assert base_config["experiment"] == "EXP227_TARGET6BBA_CHUNK"
    assert base_config["pool"] == "a100" and base_config["max_seconds"] == 10800
    assert base_config["resources"] == {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4}
    assert base_config["script"] == "run_exp227_target_chunk.py"
    assert base_config["arguments"] == [stage["code"] + "/plan.json", "--plan-sha256",
                                         stage["plan_sha256"]]
    if attempt > 0:
        previous = json.loads(paths(attempt - 1)["result"].read_text())
        assert previous["status"] in (
            "WAITING_FOR_FAIR_A100_NO_REQUEST",
            "WAITING_RESOURCE_CANCELLED_NO_RUN")
        assert previous["attempt"] == attempt - 1
        assert previous["run"] == stage["run"]
        assert previous["kaggle_post"] is False
    return stage, {**base_config, "lease_id": attempt_lease(base_config["lease_id"], attempt)}


def no_run_worker(config: dict) -> dict:
    source = r'''import json,pathlib,subprocess
run=pathlib.Path(@@RUN@@);code=@@CODE@@;token=@@TOKEN@@
matches=[]
for cmdline in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
 try:
  raw=cmdline.read_bytes().replace(b'\x00',b' ').decode(errors='replace')
  if any(s in raw for s in (str(run),code,token)):
   matches.append({'pid':int(cmdline.parent.name),'cmdline':raw[:300]})
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid',
                    '--format=csv,noheader'],capture_output=True,text=True,check=True)
gpu_pids=[int(line.split(',')[0]) for line in gpu.stdout.splitlines() if line.strip()]
print(json.dumps({'run_absent':not run.exists(),'matching_processes':matches,
                  'matching_gpu_pids':[row['pid'] for row in matches if row['pid'] in gpu_pids]}))
'''.replace("@@RUN@@", repr(config["run"])).replace(
        "@@CODE@@", repr(config["code"])).replace("@@TOKEN@@", repr(config["token"]))
    result = ssh("nsu-a100", "python3 -", source)
    assert result == {"run_absent": True, "matching_processes": [],
                      "matching_gpu_pids": []}
    return result


def cancelled_unlaunched(config: dict) -> dict:
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    rows = [row for row in queue["requests"] if row["id"] == config["lease_id"]]
    assert len(rows) == 1
    row = rows[0]
    assert row["state"] == "CANCELLED" and row["gpus"] == [] and row["process"] is None
    assert row["run_path"] == config["run"] and row["token"] == config["token"]
    physical = no_run_worker(config)
    return {"queue_row": row, "run_worker": physical,
            "queue_snapshot_sha256": coord.digest_object(queue)}


def write(path: Path, body: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(body, indent=2) + "\n")


def launch_attempt(attempt: int) -> dict:
    stage, config = local_gate(attempt)
    output = paths(attempt)
    if attempt > 0:
        previous = json.loads(paths(attempt - 1)["result"].read_text())
        if previous["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN":
            prior_config = {**config, "lease_id": previous["lease_id"]}
            current_cancelled = cancelled_unlaunched(prior_config)
            assert current_cancelled["queue_row"]["state"] == "CANCELLED"
    no_run_worker(config)
    remote_gate = ssh("nsu-a100", "python3 -", preflight_source(stage, config))
    assert remote_gate == {"status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
                           "manifest_sha256": stage["manifest_sha256"],
                           "plan_sha256": stage["plan_sha256"], "run_absent": True}
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    physical = ssh("nsu-a100", "python3 -", PHYSICAL_IDLE_SOURCE)
    fair_snapshot = {"queue": queue, "physical": physical}
    fair_gpu, reason = coord._fair_a100_available(fair_snapshot, config["lease_id"])
    exp236 = [row for row in queue["requests"] if row["id"].startswith("exp236-target44b6-chunk")
              and row["state"] in ("WAITING_RESOURCE", "RESERVED", "RUNNING")]
    if exp236:
        fair_gpu, reason = None, "EXP236_TARGET_COORDINATOR_ACTIVE_OR_WAITING"
    fair = {"status": reason, "gpu": fair_gpu,
            "queue_snapshot_sha256": coord.digest_object(queue),
            "physical": physical,
            "exp236_active_or_waiting": [{"id": row["id"], "state": row["state"],
                                           "gpus": row["gpus"]} for row in exp236]}
    if fair_gpu is None:
        result = {"status": "WAITING_FOR_FAIR_A100_NO_REQUEST", "attempt": attempt,
                  "lease_id": config["lease_id"], "run": config["run"],
                  "remote_preflight": remote_gate, "fair": fair,
                  "target_labels_read": False, "kaggle_post": False}
        write(output["result"], result)
        return result
    write(output["intent"], {"status": "INTENT_EXP227_CHUNK07_V3_QUEUE_REQUEST",
         "attempt": attempt, "config": config, "remote_preflight": remote_gate,
         "fair": fair, "stage_sha256": sha(STAGE), "target_labels_read": False,
         "kaggle_post": False})
    resources = config["resources"]
    args = ["python3", QUEUE, "request", "--id", config["lease_id"],
            "--owner", "biohub-agent", "--token", config["token"],
            "--project", "biohub-cell-tracking-during-development",
            "--run-path", config["run"], "--pool", "a100", "--count", "1",
            "--cpu", str(resources["cpu"]), "--ram-gib", str(resources["ram_gib"]),
            "--disk-gib", str(resources["disk_growth_gib"]),
            "--minutes", str(config["max_seconds"] // 60 + 10)]
    try:
        lease = queue_request(args, config["lease_id"], config["token"])
    except RuntimeError as error:
        expected = ("Queue returned WAITING_RESOURCE; cancelled unlaunched request "
                    + config["lease_id"])
        if str(error) != expected:
            raise
        cancelled = cancelled_unlaunched(config)
        result = {"status": "WAITING_RESOURCE_CANCELLED_NO_RUN", "attempt": attempt,
                  "lease_id": config["lease_id"], "run": config["run"],
                  "cancelled": cancelled, "remote_preflight": remote_gate,
                  "fair": fair, "target_labels_read": False, "kaggle_post": False}
        write(output["result"], result)
        return result
    write(output["reservation"], {"status": "RESERVED_EXP227_CHUNK07_V3",
          "attempt": attempt, "lease": lease, "config": config, "fair": fair})
    assert lease["state"] == "RESERVED" and lease["id"] == config["lease_id"]
    assert lease["alias"] == "nsu-a100" and lease["run_path"] == config["run"]
    assert lease["token"] == config["token"] and len(lease["gpus"]) == 1
    prior_occupied = {gpu for row in queue["requests"]
                      if row["state"] in ("RESERVED", "RUNNING")
                      for gpu in row.get("gpus", [])}
    if (lease["gpus"][0] not in physical["idle_gpus"] or
            lease["gpus"][0] in prior_occupied):
        release_if_no_run(config, output["prelaunch_release"],
                          "Allocated GPU differs from fair physical idle preclaim")
        raise AssertionError("Allocated GPU failed fair physical-idle gate")
    assigned = {**config, "gpu": lease["gpus"][0], "alias": lease["alias"]}
    try:
        launched = ssh("nsu-a100", "python3 -", launch_source(assigned, stage))
    except Exception:
        release_if_no_run(config, output["prelaunch_release"],
                          "Remote launch rejected before run creation")
        raise
    partial = {"status": "PARTIAL_EXP227_CHUNK07_V3_LAUNCH", "attempt": attempt,
               "lease": lease, "config": assigned, "launch": launched,
               "remote_preflight": remote_gate, "fair": fair,
               "stage_sha256": sha(STAGE), "target_labels_read": False}
    write(output["partial"], partial)
    control = ssh("nsu-quadro", "python3 -", controller_source(assigned))
    assert isinstance(control["controller_pid"], int) and control["controller_pid"] > 0
    result = {**partial, "status": "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V3",
              "control": control, "kaggle_post": False}
    write(output["result"], result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    result = launch_attempt(args.attempt)
    print(json.dumps({"status": result["status"], "attempt": args.attempt,
                      "run": result.get("run", result.get("config", {}).get("run")),
                      "result_receipt_sha256": sha(paths(args.attempt)["result"])}))


if __name__ == "__main__":
    main()
