import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_exp192_chunk_structure import sha256
from validate_exp206_centroid_chunks_no_metrics import validate_all


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def metric(name):
    return {"dataset": name, "edge_tp": 1, "edge_fp": 0, "edge_fn": 0}


def test_validates_exact_five_chunk_coverage_without_metrics(tmp_path):
    runs = tmp_path / "runs"
    results = tmp_path / "results"
    chunks = []
    offset = 0
    for number, size in enumerate((24, 24, 24, 24, 20)):
        names = [f"6bba_{index:04x}.zarr" for index in range(offset, offset + size)]
        offset += size
        movies = write(
            runs / f"exp192_confirm_forward_{number:02d}_20260911/movies.json",
            {"target_development": names},
        )
        chunks.append({"direction": "forward", "number": number, "movies": size, "sha256": sha256(movies)})
        rows = [metric(name) for name in names]
        write(results / f"exp206_forward_{number:02d}.json", {
            "status": "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT",
            "per_movie_by_arm": {"translation": rows, "intensity_centroid_r2_5_5": rows},
            "summary_by_arm": {"translation": {}, "intensity_centroid_r2_5_5": {}},
        })
    index = write(tmp_path / "chunk_index.json", {"chunks": chunks})
    result = validate_all(index, runs, results)
    assert result["movie_count"] == 116
    assert result["scientific_metrics_emitted"] is False
    assert len(result["validations"]) == 5
