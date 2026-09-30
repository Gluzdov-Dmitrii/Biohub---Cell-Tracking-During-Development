"""Create a frozen, reciprocal leave-one-embryo-out split for the 24-movie pilot.

The split is intentionally independent of model scores: all movies from one
embryo are training data and the first four movies of the other embryo are a
held-out audit set.  The remaining four movies of the target embryo are kept
as an untouched confirmation set.  This is a small, honest transfer check for
the community pretraining experiment, not a replacement for the full
competition validation set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_EMBRYOS = ("44b6", "6bba")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(data_dir: Path, output: Path, allow_single_embryo: bool = False, embryo_filter: str | None = None) -> None:
    movies = sorted(path.name for path in data_dir.glob("*.zarr"))
    groups = {embryo: [name for name in movies if name.startswith(f"{embryo}_")] for embryo in EXPECTED_EMBRYOS}
    if embryo_filter is not None:
        groups = {key: value for key, value in groups.items() if key == embryo_filter}
    if allow_single_embryo and sum(bool(names) for names in groups.values()) == 1:
        embryo, names = next((key, value) for key, value in groups.items() if value)
        if len(names) < 8:
            raise RuntimeError({embryo: len(names) for embryo, names in groups.items()})
        receipt = {
            "status": "PASS_SINGLE_EMBRYO_DIAGNOSTIC_SPLIT",
            "purpose": "within-embryo diagnostic only; never a reciprocal promotion gate",
            "data_dir": str(data_dir),
            "movie_counts": {key: len(value) for key, value in groups.items()},
            "folds": [{"train": names[:4], "test": names[4:8], "confirmation": names[8:], "source_embryo": embryo, "holdout_embryo": embryo}],
            "selection_policy": "lexicographic movie order frozen before any model run; no LB score used",
            "promotion_gate": "diagnostic only; requires reciprocal embryo-disjoint evidence before promotion",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return
    if any(len(names) < 12 for names in groups.values()):
        raise RuntimeError({embryo: len(names) for embryo, names in groups.items()})

    folds = []
    for source, target in (("44b6", "6bba"), ("6bba", "44b6")):
        target_movies = groups[target]
        folds.append(
            {
                "train": groups[source],
                "test": target_movies[:4],
                "confirmation": target_movies[4:8],
                "unused_target": target_movies[8:],
                "source_embryo": source,
                "holdout_embryo": target,
            }
        )

    inventory = [{"name": name} for name in movies]
    inventory_digest = hashlib.sha256(json.dumps(inventory, sort_keys=True).encode("utf-8")).hexdigest()
    receipt = {
        "status": "PASS_PILOT_RECIPROCAL_LEO",
        "purpose": "small frozen transfer check for Zebrahub initialization",
        "data_dir": str(data_dir),
        "data_dir_file_inventory_sha256": inventory_digest,
        "movie_counts": {embryo: len(names) for embryo, names in groups.items()},
        "folds": folds,
        "selection_policy": "lexicographic movie order frozen before any model run; no LB score used",
        "promotion_gate": "pretraining must improve paired held-out score on both reciprocal folds or remain research-only",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-single-embryo", action="store_true")
    parser.add_argument("--embryo", choices=EXPECTED_EMBRYOS, default=None)
    args = parser.parse_args()
    build(args.data_dir, args.output, allow_single_embryo=args.allow_single_embryo, embryo_filter=args.embryo)
    print(args.output)


if __name__ == "__main__":
    main()
