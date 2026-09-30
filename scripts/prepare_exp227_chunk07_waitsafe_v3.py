"""Prepare an immutable v3 chunk07 bundle with a tested runner namespace."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
FAILED = ROOT / "reports/exp227_target6bba_chunk07_v2_failed_reconciliation_20260927.json"
V2_LOCAL = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v2_local_prepare_20260927.json"
V2_BUNDLE = ROOT / "work/exp227_target6bba_chunk07_waitsafe_v2_20260927"
BUNDLE = ROOT / "work/exp227_target6bba_chunk07_waitsafe_v3_20260927"
RECEIPT = ROOT / "reports/exp227_target6bba_chunk07_waitsafe_v3_local_prepare_20260927.json"
EXPECTED_FAILED_SHA = "5c777467215e6fe4f984cdcf4920070d07a2f704c819144b1cd4896af0981796"
EXPECTED_V2_LOCAL_SHA = "ff1b87073ca1bd7ecbf48999265a89e2559c2ff85ddc3fdf2f8475cf5aaba910"
EXPECTED_V2_MANIFEST_SHA = "c63813871dc002a0b9bcf0c1fc0e19d7f85db68284a5b1cd39cd51a99df42ffa"
TOKEN = "exp227_target6bba_chunk07_v3_20260927"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
IDENTITY = {"code": REMOTE + "/code/" + TOKEN,
            "run": REMOTE + "/runs/" + TOKEN,
            "lease_id": "exp227-target6bba-chunk07-v3-20260927",
            "token": TOKEN}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_actual_runner(bundle: Path, plan: dict) -> dict:
    """Execute the exact bundled function with local copies of frozen inputs."""
    runner_path = bundle / "run_exp227_target_chunk.py"
    namespace = {"__name__": "exp227_chunk07_v3_runner_contract",
                 "__file__": str(runner_path)}
    exec(compile(runner_path.read_bytes(), str(runner_path), "exec"), namespace)
    local_plan = {**plan, "assignment": str(bundle / "assignment.json"),
                  "selection": str(bundle / "selection.json")}
    selected = namespace["validate_plan"](local_plan)
    assert selected["checkpoint_sha256"] == plan["checkpoint_sha256"]
    for key, wrong in (("code", V2_LOCAL_IDENTITY["code"]),
                       ("output", V2_LOCAL_IDENTITY["run"] + "/output")):
        altered = {**local_plan, key: wrong}
        try:
            namespace["validate_plan"](altered)
        except AssertionError:
            pass
        else:
            raise AssertionError("V3 runner accepted wrong " + key + " identity")
    return {"status": "PASS_EXP227_CHUNK07_V3_ACTUAL_VALIDATE_PLAN",
            "runner_sha256": sha(bundle / "run_exp227_target_chunk.py"),
            "plan_sha256": sha(bundle / "plan.json"),
            "assignment_sha256": sha(bundle / "assignment.json"),
            "selection_sha256": sha(bundle / "selection.json"),
            "wrong_v2_code_rejected": True, "wrong_v2_output_rejected": True,
            "target_labels_read": False}


V2_LOCAL_IDENTITY = {
    "code": REMOTE + "/code/exp227_target6bba_chunk07_v2_20260927",
    "run": REMOTE + "/runs/exp227_target6bba_chunk07_v2_20260927",
}


def main() -> None:
    assert not BUNDLE.exists() and not RECEIPT.exists(), "V3 preparation already exists"
    assert sha(FAILED) == EXPECTED_FAILED_SHA and sha(V2_LOCAL) == EXPECTED_V2_LOCAL_SHA
    failed = json.loads(FAILED.read_text())
    previous = json.loads(V2_LOCAL.read_text())
    assert failed["status"] == "RECONCILED_EXP227_CHUNK07_V2_FAILED_BEFORE_GRAPHS"
    assert failed["graph_count"] == 0 and failed["queue_row"]["state"] == "RELEASED"
    assert failed["remote"]["output_exists"] is False
    assert failed["process"]["identity_alive"] is False
    assert failed["process"]["group_alive"] is False
    assert failed["process"]["gpu_pids"] == []
    assert previous["status"] == "PREPARED_EXP227_CHUNK07_WAITSAFE_V2_LOCAL_ONLY"
    assert previous["identity"]["code"] == V2_LOCAL_IDENTITY["code"]
    assert previous["identity"]["run"] == V2_LOCAL_IDENTITY["run"]
    manifest_path = V2_BUNDLE / "local_bundle_manifest.json"
    assert sha(manifest_path) == EXPECTED_V2_MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    assert set(p.name for p in V2_BUNDLE.iterdir()) == set(manifest) | {"local_bundle_manifest.json"}
    assert all(sha(V2_BUNDLE / name) == digest for name, digest in manifest.items())
    remote = ssh("nsu-a100", "python3 -", "import json,pathlib\n"
                 + f"code=pathlib.Path({IDENTITY['code']!r});run=pathlib.Path({IDENTITY['run']!r})\n"
                 + "print(json.dumps({'code_absent':not code.exists(),'run_absent':not run.exists()}))\n")
    assert remote == {"code_absent": True, "run_absent": True}
    files = {name: (V2_BUNDLE / name).read_bytes() for name in manifest}
    runner = files["run_exp227_target_chunk.py"].decode("utf-8")
    old = "token = f\"exp227_target6bba_chunk{plan['chunk_index']:02d}_v1_20260927\""
    new = "token = f\"exp227_target6bba_chunk{plan['chunk_index']:02d}_v3_20260927\""
    assert runner.count(old) == 1
    runner = runner.replace(old, new)
    ast.parse(runner, filename="run_exp227_target_chunk.py")
    files["run_exp227_target_chunk.py"] = runner.encode()
    plan = json.loads(files["plan.json"])
    assert plan["code"] == previous["identity"]["code"]
    assert plan["output"] == previous["identity"]["run"] + "/output"
    assert plan["movies"] == previous["movies"] and len(plan["movies"]) == 14
    plan.update({"code": IDENTITY["code"], "output": IDENTITY["run"] + "/output",
                 "assignment": IDENTITY["code"] + "/assignment.json",
                 "selection": IDENTITY["code"] + "/selection.json"})
    files["plan.json"] = (json.dumps(plan, indent=2) + "\n").encode()
    recipe = json.loads(files["stage_recipe.json"])
    assert recipe["target_code"] == previous["identity"]["code"]
    assert recipe["target_run"] == previous["identity"]["run"]
    recipe["target_code"] = IDENTITY["code"]
    recipe["target_run"] = IDENTITY["run"]
    recipe["completion_requires"] = [
        "exit0/no timeout", "all 14 graph CSV and receipt hashes",
        "dynamic assigned dataset IDs and graph invariants", "RELEASED lease"]
    files["stage_recipe.json"] = (json.dumps(recipe, indent=2) + "\n").encode()
    assert all(files[name] == (V2_BUNDLE / name).read_bytes() for name in manifest
               if name not in ("plan.json", "stage_recipe.json", "run_exp227_target_chunk.py"))
    BUNDLE.mkdir(parents=True, exist_ok=False)
    for name, body in files.items():
        (BUNDLE / name).write_bytes(body)
    new_manifest = {name: sha(BUNDLE / name) for name in sorted(files)}
    (BUNDLE / "local_bundle_manifest.json").write_bytes(
        (json.dumps(new_manifest, indent=2) + "\n").encode())
    assert new_manifest["assignment.json"] == previous["assignment_sha256"]
    assert new_manifest["selection.json"] == previous["selection_sha256"]
    contract = validate_actual_runner(BUNDLE, plan)
    receipt = {"status": "PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY",
               "source_stopped_sha256": failed["source_stopped_sha256"],
               "failed_v2_reconciliation_sha256": sha(FAILED),
               "source_v2_local_prepare_sha256": sha(V2_LOCAL),
               "source_v2_bundle_manifest_sha256": sha(manifest_path),
               "bundle": str(BUNDLE),
               "bundle_manifest_sha256": sha(BUNDLE / "local_bundle_manifest.json"),
               "plan_sha256": new_manifest["plan.json"],
               "runner_sha256": new_manifest["run_exp227_target_chunk.py"],
               "assignment_sha256": new_manifest["assignment.json"],
               "selection_sha256": new_manifest["selection.json"],
               "checkpoint_sha256": previous["checkpoint_sha256"],
               "movies": previous["movies"], "identity": IDENTITY,
               "actual_runner_contract": contract,
               "remote_v3_absence_checked": remote,
               "remote_staged": False, "remote_run_created": False,
               "gpu_claimed": False, "target_labels_read": False,
               "target_score_computed": False, "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"],
                      "runner_sha256": receipt["runner_sha256"],
                      "plan_sha256": receipt["plan_sha256"],
                      "bundle_manifest_sha256": receipt["bundle_manifest_sha256"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
