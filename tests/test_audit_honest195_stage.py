from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_honest195_stage import audit


def test_small_stage_audit(tmp_path):
    files = []
    for movie in ("44b6_a", "6bba_b"):
        for kind in ("zarr", "geff"):
            name = f"train/{movie}.{kind}/payload"
            path = tmp_path / Path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x")
            files.append({"name": name, "size": 1})
    result = audit(
        {"files": files}, tmp_path,
        expected_prefix_movies={"44b6": 1, "6bba": 1},
        zarr_files_per_movie=1, geff_files_per_movie=1,
        content_hash=True,
    )
    assert result["status"] == "PASS_EXP192_DATA_AUDIT"
    assert result["movies"] == 2
    assert len(result["content_sha256_by_movie"]) == 2
