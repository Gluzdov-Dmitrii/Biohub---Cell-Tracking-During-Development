from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kaggle_notebooks/exp212_exp209_oof_frontier/exp209_oof_frontier.py"
METADATA = ROOT / "kaggle_notebooks/exp212_exp209_oof_frontier/kernel-metadata.json"
DATASET = ROOT / "kaggle_datasets/exp212_exp209_oof_frontier_models"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source_is_dynamic_and_compiles() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    compile(source, str(SOURCE), "exec")
    assert 'COMPETITION = "biohub-cell-tracking-during-development"' in source
    assert 'TEST_DIR.glob("*.zarr")' in source
    assert "submission.csv" in source
    assert "rglob(\"submission.csv\")" not in source
    assert "unexpected_test_names" not in source


def test_exp209_policy_is_frozen() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for anchor in (
        "0.6815218332750073",
        "(3, 5, 5)",
        "filter_family(refined_coords, links, {}, 8)",
        "gap_close_um=4.5",
        "deepcenter_threshold=0.20",
        "deepcenter_confirm_min_span_um=8.5",
        "synthetic_max_fraction=0.05",
        "filter_family(gap_coords, gap_edges, {}, 6)",
        "mutual_matches_2um",
    ):
        assert anchor in source


def test_metadata_is_offline_private_gpu_code_run() -> None:
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata["is_private"] is True
    assert metadata["enable_gpu"] is True
    assert metadata["enable_internet"] is False
    assert metadata["competition_sources"] == ["biohub-cell-tracking-during-development"]
    assert "dmitriigluzdov/biohub-exp209-pooled-oof-frontier-models" in metadata["dataset_sources"]


def test_dataset_manifest_verifies() -> None:
    for line in (DATASET / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        assert digest(DATASET / relative) == expected
