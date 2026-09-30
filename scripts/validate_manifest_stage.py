"""Validate a staged Kaggle per-file download using official names and sizes."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def validate(manifest: dict, destination: Path, holdout: str) -> dict:
    entries = [
        item for item in manifest["files"]
        if len(Path(str(item["name"])).parts) > 1
        and Path(str(item["name"])).parts[1].startswith(holdout + "_")
    ]
    expected_by_movie: dict[str, list[dict]] = defaultdict(list)
    complete_by_movie: dict[str, int] = defaultdict(int)
    missing, mismatched = [], []
    complete_bytes = 0
    for item in entries:
        name, expected = str(item["name"]), int(item["size"])
        movie = Path(name).parts[1].split(".", 1)[0]
        expected_by_movie[movie].append(item)
        path = destination / Path(name)
        if not path.is_file():
            missing.append(name)
            continue
        actual = path.stat().st_size
        if actual != expected:
            mismatched.append({"name": name, "expected": expected, "actual": actual})
            continue
        complete_by_movie[movie] += 1
        complete_bytes += actual
    complete_movies = sorted(
        movie for movie, movie_entries in expected_by_movie.items()
        if complete_by_movie[movie] == len(movie_entries)
    )
    return {
        "status": "PASS_COMPLETE" if not missing and not mismatched else "INCOMPLETE",
        "holdout": holdout,
        "expected_files": len(entries),
        "expected_bytes": sum(int(item["size"]) for item in entries),
        "complete_files": len(entries) - len(missing) - len(mismatched),
        "complete_bytes": complete_bytes,
        "expected_movies": len(expected_by_movie),
        "complete_movies": complete_movies,
        "complete_movie_count": len(complete_movies),
        "missing_count": len(missing),
        "mismatch_count": len(mismatched),
        "first_missing": missing[:10],
        "first_mismatched": mismatched[:10],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--holdout", choices=("44b6", "6bba"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(json.loads(args.manifest.read_text(encoding="utf-8")), args.destination, args.holdout)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS_COMPLETE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
