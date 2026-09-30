"""Guarded one-shot v2 stage for EXP227 chunk07; never launches a worker."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from prepare_exp227_target_chunk0_local import validate_assignment, validate_selection
from stage_exp227_target_chunk import remote_preflight_source, remote_stage_source


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_local_prepare_20260927.json"
AUDIT = ROOT / "reports/exp227_target6bba_chunk07_waiting_successor_20260927.json"
STAGE = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_stage_20260927.json"
CONFIG = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_config_20260927.json"
EXPECTED_LOCAL_SHA = "ff1b87073ca1bd7ecbf48999265a89e2559c2ff85ddc3fdf2f8475cf5aaba910"
EXPECTED_AUDIT_SHA = "ed9755fdfeb1b19846845c9858ab05e825902011350bc43abe19f1f3afba0d3f"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_gate():
    assert not STAGE.exists() and not CONFIG.exists(), "Existing v2 stage requires reconciliation"
    assert sha(LOCAL) == EXPECTED_LOCAL_SHA and sha(AUDIT) == EXPECTED_AUDIT_SHA
    prepared = json.loads(LOCAL.read_text())
    audit = json.loads(AUDIT.read_text())
    assert prepared["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V2_LOCAL_ONLY"
    assert audit["status"] == "RECONCILED_EXP227_CHUNK07_WAITING_NO_LAUNCH"
    assert prepared["successor_audit_sha256"] == sha(AUDIT)
    assert prepared["source_stopped_sha256"] == audit["source_stopped_sha256"]
    assert sha(ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json") == audit["source_stopped_sha256"]
    assert audit["remote"]["queue_row"]["state"] == "CANCELLED"
    assert sha(ROOT / "reports/exp227_target6bba_chunk07_stage_20260927.json") == prepared["source_stage_sha256"]
    bundle = Path(prepared["bundle"])
    assert sha(bundle / "local_bundle_manifest.json") == prepared["bundle_manifest_sha256"]
    manifest = json.loads((bundle / "local_bundle_manifest.json").read_text())
    assert set(p.name for p in bundle.iterdir()) == set(manifest) | {"local_bundle_manifest.json"}
    for name, digest in manifest.items():
        file = (bundle / name).resolve()
        assert file.is_relative_to(bundle.resolve()) and sha(file) == digest
        if name.endswith(".py"):
            ast.parse(file.read_text(), filename=name)
    assert manifest["plan.json"] == prepared["plan_sha256"]
    assert manifest["selection.json"] == prepared["selection_sha256"]
    assert manifest["assignment.json"] == prepared["assignment_sha256"]
    selection = json.loads((bundle / "selection.json").read_text())
    chosen = validate_selection(selection, json.loads((bundle / "plan.json").read_text())["prereg_sha256"])
    assignment = json.loads((bundle / "assignment.json").read_text())
    assert validate_assignment(assignment, 7) == prepared["movies"]
    plan = json.loads((bundle / "plan.json").read_text())
    identity = prepared["identity"]
    assert plan["code"] == identity["code"] and plan["output"] == identity["run"] + "/output"
    assert plan["assignment"] == identity["code"] + "/assignment.json"
    assert plan["selection"] == identity["code"] + "/selection.json"
    assert plan["checkpoint_sha256"] == prepared["checkpoint_sha256"]
    recipe = json.loads((bundle / "stage_recipe.json").read_text())
    assert recipe["target_code"] == identity["code"] and recipe["target_run"] == identity["run"]
    assert recipe["parent_manifest_sha256"] == chosen["graph_manifest_sha256"]
    assert recipe["copy_parent_code"] == chosen["graph_code"]
    assert recipe["overlay_files"] == sorted(set(manifest) - {"stage_recipe.json"})
    assert prepared["remote_staged"] is False and prepared["remote_run_created"] is False
    assert prepared["gpu_claimed"] is False and prepared["target_labels_read"] is False
    return prepared, chosen, plan, recipe, manifest


def stage_v2() -> dict:
    prepared, chosen, plan, recipe, manifest = local_gate()
    identity = prepared["identity"]
    parent = ssh("nsu-a100", "python3 -", remote_preflight_source(identity, chosen))
    assert parent["status"] == "PASS_EXP227_TARGET_STAGE_PARENT_PREFLIGHT"
    assert parent["parent_manifest_sha256"] == chosen["graph_manifest_sha256"]
    assert parent["checkpoint_sha256"] == prepared["checkpoint_sha256"]
    bundle = Path(prepared["bundle"])
    files = {name: (bundle / name).read_bytes() for name in recipe["overlay_files"]}
    transfer = {name: manifest[name] for name in recipe["overlay_files"]}
    staged = ssh("nsu-a100", "python3 -",
                 remote_stage_source(identity, recipe, transfer, files))
    assert staged["status"] == "STAGED_EXP227_TARGET6BBA_CHUNK_NO_LABELS"
    assert staged["code"] == identity["code"] and staged["run"] == identity["run"]
    assert staged["plan_sha256"] == prepared["plan_sha256"]
    assert staged["runner_sha256"] == manifest["run_exp227_target_chunk.py"]
    assert staged["selection_sha256"] == prepared["selection_sha256"]
    assert staged["assignment_sha256"] == prepared["assignment_sha256"]
    config = {"experiment": "EXP227_TARGET6BBA_CHUNK", "chunk_index": 7,
              "lease_id": identity["lease_id"], "token": identity["token"],
              "pool": "a100", "code": identity["code"], "run": identity["run"],
              "max_seconds": 10800, "cpu_affinity": "0-7",
              "resources": {"cpu": 8, "ram_gib": 32, "disk_growth_gib": 4},
              "script": "run_exp227_target_chunk.py",
              "arguments": [identity["code"] + "/plan.json", "--plan-sha256",
                            staged["plan_sha256"]]}
    receipt = {"status": "STAGED_EXP227_CHUNK07_WAITSAFE_V2_NO_LABELS",
               "chunk_index": 7, "code": identity["code"], "run": identity["run"],
               "lease_id": identity["lease_id"], "token": identity["token"],
               "manifest_sha256": staged["manifest_sha256"],
               "plan_sha256": staged["plan_sha256"],
               "selection_sha256": staged["selection_sha256"],
               "assignment_sha256": staged["assignment_sha256"],
               "checkpoint_sha256": prepared["checkpoint_sha256"],
               "movies": prepared["movies"], "parent": parent, "staged": staged,
               "local_prepare_sha256": sha(LOCAL),
               "local_bundle_manifest_sha256": prepared["bundle_manifest_sha256"],
               "source_stopped_sha256": prepared["source_stopped_sha256"],
               "remote_run_created": False, "gpu_claimed": False,
               "target_labels_read": False, "kaggle_post": False}
    CONFIG.write_bytes((json.dumps(config, indent=2) + "\n").encode())
    STAGE.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "manifest_sha256": receipt["manifest_sha256"],
                      "stage_receipt_sha256": sha(STAGE)}))
    return receipt


if __name__ == "__main__":
    stage_v2()
