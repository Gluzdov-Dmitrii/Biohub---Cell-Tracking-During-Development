"""Prepare immutable local-only EXP236 source6bba to target44b6 chunks.

No SSH, remote stage, queue request, GPU, target label, or scorer is used.
"""
import hashlib
import json
from pathlib import Path
import re

from run_exp236_target_chunk import (
    ASSIGNMENT_SHA, CHECKPOINT, CHECKPOINT_SHA, HANDOFF_SHA, PREREG_SHA,
    REMOTE, SCORE_SHA, SOURCE_GRAPH_CODE, SOURCE_MANIFEST_SHA, SOURCE_PLAN_SHA,
    TRAINING_SHA,
)


ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
PREREG = ROOT / "reports/EXP236_SOURCE6BBA_TARGET44B6_PREREG_20260927.md"
TRAINING = ROOT / "reports/exp236_source_v2_epoch10_recovery_20260927.json"
HANDOFF = ROOT / "reports/exp236_source11_handoff_recovery_20260927.json"
SCORE = ROOT / "reports/exp236_source_graph10_score_20260927.json"
SOURCE_PLAN = ROOT / "reports/exp236_source_graph10_v2_plan_20260927.json"
DATASET = re.compile(r"44b6_[0-9a-f]{8}\Z")


def paths(index):
    assert isinstance(index, int) and 0 <= index < 4
    token = f"exp236_target44b6_chunk{index:02d}_v1_20260927"
    return {"bundle": ROOT / f"work/exp236_target44b6_chunk{index:02d}_local_20260927",
            "receipt": ROOT / f"reports/exp236_target44b6_chunk{index:02d}_local_prepare_20260927.json",
            "code": REMOTE + "/code/" + token, "run": REMOTE + "/runs/" + token,
            "lease_id": f"exp236-target44b6-chunk{index:02d}-v1-20260927",
            "token": token}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def validate_assignment(assignment, index):
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["thresholds_selected"] is False and assignment["target_labels_read"] is False
    direction = assignment["directions"]["6bba"]
    assert direction["target_embryo"] == "44b6" and direction["movie_count"] == 59
    chunks = direction["chunks"]
    assert len(chunks) == 4 and [len(chunk) for chunk in chunks] == [15, 15, 15, 14]
    names = [name for chunk in chunks for name in chunk]
    assert len(names) == len(set(names)) == 59
    assert all(isinstance(name, str) and DATASET.fullmatch(name) for name in names)
    assert isinstance(index, int) and 0 <= index < 4
    return chunks[index]


def validate_source(training, handoff, score, source_plan):
    assert training["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    assert handoff["status"] == "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF"
    assert handoff["training_verified"]["controller_sha256"] == TRAINING_SHA
    assert handoff["training_verified"]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert handoff["graph_stage"]["graph_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert handoff["graph_stage"]["graph_plan_sha256"] == SOURCE_PLAN_SHA
    assert handoff["target_data_opened"] is False
    assert handoff["score_verified"]["target_labels_read"] is False
    assert handoff["score_verified"]["source_score"] == score["source_score"] == 0.8458659187983504
    assert score["status"] == "VERIFIED_EXP236_SOURCE10_OFFICIAL"
    assert score["checkpoint_sha256"] == CHECKPOINT_SHA and score["target_labels_read"] is False
    assert source_plan["experiment"] == "EXP236_SOURCE_GRAPH10"
    assert source_plan["checkpoint"] == CHECKPOINT
    assert source_plan["checkpoint_sha256"] == CHECKPOINT_SHA
    assert source_plan["code"] == SOURCE_GRAPH_CODE
    assert source_plan["training_chain"][-1]["checkpoint_sha256"] == CHECKPOINT_SHA


def fair_idle_a100(queue_state, physical_idle_uuids, lease_id):
    requests = queue_state["requests"]
    assert not any(row["id"] == lease_id for row in requests), "Existing target lease requires reconciliation"
    assert not any(row["state"].startswith("WAITING") and
                   row["project"] != "biohub-cell-tracking-during-development"
                   for row in requests), "Foreign project is waiting"
    occupied = {gpu for row in requests if row["state"] in ("RESERVED", "RUNNING")
                for gpu in row.get("gpus", [])}
    candidates = sorted(set(physical_idle_uuids) - occupied)
    assert candidates, "No fair physically idle A100"
    return candidates[0]


def build_bundle(index, bundle, inputs):
    destination = paths(index)
    bundle = Path(bundle)
    assignment = json.loads(inputs["assignment.json"])
    training = json.loads(inputs["source_training.json"])
    handoff = json.loads(inputs["source_handoff.json"])
    score = json.loads(inputs["source_score.json"])
    source_plan = json.loads(inputs["source_graph_plan.json"])
    movies = validate_assignment(assignment, index)
    validate_source(training, handoff, score, source_plan)
    bundle.mkdir(parents=True, exist_ok=False)
    code, run = destination["code"], destination["run"]
    files = dict(inputs)
    for filename in ("run_exp236_target_chunk.py", "run_exp223_inference.py",
                     "verify_exp236_target_chunk.py"):
        files[filename] = (ROOT / "scripts" / filename).read_bytes()
    plan = {"experiment": "EXP236_TARGET44B6_CHUNK", "source_embryo": "6bba",
            "target_embryo": "44b6", "chunk_index": index, "chunk_count": 4,
            "assignment": code + "/assignment.json", "assignment_sha256": ASSIGNMENT_SHA,
            "prereg_sha256": PREREG_SHA,
            "source_training": code + "/source_training.json", "source_training_sha256": TRAINING_SHA,
            "source_handoff": code + "/source_handoff.json", "source_handoff_sha256": HANDOFF_SHA,
            "source_score": code + "/source_score.json", "source_score_sha256": SCORE_SHA,
            "source_graph_plan": code + "/source_graph_plan.json",
            "source_graph_plan_sha256": SOURCE_PLAN_SHA,
            "checkpoint_epoch": 10, "checkpoint": CHECKPOINT, "checkpoint_sha256": CHECKPOINT_SHA,
            "data_root": REMOTE + "/data/exp213_source_view_20260912",
            "code": code, "output": run + "/output", "movies": movies}
    files["plan.json"] = (json.dumps(plan, indent=2) + "\n").encode()
    recipe = {"status": "LOCAL_ONLY_STAGE_RECIPE_NOT_EXECUTED",
              "copy_parent_code": SOURCE_GRAPH_CODE,
              "parent_manifest_sha256": SOURCE_MANIFEST_SHA,
              "parent_plan_sha256": SOURCE_PLAN_SHA,
              "checkpoint": CHECKPOINT, "checkpoint_sha256": CHECKPOINT_SHA,
              "target_code": code, "target_run": run,
              "wrapper_old_assertion": "assert config['script'] == 'run_exp236_source_graph10_v2.py'",
              "wrapper_new_assertion": "assert config['script'] == 'run_exp236_target_chunk.py'",
              "overlay_files": sorted(files),
              "stage_requires": ["exact parent manifest and all files", "exact source graph plan",
                                 "exact fixed source checkpoint", "absent target code and run",
                                 "wrapper assertion replaced exactly once", "all Python AST-parse"],
              "launch_requires": ["foreign WAITING fairness", "physical and queue GPU idleness",
                                  "no existing lease/run/launch artifact"],
              "completion_requires": ["exit0/no timeout", "all graph CSV/receipt SHA and invariants",
                                      "dead process group", "live RELEASED lease"]}
    files["stage_recipe.json"] = (json.dumps(recipe, indent=2) + "\n").encode()
    for name, data in files.items():
        (bundle / name).write_bytes(data)
    manifest = {name: sha(bundle / name) for name in sorted(files)}
    (bundle / "local_bundle_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return plan, manifest


def prepare_index(index):
    destination = paths(index)
    assert not destination["bundle"].exists() and not destination["receipt"].exists()
    pinned = {"assignment.json": (ASSIGNMENT, ASSIGNMENT_SHA),
              "source_training.json": (TRAINING, TRAINING_SHA),
              "source_handoff.json": (HANDOFF, HANDOFF_SHA),
              "source_score.json": (SCORE, SCORE_SHA),
              "source_graph_plan.json": (SOURCE_PLAN, SOURCE_PLAN_SHA)}
    assert sha(PREREG) == PREREG_SHA
    inputs = {}
    for name, (path, digest) in pinned.items():
        data = path.read_bytes()
        assert sha_bytes(data) == digest, name
        inputs[name] = data
    plan, manifest = build_bundle(index, destination["bundle"], inputs)
    receipt = {"status": "PREPARED_EXP236_TARGET44B6_CHUNK_LOCAL_ONLY",
               "chunk_index": index, "bundle": str(destination["bundle"]),
               "bundle_manifest_sha256": sha(destination["bundle"] / "local_bundle_manifest.json"),
               "plan_sha256": manifest["plan.json"], "assignment_sha256": ASSIGNMENT_SHA,
               "prereg_sha256": PREREG_SHA, "source_training_sha256": TRAINING_SHA,
               "source_handoff_sha256": HANDOFF_SHA, "source_score_sha256": SCORE_SHA,
               "source_graph_plan_sha256": SOURCE_PLAN_SHA,
               "movies": plan["movies"], "checkpoint_epoch": 10,
               "checkpoint_sha256": CHECKPOINT_SHA, "code": destination["code"],
               "run": destination["run"], "lease_id": destination["lease_id"],
               "remote_stage_created": False, "remote_run_created": False,
               "gpu_claimed": False, "target_labels_read": False,
               "future_target_evidence_class": "leakage-controlled reciprocal evaluation"}
    destination["receipt"].write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "chunk_index": index,
                      "movies": len(plan["movies"])}))
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int)
    prepare_index(parser.parse_args().index)
