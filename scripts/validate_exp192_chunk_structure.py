"""Validate one EXP192 chunk without exposing any scientific metric values."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_finite(value: Any, location: str = "root") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_finite(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_finite(item, f"{location}[{index}]")


def validate_metric_file(
    path: Path,
    expected_status: str,
    expected_arms: set[str],
    expected_movies: list[str],
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_finite(payload)
    if payload.get("status") != expected_status:
        raise ValueError(f"{path}: unexpected status")
    arms = payload.get("per_movie_by_arm")
    if not isinstance(arms, dict) or set(arms) != expected_arms:
        raise ValueError(f"{path}: unexpected arms")
    expected_set = set(expected_movies)
    for arm, rows in arms.items():
        if not isinstance(rows, list) or len(rows) != len(expected_movies):
            raise ValueError(f"{path}: {arm} row count mismatch")
        names = [row.get("dataset") for row in rows if isinstance(row, dict)]
        if len(names) != len(rows) or set(names) != expected_set or len(set(names)) != len(names):
            raise ValueError(f"{path}: {arm} movie membership mismatch")
        if any(set(row) != set(rows[0]) for row in rows[1:]):
            raise ValueError(f"{path}: {arm} metric row schemas differ")
    summaries = payload.get("summary_by_arm")
    if not isinstance(summaries, dict) or set(summaries) != expected_arms:
        raise ValueError(f"{path}: summary arms mismatch")
    return {"path": str(path), "sha256": sha256(path), "arms": sorted(expected_arms)}


def validate(run_dir: Path, direction: str) -> dict[str, Any]:
    movies_path = run_dir / "movies.json"
    movie_payload = json.loads(movies_path.read_text(encoding="utf-8"))
    movies = list(movie_payload["target_development"])
    if not movies or len(set(movies)) != len(movies):
        raise ValueError("movie list must be non-empty and unique")
    prefix = "6bba_" if direction == "forward" else "44b6_"
    if any(not str(movie).startswith(prefix) for movie in movies):
        raise ValueError("movie direction/prefix mismatch")

    specifications = [
        (
            "base_raw.json",
            "PASS_FROZEN_REGISTERED_MODEL_EVALUATION",
            {"registered_hungarian", "registered_weak_hungarian"},
        ),
        (
            "base_filtered.json",
            "PASS_CACHED_SHORT_TRACK_FAMILY",
            {"no_filter", "min8"} if direction == "forward" else {"no_filter", "min3"},
        ),
        (
            "local_flow.json",
            "PASS_CACHED_FIXED_LOCAL_FLOW",
            {"translation", "fixed_local_flow"},
        ),
    ]
    if direction == "reverse":
        specifications.extend(
            [
                (
                    "gap.json",
                    "PASS_SYNTHETIC_GAP_EVALUATION",
                    {"registered_hungarian", "synthetic_gap_no_veto", "synthetic_gap_deepcenter"},
                ),
                (
                    "gap_filtered.json",
                    "PASS_CACHED_SELECTED_EDGE_SHORT_TRACKS",
                    {"no_filter", "min6"},
                ),
            ]
        )

    files = [
        validate_metric_file(run_dir / "results" / name, status, arms, movies)
        for name, status, arms in specifications
    ]
    if direction == "reverse":
        reproduction_path = run_dir / "results" / "gap_cache_reproduction.json"
        reproduction = json.loads(reproduction_path.read_text(encoding="utf-8"))
        assert_finite(reproduction)
        if reproduction.get("status") != "PASS_EXACT_CACHED_ARM_REPRODUCTION":
            raise ValueError("gap cache reproduction did not pass")
        files.append({"path": str(reproduction_path), "sha256": sha256(reproduction_path)})

    return {
        "status": "PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS",
        "direction": direction,
        "movie_count": len(movies),
        "movies_sha256": sha256(movies_path),
        "validated_files": files,
        "scientific_metrics_emitted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--direction", choices=("forward", "reverse"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.run_dir, args.direction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "movie_count": result["movie_count"]}))


if __name__ == "__main__":
    main()
