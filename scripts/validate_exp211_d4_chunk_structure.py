"""Validate one EXP211 D4 detector chunk without emitting scientific metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list):
        return all(finite(item) for item in value)
    return True


def metric_file(path: Path, status: str, arms: set[str], movies: list[str]) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != status or not finite(payload):
        raise ValueError(f"Invalid status or non-finite value: {path}")
    per_arm = payload.get("per_movie_by_arm")
    summaries = payload.get("summary_by_arm")
    if not isinstance(per_arm, dict) or set(per_arm) != arms:
        raise ValueError(f"Unexpected per-movie arms: {path}")
    if not isinstance(summaries, dict) or set(summaries) != arms:
        raise ValueError(f"Unexpected summary arms: {path}")
    expected = set(movies)
    for rows in per_arm.values():
        names = [row.get("dataset") for row in rows if isinstance(row, dict)]
        if len(names) != len(movies) or set(names) != expected or len(set(names)) != len(names):
            raise ValueError(f"Movie membership mismatch: {path}")
    return {"path": str(path), "sha256": sha256(path), "arms": sorted(arms)}


def validate(run_dir: Path, direction: str) -> dict:
    movies_path = run_dir / "movies.json"
    movies = json.loads(movies_path.read_text(encoding="utf-8"))["target_development"]
    if not movies or len(movies) != len(set(movies)):
        raise ValueError("Movie list must be non-empty and unique")
    prefix = "6bba_" if direction == "forward" else "44b6_"
    if any(not movie.startswith(prefix) for movie in movies):
        raise ValueError("Movie direction mismatch")
    minimum = "min8" if direction == "forward" else "min3"
    raw = metric_file(
        run_dir / "results" / "d4_raw.json",
        "PASS_FROZEN_REGISTERED_MODEL_EVALUATION",
        {"registered_hungarian", "registered_weak_hungarian"},
        movies,
    )
    filtered = metric_file(
        run_dir / "results" / "d4_filtered.json",
        "PASS_CACHED_SHORT_TRACK_FAMILY",
        {"no_filter", minimum},
        movies,
    )
    cache = run_dir / "results" / "d4_raw_candidate_cache"
    cache_files = sorted(cache.glob("*.npz"))
    if [path.stem for path in cache_files] != sorted(Path(movie).stem for movie in movies):
        raise ValueError("Candidate cache coverage mismatch")
    return {
        "status": "PASS_EXP211_D4_CHUNK_STRUCTURE_NO_METRICS",
        "direction": direction,
        "movie_count": len(movies),
        "movies_sha256": sha256(movies_path),
        "validated_files": [raw, filtered],
        "candidate_cache_files": len(cache_files),
        "scientific_metrics_emitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--direction", choices=("forward", "reverse"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.run_dir, args.direction)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "movie_count": result["movie_count"]}))


if __name__ == "__main__":
    main()

