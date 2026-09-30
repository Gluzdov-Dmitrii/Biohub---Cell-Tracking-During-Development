"""Focused local-only checks for the EXP209 current-metric rescore gate."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "exp209_current_readiness", ROOT / "scripts/prepare_exp209_current_metric_rescore_local.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_real_archive_blocks_rescore_before_any_label_read(monkeypatch):
    original_bytes = Path.read_bytes
    original_text = Path.read_text
    opened: list[str] = []

    def checked_bytes(path: Path, *args, **kwargs):
        opened.append(str(path))
        assert path.suffix.lower() not in {".geff", ".zarr"}
        return original_bytes(path, *args, **kwargs)

    def checked_text(path: Path, *args, **kwargs):
        opened.append(str(path))
        assert path.suffix.lower() not in {".geff", ".zarr"}
        return original_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", checked_bytes)
    monkeypatch.setattr(Path, "read_text", checked_text)
    result = MODULE.audit(ROOT)
    assert result["status"] == "BLOCKED_NO_SEALED_FINAL_GRAPH175"
    assert result["historical_score_preserved"] == pytest.approx(0.6815218332750073)
    assert result["current_organizer_score"] is None
    assert result["missing_prerequisite"]["movie_count"] == 175
    assert len(result["selected_movie_ids"]["forward"]) == 116
    assert len(result["selected_movie_ids"]["reverse"]) == 59
    assert result["source_provenance"]["forward"]["embryo_prefix_disjoint"]
    assert result["source_provenance"]["reverse"]["embryo_prefix_disjoint"]
    assert opened and all("labels" not in path.lower() for path in opened)


def test_archive_tamper_rejected_before_rescore(tmp_path):
    source = ROOT / MODULE.ARCHIVE
    for item in source.iterdir():
        if item.is_file():
            shutil.copyfile(item, tmp_path / item.name)
    with (tmp_path / "forward_merged.json").open("ab") as out:
        out.write(b"\n")
    with pytest.raises(MODULE.GateError, match="entry SHA mismatch"):
        MODULE.audit_archive(tmp_path, MODULE.PINNED_SHA["manifest"])


def test_embryo_leakage_and_duplicate_target_rejected():
    split = [{"train": [f"44b6_{n:08x}.zarr" for n in range(10)],
              "test": [f"44b6_{n:08x}.zarr" for n in range(10, 12)]}]
    with pytest.raises(MODULE.GateError, match="embryo overlap"):
        MODULE.audit_source_split(split, 0, "44b6", ["44b6_10000000"])
    rows = [{"dataset": "6bba_00000001.zarr"}] * 2
    result = {"directions": {"forward": {"selected_rows": rows},
                             "reverse": {"selected_rows": [{"dataset": "44b6_00000001.zarr"}]}}}
    with pytest.raises(MODULE.GateError, match="duplicate movie"):
        MODULE.selected_ids(result, {"forward": 2, "reverse": 1})


def test_receipt_is_one_shot(tmp_path):
    target = tmp_path / "receipt.json"
    MODULE.write_once(target, {"status": "BLOCKED_NO_SEALED_FINAL_GRAPH175"})
    before = target.read_bytes()
    with pytest.raises(FileExistsError):
        MODULE.write_once(target, {"status": "PASS"})
    assert target.read_bytes() == before
