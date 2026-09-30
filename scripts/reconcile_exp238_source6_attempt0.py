"""Read-only reconciliation of EXP238 source6 attempt0 WAITING_RESOURCE cancellation.

Only writes one local evidence receipt. Never requests/cancels/releases a lease,
stages code, starts a worker, or opens image/GEFF data.
"""

import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh
from stage_exp238_peak_cache import ROOT, REPORTS, atomic_json, local_preflight, sha


LEASE_ID = "exp238-source6-peak-cache-v1-20260927"
INTENT = REPORTS / "exp238_source6_peak_cache_launch_20260927_intent.json"
STAGE = REPORTS / "exp238_source6_peak_cache_stage_20260927.json"
RECEIPT = REPORTS / "exp238_source6_peak_cache_attempt0_wait_20260927.json"
INTENT_SHA = "c579e7096c0688a0837b0733fa24bf6d07c1c64a5cf84441e6618c765317d0f4"
STAGE_SHA = "50aad2cabfa71c12ce28a701e9a69e960be5800ea3182d13da149508df0d07cf"


def verify_local(plan: dict, local: dict) -> tuple[dict, dict]:
    assert sha(INTENT) == INTENT_SHA
    assert sha(STAGE) == STAGE_SHA
    intent = json.loads(INTENT.read_text())
    stage = json.loads(STAGE.read_text())
    assert intent["status"] == "INTENT_EXP238_A100_REQUEST"
    assert intent["config"]["lease_id"] == LEASE_ID
    assert intent["config"]["run"] == plan["run"]
    assert intent["config"]["code"] == plan["code"]
    assert intent["config"]["token"] == Path(plan["code"]).name
    assert intent["config"]["arguments"] == [plan["code"] + "/exp238_plan.json",
                                              "--plan-sha256", local["plan_sha256"],
                                              "--manifest-sha256", stage["stage"]["manifest_sha256"]]
    assert intent["preflight"] == {"status": "PASS_EXP238_LAUNCH_PREFLIGHT_NO_LABELS",
                                   "movies": 11, "run_absent": True, "labels_read": False}
    assert intent["stage_receipt_sha256"] == STAGE_SHA
    assert stage["status"] == "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS"
    assert stage["cohort"] == "source6" and stage["run_started"] is False
    assert stage["stage"]["plan_sha256"] == local["plan_sha256"]
    base = REPORTS / "exp238_source6_peak_cache_launch_20260927"
    assert not base.with_name(base.name + "_reservation.json").exists()
    assert not base.with_name(base.name + "_partial.json").exists()
    assert not base.with_suffix(".json").exists()
    return intent, stage


def queue_state(plan: dict, intent: dict) -> dict:
    status = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    rows = [item for item in status["requests"] if item["id"] == LEASE_ID]
    assert len(rows) == 1
    row = rows[0]
    assert row["state"] == "CANCELLED" and row["health"] == "CURRENT"
    assert row["gpus"] == [] and row["process"] is None
    assert row["owner"] == "biohub-agent" and row["project"] == (
        "biohub-cell-tracking-during-development")
    assert row["token"] == intent["config"]["token"]
    assert row["run_path"] == plan["run"] and row["pool"] == "a100"
    assert row["count"] == 1 and row["cpu"] == 8
    assert row["ram_gib"] == 32 and row["disk_gib"] == 4 and row["minutes"] == 130
    return row


def remote_probe(plan: dict, stage: dict, alias: str) -> dict:
    expected = stage["stage"]
    script = '''import hashlib,json,pathlib,subprocess
p=json.loads(PLAN);s=json.loads(STAGE)
code=pathlib.Path(p['code']);run=pathlib.Path(p['run']);marker=code.name
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert code.is_dir()
stage_hashes={'manifest_sha256':sha(code/'code_manifest.json'),
              'plan_sha256':sha(code/'exp238_plan.json'),
              'runner_sha256':sha(code/'run_exp238_peak_cache.py'),
              'engine_sha256':sha(code/'horaz/src/src/engine.py'),
              'detection_sha256':sha(code/'horaz/src/src/detection.py')}
assert stage_hashes['manifest_sha256']==s['manifest_sha256']
assert stage_hashes['plan_sha256']==s['plan_sha256']
assert stage_hashes['runner_sha256']==p['runner_sha256']
assert stage_hashes['engine_sha256']==p['patched_engine_sha256']
assert stage_hashes['detection_sha256']==p['patched_detection_sha256']
matches=[]
for proc in pathlib.Path('/proc').glob('[0-9]*'):
 try:
  cmd=(proc/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
  if marker in cmd:matches.append({'pid':int(proc.name),'cmd':cmd[:300]})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
gpu_matches=[]
if GPU:
 query=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid',
                       '--format=csv,noheader'],capture_output=True,text=True,check=True)
 gpu_pids={int(line.split(',')[0].strip()) for line in query.stdout.splitlines()
           if line.strip() and line.split(',')[0].strip().isdigit()}
 gpu_matches=[row for row in matches if row['pid'] in gpu_pids]
print(json.dumps({'alias':ALIAS,'run_exists':run.exists(),'matched_processes':matches,
                  'gpu_matches':gpu_matches,'stage_hashes':stage_hashes,
                  'labels_read':False}))
'''.replace("PLAN", repr(json.dumps(plan, sort_keys=True))).replace(
        "STAGE", repr(json.dumps(expected, sort_keys=True))).replace(
        "GPU", "True" if alias == "nsu-a100" else "False").replace(
        "ALIAS", repr(alias))
    return ssh(alias, "python3 -", script)


def reconcile() -> dict:
    assert not RECEIPT.exists(), "Attempt0 receipt already exists; preserve it"
    plan, local = local_preflight("source6")
    intent, stage = verify_local(plan, local)
    queue = queue_state(plan, intent)
    probes = [remote_probe(plan, stage, alias) for alias in ("nsu-a100", "nsu-quadro")]
    assert all(row["run_exists"] is False and row["matched_processes"] == []
               and row["gpu_matches"] == [] and row["labels_read"] is False for row in probes)
    for row in probes:
        assert row["stage_hashes"]["manifest_sha256"] == stage["stage"]["manifest_sha256"]
        assert row["stage_hashes"]["plan_sha256"] == local["plan_sha256"]
    receipt = {"status": "WAITING_RESOURCE_CANCELLED_UNLAUNCHED_EXP238_SOURCE6_ATTEMPT0",
               "interpretation": "Queue request returned WAITING_RESOURCE; queue_request cancelled the unlaunched request. No reservation, remote run, or worker exists.",
               "lease": queue, "intent_sha256": INTENT_SHA, "stage_receipt_sha256": STAGE_SHA,
               "local_plan_sha256": local["plan_sha256"],
               "remote_probes": probes, "source_labels_read": False,
               "target_data_opened": False, "gpu_requested_again": False,
               "remote_mutation": False, "kaggle_post": False}
    atomic_json(RECEIPT, receipt)
    return receipt


def main() -> None:
    result = reconcile()
    print(json.dumps({"status": result["status"], "lease_id": result["lease"]["id"],
                      "queue_state": result["lease"]["state"],
                      "run_absent": all(not row["run_exists"] for row in result["remote_probes"]),
                      "receipt_sha256": sha(RECEIPT)}, sort_keys=True))


if __name__ == "__main__":
    main()
