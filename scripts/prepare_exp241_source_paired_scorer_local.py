"""Prepare EXP241 scorer locally; seal only after independent graph verification.

No SSH, GEFF read, metric evaluation, GPU use, or submission is done here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


if not __debug__:
    raise RuntimeError("EXP241 local preparation requires Python assertions")

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "work/exp241_source_paired_scorer_v1_20260927"
V2 = ROOT / "work/source_inner_error_decomposition_v2_20260927"
PREREG = ROOT / "reports/EXP241_FIXED_TWO_PEAK_SOURCE_CANDIDATE_PREREG_20260927.md"
SOURCE_VERIFIED = ROOT / "reports/source_inner_error_decomposition_v2_verified_20260927.json"
GRAPH_VERIFIED = ROOT / "reports/exp241_fixed_two_peak_source_candidate_verified_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
GRAPH_RUN = REMOTE + "/runs/exp241_fixed_two_peak_source_candidate_v1_20260927"
OUTPUT = REMOTE + "/runs/exp241_source_paired_scorer_v1_20260927/output"
PREREG_SHA = "6e602f1374f74282493541cfaa214de6bdff82396e22eec8995674e48bd4fe0f"
SOURCE_MANIFEST_SHA = "3216b95fe675de7b19d0cdb8c592dafa4c84174e26cc9b2b15b5ae3a10a3deec"
SOURCE_VERIFIED_SHA = "eb8de29eea2aec8ee926f8b90fb46aed05b594029e440018dbbe579f27b675d6"
SOURCE_CONFIG_SHA = "6e1d2dce0a40a0bcf9c8ed23fbc8ce1396d6557377d15dd905ef07e496a2e061"
SOURCE_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
GRAPH_VERIFIED_STATUS = "PASS_EXP241_INDEPENDENT_LABEL_FREE_GRAPH_VERIFICATION"
EXPECTED_IDS = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
    "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1", "6bba_786893ac",
    "6bba_825bd1c6", "6bba_a5e926bb", "6bba_b329af44", "6bba_b693381b",
    "6bba_bb9f20c3", "6bba_f20478e9", "6bba_f4ae811c",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path: Path, digest: str) -> None:
    if not path.is_file() or sha(path) != digest:
        raise ValueError(f"SHA256 mismatch: {path}")


def copy_pinned(source: Path, dest: Path, digest: str) -> None:
    verify(source, digest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        verify(dest, digest)
    else:
        shutil.copyfile(source, dest)
        verify(dest, digest)


def prepare_dependencies() -> dict:
    verify(PREREG, PREREG_SHA)
    verify(SOURCE_VERIFIED, SOURCE_VERIFIED_SHA)
    verify(V2 / "manifest.json", SOURCE_MANIFEST_SHA)
    source_manifest = json.loads((V2 / "manifest.json").read_text())
    assert source_manifest["status"] == "SEALED_SOURCE_INNER_ERROR_DECOMPOSITION_LOCAL_ONLY"
    for relative, digest in source_manifest["files"].items():
        verify(V2 / relative, digest)
    copy_pinned(V2 / "audit_source_inner.py", PACKAGE / "audit_source_inner.py",
                source_manifest["files"]["audit_source_inner.py"])
    copy_pinned(V2 / "check_current_organizer_metric_runtime.py",
                PACKAGE / "check_current_organizer_metric_runtime.py",
                source_manifest["files"]["check_current_organizer_metric_runtime.py"])
    copy_pinned(V2 / "source_inner19_image_scale_audit_v2_20260927.json",
                PACKAGE / "source_inner19_image_scale_audit_v2_20260927.json",
                source_manifest["files"]["source_inner19_image_scale_audit_v2_20260927.json"])
    copy_pinned(V2 / "config.json", PACKAGE / "source_inner_config.json", SOURCE_CONFIG_SHA)
    copy_pinned(SOURCE_VERIFIED, PACKAGE / "source_inner_verified.json", SOURCE_VERIFIED_SHA)
    copy_pinned(PREREG, PACKAGE / "prereg.md", PREREG_SHA)
    for relative, digest in source_manifest["files"].items():
        if relative.startswith("tracking_cellmot_official/"):
            copy_pinned(V2 / relative, PACKAGE / relative, digest)
    runner = PACKAGE / "score_exp241_source_paired.py"
    assert runner.is_file()
    compile(runner.read_bytes(), str(runner), "exec")
    return {"runner_sha256": sha(runner), "copied_source_manifest_sha256": SOURCE_MANIFEST_SHA,
            "source_inner_result_sha256_pin_only": SOURCE_RESULT_SHA}


def seal_after_graph() -> dict:
    assert not (PACKAGE / "config.json").exists()
    assert not (PACKAGE / "manifest.json").exists()
    assert not (PACKAGE / "graph_verified.json").exists()
    receipt = json.loads(GRAPH_VERIFIED.read_text())
    receipt_sha = sha(GRAPH_VERIFIED)
    assert receipt["status"] == GRAPH_VERIFIED_STATUS
    assert receipt["run"] == GRAPH_RUN
    assert receipt["source_labels_read"] is False
    assert receipt["target_data_opened"] is False
    assert receipt["metric_computed"] is False
    assert receipt["gpu_used"] is False and receipt["kaggle_post"] is False
    remote = receipt["remote"]
    assert remote["run"] == GRAPH_RUN
    assert remote["ordered_ids"] == list(EXPECTED_IDS)
    assert [row["dataset"] for row in remote["rows"]] == list(EXPECTED_IDS)
    assert remote["selected_chains"] == {"source44": 835, "source6": 358}
    assert all(remote[key] is True for key in
               ("exact_original_byte_prefix", "selected_peak_and_graph_provenance",
                "exclusive_new_paths", "graph_invariants"))
    assert len(remote["result_sha256"]) == len(remote["no_label_gate_sha256"]) == 64
    config = {
        "status": "SEALED_EXP241_SOURCE_PAIRED_SCORER_V1",
        "prereg_sha256": PREREG_SHA,
        "source_only": True,
        "labels_read_at_prepare": False,
        "target_data_opened": False,
        "gpu_used": False,
        "kaggle_post": False,
        "source_inner_config_sha256": SOURCE_CONFIG_SHA,
        "source_inner_result_sha256": SOURCE_RESULT_SHA,
        "source_inner_verified_sha256": SOURCE_VERIFIED_SHA,
        "graph_run": GRAPH_RUN,
        "graph_manifest_sha256": receipt["manifest_sha256"],
        "graph_verified_receipt_sha256": receipt_sha,
        "graph_result_sha256": remote["result_sha256"],
        "graph_no_label_gate_sha256": remote["no_label_gate_sha256"],
        "output": OUTPUT,
    }
    shutil.copyfile(GRAPH_VERIFIED, PACKAGE / "graph_verified.json")
    (PACKAGE / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    files = (
        "score_exp241_source_paired.py", "audit_source_inner.py",
        "check_current_organizer_metric_runtime.py",
        "source_inner19_image_scale_audit_v2_20260927.json",
        "source_inner_config.json", "source_inner_verified.json",
        "prereg.md",
        "tracking_cellmot_official/__init__.py",
        "tracking_cellmot_official/metrics.py",
        "tracking_cellmot_official/division_metrics.py",
        "graph_verified.json", "config.json",
    )
    manifest = {"status": "SEALED_EXP241_SOURCE_PAIRED_SCORER_V1",
                "files": {name: sha(PACKAGE / name) for name in files}}
    (PACKAGE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {"status": "SEALED_EXP241_SOURCE_PAIRED_SCORER_V1",
            "manifest_sha256": sha(PACKAGE / "manifest.json"),
            "config_sha256": sha(PACKAGE / "config.json"),
            "graph_verified_receipt_sha256": receipt_sha, "files": len(files)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal-after-graph", action="store_true")
    args = parser.parse_args()
    prepared = prepare_dependencies()
    if args.seal_after_graph:
        if not GRAPH_VERIFIED.exists():
            raise FileNotFoundError("Independent EXP241 graph receipt is required")
        prepared.update(seal_after_graph())
    else:
        prepared["status"] = "EXP241_SCORER_CODE_ONLY_AWAITING_VERIFIED_GRAPH_RECEIPT"
        prepared["graph_verified_receipt_present"] = GRAPH_VERIFIED.exists()
        prepared["source_labels_read"] = False
        prepared["remote_stage_or_launch"] = False
    print(json.dumps(prepared, indent=2))


if __name__ == "__main__":
    main()
