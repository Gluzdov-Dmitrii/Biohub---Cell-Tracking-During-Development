"""Read-only final gate for EXP227's 116 target graphs after chunk07 v2.

Default mode only checks and prints a digest. --write-receipt creates one new
local receipt after every local and remote no-label check succeeds. The stopped
coordinator, its v1 chunk07 intent and all launcher receipts stay untouched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import coordinate_exp227_target6bba as coord
from launch_exp227_chunk07_waitsafe_v2 import attempt_lease, paths as attempt_paths
from launch_exp227_target_chunk import launch_paths
from monitor_exp213_job import ssh
from prepare_exp227_target_chunk0_local import paths as prepare_paths
from stage_exp227_target_chunk import stage_paths
from verify_exp227_target_chunk0 import live_release


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
LOCAL = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_local_prepare_20260927.json"
AUDIT = ROOT / "reports/exp227_target6bba_chunk07_waiting_successor_20260927.json"
STAGE = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_stage_20260927.json"
CONFIG = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_config_20260927.json"
RECEIPT = ROOT / "reports/exp227_target6bba_all116_waitsafe_v2_final_20260927.json"
SOURCE_SHA = "8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3"
LOCAL_SHA = "ff1b87073ca1bd7ecbf48999265a89e2559c2ff85ddc3fdf2f8475cf5aaba910"
AUDIT_SHA = "ed9755fdfeb1b19846845c9858ab05e825902011350bc43abe19f1f3afba0d3f"
STAGE_SHA = "498a4cf13537bfffa9a90f601e4f909838583e3f334fc1d8b458c55f33bb3d3e"
CONFIG_SHA = "d796b7def03ef1a56d0303b9af6ddc0c1e58c69fd58ab97dc2b858c69942d7b3"
MANIFEST_SHA = "a828a02ef88bd313a30da12aca8eb2a956337c3641c4dc2851e49e50a203fade"
PLAN_SHA = "583fdae80ed8145ceca92d2405e69a6093b26700acc8986540a5f0ace6afcbd2"


def require(condition: bool, message: str) -> None:
    coord.require(condition, message)


def read_pinned(path: Path, expected: str) -> dict:
    require(coord.sha(path) == expected, f"Changed pinned receipt: {path.name}")
    return json.loads(path.read_text())


def local_sources(attempt: int) -> dict:
    """Validate immutable first-seven receipts and the actual v2 launch chain."""
    require(0 <= attempt <= 99, "Attempt must be in 0..99")
    stopped = coord._read_state(SOURCE)
    require(coord.sha(SOURCE) == SOURCE_SHA and
            stopped["status"] == "STOPPED_NEEDS_RECONCILIATION", "Stopped source changed")
    frozen = coord.frozen_inputs()
    require(stopped["frozen"] == frozen and len(stopped["chunks"]) == 8,
            "Stopped source changed frozen assignment")
    require(stopped["target_labels_read"] is False and
            stopped["target_score_computed"] is False, "Stopped source opened target labels")
    first_seven_hashes = []
    source_receipts = []
    for index in range(7):
        chunk = stopped["chunks"][index]
        require(set(chunk) == {"prepare", "stage", "fair_prelaunch", "launch", "postrun"},
                f"Chunk{index:02d} phases changed")
        prepare, stage, launch = (chunk[phase]["result"] for phase in
                                  ("prepare", "stage", "launch"))
        for phase in ("prepare", "stage", "launch", "postrun"):
            require(chunk[phase]["validated"] is True, f"Chunk{index:02d} unvalidated {phase}")
        coord._validate_prepare(prepare, index, frozen)
        coord._validate_stage(stage, index, frozen, prepare)
        coord._validate_launch(launch, index, stage)
        coord._validate_postrun(chunk["postrun"]["gate"], index, frozen, stage)
        require(chunk["postrun"]["queue_row"]["id"] == stage["lease_id"] and
                chunk["postrun"]["queue_row"]["state"] == "RELEASED",
                f"Chunk{index:02d} saved lease identity changed")
        files = {"prepare": prepare_paths(index)["receipt"],
                 "stage": stage_paths(index)["stage"],
                 "launch": launch_paths(index)["launch"]}
        for phase, path in files.items():
            require(json.loads(path.read_text()) == chunk[phase]["result"],
                    f"Chunk{index:02d} local {phase} receipt changed")
        source_receipts.append({"chunk_index": index,
                                **{phase + "_sha256": coord.sha(path)
                                   for phase, path in files.items()},
                                "graph_hashes_sha256": coord.digest_object(
                                    chunk["postrun"]["gate"]["graph_hashes"])})
        first_seven_hashes.extend(chunk["postrun"]["gate"]["graph_hashes"])
    require(len(first_seven_hashes) == 102, "First seven graph count changed")
    require(set(stopped["chunks"][7]) == {"prepare", "stage", "fair_prelaunch", "launch"}
            and "result" not in stopped["chunks"][7]["launch"],
            "Stopped chunk07 no longer has the preserved launch intent")

    audit = read_pinned(AUDIT, AUDIT_SHA)
    prepared = read_pinned(LOCAL, LOCAL_SHA)
    stage = read_pinned(STAGE, STAGE_SHA)
    config = read_pinned(CONFIG, CONFIG_SHA)
    require(audit["status"] == "RECONCILED_EXP227_CHUNK07_WAITING_NO_LAUNCH" and
            audit["remote"]["queue_row"]["state"] == "CANCELLED" and
            audit["source_stopped_sha256"] == SOURCE_SHA, "V1 cancellation audit changed")
    require(prepared["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V2_LOCAL_ONLY" and
            prepared["successor_audit_sha256"] == AUDIT_SHA and
            prepared["source_stopped_sha256"] == SOURCE_SHA, "V2 local prepare changed")
    require(stage["status"] == "STAGED_EXP227_CHUNK07_WAITSAFE_V2_NO_LABELS" and
            stage["source_stopped_sha256"] == SOURCE_SHA and
            stage["local_prepare_sha256"] == LOCAL_SHA, "V2 stage changed")
    require(stage["manifest_sha256"] == MANIFEST_SHA and stage["plan_sha256"] == PLAN_SHA,
            "V2 remote manifest or plan changed")
    require(stage["movies"] == frozen["chunks"][7] == prepared["movies"] and
            stage["assignment_sha256"] == frozen["assignment_sha256"] and
            stage["selection_sha256"] == frozen["selection_sha256"] and
            stage["checkpoint_sha256"] == frozen["checkpoint_sha256"] and
            prepared["checkpoint_sha256"] == frozen["checkpoint_sha256"],
            "V2 assignment, selection or checkpoint changed")
    require(stage["target_labels_read"] is False and
            prepared["target_labels_read"] is False and
            prepared["target_score_computed"] is False and
            stage["kaggle_post"] is False, "V2 no-label assertion changed")
    for key in ("code", "run", "lease_id", "token"):
        require(stage[key] == prepared["identity"][key] == config[key],
                f"V2 {key} changed")
    require(config["arguments"] == [stage["code"] + "/plan.json", "--plan-sha256",
                                     PLAN_SHA] and config["pool"] == "a100" and
            config["chunk_index"] == 7, "V2 configuration changed")

    earlier = []
    for prior in range(attempt):
        path = attempt_paths(prior)["result"]
        result = json.loads(path.read_text())
        require(result["status"] in ("WAITING_FOR_FAIR_A100_NO_REQUEST",
                                     "WAITING_RESOURCE_CANCELLED_NO_RUN") and
                result["attempt"] == prior and
                result["lease_id"] == attempt_lease(stage["lease_id"], prior) and
                result["run"] == stage["run"] and
                result["target_labels_read"] is False and
                result["kaggle_post"] is False, "Earlier attempt not a sealed wait")
        if result["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN":
            cancellation = result["cancelled"]
            require(cancellation["queue_row"]["state"] == "CANCELLED" and
                    cancellation["queue_row"]["gpus"] == [] and
                    cancellation["queue_row"]["process"] is None and
                    cancellation["run_worker"] == {
                        "run_absent": True, "matching_processes": [], "matching_gpu_pids": []},
                    "Earlier attempt cancellation was not proved")
        earlier.append({"attempt": prior, "lease_id": result["lease_id"],
                        "status": result["status"], "result_sha256": coord.sha(path)})
    for later in range(attempt + 1, 100):
        require(not attempt_paths(later)["result"].exists(),
                "A later attempt result exists; reconcile before finalizing")
    files = attempt_paths(attempt)
    result = json.loads(files["result"].read_text())
    require(result["status"] == "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V2" and
            result["attempt"] == attempt and result["stage_sha256"] == STAGE_SHA and
            result["target_labels_read"] is False and result["kaggle_post"] is False,
            "Chosen attempt was not an exact no-label v2 launch")
    actual_lease = attempt_lease(stage["lease_id"], attempt)
    lease, assigned = result["lease"], result["config"]
    require(assigned["lease_id"] == actual_lease and
            all(assigned[key] == config[key] for key in config if key != "lease_id") and
            assigned["gpu"] in lease["gpus"] and assigned["alias"] == "nsu-a100",
            "Chosen attempt config or GPU changed")
    require(lease["state"] == "RESERVED" and lease["id"] == actual_lease and
            lease["run_path"] == stage["run"] and lease["token"] == stage["token"] and
            lease["owner"] == "biohub-agent" and
            lease["project"] == "biohub-cell-tracking-during-development" and
            lease["pool"] == "a100" and lease["alias"] == "nsu-a100" and
            len(lease["gpus"]) == 1, "Chosen attempt lease identity changed")
    require(result["remote_preflight"] == {
        "status": "PASS_EXP227_TARGET_CHUNK_LAUNCH_PREFLIGHT",
        "manifest_sha256": MANIFEST_SHA, "plan_sha256": PLAN_SHA, "run_absent": True},
        "Chosen attempt remote preflight changed")
    fair = result["fair"]
    physical = fair["physical"]
    require(fair["status"] == "FAIR_IDLE_A100_AVAILABLE" and
            fair["gpu"] == assigned["gpu"] and
            set(physical["idle_gpus"]) == set(physical["all_gpus"]) -
            set(physical["busy_gpus"]) and assigned["gpu"] in physical["idle_gpus"] and
            fair["exp236_active_or_waiting"] == [], "Chosen attempt fair GPU proof changed")
    require(isinstance(result["launch"]["wrapper"], int) and
            isinstance(result["launch"]["observe"], int) and
            result["control"]["controller_pid"] > 0, "Chosen attempt process launch missing")
    intent = json.loads(files["intent"].read_text())
    reservation = json.loads(files["reservation"].read_text())
    partial = json.loads(files["partial"].read_text())
    # Intent and reservation hold the config before GPU assignment.
    base_config = {key: value for key, value in assigned.items() if key not in ("gpu", "alias")}
    require(intent["status"] == "INTENT_EXP227_CHUNK07_V2_QUEUE_REQUEST" and
            intent["attempt"] == attempt and intent["stage_sha256"] == STAGE_SHA and
            intent["config"] == base_config and
            intent["remote_preflight"] == result["remote_preflight"] and
            intent["fair"] == fair and intent["target_labels_read"] is False and
            intent["kaggle_post"] is False, "Launch intent changed")
    require(reservation == {"status": "RESERVED_EXP227_CHUNK07_V2",
                            "attempt": attempt, "lease": lease,
                            "config": base_config, "fair": fair},
            "Reservation receipt changed")
    require(partial == {key: value for key, value in result.items()
                        if key not in ("status", "control", "kaggle_post")} |
            {"status": "PARTIAL_EXP227_CHUNK07_V2_LAUNCH"},
            "Partial launch receipt changed")
    return {"stopped": stopped, "frozen": frozen, "stage": stage,
            "result": result, "actual_lease": actual_lease,
            "first_seven_receipts": source_receipts,
            "first_seven_graph_hashes_sha256": coord.digest_object(first_seven_hashes),
            "earlier_attempts": earlier,
            "attempt_receipts": {name + "_sha256": coord.sha(path)
                                 for name, path in files.items() if path.exists()},
            "actual_attempt": attempt}


def process_source(config: dict) -> str:
    """Read only procfs and GPU PIDs, tied to this run's exact identity."""
    return '''import json,pathlib,subprocess
c=CONFIG;run=pathlib.Path(c['run'])
launch=json.loads((run/'launch.json').read_text())
pid=launch['pid'];start=launch['start'];identity=False;group=False;matches=[]
for stat in pathlib.Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=stat.read_text();f=raw[raw.rfind(')')+2:].split();p=int(stat.parent.name)
  if f[0]=='Z':continue
  if p==pid and f[19]==start:identity=True
  if int(f[2])==pid:group=True
  cmdline=(stat.parent/'cmdline').read_bytes().replace(b'\\x00',b' ').decode(errors='replace')
  if any(marker in cmdline for marker in (c['run'],c['code'],c['token'])):
   matches.append({'pid':p,'cmdline':cmdline[:300]})
 except (FileNotFoundError,PermissionError,ProcessLookupError):pass
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid',
                    '--format=csv,noheader'],capture_output=True,text=True,check=True)
gpu_pids={int(line.split(',')[0]) for line in gpu.stdout.splitlines() if line.strip()}
print(json.dumps({'launch':launch,'identity_alive':identity,'group_alive':group,
                  'matching_processes':matches,
                  'matching_gpu_pids':sorted(gpu_pids & {x['pid'] for x in matches})}))
'''.replace("CONFIG", repr(config))


def audit_remote(local: dict, ops=None, process_probe=None) -> dict:
    """Recheck 102 saved graphs and all 14 new graphs without opening labels."""
    ops = ops or coord.DefaultOps()
    process_probe = process_probe or (lambda config: ssh("nsu-a100", "python3 -",
                                                         process_source(config)))
    stopped, frozen = local["stopped"], local["frozen"]
    actual_stage = {**local["stage"], "lease_id": local["actual_lease"]}
    queue = ops.queue_status()
    rows = []
    for index in range(8):
        stage = stopped["chunks"][index]["stage"]["result"] if index < 7 else actual_stage
        launch = stopped["chunks"][index]["launch"]["result"] if index < 7 else local["result"]
        lease = launch["lease"]
        completion = ops.completion(stage["run"])
        require(coord._completion_ready(completion, stage["run"]),
                f"Chunk{index:02d} has no exit0 and completed release")
        control_row = completion["control"]["queue"]
        row = live_release(queue, stage["lease_id"], stage["run"])
        for key in ("id", "owner", "token", "project", "run_path", "pool"):
            require(row.get(key) == lease[key] == control_row.get(key),
                    f"Chunk{index:02d} live release changed {key}")
        require(row["gpus"] == [] and row["process"] == control_row["process"] and
                completion["exit"]["returncode"] == 0 and
                completion["exit"]["hard_timeout"] is False,
                f"Chunk{index:02d} did not cleanly release")
        config = launch["config"]
        process = process_probe(config)
        require(process["identity_alive"] is False and
                process["group_alive"] is False and
                process["matching_processes"] == [] and
                process["matching_gpu_pids"] == [] and
                process["launch"] == row["process"],
                f"Chunk{index:02d} still has a worker or GPU process")
        gate = ops.postrun(stage)
        coord._validate_postrun(gate, index, frozen, stage)
        if index < 7:
            require(gate == stopped["chunks"][index]["postrun"]["gate"],
                    f"Chunk{index:02d} graph or receipt hash changed")
        rows.append({"index": index, "stage": stage, "gate": gate, "queue_row": row,
                     "process": process})
    # Close the time gap created by rehashing 116 graphs with a fresh queue read.
    final_queue = ops.queue_status()
    for entry in rows:
        stage = entry["stage"]
        current = live_release(final_queue, stage["lease_id"], stage["run"])
        require(current == entry["queue_row"],
                f"Chunk{entry['index']:02d} live lease changed during graph checks")
    for prior in local["earlier_attempts"]:
        matches = [row for row in final_queue["requests"] if row["id"] == prior["lease_id"]]
        if prior["status"] == "WAITING_RESOURCE_CANCELLED_NO_RUN":
            require(len(matches) == 1 and matches[0]["state"] == "CANCELLED" and
                    matches[0]["gpus"] == [] and matches[0]["process"] is None,
                    "Earlier cancelled lease became active")
        else:
            require(matches == [], "Earlier no-request wait acquired a lease")
    all_hashes = [hash_row for entry in rows for hash_row in entry["gate"]["graph_hashes"]]
    require(len(all_hashes) == 116 and len({row["dataset"] for row in all_hashes}) == 116 and
            [row["dataset"] for row in all_hashes] ==
            [name for chunk in frozen["chunks"] for name in chunk],
            "All-116 graph assignment changed")
    return {"rows": rows, "queue_snapshot_sha256": coord.digest_object(final_queue),
            "graph_hashes_sha256": coord.digest_object(all_hashes),
            "chunk07_graph_hashes_sha256": coord.digest_object(rows[7]["gate"]["graph_hashes"])}


def final_state(local: dict, remote: dict) -> dict:
    state = {key: value for key, value in local["stopped"].items()
             if key not in ("status", "chunks", "updated_unix", "state_sha256", "error")}
    state["chunks"] = list(local["stopped"]["chunks"][:7])
    stage = remote["rows"][7]["stage"]
    result = local["result"]
    state["chunks"].append({
        "prepare": {"validated": True, "chunk_index": 7,
                    "result": json.loads(LOCAL.read_text()),
                    "source_receipt_sha256": LOCAL_SHA},
        "stage": {"validated": True, "chunk_index": 7, "result": stage,
                  "result_is_derived_lease_binding":
                      local["actual_lease"] != local["stage"]["lease_id"],
                  "source_receipt_sha256": STAGE_SHA,
                  "source_stage_lease_id": local["stage"]["lease_id"],
                  "actual_launch_lease_id": local["actual_lease"]},
        "launch": {"validated": True, "chunk_index": 7, "result": result,
                   "attempt": local["actual_attempt"],
                   "source_receipt_sha256": local["attempt_receipts"]["result_sha256"]},
        "postrun": {"validated": True, "gate": remote["rows"][7]["gate"],
                    "queue_row": remote["rows"][7]["queue_row"],
                    "queue_snapshot_sha256": remote["queue_snapshot_sha256"],
                    "live_release_checked_unix": time.time()},
    })
    state.update({"status": "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED",
                  "movie_count": 116, "graph_count": 116, "all_leases_released": True,
                  "target_labels_read": False, "target_score_computed": False,
                  "separate_guarded_scorer_may_be_prepared": True,
                  "successor_audit": {"status": "PASS_EXP227_TARGET6BBA_WAITSAFE_V2_FINAL_NO_LABELS",
                      "evidence_class": "image-only target inference; broader research previously inspected target labels",
                      "source_stopped_sha256": SOURCE_SHA,
                      "source_stopped_state_sha256": local["stopped"]["state_sha256"],
                      "first_seven_receipts": local["first_seven_receipts"],
                      "first_seven_graph_hashes_sha256": local["first_seven_graph_hashes_sha256"],
                      "successor_prepare_sha256": LOCAL_SHA,
                      "successor_stage_sha256": STAGE_SHA,
                      "successor_config_sha256": CONFIG_SHA,
                      "actual_attempt": local["actual_attempt"],
                      "actual_lease_id": local["actual_lease"],
                      "earlier_attempts": local["earlier_attempts"],
                      "attempt_receipts": local["attempt_receipts"],
                      "remote_manifest_sha256": MANIFEST_SHA,
                      "remote_plan_sha256": PLAN_SHA,
                      "queue_snapshot_sha256": remote["queue_snapshot_sha256"],
                      "graph_hashes_sha256": remote["graph_hashes_sha256"],
                      "chunk07_graph_hashes_sha256": remote["chunk07_graph_hashes_sha256"],
                      "process_evidence": [{"chunk_index": item["index"],
                                            "process": item["process"]}
                                           for item in remote["rows"]],
                      "target_labels_read": False, "target_score_computed": False,
                      "kaggle_post": False}})
    coord._seal(state)
    return state


def finalize(attempt: int, *, write_receipt: bool = False,
             ops=None, process_probe=None, receipt: Path = RECEIPT) -> dict:
    receipt = Path(receipt)
    if write_receipt:
        require(not receipt.exists(), "Final receipt exists; one-shot mode cannot overwrite it")
    local = local_sources(attempt)
    remote = audit_remote(local, ops=ops, process_probe=process_probe)
    state = final_state(local, remote)
    if write_receipt:
        coord._save(receipt, state, create=True)
        require(coord._read_state(receipt) == state, "Written final receipt failed integrity check")
    return {"status": state["status"], "mode": "WRITE_RECEIPT" if write_receipt else "CHECK_ONLY",
            "attempt": attempt, "actual_lease_id": local["actual_lease"],
            "graph_count": state["graph_count"],
            "graph_hashes_sha256": remote["graph_hashes_sha256"],
            "state_sha256": state["state_sha256"],
            "receipt": str(receipt) if write_receipt else None,
            "receipt_sha256": coord.sha(receipt) if write_receipt else None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True,
                        help="The reviewed v2 attempt that actually launched")
    parser.add_argument("--write-receipt", action="store_true",
                        help="Create the separate final receipt once, after every gate")
    args = parser.parse_args()
    print(json.dumps(finalize(args.attempt, write_receipt=args.write_receipt)))


if __name__ == "__main__":
    main()
