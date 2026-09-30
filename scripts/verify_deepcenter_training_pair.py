"""Verify both explicit-split DeepCenter training artifacts for EXP180."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_fold(path: Path, embryo: str) -> dict:
    split = json.loads((path / "split_manifest.json").read_text(encoding="utf-8"))
    if split.get("mode") != "explicit_predeclared":
        raise ValueError(f"{embryo}: split was not explicit")
    train = list(split["train"])
    val = list(split["val"])
    if len(train) != 10 or len(val) != 2 or set(train) & set(val):
        raise ValueError(f"{embryo}: expected disjoint 10/2 split")
    if any(not name.startswith(f"{embryo}_") for name in train + val):
        raise ValueError(f"{embryo}: cross-embryo item in source fold")
    with (path / "history.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 2:
        raise ValueError(f"{embryo}: expected exactly two epochs")
    for row in rows:
        for key in ("train_loss", "val_loss", "score"):
            value = float(row[key])
            if not (-1e20 < value < 1e20):
                raise ValueError(f"{embryo}: non-finite {key}")
    best = path / "best.pt"
    last = path / "checkpoint_last.pt"
    if not best.is_file() or not last.is_file():
        raise FileNotFoundError(f"{embryo}: missing checkpoint")
    return {
        "embryo": embryo,
        "train_movies": train,
        "validation_movies": val,
        "history": rows,
        "best_sha256": sha256(best),
        "best_bytes": best.stat().st_size,
        "last_sha256": sha256(last),
        "last_bytes": last.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fold", action="append", required=True, help="embryo=directory")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    folds = []
    for item in args.fold:
        embryo, raw_path = item.split("=", 1)
        folds.append(verify_fold(Path(raw_path), embryo))
    if {row["embryo"] for row in folds} != {"44b6", "6bba"}:
        raise ValueError("Expected exactly the 44b6 and 6bba folds")
    result = {
        "status": "PASS_RECIPROCAL_EXPLICIT_SOURCE_TRAINING",
        "folds": folds,
        "target_embryo_opened": False,
        "eligible_for_gap_source_evaluation": True,
        "eligible_for_official24_target_evaluation": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
