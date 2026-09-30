"""Read-only audit of the cancelled EXP227 chunk07 launch intent.

--write-receipt creates one separate successor audit receipt. It never touches
the stopped coordinator, claims a GPU, creates a remote run, or reads labels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import coordinate_exp227_target6bba as coord
from launch_exp227_target_chunk import launch_paths, preflight_source
from monitor_exp213_job import ssh
from prepare_exp227_target_chunk0_local import paths
from stage_exp227_target_chunk import stage_paths


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
RECEIPT = ROOT / "reports/exp227_target6bba_chunk07_waiting_successor_20260927.json"
EXPECTED_SOURCE_SHA = "8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3"
EXPECTED_RESERVATION_SHA = "3d98527cd06aeff2fb4dea390f4a8b3e8256dd23bd759ecd5d6a119d5743997e"
EXPECTED_STAGE_SHA = "26def087b9164509ca1aa8bf6934d96b4350bf7a934364683f269c0e11ff040c"
QUEUE = "/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    assert sha(SOURCE) == EXPECTED_SOURCE_SHA
    assert not SOURCE.with_name(SOURCE.name + ".lock").exists()
    state = coord._read_state(SOURCE)
    assert state["status"] == "STOPPED_NEEDS_RECONCILIATION"
    assert state["target_labels_read"] is False and state["target_score_computed"] is False
    assert state["frozen"] == coord.frozen_inputs()
    assert len(state["chunks"]) == 8
    old_graphs = []
    for index in range(7):
        chunk = state["chunks"][index]
        assert chunk["postrun"]["validated"] is True
        stage = chunk["stage"]["result"]
        gate = chunk["postrun"]["gate"]
        coord._validate_postrun(gate, index, state["frozen"], stage)
        assert chunk["postrun"]["queue_row"]["state"] == "RELEASED"
        old_graphs += gate["graph_hashes"]
    assert len(old_graphs) == 102
    last = state["chunks"][7]
    assert set(last) == {"prepare", "stage", "fair_prelaunch", "launch"}
    assert last["prepare"]["validated"] is last["stage"]["validated"] is True
    assert set(last["launch"]) == {"intent_unix", "chunk_index"}
    assert last["launch"]["chunk_index"] == 7
    destination = paths(7)
    stage_file = stage_paths(7)["stage"]
    config_file = stage_paths(7)["config"]
    reservation_file = launch_paths(7)["reservation"]
    assert sha(stage_file) == EXPECTED_STAGE_SHA
    assert sha(reservation_file) == EXPECTED_RESERVATION_SHA
    assert not any(launch_paths(7)[name].exists()
                   for name in ("partial", "launch", "prelaunch_release"))
    stage = json.loads(stage_file.read_text())
    prepared = json.loads(destination["receipt"].read_text())
    config = json.loads(config_file.read_text())
    reservation = json.loads(reservation_file.read_text())
    assert stage == last["stage"]["result"]
    assert prepared == last["prepare"]["result"]
    coord._validate_prepare(prepared, 7, state["frozen"])
    coord._validate_stage(stage, 7, state["frozen"], prepared)
    assert stage["local_prepare_sha256"] == sha(destination["receipt"])
    assert stage["local_bundle_manifest_sha256"] == sha(destination["bundle"] / "local_bundle_manifest.json")
    assert stage["code"] == config["code"] == destination["code"]
    assert stage["run"] == config["run"] == destination["run"]
    assert stage["lease_id"] == config["lease_id"] == destination["lease_id"]
    assert reservation["status"] == "AMBIGUOUS_QUEUE_REQUEST_STOP"
    assert "WAITING_RESOURCE; cancelled unlaunched request " + stage["lease_id"] in reservation["error"]
    assert reservation["config"] == config
    assert reservation["fair_proof"]["first_fair_idle_gpu"] in (
        reservation["fair_proof"]["physical_preclaim"]["idle_gpus"])
    remote_preflight = ssh("nsu-a100", "python3 -", preflight_source(stage, config))
    assert remote_preflight == {
        "status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
        "manifest_sha256": stage["manifest_sha256"],
        "plan_sha256": stage["plan_sha256"], "run_absent": True}
    queue_source = r'''import hashlib,json,subprocess
state=json.loads(subprocess.check_output(['python3',@@QUEUE@@,'status'],text=True))
rows=[row for row in state['requests'] if row['id']==@@LEASE@@]
assert len(rows)==1
row=rows[0]
assert row['state']=='CANCELLED' and row['gpus']==[] and row['process'] is None
assert row['run_path']==@@RUN@@ and row['token']==@@TOKEN@@
assert row['owner']=='biohub-agent' and row['project']=='biohub-cell-tracking-during-development'
assert row['pool']=='a100' and row['count']==1
exp236=[r for r in state['requests'] if r['id']=='exp236-target44b6-chunk00-v1-20260927']
print(json.dumps({'status':'PASS_EXP227_CHUNK07_QUEUE_CANCELLED',
 'row':row,'snapshot_sha256':hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'exp236_chunk00':exp236[0] if exp236 else None}))
'''.replace("@@QUEUE@@", repr(QUEUE)).replace("@@LEASE@@", repr(stage["lease_id"])).replace(
        "@@RUN@@", repr(stage["run"])).replace("@@TOKEN@@", repr(config["token"]))
    queue_remote = ssh("nsu-quadro", "python3 -", queue_source)
    assert queue_remote["status"] == "PASS_EXP227_CHUNK07_QUEUE_CANCELLED"
    source = r'''import hashlib,json,pathlib,subprocess
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not run.exists()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'plan.json')==@@PLAN_SHA@@
assert sha(code/'selection.json')==@@SELECTION_SHA@@
assert sha(code/'assignment.json')==@@ASSIGNMENT_SHA@@
assert sha(code/'run_exp227_target_chunk.py')==@@RUNNER_SHA@@
matches=[]
for cmdline in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
 try:
  raw=cmdline.read_bytes().replace(b'\x00',b' ').decode(errors='replace')
  if any(s in raw for s in (@@CODE@@,@@RUN@@,@@TOKEN@@)):
   matches.append({'pid':int(cmdline.parent.name),'cmdline':raw[:350]})
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert matches==[],matches
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid',
 '--format=csv,noheader'],capture_output=True,text=True,check=True)
gpu_pids=[int(line.split(',')[0]) for line in gpu.stdout.splitlines() if line.strip()]
assert not any(item['pid'] in gpu_pids for item in matches)
print(json.dumps({'status':'PASS_EXP227_CHUNK07_CANCELLED_UNLAUNCHED_REMOTE_AUDIT',
 'queue_row':@@QUEUE_ROW@@,'queue_snapshot_sha256':@@QUEUE_SHA@@,
 'stage_manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'plan.json'),'selection_sha256':sha(code/'selection.json'),
 'assignment_sha256':sha(code/'assignment.json'),
 'runner_sha256':sha(code/'run_exp227_target_chunk.py'),
 'run_absent':True,'matching_processes':matches,'matching_gpu_pids':[],
 'exp236_chunk00':@@EXP236_ROW@@,
 'target_labels_read':False,'kaggle_post':False}))
'''
    replace = {
        "@@CODE@@": repr(stage["code"]), "@@RUN@@": repr(stage["run"]),
        "@@TOKEN@@": repr(config["token"]),
        "@@QUEUE_ROW@@": repr(queue_remote["row"]),
        "@@QUEUE_SHA@@": repr(queue_remote["snapshot_sha256"]),
        "@@EXP236_ROW@@": repr(queue_remote["exp236_chunk00"]),
        "@@MANIFEST_SHA@@": repr(stage["manifest_sha256"]),
        "@@PLAN_SHA@@": repr(stage["plan_sha256"]),
        "@@SELECTION_SHA@@": repr(stage["selection_sha256"]),
        "@@ASSIGNMENT_SHA@@": repr(state["frozen"]["assignment_sha256"]),
        "@@RUNNER_SHA@@": repr(stage["staged"]["runner_sha256"]),
    }
    for token, value in replace.items():
        source = source.replace(token, value)
    remote = ssh("nsu-a100", "python3 -", source)
    assert remote["status"] == "PASS_EXP227_CHUNK07_CANCELLED_UNLAUNCHED_REMOTE_AUDIT"
    assert remote["queue_row"]["state"] == "CANCELLED"
    assert remote["run_absent"] and remote["matching_processes"] == []
    assert remote["matching_gpu_pids"] == [] and remote["target_labels_read"] is False
    assert sha(SOURCE) == EXPECTED_SOURCE_SHA
    return {"status": "RECONCILED_EXP227_CHUNK07_WAITING_NO_LAUNCH",
            "source_stopped_sha256": EXPECTED_SOURCE_SHA,
            "source_state_sha256": state["state_sha256"],
            "verified_prior_chunks": 7, "verified_prior_graphs": len(old_graphs),
            "prior_graph_hashes_sha256": coord.digest_object(old_graphs),
            "chunk07_prepare_sha256": sha(destination["receipt"]),
            "chunk07_stage_sha256": sha(stage_file),
            "chunk07_config_sha256": sha(config_file),
            "chunk07_reservation_sha256": sha(reservation_file),
            "remote_preflight": remote_preflight,
            "remote": remote,
            "next_identity": {
                "code": coord.RUN_PREFIX + "/code/exp227_target6bba_chunk07_v2_20260927",
                "run": coord.RUN_PREFIX + "/runs/exp227_target6bba_chunk07_v2_20260927",
                "lease_id": "exp227-target6bba-chunk07-v2-20260927",
                "token": "exp227_target6bba_chunk07_v2_20260927"},
            "resume_gate": ("Versioned v2 local bundle and remote stage require review; "
                            "wait for a fair A100, then request a new lease only. "
                            "If WAITING_RESOURCE recurs, cancel and record waiting without launch."),
            "remote_stage_created_v2": False, "remote_run_created_v2": False,
            "gpu_claimed_v2": False, "target_labels_read": False,
            "target_score_computed": False, "kaggle_post": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    if args.write_receipt:
        assert not RECEIPT.exists(), "Successor receipt already exists"
    result = audit()
    if args.write_receipt:
        RECEIPT.write_bytes((json.dumps(result, indent=2) + "\n").encode())
        result = {"status": result["status"], "receipt_sha256": sha(RECEIPT)}
    else:
        result = {"status": result["status"], "source_stopped_sha256": result["source_stopped_sha256"],
                  "verified_prior_chunks": result["verified_prior_chunks"],
                  "queue_state": result["remote"]["queue_row"]["state"],
                  "run_absent": result["remote"]["run_absent"]}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
