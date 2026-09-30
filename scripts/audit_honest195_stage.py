"""Audit EXP192 missing data by path, size, structure, metadata and content hash."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from build_official24_private_splits import content_tree_sha256, file_sha256, safe_manifest_path


PUBLIC_TWINS = {
    "44b6_0113de3b", "44b6_0b24845f", "6bba_05b6850b", "6bba_05db0fb1"
}


def audit(
    manifest: dict,
    data_root: Path,
    *,
    expected_prefix_movies: dict[str, int],
    zarr_files_per_movie: int,
    geff_files_per_movie: int,
    content_hash: bool,
) -> dict:
    entries = [{"name": str(row["name"]), "size": int(row["size"])} for row in manifest["files"]]
    names = [row["name"] for row in entries]
    if len(names) != len(set(names)):
        raise ValueError("duplicate manifest path")
    by_movie: dict[str, list[dict]] = defaultdict(list)
    problems = []
    metadata_count = 0
    for row in entries:
        relative = safe_manifest_path(row["name"])
        movie_dir = relative.parts[1]
        if not movie_dir.endswith((".zarr", ".geff")):
            raise ValueError(f"unexpected movie directory: {movie_dir}")
        movie = movie_dir.rsplit(".", 1)[0]
        if movie in PUBLIC_TWINS:
            raise ValueError(f"public twin leaked into stage: {movie}")
        by_movie[movie].append(row)
        actual = data_root / relative
        if not actual.is_file():
            problems.append({"name": row["name"], "problem": "missing"})
        elif actual.stat().st_size != row["size"]:
            problems.append({"name": row["name"], "problem": "size_mismatch"})
        elif actual.name == "zarr.json":
            metadata_count += 1
            try:
                meta = json.loads(actual.read_text(encoding="utf-8"))
                if meta.get("zarr_format") != 3 or meta.get("node_type") not in ("array", "group"):
                    raise ValueError("unexpected Zarr metadata")
            except Exception as exc:
                problems.append({"name": row["name"], "problem": "invalid_zarr_metadata", "detail": repr(exc)})
    counts = {prefix: sum(name.startswith(prefix + "_") for name in by_movie) for prefix in expected_prefix_movies}
    if counts != expected_prefix_movies:
        problems.append({"problem": "prefix_movie_counts", "expected": expected_prefix_movies, "actual": counts})
    per_movie = {}
    for movie, movie_entries in sorted(by_movie.items()):
        zarr_count = sum(".zarr" in Path(row["name"]).parts[1] for row in movie_entries)
        geff_count = sum(".geff" in Path(row["name"]).parts[1] for row in movie_entries)
        per_movie[movie] = {
            "zarr_files": zarr_count,
            "geff_files": geff_count,
            "bytes": sum(row["size"] for row in movie_entries),
        }
        if (zarr_count, geff_count) != (zarr_files_per_movie, geff_files_per_movie):
            problems.append({"movie": movie, "problem": "component_count", **per_movie[movie]})
    if problems:
        raise RuntimeError(json.dumps(problems[:20], indent=2))
    hashes = (
        {movie: content_tree_sha256(data_root, rows) for movie, rows in sorted(by_movie.items())}
        if content_hash else None
    )
    return {
        "status": "PASS_EXP192_DATA_AUDIT",
        "files": len(entries),
        "bytes": sum(row["size"] for row in entries),
        "movies": len(by_movie),
        "movie_counts": counts,
        "zarr_metadata_json_files_parsed": metadata_count,
        "per_movie": per_movie,
        "content_sha256_by_movie": hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--content-hash", action="store_true")
    args = parser.parse_args()
    result = audit(
        json.loads(args.manifest.read_text(encoding="utf-8")), args.data_root,
        expected_prefix_movies={"44b6": 59, "6bba": 116},
        zarr_files_per_movie=102, geff_files_per_movie=21,
        content_hash=args.content_hash,
    )
    result["manifest"] = str(args.manifest)
    result["manifest_sha256"] = file_sha256(args.manifest)
    result["data_root"] = str(args.data_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "files", "bytes", "movies", "movie_counts", "zarr_metadata_json_files_parsed")}, indent=2))


if __name__ == "__main__":
    main()
