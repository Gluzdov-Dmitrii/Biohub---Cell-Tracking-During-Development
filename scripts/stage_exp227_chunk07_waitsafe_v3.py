"""Guarded one-shot v3 stage for EXP227 chunk07; never launches a worker."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from prepare_exp227_chunk07_waitsafe_v3 import validate_actual_runner
from prepare_exp227_target_chunk0_local import validate_assignment, validate_selection
from stage_exp227_target_chunk import remote_preflight_source, remote_stage_source


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_local_prepare_20260927.json"
AUDIT = ROOT / "reports/exp227_target6bba_chunk07_v2_failed_reconciliation_20260927.json"
SOURCE = ROOT / "reports/exp227_target6bba_eight_chunk_recovered_20260927.json"
STAGE = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_stage_20260927.json"
CONFIG = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_config_20260927.json"
EXPECTED_LOCAL_SHA = "9bae3cfe842e9772aadf07bce8572fc84802ed54af0a84838fad450dfa24e0d8"
EXPECTED_AUDIT_SHA = "5c777467215e6fe4f984cdcf4920070d07a2f704c819144b1cd4896af0981796"
EXPECTED_STOPPED_SHA = "8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_gate():
    assert not STAGE.exists() and not CONFIG.exists(), "Existing v3 stage requires reconciliation"
    assert sha(LOCAL) == EXPECTED_LOCAL_SHA and sha(AUDIT) == EXPECTED_AUDIT_SHA
    prepared = json.loads(LOCAL.read_text())
    audit = json.loads(AUDIT.read_text())
    assert prepared["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY"
    assert audit["status"] == "RECONCILED_EXP227_CHUNK07_V2_FAILED_BEFORE_GRAPHS"
    assert prepared["failed_v2_reconciliation_sha256"] == sha(AUDIT)
    assert prepared["source_stopped_sha256"] == audit["source_stopped_sha256"] == EXPECTED_STOPPED_SHA
    assert sha(SOURCE) == EXPECTED_STOPPED_SHA
    assert audit["queue_row"]["state"] == "RELEASED" and audit["graph_count"] == 0
    assert audit["remote"]["output_exists"] is False and audit["remote"]["graph_files"] == []
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
    assert manifest["run_exp227_target_chunk.py"] == prepared["runner_sha256"]
    assert prepared["actual_runner_contract"]["status"] == "PASS_EXP227_CHUNK07_V3_ACTUAL_VALIDATE_PLAN"
    assert prepared["actual_runner_contract"]["runner_sha256"] == prepared["runner_sha256"]
    assert prepared["actual_runner_contract"]["plan_sha256"] == prepared["plan_sha256"]
    assert prepared["actual_runner_contract"]["wrong_v2_code_rejected"] is True
    assert prepared["actual_runner_contract"]["wrong_v2_output_rejected"] is True
    assert manifest["selection.json"] == prepared["selection_sha256"]
    assert manifest["assignment.json"] == prepared["assignment_sha256"]
    selection = json.loads((bundle / "selection.json").read_text())
    chosen = validate_selection(selection, json.loads((bundle / "plan.json").read_text())["prereg_sha256"])
    assignment = json.loads((bundle / "assignment.json").read_text())
    assert validate_assignment(assignment, 7) == prepared["movies"]
    plan = json.loads((bundle / "plan.json").read_text())
    assert validate_actual_runner(bundle, plan) == prepared["actual_runner_contract"]
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
    assert prepared["remote_v3_absence_checked"] == {"code_absent": True, "run_absent": True}
    assert prepared["remote_staged"] is False and prepared["remote_run_created"] is False
    assert prepared["gpu_claimed"] is False and prepared["target_labels_read"] is False
    return prepared, chosen, plan, recipe, manifest


def stage_v3() -> dict:
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
    receipt = {"status": "STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS",
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
               "failed_v2_reconciliation_sha256": sha(AUDIT),
               "runner_contract": prepared["actual_runner_contract"],
               "remote_run_created": False, "gpu_claimed": False,
               "target_labels_read": False, "kaggle_post": False}
    CONFIG.write_bytes((json.dumps(config, indent=2) + "\n").encode())
    STAGE.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "manifest_sha256": receipt["manifest_sha256"],
                      "stage_receipt_sha256": sha(STAGE)}))
    return receipt


if __name__ == "__main__":
    stage_v3()
