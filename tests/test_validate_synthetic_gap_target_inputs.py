import json

import pytest

from scripts.validate_synthetic_gap_target_inputs import validate


def _inputs(tmp_path, key="target_development"):
    movies = [f"movie_{index:02d}.zarr" for index in range(12)]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({key: movies}), encoding="utf-8")
    cache = tmp_path / "cache"
    cache.mkdir()
    for movie in movies:
        (cache / f"{movie[:-5]}.npz").write_bytes(b"cache")
    return manifest, cache


def test_validator_accepts_exact_target_mapping(tmp_path):
    manifest, cache = _inputs(tmp_path)
    result = validate(manifest, cache, "target_development")
    assert result["status"] == "PASS"
    assert result["n_movies"] == 12


def test_validator_rejects_wrong_key(tmp_path):
    manifest, cache = _inputs(tmp_path)
    with pytest.raises(ValueError, match="missing manifest key"):
        validate(manifest, cache, "source_checkpoint_validation")


def test_validator_rejects_cache_mismatch(tmp_path):
    manifest, cache = _inputs(tmp_path)
    (cache / "movie_00.npz").unlink()
    with pytest.raises(ValueError, match="manifest/cache mismatch"):
        validate(manifest, cache, "target_development")
