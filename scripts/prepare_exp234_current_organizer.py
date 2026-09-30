"""Prepare local-only immutable EXP234 current-organizer scorer bundle.

This script neither contacts nsu-quadro nor opens any target label. Staging the
bundle, creating the remote isolated environment, and scoring are separate
reviewed actions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from check_current_organizer_metric_runtime import (
    METRIC_SHA256, ORGANIZER_COMMIT, TRACKSDATA_COMMIT,
)


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
BUNDLE = ROOT / "work/exp234_current_organizer_v1"
RECEIPT = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
REMOTE_CODE = REMOTE + "/code/exp234_current_organizer_v1_20260927"
REMOTE_RUN = REMOTE + "/runs/exp234_current_organizer_score175_v1_20260927"
REMOTE_PYTHON = REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python"
HISTORICAL_CODE = REMOTE + "/code/exp234_target_official_scorer_v1_20260927"
HISTORICAL_RUN = REMOTE + "/runs/exp234_target_official_score175_20260927"
EXPECTED_LOCAL = {
    "reports/exp234_target_score_handoff_20260927.json":
        "336757ebebf325712f22ffc80d432d35a274654a81d5fc60666b8f0cb7ae9bc1",
    "reports/exp234_target_official_scorer_prepare_20260927.json":
        "1b4d5cc33f9e1130dd1488ca213df3ad26b6a361e778551e27e04442fce2aec6",
    "reports/exp234_target_official_scorer_launch_20260927.json":
        "219f874cc788f861a6a3c71330a4a2b70b55fb745cc2c40dffb6184d59b96b88",
    "reports/exp234_target_release_manifest_v2_20260927.json":
        "017ce93049a4cfcbf983d9265b641a42a1266fbcfa9c7c1125f7643979f19b04",
    "reports/exp234_target_recovery_v2_20260927.json":
        "b2d2e7e7de0b81e21a963182c9e935a50bf4c913f194632ad20fce5f540f1033",
    "scripts/score_exp234_target_official.py":
        "64cc0fe20c0a7b14eb18d2170470ada1cd1e04a0e196ad3d82e67f7957409877",
}
SOURCE_FILES = {
    "score_exp234_current_organizer.py": ROOT / "scripts/score_exp234_current_organizer.py",
    "check_current_organizer_metric_runtime.py":
        ROOT / "scripts/check_current_organizer_metric_runtime.py",
    "requirements_current_organizer_py311.txt":
        ROOT / "scripts/requirements_current_organizer_py311.txt",
    "tracking_cellmot_official/__init__.py":
        ROOT / "work/x138_provenance/official_metric/tracking_cellmot_official/__init__.py",
    "tracking_cellmot_official/metrics.py":
        ROOT / "work/x138_provenance/official_metric/tracking_cellmot_official/metrics.py",
    "tracking_cellmot_official/division_metrics.py":
        ROOT / "work/x138_provenance/official_metric/tracking_cellmot_official/division_metrics.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(bundle: Path = BUNDLE, receipt: Path = RECEIPT) -> dict:
    assert not bundle.exists() and not receipt.exists(), "Existing prepare state needs reconciliation"
    for relative, digest in EXPECTED_LOCAL.items():
        assert sha(ROOT / relative) == digest, relative
    assert sha(SOURCE_FILES["tracking_cellmot_official/metrics.py"]) == METRIC_SHA256["metrics.py"]
    assert sha(SOURCE_FILES["tracking_cellmot_official/division_metrics.py"]) == (
        METRIC_SHA256["division_metrics.py"])
    bundle.mkdir(parents=True, exist_ok=False)
    manifest = {}
    for name, source in SOURCE_FILES.items():
        dest = bundle / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        manifest[name] = sha(dest)
    (bundle / "code_manifest.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode())
    config = {
        "experiment": "EXP234_CURRENT_ORGANIZER_TARGET175_V1",
        "code": REMOTE_CODE,
        "code_manifest_sha256": sha(bundle / "code_manifest.json"),
        "run": REMOTE_RUN, "output": REMOTE_RUN + "/output",
        "python": REMOTE_PYTHON,
        "organizer_commit": ORGANIZER_COMMIT, "metric_sha256": METRIC_SHA256,
        "tracksdata_commit": TRACKSDATA_COMMIT,
        "historical_code": HISTORICAL_CODE,
        "historical_manifest_sha256":
            "58f42f9b7640680739092025e106fe755da7c53df4fdccf496f9fd3f36e90e80",
        "historical_scorer_sha256": EXPECTED_LOCAL["scripts/score_exp234_target_official.py"],
        "historical_config": HISTORICAL_CODE + "/score_config.json",
        "historical_config_sha256":
            "45c9a8931e8e8ff243c0e8f09840ee0530a5855fa42b1d26eb91430ab31055a3",
        "historical_run": HISTORICAL_RUN,
        "historical_gate": HISTORICAL_RUN + "/output/no_metric_gate.json",
        "historical_gate_sha256":
            "37b07134c9ff27bf3eaf318d51185fdefb11737cb4721a1bf2fdd390dd94a664",
        "historical_result": HISTORICAL_RUN + "/output/result.json",
        "historical_result_sha256":
            "124541f647432c7b01a9e2223ef76524927ff2587ec95f8609f7b1765e43c07c",
    }
    (bundle / "score_config.json").write_bytes((json.dumps(config, indent=2) + "\n").encode())
    result = {
        "status": "PREPARED_EXP234_CURRENT_ORGANIZER_TARGET175_NO_LABELS_LOCAL_ONLY",
        "bundle": str(bundle), "remote_code_intended": REMOTE_CODE,
        "remote_run_intended": REMOTE_RUN, "interpreter_intended": REMOTE_PYTHON,
        "code_manifest_sha256": config["code_manifest_sha256"],
        "score_config_sha256": sha(bundle / "score_config.json"),
        "source_hashes": manifest, "prerequisite_local_sha256": EXPECTED_LOCAL,
        "historical_gate_sha256": config["historical_gate_sha256"],
        "historical_result_sha256": config["historical_result_sha256"],
        "organizer_commit": ORGANIZER_COMMIT, "metric_sha256": METRIC_SHA256,
        "tracksdata_commit": TRACKSDATA_COMMIT,
        "target_labels_read": False, "remote_staged": False,
        "scorer_launched": False, "kaggle_post": False,
    }
    receipt.write_bytes((json.dumps(result, indent=2) + "\n").encode())
    return result


if __name__ == "__main__":
    print(json.dumps(prepare()))
