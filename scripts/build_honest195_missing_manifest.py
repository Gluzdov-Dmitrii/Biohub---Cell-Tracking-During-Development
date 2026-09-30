"""Build the frozen EXP192 data manifest from Kaggle file metadata only.

This script never opens or downloads competition image/label data. It excludes
the four public-test twins and subtracts the already verified official24 corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


PUBLIC_TWINS = frozenset(
    {
        "44b6_0113de3b",
        "44b6_0b24845f",
        "6bba_05b6850b",
        "6bba_05db0fb1",
    }
)
TRAIN_PATH = re.compile(r"^train/([^/]+)\.(zarr|geff)(?:/|$)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(inventory: list[dict], existing_movies: set[str]) -> dict:
    train_files: list[dict[str, object]] = []
    files_by_movie: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in inventory:
        name = str(item["name"])
        match = TRAIN_PATH.match(name)
        if not match:
            continue
        movie = match.group(1)
        size = int(item.get("bytes", item.get("size", 0)))
        if size < 0:
            raise ValueError(f"negative size for {name}")
        row = {"name": name, "size": size}
        train_files.append(row)
        files_by_movie[movie].append(row)

    movie_names = set(files_by_movie)
    if len(movie_names) != 199:
        raise ValueError(f"expected 199 train movies, got {len(movie_names)}")
    if not PUBLIC_TWINS <= movie_names:
        raise ValueError(f"public twins absent from inventory: {sorted(PUBLIC_TWINS - movie_names)}")
    if not existing_movies <= movie_names:
        raise ValueError(f"existing movies absent from inventory: {sorted(existing_movies - movie_names)}")

    honest_movies = movie_names - PUBLIC_TWINS
    existing_honest = existing_movies - PUBLIC_TWINS
    missing_movies = honest_movies - existing_honest
    if len(honest_movies) != 195 or len(existing_honest) != 20 or len(missing_movies) != 175:
        raise ValueError(
            "unexpected cohort sizes: "
            f"honest={len(honest_movies)} existing_honest={len(existing_honest)} "
            f"missing={len(missing_movies)}"
        )

    missing_files = sorted(
        (row for movie in missing_movies for row in files_by_movie[movie]),
        key=lambda row: str(row["name"]),
    )

    def summarize(names: set[str]) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for prefix in ("44b6", "6bba"):
            selected = sorted(name for name in names if name.startswith(prefix + "_"))
            result[prefix] = {
                "movies": len(selected),
                "files": sum(len(files_by_movie[name]) for name in selected),
                "bytes": sum(int(row["size"]) for name in selected for row in files_by_movie[name]),
            }
        return result

    return {
        "competition": "biohub-cell-tracking-during-development",
        "purpose": "EXP192 frozen 195-movie reciprocal embryo-disjoint confirmation corpus",
        "public_twins_excluded": sorted(PUBLIC_TWINS),
        "all_train": {
            "movies": len(movie_names),
            "files": len(train_files),
            "bytes": sum(int(row["size"]) for row in train_files),
        },
        "honest_evaluation": {
            "movies": len(honest_movies),
            "bytes": sum(
                int(row["size"]) for name in honest_movies for row in files_by_movie[name]
            ),
            "by_prefix": summarize(honest_movies),
        },
        "already_verified": {
            "movies": sorted(existing_honest),
            "by_prefix": summarize(existing_honest),
        },
        "missing": {
            "movies": sorted(missing_movies),
            "file_count": len(missing_files),
            "total_bytes": sum(int(row["size"]) for row in missing_files),
            "by_prefix": summarize(missing_movies),
        },
        "files": missing_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--official24-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    contract = json.loads(args.official24_contract.read_text(encoding="utf-8"))
    existing = set(contract["integrity"]["per_movie"])
    result = build_manifest(inventory, existing)
    result["inputs"] = {
        "competition_inventory": str(args.inventory),
        "competition_inventory_sha256": sha256(args.inventory),
        "official24_contract": str(args.official24_contract),
        "official24_contract_sha256": sha256(args.official24_contract),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("all_train", "honest_evaluation", "missing")}, indent=2))


if __name__ == "__main__":
    main()
