"""Prepare a new local-only EXP227 chunk07 identity after cancelled v1 lease."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/exp227_target6bba_chunk07_waiting_successor_20260927.json"
SOURCE_PREPARE = ROOT / "reports/exp227_target6bba_chunk07_local_prepare_20260927.json"
SOURCE_STAGE = ROOT / "reports/exp227_target6bba_chunk07_stage_20260927.json"
BUNDLE = ROOT / "work/exp227_target6bba_chunk07_waitsafe_v2_20260927"
RECEIPT = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_local_prepare_20260927.json"
EXPECTED_AUDIT_SHA = "ed9755fdfeb1b19846845c9858ab05e825902011350bc43abe19f1f3afba0d3f"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not BUNDLE.exists() and not RECEIPT.exists(), "v2 local preparation already exists"
    assert sha(AUDIT) == EXPECTED_AUDIT_SHA
    audit = json.loads(AUDIT.read_text())
    assert audit["status"] == "RECONCILED_EXP227_CHUNK07_WAITING_NO_LAUNCH"
    assert audit["verified_prior_chunks"] == 7 and audit["verified_prior_graphs"] == 102
    assert audit["remote"]["queue_row"]["state"] == "CANCELLED"
    assert audit["remote"]["run_absent"] is True
    assert audit["target_labels_read"] is False and audit["kaggle_post"] is False
    assert sha(SOURCE_PREPARE) == audit["chunk07_prepare_sha256"]
    assert sha(SOURCE_STAGE) == audit["chunk07_stage_sha256"]
    original = json.loads(SOURCE_PREPARE.read_text())
    old_bundle = Path(original["bundle"])
    old_manifest_path = old_bundle / "local_bundle_manifest.json"
    assert sha(old_manifest_path) == original["bundle_manifest_sha256"]
    old_manifest = json.loads(old_manifest_path.read_text())
    assert set(p.name for p in old_bundle.iterdir()) == set(old_manifest) | {"local_bundle_manifest.json"}
    assert all(sha(old_bundle / name) == digest for name, digest in old_manifest.items())
    assert original["chunk_index"] == 7 and len(original["movies"]) == 14
    identity = audit["next_identity"]
    assert identity["code"].endswith("/code/exp227_target6bba_chunk07_v2_20260927")
    assert identity["run"].endswith("/runs/exp227_target6bba_chunk07_v2_20260927")
    assert identity["lease_id"] == "exp227-target6bba-chunk07-v2-20260927"
    assert identity["token"] == "exp227_target6bba_chunk07_v2_20260927"
    remote = ssh("nsu-a100", "python3 -", "import json,pathlib\n"
                 + f"code=pathlib.Path({identity['code']!r});run=pathlib.Path({identity['run']!r})\n"
                 + "print(json.dumps({'code_absent':not code.exists(),'run_absent':not run.exists()}))\n")
    assert remote == {"code_absent": True, "run_absent": True}
    files = {name: (old_bundle / name).read_bytes() for name in old_manifest}
    plan = json.loads(files["plan.json"])
    assert plan["code"] == original["code"] and plan["output"] == original["run"] + "/output"
    assert plan["chunk_index"] == 7 and plan["movies"] == original["movies"]
    assert plan["checkpoint_sha256"] == original["checkpoint_sha256"]
    plan["code"] = identity["code"]
    plan["output"] = identity["run"] + "/output"
    plan["assignment"] = identity["code"] + "/assignment.json"
    plan["selection"] = identity["code"] + "/selection.json"
    files["plan.json"] = (json.dumps(plan, indent=2) + "\n").encode()
    recipe = json.loads(files["stage_recipe.json"])
    assert recipe["target_code"] == original["code"] and recipe["target_run"] == original["run"]
    recipe["target_code"] = identity["code"]
    recipe["target_run"] = identity["run"]
    recipe["launch_requires"] = [
        "fresh fair queue and physical GPU check before every attempt",
        "new lease ID for every cancelled WAITING_RESOURCE attempt",
        "cancelled attempt and absent run reverified before next attempt",
        "queue-free physically idle A100 immediately before claim",
        "exact stage manifest, plan and frozen checkpoint hashes",
        "no existing run or successful launch receipt",
    ]
    files["stage_recipe.json"] = (json.dumps(recipe, indent=2) + "\n").encode()
    assert all(files[name] == (old_bundle / name).read_bytes()
               for name in old_manifest if name not in ("plan.json", "stage_recipe.json"))
    BUNDLE.mkdir(parents=True, exist_ok=False)
    for name, body in files.items():
        (BUNDLE / name).write_bytes(body)
    manifest = {name: sha(BUNDLE / name) for name in sorted(files)}
    (BUNDLE / "local_bundle_manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode())
    assert manifest["assignment.json"] == original["assignment_sha256"]
    assert manifest["selection.json"] == original["selection_sha256"]
    for name in old_manifest:
        if name not in ("plan.json", "stage_recipe.json"):
            assert manifest[name] == old_manifest[name]
    receipt = {"status": "PREPARED_EXP227_CHUNK07_WAITSAFE_V2_LOCAL_ONLY",
               "source_stopped_sha256": audit["source_stopped_sha256"],
               "successor_audit_sha256": sha(AUDIT),
               "source_prepare_sha256": sha(SOURCE_PREPARE),
               "source_stage_sha256": sha(SOURCE_STAGE),
               "source_bundle_manifest_sha256": sha(old_manifest_path),
               "bundle": str(BUNDLE), "bundle_manifest_sha256": sha(BUNDLE / "local_bundle_manifest.json"),
               "plan_sha256": manifest["plan.json"],
               "assignment_sha256": manifest["assignment.json"],
               "selection_sha256": manifest["selection.json"],
               "checkpoint_sha256": original["checkpoint_sha256"],
               "movies": original["movies"], "identity": identity,
               "remote_v2_absence_checked": remote,
               "remote_staged": False, "remote_run_created": False,
               "gpu_claimed": False, "target_labels_read": False,
               "target_score_computed": False, "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    assert sha(SOURCE_PREPARE) == audit["chunk07_prepare_sha256"]
    assert sha(SOURCE_STAGE) == audit["chunk07_stage_sha256"]
    print(json.dumps({"status": receipt["status"], "plan_sha256": receipt["plan_sha256"],
                      "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
