"""Create/reseal the local-only EXP238 CPU source audit bundle.

This does not call SSH, open GEFF, inspect target data, or start the audit.
After both cache jobs are independently verified, copy the two verification
receipts into bundle/verification, fill only the null hash fields in config,
then rerun with --reseal. The SHA of that final manifest is the launch pin.
"""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp238_source_peak_cpu_audit_20260927"
CONFIG = BUNDLE / "config.json"
MANIFEST = BUNDLE / "manifest.json"
SOURCE = ROOT / "work/source_inner_error_decomposition_v2_20260927/config.json"
PLANS = ROOT / "work/exp238_source_peak_cache_local_20260927"
STAGES = ROOT / "reports"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PREREG_SHA = "61f0acbda553da984a6e6e9b1d946ba713f3690a407993036b857b88a2e69041"
BASELINE_VERIFIED_SHA = "eb8de29eea2aec8ee926f8b90fb46aed05b594029e440018dbbe579f27b675d6"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_config() -> dict:
    prior = json.loads(SOURCE.read_text())
    assert [(row["experiment"], len(row["ids"])) for row in prior["cohorts"]] == [
        ("EXP227", 8), ("EXP236", 11)]
    cohorts = []
    for previous, short in zip(prior["cohorts"], ("source44", "source6")):
        plan_path = PLANS / short / "exp238_plan.json"
        plan = json.loads(plan_path.read_text())
        stage = json.loads((STAGES / f"exp238_{short}_peak_cache_stage_20260927.json").read_text())
        assert stage["status"] == "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS"
        assert stage["stage"]["plan_sha256"] == sha(plan_path)
        assert plan["prereg_sha256"] == PREREG_SHA
        assert plan["source_embryo"] == previous["source_embryo"]
        assert plan["checkpoint_sha256"] == previous["checkpoint_sha256"]
        assert [row["dataset"] for row in plan["movies"]] == previous["ids"]
        assert [{"dataset": row["dataset"], "csv_sha256": row["graph_csv_sha256"],
                 "receipt_sha256": row["graph_receipt_sha256"]} for row in plan["movies"]] == \
            previous["graph_hashes"]
        cohorts.append({
            "experiment": previous["experiment"], "source_embryo": previous["source_embryo"],
            "ids": previous["ids"], "cache_cohort": short,
            "cache_code": plan["code"], "cache_run": plan["run"],
            "checkpoint_sha256": previous["checkpoint_sha256"],
            "manifest_sha256": stage["stage"]["manifest_sha256"],
            "plan_sha256": sha(plan_path),
            "status_sha256": None, "exit_sha256": None,
            "complete_sha256": None, "control_sha256": None,
            "independent_receipt": REMOTE + "/code/exp238_source_peak_cpu_audit_v1_20260927/verification/" + short + ".json",
            "independent_receipt_sha256": None,
            "guarded_recheck_receipt": (REMOTE + "/code/exp238_source_peak_cpu_audit_v1_20260927/verification/source44_guarded_recheck.json")
            if short == "source44" else None,
            "guarded_recheck_receipt_sha256": None,
            "optimization_correction_receipt": (REMOTE + "/code/exp238_source_peak_cpu_audit_v1_20260927/verification/source44_optimization_correction.json")
            if short == "source44" else None,
            "optimization_correction_receipt_sha256": None,
        })
    return {
        "status": "PREREGISTERED_EXP238_SOURCE_PEAK_CPU_LOCAL_ONLY",
        "source_only": True, "prereg_sha256": PREREG_SHA,
        "baseline_verified_receipt_sha256": BASELINE_VERIFIED_SHA,
        "output": REMOTE + "/runs/exp238_source_peak_cpu_audit_v1_20260927/output",
        "floor": 0.075, "radius_um": 7.0, "minimum_recoverability": 0.4,
        "definition": "off-graph if no sealed graph node within 7 um in same frame; peak qualifies within 7 um of missed GT node",
        "cohorts": cohorts,
        "reciprocal_target_score": None, "kaggle_post": False,
    }


def reseal() -> dict:
    config = json.loads(CONFIG.read_text())
    assert config["status"] == "PREREGISTERED_EXP238_SOURCE_PEAK_CPU_LOCAL_ONLY"
    assert config["prereg_sha256"] == PREREG_SHA
    assert config["floor"] == 0.075 and config["radius_um"] == 7.0
    assert config["minimum_recoverability"] == 0.4
    assert [row["cache_cohort"] for row in config["cohorts"]] == ["source44", "source6"]
    files = {}
    for path in sorted(BUNDLE.rglob("*")):
        if (path.is_file() and path != MANIFEST and
                not any(part.startswith("pytest_tmp") or part in ("__pycache__", ".pytest_cache")
                        for part in path.parts)):
            files[path.relative_to(BUNDLE).as_posix()] = sha(path)
    assert "audit_exp238_source_peaks.py" in files and "config.json" in files
    assert "baseline/manifest.json" in files
    assert files["baseline/manifest.json"] == "3216b95fe675de7b19d0cdb8c592dafa4c84174e26cc9b2b15b5ae3a10a3deec"
    dynamic_ready = all(
        row[key] is not None for row in config["cohorts"]
        for key in ("status_sha256", "exit_sha256", "complete_sha256",
                    "control_sha256", "independent_receipt_sha256")) and \
        config["cohorts"][0]["guarded_recheck_receipt_sha256"] is not None and \
        config["cohorts"][0]["optimization_correction_receipt_sha256"] is not None and \
        all((BUNDLE / "verification" / name).exists() for name in
            ("source44.json", "source6.json", "source44_guarded_recheck.json",
             "source44_optimization_correction.json"))
    manifest = {"status": ("SEALED_EXP238_SOURCE_PEAK_CPU_AUDIT_LOCAL_ONLY" if dynamic_ready
                           else "PROVISIONAL_EXP238_SOURCE_PEAK_CPU_AUDIT_LOCAL_ONLY"),
                "files": files}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"status": "EXP238_CPU_AUDIT_BUNDLE_LOCAL_ONLY",
            "config_sha256": sha(CONFIG), "manifest_sha256": sha(MANIFEST),
            "file_count": len(files), "dynamic_pins_ready": dynamic_ready,
            "remote_mutation": False, "labels_read": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reseal", action="store_true")
    args = parser.parse_args()
    if args.reseal:
        assert CONFIG.exists()
    else:
        with CONFIG.open("x") as stream:
            stream.write(json.dumps(create_config(), indent=2) + "\n")
    print(json.dumps(reseal(), sort_keys=True))


if __name__ == "__main__":
    main()
