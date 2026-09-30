from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_manifest_stage import validate


def test_validator_reports_complete_movies_and_partial_files(tmp_path):
    manifest = {"files": [
        {"name": "train/44b6_a.zarr/a", "size": 1},
        {"name": "train/44b6_a.geff/b", "size": 2},
        {"name": "train/44b6_b.zarr/a", "size": 3},
        {"name": "train/6bba_c.zarr/a", "size": 4},
    ]}
    for name, data in (
        ("train/44b6_a.zarr/a", b"x"),
        ("train/44b6_a.geff/b", b"xx"),
        ("train/44b6_b.zarr/a", b"xx"),
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    result = validate(manifest, tmp_path, "44b6")
    assert result["status"] == "INCOMPLETE"
    assert result["complete_files"] == 2
    assert result["complete_movies"] == ["44b6_a"]
    assert result["mismatch_count"] == 1
