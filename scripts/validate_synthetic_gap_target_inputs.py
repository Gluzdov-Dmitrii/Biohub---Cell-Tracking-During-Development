"""Validate frozen target manifests against candidate-cache inventories without opening movies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(manifest_path: Path, cache_dir: Path, key: str) -> dict:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if key not in payload:
        raise ValueError(f"missing manifest key: {key}")
    movies = payload[key]
    if not isinstance(movies, list) or len(movies) != 12 or len(set(movies)) != 12:
        raise ValueError("target manifest must contain exactly 12 unique movie names")
    cache_names = sorted(path.stem for path in cache_dir.glob("*.npz") if path.is_file())
    movie_names = sorted(Path(movie).stem for movie in movies)
    if cache_names != movie_names:
        raise ValueError(
            f"manifest/cache mismatch: missing={sorted(set(movie_names)-set(cache_names))}, "
            f"extra={sorted(set(cache_names)-set(movie_names))}"
        )
    return {"status": "PASS", "key": key, "n_movies": len(movies), "movies": sorted(movies)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--key", required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.manifest, args.cache_dir, args.key), indent=2))


if __name__ == "__main__":
    main()
