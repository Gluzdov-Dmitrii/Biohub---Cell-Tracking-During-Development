import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_exp192_chunk_structure import sha256
from validate_exp209_selected_centroid_chunks_no_metrics import POLICY, validate_all


def write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def metric(name):
    return {"dataset": name, "edge_tp": 1, "edge_fp": 0, "edge_fn": 0}


def test_validates_exact_all_eight_without_emitting_metrics(tmp_path):
    runs = tmp_path / "runs"
    results = tmp_path / "results"
    chunks = []
    for direction, sizes in (("forward", (24, 24, 24, 24, 20)), ("reverse", (24, 24, 11))):
        prefix = "6bba" if direction == "forward" else "44b6"
        offset = 0
        policy = POLICY[direction]
        for number, size in enumerate(sizes):
            names = [f"{prefix}_{index:04x}.zarr" for index in range(offset, offset + size)]
            offset += size
            movies = write(
                runs / f"exp192_confirm_{direction}_{number:02d}_20260911/movies.json",
                {"target_development": names},
            )
            chunks.append({"direction": direction, "number": number, "movies": size, "sha256": sha256(movies)})
            rows = [metric(name) for name in names]
            write(results / f"exp209_{direction}_{number:02d}.json", {
                "status": "PASS_FIXED_INTENSITY_CENTROID_FAMILY",
                "movie_key": "target_development",
                "radii_zyx_voxels": [policy["radius"]],
                "minimum_length": policy["minimum_length"],
                "per_movie_by_arm": {"translation": rows, policy["arm"]: rows},
                "summary_by_arm": {"translation": {}, policy["arm"]: {}},
            })
    result = validate_all(write(tmp_path / "chunk_index.json", {"chunks": chunks}), runs, results)
    assert result["movie_count"] == 175
    assert result["direction_counts"] == {"forward": 116, "reverse": 59}
    assert result["scientific_metrics_emitted"] is False

