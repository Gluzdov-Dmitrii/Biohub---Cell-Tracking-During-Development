"""Future one-shot stage of the EXP236 target59 scorer after four releases.

Do not run while the no-label target coordinator is incomplete. This script
creates an intent receipt before any remote mutation and never retries an
uncertain stage automatically.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from monitor_exp213_job import ssh
from prepare_exp236_target44b6_scorer_local import ROOT, BUNDLE, RECEIPT as LOCAL, verify_bundle


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp236_target44b6_current_scorer_v2_20260927"
RUN = REMOTE + "/runs/exp236_target44b6_current59_v2_20260927"
COORDINATOR = ROOT / "reports/exp236_target44b6_four_chunk_coordinator_20260927.json"
INTENT = ROOT / "reports/exp236_target44b6_scorer_stage_intent_v2_20260927.json"
RECEIPT = ROOT / "reports/exp236_target44b6_scorer_stage_v2_20260927.json"


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


def local_gate():
    assert not INTENT.exists() and not RECEIPT.exists(), "Existing stage intent requires reconciliation"
    local = json.loads(LOCAL.read_text())
    assert local["status"] == "PREPARED_EXP236_TARGET44B6_SCORER_LOCAL_ONLY"
    assert local["target_labels_read"] is False and local["remote_stage_created"] is False
    manifest_sha, manifest = verify_bundle()
    assert local["local_manifest_sha256"] == manifest_sha and local["source_hashes"] == manifest
    baseline = json.loads((BUNDLE / "baseline_reference.json").read_text())
    assert local["baseline_metrics_sha256"] == manifest["baseline_reference.json"]
    assert local["baseline_target_input_hashes"] == [part for part in baseline["input_hashes"]["public"]
                                                       if "_44b6_" in part["csv"]]
    target_rows = [row for row in baseline["rows"]["public"] if row["dataset"].startswith("44b6_")]
    assert len(target_rows) == 59
    target_sha = text_sha(json.dumps(target_rows, sort_keys=True, separators=(",", ":")))
    assert local["baseline_target_rows_sha256"] == target_sha
    coordinator = json.loads(COORDINATOR.read_text())
    assert coordinator["status"] == "PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED"
    assert coordinator["movie_count"] == coordinator["graph_count"] == 59
    assert coordinator["all_leases_released"] is True
    assert coordinator["target_labels_read"] is False and coordinator["target_score_computed"] is False
    assert len(coordinator["chunks"]) == 4
    from coordinate_exp236_target44b6 import _read_state, frozen_inputs
    assert _read_state(COORDINATOR) == coordinator
    frozen = frozen_inputs()
    assert coordinator["frozen"] == frozen
    for index, entry in enumerate(coordinator["chunks"]):
        assert entry["postrun"]["validated"] is True
        assert entry["postrun"]["gate"]["chunk_index"] == index
        assert entry["postrun"]["gate"]["movies"] == frozen["chunks"][index]
    return local, coordinator, frozen


def sealed_sources(local):
    """Read the exact source bytes that will be transmitted to Linux."""
    sources = {name: (BUNDLE / name).read_bytes().decode("utf-8")
               for name in local["source_hashes"]}
    assert all(text_sha(body) == local["source_hashes"][name]
               for name, body in sources.items())
    return sources


def stage():
    local, coordinator, frozen = local_gate()
    # Preserve CRLF in the frozen assignment and coordinator bytes.
    # Text-mode reads on Windows normalize them and would break their SHA pins.
    sources = sealed_sources(local)
    coordinator_text = COORDINATOR.read_bytes().decode("utf-8")
    sources["coordinator_snapshot.json"] = coordinator_text
    names = [name for group in frozen["chunks"] for name in group]
    config = {
        "experiment": "EXP236_SOURCE6BBA_TARGET44B6_CURRENT59",
        "evidence_class": "leakage-controlled reciprocal evaluation; historically exposed target labels",
        "assignment": CODE + "/assignment.json", "assignment_sha256": frozen["assignment_sha256"],
        "source_training": CODE + "/source_training.json",
        "source_training_sha256": frozen["source_training_sha256"],
        "source_handoff": CODE + "/source_handoff.json",
        "source_handoff_sha256": frozen["source_handoff_sha256"],
        "source_score": CODE + "/source_score.json",
        "source_score_sha256": frozen["source_score_sha256"],
        "source_graph_plan": CODE + "/source_graph_plan.json",
        "source_graph_plan_sha256": frozen["source_graph_plan_sha256"],
        "prereg_sha256": frozen["prereg_sha256"],
        "checkpoint": REMOTE + "/runs/exp236_horaz_source6bba_block04_v2_20260927/output/fold0/last.pt",
        "checkpoint_sha256": frozen["checkpoint_sha256"],
        "parent_graph_code": REMOTE + "/code/exp236_source_graph10_v2_20260927",
        "parent_graph_manifest_sha256": "92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2",
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
    intent = {"status": "EXP236_TARGET59_SCORER_STAGE_INTENT",
              "coordinator_local_sha256": sha(COORDINATOR),
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
print(json.dumps({'status':'PASS_EXP236_TARGET59_SCORER_STAGE_PREFLIGHT'}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@COHORT@@", repr(config["cohort"])).replace("@@COHORT_SHA@@", repr(config["cohort_sha256"])).replace(
        "@@BASELINE@@", repr(config["baseline_metrics"])).replace(
        "@@BASELINE_SHA@@", repr(config["baseline_metrics_sha256"])).replace(
        "@@CHECKPOINT@@", repr(config["checkpoint"])).replace(
        "@@CHECKPOINT_SHA@@", repr(config["checkpoint_sha256"]))
    pre = ssh("nsu-quadro", "python3 -", preflight)
    assert pre["status"] == "PASS_EXP236_TARGET59_SCORER_STAGE_PREFLIGHT"
    stage_source = '''import ast,hashlib,json,pathlib
code=pathlib.Path(@@CODE@@);assert not code.exists();code.mkdir(parents=True)
files=@@FILES@@
for name,body in files.items():
 path=code/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP236_TARGET59_SCORER','code':str(code),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json')}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@FILES@@", repr(sources))
    staged = ssh("nsu-quadro", "python3 -", stage_source)
    assert staged["status"] == "STAGED_EXP236_TARGET59_SCORER"
    assert staged["score_config_sha256"] == intent["score_config_sha256"]
    # This is a full label-free replay on the staged code, graph outputs and live queue.
    import shlex
    check = ssh_gate_only(shlex.join([
        REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python",
        CODE + "/score_exp236_target44b6_current.py", CODE + "/score_config.json",
        "--config-sha256", staged["score_config_sha256"], "--gate-only"]))
    assert check["status"] == "PASS_EXP236_ALL_59_GRAPHS_BEFORE_LABEL_ACCESS"
    receipt = {"status": "STAGED_EXP236_TARGET59_SCORER_NO_LABELS",
               "stage": staged, "gate_only": check, "config": config,
               "intent_sha256": sha(INTENT), "coordinator_local_sha256": sha(COORDINATOR),
               "target_labels_read": False, "target_score_computed": False}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    result = stage()
    print(json.dumps({"status": result["status"], "code": result["stage"]["code"]}))
