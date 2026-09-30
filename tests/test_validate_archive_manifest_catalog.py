import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_archive_manifest_catalog import validate


def make(tmp_path, manifest_size=3):
    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("train/6bba_x.zarr/c/0", b"abc")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": [{"name": "train/6bba_x.zarr/c/0", "size": manifest_size}]}), encoding="utf-8")
    return archive, manifest


def test_catalog_matches(tmp_path):
    archive, manifest = make(tmp_path)
    result = validate(archive, manifest)
    assert result["status"] == "PASS_ARCHIVE_MANIFEST_CATALOG"
    assert result["manifest_files"] == 1
    assert result["wrong_size"] == 0


def test_catalog_rejects_wrong_size(tmp_path):
    archive, manifest = make(tmp_path, manifest_size=4)
    with pytest.raises(RuntimeError, match="wrong_size"):
        validate(archive, manifest)
