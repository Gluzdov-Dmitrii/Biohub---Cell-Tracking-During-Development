"""Future one-shot stage of the EXP227 target116 scorer after eight releases.

Do not run while the no-label target coordinator is incomplete. This script
creates an intent receipt before any remote mutation and never retries an
uncertain stage automatically.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from monitor_exp213_job import ssh
from prepare_exp227_target6bba_scorer_local_v4 import ROOT, BUNDLE, RECEIPT as LOCAL, verify_bundle


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp227_target6bba_current_scorer_v4_20260927"
RUN = REMOTE + "/runs/exp227_target6bba_current116_v4_20260927"
STOPPED_COORDINATOR = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
FINAL = ROOT / "reports/exp227_target6bba_all116_waitsafe_v3_final_20260927.json"
FINALIZER_SOURCE = ROOT / "scripts/finalize_exp227_target6bba_waitsafe_v3.py"
FINALIZER_TEST = ROOT / "tests/test_finalize_exp227_target6bba_waitsafe_v3.py"
FINALIZER_CORRECTION = ROOT / "reports/exp227_v3_finalizer_process_identity_correction_20260927.json"
FINALIZER_CORRECTION_SHA = "031e5802bc468cafe587846919469cc760ad6d7448f02f26903728bb9889bcc7"
FINALIZER_TEST_PRE_RECEIPT_SHA = "42cf0a7eb77f23cfe7403e266939494ed3d6f4bf975c94a1748e6a39a5d5133f"
FINALIZER_TEST_CURRENT_SHA = "876a47319a4af9d48cbd44c1558ae4af43b017fac5f319451108bea750e59c32"
ATTEMPT1_RESULT = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_attempt01_20260927_result.json"
ATTEMPT1_RESULT_SHA = "800c78e010bef37eac0f6f167f9ddb28fca819577b2aa41c6a1092c30599b9bf"
ATTEMPT1_LEASE = "exp227-target6bba-chunk07-v3a01-20260927"
INTENT = ROOT / "reports/exp227_target6bba_scorer_stage_intent_v4_20260927.json"
RECEIPT = ROOT / "reports/exp227_target6bba_scorer_stage_v4_20260927.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha(body):
    return hashlib.sha256(body.encode()).hexdigest()


def ssh_gate_only(command, timeout=900):
    """One bounded read-only graph gate; the generic SSH helper caps at 45s."""
    process = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                              "nsu-quadro", command], text=True, capture_output=True,
                             timeout=timeout)
    if process.returncode:
        raise RuntimeError(f"Gate-only exit {process.returncode}: {process.stderr[-1200:]}")
    return json.loads(process.stdout)


def exact_final_pin(coordinator, expected_sha256, coordinator_path):
    assert len(expected_sha256) == 64 and all(ch in "0123456789abcdef" for ch in expected_sha256)
    assert sha(coordinator_path) == expected_sha256
    assert sha(ATTEMPT1_RESULT) == ATTEMPT1_RESULT_SHA
    launched = json.loads(ATTEMPT1_RESULT.read_text())
    assert launched["status"] == "LAUNCHED_EXP227_CHUNK07_WAITSAFE_V3"
    assert launched["attempt"] == 1 and launched["lease"]["id"] == ATTEMPT1_LEASE
    audit = coordinator["successor_audit"]
    assert audit["actual_attempt"] == 1 and audit["actual_lease_id"] == ATTEMPT1_LEASE
    assert audit["attempt_receipts"]["result_sha256"] == ATTEMPT1_RESULT_SHA
    assert coordinator["chunks"][7]["launch"]["result"]["lease"]["id"] == ATTEMPT1_LEASE


def reviewed_finalizer_source(local, final_sha256):
    original = local["future_finalizer_source_sha256"]
    current = sha(FINALIZER_SOURCE)
    if original == current:
        return
    assert sha(FINALIZER_CORRECTION) == FINALIZER_CORRECTION_SHA
    correction = json.loads(FINALIZER_CORRECTION.read_text())
    assert correction["status"] == "PASS_EXP227_V3_FINALIZER_REAL_QUEUE_PROCESS_IDENTITY_CORRECTION"
    assert correction["old_finalizer_source_sha256"] == original
    assert correction["corrected_finalizer_source_sha256"] == current
    assert correction["corrected_test_source_sha256"] == FINALIZER_TEST_PRE_RECEIPT_SHA
    assert sha(FINALIZER_TEST) == FINALIZER_TEST_CURRENT_SHA
    assert correction["final_receipt_sha256"] == final_sha256
    assert correction["check_only_graph_count"] == 116
    assert correction["target_labels_read"] is False
    assert correction["target_score_computed"] is False
    assert correction["kaggle_post"] is False


def local_gate(coordinator_path, final_sha256):
    coordinator_path = Path(coordinator_path).resolve(strict=True)
    assert coordinator_path != STOPPED_COORDINATOR.resolve()
    assert coordinator_path == FINAL.resolve(strict=True)
    assert sha(coordinator_path) == final_sha256
    assert not INTENT.exists() and not RECEIPT.exists(), "Existing stage intent requires reconciliation"
    local = json.loads(LOCAL.read_text())
    assert local["status"] == "PREPARED_EXP227_TARGET6BBA_CURRENT_SCORER_V4_LOCAL_ONLY"
    assert local["target_labels_read"] is False and local["remote_stage_created"] is False
    assert local["final_all116_receipt_written"] is False
    reviewed_finalizer_source(local, final_sha256)
    manifest_sha, manifest = verify_bundle()
    assert local["local_manifest_sha256"] == manifest_sha and local["source_hashes"] == manifest
    baseline = json.loads((BUNDLE / "baseline_reference.json").read_text())
    assert local["baseline_metrics_sha256"] == manifest["baseline_reference.json"]
    assert local["baseline_target_input_hashes"] == [part for part in baseline["input_hashes"]["public"]
                                                       if "_6bba_" in part["csv"]]
    target = [row for row in baseline["rows"]["public"] if row["dataset"].startswith("6bba_")]
    assert len(target) == 116
    assert local["baseline_target_rows_sha256"] == text_sha(json.dumps(
        target, sort_keys=True, separators=(",", ":")))
    successor = json.loads((BUNDLE / "successor_prepare.json").read_text())
    successor_stage = json.loads((BUNDLE / "successor_stage.json").read_text())
    successor_config = json.loads((BUNDLE / "successor_config.json").read_text())
    assert local["successor_prepare_sha256"] == sha(BUNDLE / "successor_prepare.json")
    assert local["successor_stage_sha256"] == sha(BUNDLE / "successor_stage.json")
    assert local["successor_config_sha256"] == sha(BUNDLE / "successor_config.json")
    assert successor_stage["status"] == "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS"
    assert local["successor_identity"] == successor["identity"]
    assert sha(STOPPED_COORDINATOR) == successor["source_stopped_sha256"]
    assert successor_stage["local_prepare_sha256"] == local["successor_prepare_sha256"]
    assert successor_stage["staged"]["runner_sha256"] == successor["runner_sha256"]
    assert successor_stage["runner_contract"] == successor["actual_runner_contract"]
    assert successor_config["arguments"] == [successor["identity"]["code"] + "/plan.json",
                                             "--plan-sha256", successor["plan_sha256"]]
    coordinator = json.loads(coordinator_path.read_text())
    exact_final_pin(coordinator, final_sha256, coordinator_path)
    assert coordinator["status"] == "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED"
    assert coordinator["movie_count"] == coordinator["graph_count"] == 116
    assert coordinator["all_leases_released"] is True
    assert coordinator["target_labels_read"] is False and coordinator["target_score_computed"] is False
    assert len(coordinator["chunks"]) == 8
    audit = coordinator["successor_audit"]
    assert audit["status"] == "PASS_EXP227_TARGET6BBA_WAITSAFE_V3_FINAL_NO_LABELS"
    assert audit["source_stopped_sha256"] == sha(STOPPED_COORDINATOR)
    assert audit["successor_prepare_sha256"] == local["successor_prepare_sha256"]
    assert audit["successor_stage_sha256"] == local["successor_stage_sha256"]
    assert audit["successor_config_sha256"] == local["successor_config_sha256"]
    assert audit["remote_manifest_sha256"] == successor_stage["manifest_sha256"]
    assert audit["remote_plan_sha256"] == successor["plan_sha256"]
    assert audit["remote_runner_sha256"] == successor["runner_sha256"]
    assert audit["target_labels_read"] is False and audit["target_score_computed"] is False
    from coordinate_exp227_target6bba import _read_state, frozen_inputs
    assert _read_state(coordinator_path) == coordinator
    frozen = frozen_inputs()
    assert coordinator["frozen"] == frozen
    for index, entry in enumerate(coordinator["chunks"]):
        assert entry["stage"]["validated"] is True
        assert entry["launch"]["validated"] is True
        assert entry["postrun"]["validated"] is True
        assert entry["postrun"]["gate"]["chunk_index"] == index
        assert entry["postrun"]["gate"]["movies"] == frozen["chunks"][index]
    final = coordinator["chunks"][7]["stage"]["result"]
    assert final["code"] == successor["identity"]["code"]
    assert final["run"] == successor["identity"]["run"]
    actual_lease = audit["actual_lease_id"]
    attempt = audit["actual_attempt"]
    assert isinstance(attempt, int) and 0 <= attempt <= 99
    expected_lease = (successor["identity"]["lease_id"] if attempt == 0 else
        successor["identity"]["lease_id"].replace("-v3-", f"-v3a{attempt:02d}-"))
    assert actual_lease == expected_lease
    assert final["lease_id"] == actual_lease
    assert coordinator["chunks"][7]["launch"]["result"]["config"]["lease_id"] == actual_lease
    assert coordinator["chunks"][7]["postrun"]["queue_row"]["id"] == actual_lease
    assert coordinator["chunks"][7]["stage"]["source_stage_lease_id"] == successor["identity"]["lease_id"]
    assert coordinator["chunks"][7]["stage"]["source_receipt_sha256"] == local["successor_stage_sha256"]
    assert final["plan_sha256"] == successor["plan_sha256"]
    assert final["manifest_sha256"] == successor_stage["manifest_sha256"]
    graph_hashes = [row for entry in coordinator["chunks"]
                    for row in entry["postrun"]["gate"]["graph_hashes"]]
    assert len(graph_hashes) == 116
    assert [row["dataset"] for row in graph_hashes] == [name for group in frozen["chunks"]
                                                       for name in group]
    graph_sha = text_sha(json.dumps(graph_hashes, sort_keys=True, separators=(",", ":")))
    assert audit["graph_hashes_sha256"] == graph_sha
    return local, coordinator, frozen, coordinator_path, graph_sha


def sealed_sources(local):
    """Read the exact source bytes that will be transmitted to Linux."""
    sources = {name: (BUNDLE / name).read_bytes().decode("utf-8")
               for name in local["source_hashes"]}
    assert all(text_sha(body) == local["source_hashes"][name]
               for name, body in sources.items())
    return sources


def stage(coordinator_path, final_sha256):
    local, coordinator, frozen, coordinator_path, graph_sha = local_gate(coordinator_path, final_sha256)
    # Preserve CRLF in the frozen assignment/selection and coordinator bytes.
    # Text-mode reads on Windows normalize them and would break their SHA pins.
    sources = sealed_sources(local)
    coordinator_text = coordinator_path.read_bytes().decode("utf-8")
    sources["coordinator_snapshot.json"] = coordinator_text
    names = [name for group in frozen["chunks"] for name in group]
    config = {
        "experiment": "EXP227_SOURCE44_TARGET6BBA_CURRENT116_V4",
        "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
        "assignment": CODE + "/assignment.json", "assignment_sha256": frozen["assignment_sha256"],
        "selection": CODE + "/selection.json", "selection_sha256": frozen["selection_sha256"],
        "successor_prepare": CODE + "/successor_prepare.json",
        "successor_prepare_sha256": local["successor_prepare_sha256"],
        "successor_stage": CODE + "/successor_stage.json",
        "successor_stage_sha256": local["successor_stage_sha256"],
        "successor_config": CODE + "/successor_config.json",
        "successor_config_sha256": local["successor_config_sha256"],
        "final_graph_hashes_sha256": graph_sha,
        "checkpoint_sha256": frozen["checkpoint_sha256"],
        "coordinator": CODE + "/coordinator_snapshot.json",
        "coordinator_sha256": text_sha(coordinator_text),
        "target_ids": names,
        "cohort": REMOTE + "/code/exp228_horaz_ensemble_quadro_v2_20260923/heldout175_manifest.json",
        "cohort_sha256": "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4",
        "baseline_metrics": REMOTE + "/runs/exp214_gapfix_score175_20260914/output/new90/metrics.json",
        "baseline_metrics_sha256": "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5",
        "baseline_input_hashes": json.loads(sources["baseline_reference.json"])["input_hashes"]["public"],
        "baseline_target_rows_sha256": local["baseline_target_rows_sha256"],
        "evaluator_config": CODE + "/exp223_config.json",
        "evaluator_config_sha256": text_sha(sources["exp223_config.json"]),
        "current_metrics": CODE + "/current_official/metrics.py",
        "current_metrics_sha256": text_sha(sources["current_official/metrics.py"]),
        "current_division": CODE + "/current_official/division_metrics.py",
        "current_division_sha256": text_sha(sources["current_official/division_metrics.py"]),
        "tracksdata_commit": "e13cf379b5127deeb8301ce56410fda35b5a3cf9",
        "image_scale_audit": CODE + "/image_scale_audit.json",
        "image_scale_audit_sha256": text_sha(sources["image_scale_audit.json"]),
        "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
        "data_dir": REMOTE + "/data/exp213_source_view_20260912",
        "python": REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python",
        "output": RUN + "/output",
    }
    sources["score_config.json"] = json.dumps(config, indent=2) + "\n"
    intent = {"status": "EXP227_TARGET116_CURRENT_SCORER_V4_STAGE_INTENT",
              "coordinator_local_path": str(coordinator_path),
              "coordinator_local_sha256": final_sha256,
              "successor_actual_attempt": 1,
              "successor_actual_lease_id": ATTEMPT1_LEASE,
              "successor_launch_result_sha256": ATTEMPT1_RESULT_SHA,
              "final_graph_hashes_sha256": graph_sha,
              "local_prepare_sha256": sha(LOCAL), "local_manifest_sha256": local["local_manifest_sha256"],
              "score_config_sha256": text_sha(sources["score_config.json"]),
              "remote_code": CODE, "remote_run": RUN, "target_labels_read": False}
    with INTENT.open("x") as stream:
        stream.write(json.dumps(intent, indent=2) + "\n")
    preflight = '''import hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert not code.exists() and not run.exists()
assert sha(@@COHORT@@)==@@COHORT_SHA@@
assert sha(@@BASELINE@@)==@@BASELINE_SHA@@
assert sha(@@CHECKPOINT@@)==@@CHECKPOINT_SHA@@
print(json.dumps({'status':'PASS_EXP227_TARGET116_CURRENT_SCORER_V4_STAGE_PREFLIGHT'}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@COHORT@@", repr(config["cohort"])).replace("@@COHORT_SHA@@", repr(config["cohort_sha256"])).replace(
        "@@BASELINE@@", repr(config["baseline_metrics"])).replace(
        "@@BASELINE_SHA@@", repr(config["baseline_metrics_sha256"])).replace(
        "@@CHECKPOINT@@", repr(json.loads((BUNDLE / "selection.json").read_text())["checkpoint"])).replace(
        "@@CHECKPOINT_SHA@@", repr(config["checkpoint_sha256"]))
    pre = ssh("nsu-quadro", "python3 -", preflight)
    assert pre["status"] == "PASS_EXP227_TARGET116_CURRENT_SCORER_V4_STAGE_PREFLIGHT"
    stage_source = '''import ast,hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);assert not code.exists();code.mkdir(parents=True)
files=@@FILES@@
for name,body in files.items():
 path=code/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_TARGET116_CURRENT_SCORER_V4','code':str(code),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json')}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@FILES@@", repr(sources))
    staged = ssh("nsu-quadro", "python3 -", stage_source)
    assert staged["status"] == "STAGED_EXP227_TARGET116_CURRENT_SCORER_V4"
    assert staged["score_config_sha256"] == intent["score_config_sha256"]
    # This is a full label-free replay on the staged code, graph outputs and live queue.
    import shlex
    check = ssh_gate_only(shlex.join([
        REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python",
        CODE + "/score_exp227_target6bba_current_v4.py", CODE + "/score_config.json",
        "--config-sha256", staged["score_config_sha256"], "--gate-only"]))
    assert check["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    receipt = {"status": "STAGED_EXP227_TARGET116_CURRENT_SCORER_V4_NO_LABELS",
               "stage": staged, "gate_only": check, "config": config,
               "intent_sha256": sha(INTENT),
               "coordinator_local_path": str(coordinator_path),
               "coordinator_local_sha256": final_sha256,
               "successor_actual_attempt": 1,
               "successor_actual_lease_id": ATTEMPT1_LEASE,
               "successor_launch_result_sha256": ATTEMPT1_RESULT_SHA,
               "final_graph_hashes_sha256": graph_sha,
               "target_labels_read": False, "target_score_computed": False}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coordinator", type=Path, required=True)
    parser.add_argument("--final-sha256", required=True,
                        help="Reviewed SHA256 of the completed v3 all116 final receipt")
    args = parser.parse_args()
    result = stage(args.coordinator, args.final_sha256)
    print(json.dumps({"status": result["status"], "code": result["stage"]["code"]}))
