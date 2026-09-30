"""Seal the EXP239 source-only CPU diagnostic bundle locally, without labels.

This script reads the prior *config* and pinned source files. It does not open
GEFF, graph CSV, score output or reciprocal target files, and has no remote API.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "work/source_inner_error_decomposition_20260927"
SOURCE19 = ROOT / "work/source_inner_error_decomposition_v2_20260927"
BASE_CONFIG = BASE / "config.json"
BASE_CONFIG_SHA = "4b8720083617f84bc034b07123c5ae2ffa884a536ab67f7716386abdf280a013"
DEST = ROOT / "work/exp239_source_division_fn_taxonomy_20260927/bundle"
PREREG = ROOT / "reports/EXP239_SOURCE_DIVISION_FN_TAXONOMY_PREREG_20260927.md"
OUTPUT = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp239_source_division_fn_taxonomy_v1_20260927/output"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_config(source: dict) -> dict:
    assert source["status"] == "PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY"
    assert [cohort["experiment"] for cohort in source["cohorts"]] == ["EXP227", "EXP236"]
    expected = [{"tp": 2, "fp": 6, "fn": 3},
                {"tp": 1, "fp": 9, "fn": 8}]
    keep = (
        "experiment", "source_embryo", "ids", "checkpoint_sha256",
        "scorer_code", "scorer_run", "scorer_manifest_sha256",
        "scorer_config_sha256", "graph_run", "graph_hashes",
        "score_gate_sha256", "geff_tree_hashes",
    )
    cohorts = []
    for row, counts in zip(source["cohorts"], expected, strict=True):
        cohorts.append({**{key: row[key] for key in keep},
                        "expected_division_counts": counts})
    assert [len(row["ids"]) for row in cohorts] == [8, 11]
    assert sum(row["expected_division_counts"]["tp"] +
               row["expected_division_counts"]["fn"] for row in cohorts) == 14
    return {
        "status": "PREREGISTERED_EXP239_SOURCE_DIVISION_FN_TAXONOMY",
        "source_only": True,
        "organizer_commit": source["organizer_commit"],
        "tracksdata_commit": source["tracksdata_commit"],
        "source19_image_receipt_sha256": "d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6",
        "output": OUTPUT,
        "cohorts": cohorts,
    }


def main() -> None:
    assert not DEST.exists(), "EXP239 local bundle exists; reconcile, do not overwrite"
    assert sha(BASE_CONFIG) == BASE_CONFIG_SHA
    source = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    config = build_config(source)
    sources = {
        "audit_exp239.py": ROOT / "scripts/audit_exp239_source_division_fn_taxonomy.py",
        "PREREG.md": PREREG,
        "check_current_organizer_metric_runtime.py": BASE / "check_current_organizer_metric_runtime.py",
        "source_inner19_image_scale_audit_v2_20260927.json": SOURCE19 / "source_inner19_image_scale_audit_v2_20260927.json",
        "tracking_cellmot_official/__init__.py": BASE / "tracking_cellmot_official/__init__.py",
        "tracking_cellmot_official/metrics.py": BASE / "tracking_cellmot_official/metrics.py",
        "tracking_cellmot_official/division_metrics.py": BASE / "tracking_cellmot_official/division_metrics.py",
    }
    expected_metric = {
        "tracking_cellmot_official/__init__.py": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
        "tracking_cellmot_official/metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
        "tracking_cellmot_official/division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
        "source_inner19_image_scale_audit_v2_20260927.json": "d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6",
    }
    for relative, digest in expected_metric.items():
        assert sha(sources[relative]) == digest, relative
    DEST.mkdir(parents=True, exist_ok=False)
    for relative, origin in sources.items():
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(origin.read_bytes())
    (DEST / "config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    files = {str(path.relative_to(DEST)).replace("\\", "/"): sha(path)
             for path in DEST.rglob("*") if path.is_file()}
    manifest = {"status": "SEALED_EXP239_LOCAL_ONLY",
                "source_config_sha256": BASE_CONFIG_SHA,
                "files": dict(sorted(files.items()))}
    (DEST / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": manifest["status"], "bundle": str(DEST),
                      "manifest_sha256": sha(DEST / "manifest.json"),
                      "config_sha256": sha(DEST / "config.json"),
                      "files": len(files)}, indent=2))


if __name__ == "__main__":
    main()
