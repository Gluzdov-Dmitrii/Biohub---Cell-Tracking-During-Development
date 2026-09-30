"""Build a local-only immutable EXP227 target6bba chunk00 transfer bundle.

No SSH, queue mutation, remote stage, GPU launch, or target-label access.
"""
import hashlib
import json
from pathlib import Path

from select_exp227_source_checkpoint import PREREG, RECEIPT as SELECTION, ROOT, SOURCE8, choose
from run_exp227_target_chunk import ASSIGNMENT_SHA


ASSIGNMENT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
BUNDLE = ROOT / "work/exp227_target6bba_chunk00_local_20260927"
PREPARE_RECEIPT = ROOT / "reports/exp227_target6bba_chunk00_local_prepare_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp227_target6bba_chunk00_v1_20260927"
RUN = REMOTE + "/runs/exp227_target6bba_chunk00_v1_20260927"


def paths(index):
    assert isinstance(index, int) and 0 <= index < 8
    token = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
    return {"bundle": ROOT / f"work/exp227_target6bba_chunk{index:02d}_local_20260927",
            "receipt": ROOT / f"reports/exp227_target6bba_chunk{index:02d}_local_prepare_20260927.json",
            "code": REMOTE + "/code/" + token, "run": REMOTE + "/runs/" + token,
            "lease_id": f"exp227-target6bba-chunk{index:02d}-v1-20260927",
            "token": token}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def validate_selection(selection, prereg_sha):
    assert selection["status"] == "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT"
    assert selection["target_labels_read"] is False
    assert selection["prereg_sha256"] == prereg_sha
    assert selection["source8"] == list(SOURCE8)
    assert selection["selected_epoch"] == choose(selection["scores"]["10"], selection["scores"]["20"])
    assert [item["epoch"] for item in selection["epochs"]] == [10, 20]
    assert selection["remote_audit"]["status"] == "PASS_EXP227_SOURCE10_20_SELECTION_AUDIT"
    assert [item["epoch"] for item in selection["remote_audit"]["epochs"]] == [10, 20]
    chosen = selection["epochs"][0 if selection["selected_epoch"] == 10 else 1]
    assert chosen["checkpoint"] == selection["checkpoint"]
    assert chosen["checkpoint_sha256"] == selection["checkpoint_sha256"]
    assert chosen["source_score"] == selection["scores"][str(selection["selected_epoch"])]
    assert chosen["graph_code"].startswith(REMOTE + "/code/exp227_source_graph")
    assert chosen["graph_manifest_sha256"] and len(chosen["graph_manifest_sha256"]) == 64
    return chosen


def validate_assignment(assignment, index=0):
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["thresholds_selected"] is False
    direction = assignment["directions"]["44b6"]
    assert direction["target_embryo"] == "6bba" and direction["movie_count"] == 116
    chunks = direction["chunks"]
    assert len(chunks) == 8 and len(chunks[0]) == 15
    assert isinstance(index, int) and 0 <= index < 8
    names = [name for chunk in chunks for name in chunk]
    assert len(names) == len(set(names)) == 116
    assert all(name.startswith("6bba_") for name in names)
    assert len(chunks[index]) in (14, 15)
    return chunks[index]


def fair_idle_a100(queue_state, physical_idle_uuids, lease_id):
    """Read-only precheck; a future launcher must repeat immediately before claim."""
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


def build_bundle(selection, assignment, bundle, selection_bytes, assignment_bytes, prereg_sha,
                 chunk_index=0):
    chosen = validate_selection(selection, prereg_sha)
    movies = validate_assignment(assignment, chunk_index)
    destination = paths(chunk_index)
    code = destination["code"]
    run = destination["run"]
    bundle = Path(bundle)
    bundle.mkdir(parents=True, exist_ok=False)
    files = {
        "assignment.json": assignment_bytes,
        "selection.json": selection_bytes,
        "run_exp227_target_chunk.py": (ROOT / "scripts/run_exp227_target_chunk.py").read_bytes(),
        "run_exp223_inference.py": (ROOT / "scripts/run_exp223_inference.py").read_bytes(),
        "verify_exp227_target_chunk0.py": (ROOT / "scripts/verify_exp227_target_chunk0.py").read_bytes(),
    }
    plan = {"experiment": "EXP227_TARGET6BBA_CHUNK", "source_embryo": "44b6",
            "target_embryo": "6bba", "chunk_index": chunk_index, "chunk_count": 8,
            "assignment": code + "/assignment.json", "assignment_sha256": ASSIGNMENT_SHA,
            "selection": code + "/selection.json", "selection_sha256": sha_bytes(selection_bytes),
            "prereg_sha256": prereg_sha,
            "checkpoint_epoch": selection["selected_epoch"],
            "checkpoint": selection["checkpoint"], "checkpoint_sha256": selection["checkpoint_sha256"],
            "data_root": REMOTE + "/data/exp213_source_view_20260912",
            "code": code, "output": run + "/output", "movies": movies}
    files["plan.json"] = (json.dumps(plan, indent=2) + "\n").encode()
    recipe = {"status": "LOCAL_ONLY_STAGE_RECIPE_NOT_EXECUTED",
              "copy_parent_code": chosen["graph_code"],
              "parent_manifest_sha256": chosen["graph_manifest_sha256"],
              "target_code": code, "target_run": run,
              "wrapper_old_assertion": "assert config['script'] == 'run_exp227_source_graph" +
                                       str(selection["selected_epoch"]) + ".py'",
              "wrapper_new_assertion": "assert config['script'] == 'run_exp227_target_chunk.py'",
              "overlay_files": sorted(files),
              "stage_requires": ["remote parent code manifest and every file rehash",
                                 "target code and run path absent",
                                 "replace wrapper assertion exactly once",
                                 "AST parse all Python; create final code_manifest.json",
                                 "verify copied selection, assignment, plan and runner bytes"],
              "launch_requires": ["no earlier foreign WAITING queue claim",
                                  "one queue-free physically idle A100; recheck before claim",
                                  "exact stage manifest and plan hashes",
                                  "no existing lease, run, reservation or partial launch"],
              "completion_requires": ["exit0/no timeout", "all 15 graph CSV and receipt hashes",
                                      "dynamic assigned dataset IDs and graph invariants", "RELEASED lease"]}
    files["stage_recipe.json"] = (json.dumps(recipe, indent=2) + "\n").encode()
    for name, body in files.items():
        (bundle / name).write_bytes(body)
    manifest = {name: sha(bundle / name) for name in sorted(files)}
    (bundle / "local_bundle_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"plan": plan, "recipe": recipe, "manifest": manifest,
            "bundle_manifest_sha256": sha(bundle / "local_bundle_manifest.json")}


def prepare_index(index):
    destination = paths(index)
    bundle = destination["bundle"]
    receipt_path = destination["receipt"]
    assert not bundle.exists() and not receipt_path.exists()
    assert sha(ASSIGNMENT) == ASSIGNMENT_SHA
    selection_bytes = SELECTION.read_bytes()
    selection = json.loads(selection_bytes)
    assignment_bytes = ASSIGNMENT.read_bytes()
    assignment = json.loads(assignment_bytes)
    prereg_sha = sha(PREREG)
    result = build_bundle(selection, assignment, bundle, selection_bytes, assignment_bytes,
                          prereg_sha, chunk_index=index)
    receipt = {"status": "PREPARED_EXP227_TARGET6BBA_CHUNK_LOCAL_ONLY",
               "chunk_index": index,
               "bundle": str(bundle), "bundle_manifest_sha256": result["bundle_manifest_sha256"],
               "plan_sha256": result["manifest"]["plan.json"],
               "selection_sha256": sha_bytes(selection_bytes), "assignment_sha256": ASSIGNMENT_SHA,
               "prereg_sha256": prereg_sha, "movies": result["plan"]["movies"],
               "selected_epoch": result["plan"]["checkpoint_epoch"],
               "checkpoint_sha256": result["plan"]["checkpoint_sha256"],
               "code": destination["code"], "run": destination["run"],
               "lease_id": destination["lease_id"],
               "remote_stage_created": False, "remote_run_created": False,
               "gpu_claimed": False, "target_labels_read": False,
               "future_target_evidence_class": "leakage-controlled reciprocal evaluation; broader research previously inspected target labels"}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "movies": len(receipt["movies"]),
                      "selected_epoch": receipt["selected_epoch"]}))
    return receipt


def main():
    prepare_index(0)


if __name__ == "__main__":
    main()
