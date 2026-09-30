"""Audit division supervision in a frozen training split."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(files, load_dataset_windows):
    keys = ["windows", "positive_edges", "division_windows", "division_parents", "division_daughter_edges"]
    totals = {"movies": len(files), **{key: 0 for key in keys}}
    rows = []
    for path in files:
        _, windows = load_dataset_windows(path, window_size=2, downsample=(1, 4, 4))
        movie = {key: 0 for key in keys}
        movie["windows"] = len(windows)
        for window in windows:
            target = window.targets[0]
            row_sums = target.sum(dim=1)
            divisions = row_sums > 1
            movie["positive_edges"] += int(target.sum().item())
            movie["division_windows"] += int(divisions.any().item())
            movie["division_parents"] += int(divisions.sum().item())
            movie["division_daughter_edges"] += int(row_sums[divisions].sum().item())
        rows.append({"dataset": path.name, **movie})
        for key in keys:
            totals[key] += movie[key]
    return {"totals": totals, "per_movie": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--split", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.tracking_scripts.resolve()))
    from train_unet_transformer import load_dataset_windows

    split_rows = json.loads(args.splits.read_text(encoding="utf-8"))[args.split]
    result = {
        "status": "PASS_DIVISION_SUPERVISION_AUDIT",
        "splits_path": str(args.splits.resolve()),
        "splits_sha256": file_sha256(args.splits),
        "split": args.split,
        "train": summarize([args.data_dir / name for name in split_rows["train"]], load_dataset_windows),
        "selection": summarize(
            [args.data_dir / name for name in split_rows["test"]],
            load_dataset_windows,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
