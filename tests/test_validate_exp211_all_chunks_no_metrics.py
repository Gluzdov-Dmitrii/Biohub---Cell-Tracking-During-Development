import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_exp211_all_chunks_no_metrics import validate_all


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    runs = tmp_path / "runs"
    chunks = []
    for direction, sizes in (("forward", [24, 24, 24, 24, 20]), ("reverse", [24, 24, 11])):
        for number, size in enumerate(sizes):
            run = runs / f"exp211_{direction}_{number:02d}_20260912"
            results = run / "results"
            results.mkdir(parents=True)
            prefix = "6bba" if direction == "forward" else "44b6"
            movies = [f"{prefix}_{number}_{item}.zarr" for item in range(size)]
            movies_path = run / "movies.json"
            movies_path.write_text(json.dumps({"target_development": movies}), encoding="utf-8")
            movie_sha = digest(movies_path)
            structure = {
                "status": "PASS_EXP211_D4_CHUNK_STRUCTURE_NO_METRICS",
                "direction": direction,
                "movie_count": size,
                "movies_sha256": movie_sha,
                "scientific_metrics_emitted": False,
            }
            structure_path = results / "structure_validation.json"
            structure_path.write_text(json.dumps(structure), encoding="utf-8")
            files = [movies_path, structure_path]
            for item in range(8):
                path = results / f"dummy_{item}.txt"
                path.write_text(str(item), encoding="utf-8")
                files.append(path)
            manifest = run / "SHA256SUMS"
            manifest.write_text("".join(f"{digest(path)}  {path.resolve()}\n" for path in files), encoding="utf-8")
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": movie_sha})
    index = tmp_path / "chunk_index.json"
    index.write_text(json.dumps({"chunks": chunks}), encoding="utf-8")
    return index, runs


def test_all_eight_pass_exact_gate(tmp_path):
    index, runs = fixture(tmp_path)
    result = validate_all(index, runs)
    assert result["status"] == "PASS_EXP211_ALL_D4_CHUNKS_NO_METRICS"
    assert result["chunks"] == 8
    assert result["scientific_metrics_emitted"] is False


def test_structure_failure_is_rejected(tmp_path):
    index, runs = fixture(tmp_path)
    path = runs / "exp211_forward_00_20260912" / "results" / "structure_validation.json"
    payload = json.loads(path.read_text())
    payload["status"] = "FAIL"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="structure gate failed"):
        validate_all(index, runs)
