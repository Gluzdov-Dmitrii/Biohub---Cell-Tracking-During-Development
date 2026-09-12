"""Validate all eight EXP209 selected-centroid chunks without emitting metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_exp192_chunk_structure import sha256, validate_metric_file


POLICY = {
    "forward": {"radius": [3, 5, 5], "arm": "intensity_centroid_r3_5_5", "minimum_length": 8, "count": 116},
    "reverse": {"radius": [2, 3, 3], "arm": "intensity_centroid_r2_3_3", "minimum_length": 3, "count": 59},
}


def validate_all(chunk_index_path: Path, runs_root: Path, result_dir: Path) -> dict:
    chunks = json.loads(chunk_index_path.read_text(encoding="utf-8"))["chunks"]
    expected_keys = {
        *(("forward", number) for number in range(5)),
        *(("reverse", number) for number in range(3)),
    }
    actual_keys = {(str(row["direction"]), int(row["number"])) for row in chunks}
    if actual_keys != expected_keys or len(chunks) != 8:
        raise ValueError("expected exact frozen five-forward/three-reverse chunk index")

    validations = []
    union_by_direction = {"forward": [], "reverse": []}
    for row in sorted(chunks, key=lambda item: (str(item["direction"]), int(item["number"]))):
        direction = str(row["direction"])
        number = int(row["number"])
        policy = POLICY[direction]
        source_run = runs_root / f"exp192_confirm_{direction}_{number:02d}_20260911"
        movies_path = source_run / "movies.json"
        if sha256(movies_path) != row["sha256"]:
            raise ValueError(f"{direction}_{number:02d}: movie-list hash mismatch")
        movies = list(json.loads(movies_path.read_text(encoding="utf-8"))["target_development"])
        if len(movies) != int(row["movies"]):
            raise ValueError(f"{direction}_{number:02d}: movie count mismatch")

        result_path = result_dir / f"exp209_{direction}_{number:02d}.json"
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        if payload.get("radii_zyx_voxels") != [policy["radius"]]:
            raise ValueError(f"{direction}_{number:02d}: selected radius mismatch")
        if payload.get("minimum_length") != policy["minimum_length"]:
            raise ValueError(f"{direction}_{number:02d}: minimum length mismatch")
        if payload.get("movie_key") != "target_development":
            raise ValueError(f"{direction}_{number:02d}: movie key mismatch")
        validated = validate_metric_file(
            result_path,
            "PASS_FIXED_INTENSITY_CENTROID_FAMILY",
            {"translation", policy["arm"]},
            movies,
        )
        validations.append({
            "chunk": f"{direction}_{number:02d}",
            "movie_count": len(movies),
            "movies_sha256": sha256(movies_path),
            "result_sha256": validated["sha256"],
        })
        union_by_direction[direction].extend(movies)

    for direction, movies in union_by_direction.items():
        policy = POLICY[direction]
        prefix = "6bba_" if direction == "forward" else "44b6_"
        if len(movies) != policy["count"] or len(set(movies)) != policy["count"]:
            raise ValueError(f"{direction}: full coverage mismatch")
        if any(not name.startswith(prefix) for name in movies):
            raise ValueError(f"{direction}: embryo prefix mismatch")

    return {
        "status": "PASS_EXP209_ALL_SELECTED_CENTROID_CHUNKS_NO_METRICS",
        "chunks": 8,
        "movie_count": 175,
        "direction_counts": {name: len(values) for name, values in union_by_direction.items()},
        "policy": POLICY,
        "validations": validations,
        "scientific_metrics_emitted": False,
        "next_allowed_step": "Merge immutable chunks and assemble preregistered EXP209 policies.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk-index", type=Path, required=True)
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_all(args.chunk_index, args.runs_root, args.result_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "chunks": result["chunks"],
        "movie_count": result["movie_count"],
        "scientific_metrics_emitted": False,
    }, indent=2))


if __name__ == "__main__":
    main()
