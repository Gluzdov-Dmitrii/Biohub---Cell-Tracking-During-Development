"""Validate all five EXP206 forward refinement chunks without emitting metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_exp192_chunk_structure import sha256, validate_metric_file


def validate_all(chunk_index_path: Path, runs_root: Path, result_dir: Path) -> dict:
    chunks = [
        row for row in json.loads(chunk_index_path.read_text(encoding="utf-8"))["chunks"]
        if row["direction"] == "forward"
    ]
    if len(chunks) != 5 or {int(row["number"]) for row in chunks} != set(range(5)):
        raise ValueError("expected exact five frozen forward chunks")
    validations = []
    union = []
    for row in sorted(chunks, key=lambda item: int(item["number"])):
        number = int(row["number"])
        run = runs_root / f"exp192_confirm_forward_{number:02d}_20260911"
        movies_path = run / "movies.json"
        if sha256(movies_path) != row["sha256"]:
            raise ValueError("movie-list hash mismatch")
        movies = list(json.loads(movies_path.read_text(encoding="utf-8"))["target_development"])
        if len(movies) != int(row["movies"]):
            raise ValueError("movie count mismatch")
        result_path = result_dir / f"exp206_forward_{number:02d}.json"
        validated = validate_metric_file(
            result_path,
            "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT",
            {"translation", "intensity_centroid_r2_5_5"},
            movies,
        )
        validations.append({
            "chunk": f"forward_{number:02d}",
            "movie_count": len(movies),
            "movies_sha256": sha256(movies_path),
            "result_sha256": validated["sha256"],
        })
        union.extend(movies)
    if len(union) != 116 or len(set(union)) != 116 or any(not name.startswith("6bba_") for name in union):
        raise ValueError("EXP206 forward coverage mismatch")
    return {
        "status": "PASS_EXP206_ALL_FORWARD_CHUNKS_NO_METRICS",
        "chunks": 5,
        "movie_count": 116,
        "validations": validations,
        "scientific_metrics_emitted": False,
        "next_allowed_step": "Merge the five immutable refinement results and build the frozen EXP206 composition.",
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
        "status": result["status"], "chunks": result["chunks"],
        "movie_count": result["movie_count"],
        "scientific_metrics_emitted": result["scientific_metrics_emitted"],
    }, indent=2))


if __name__ == "__main__":
    main()
