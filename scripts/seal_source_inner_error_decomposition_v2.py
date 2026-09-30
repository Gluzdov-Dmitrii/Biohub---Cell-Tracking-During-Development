"""Seal the distinct source19 image-gated SOURCE-INNER v2 bundle locally."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "work/source_inner_error_decomposition_20260927"
BUNDLE = ROOT / "work/source_inner_error_decomposition_v2_20260927"
IMAGE = ROOT / "reports/source_inner19_image_scale_audit_v2_20260927.json"
V1_SHA = "17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e"
FILES = (
    "audit_source_inner.py", "config.json", "check_current_organizer_metric_runtime.py",
    "source_inner19_image_scale_audit_v2_20260927.json",
    "tracking_cellmot_official/__init__.py",
    "tracking_cellmot_official/metrics.py",
    "tracking_cellmot_official/division_metrics.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert sha(V1 / "manifest.json") == V1_SHA, "v1 source must remain byte-preserved"
    config = json.loads((BUNDLE / "config.json").read_text())
    image = json.loads(IMAGE.read_text())
    assert config["source19_image_receipt_sha256"] == sha(IMAGE)
    assert sha(BUNDLE / IMAGE.name) == sha(IMAGE)
    assert image["status"] == "PASS_SOURCE_INNER_EXACT19_IMAGE_SCALE_NO_LABELS"
    ids = [name for cohort in config["cohorts"] for name in cohort["ids"]]
    assert len(ids) == len(set(ids)) == 19
    assert [row["dataset"] for row in image["rows"]] == ids
    assert config["output"].endswith("/runs/source_inner_error_decomposition_v2_20260927/output")
    assert {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*") if p.is_file()} == (
        set(FILES) | {"manifest.json"})
    manifest = {"status": "SEALED_SOURCE_INNER_ERROR_DECOMPOSITION_LOCAL_ONLY",
                "files": {name: sha(BUNDLE / name) for name in FILES}}
    content = (json.dumps(manifest, indent=2) + "\n").encode()
    path = BUNDLE / "manifest.json"
    assert sha(path) == V1_SHA or path.read_bytes() == content, "Unexpected v2 seal drift"
    path.write_bytes(content)
    print(json.dumps({"status": manifest["status"], "source_movies": len(ids),
                      "files": len(FILES), "manifest_sha256": sha(path)}))


if __name__ == "__main__":
    main()
