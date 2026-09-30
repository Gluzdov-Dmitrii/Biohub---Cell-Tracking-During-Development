"""Select a detector threshold using source-embryo validation results only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", nargs=2, action="append", metavar=("THRESHOLD", "PATH"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", default="registered_hungarian")
    parser.add_argument("--parent-threshold", type=float, default=0.985)
    args = parser.parse_args()

    rows = []
    seen: set[float] = set()
    for threshold_text, path_text in args.result:
        threshold = float(threshold_text)
        if not 0.0 < threshold < 1.0 or threshold in seen:
            raise ValueError(f"invalid or duplicate threshold: {threshold_text}")
        seen.add(threshold)
        path = Path(path_text)
        payload = json.loads(path.read_text(encoding="utf-8"))
        score = float(payload["summary_by_arm"][args.arm]["score"])
        recall = float(payload["summary_by_arm"][args.arm]["node_recall"])
        if not math.isfinite(score) or not math.isfinite(recall):
            raise ValueError(f"non-finite source metric at threshold {threshold}")
        datasets = sorted(str(row["dataset"]) for row in payload["per_movie_by_arm"][args.arm])
        if len(datasets) != len(set(datasets)) or not datasets:
            raise ValueError(f"invalid source dataset list at threshold {threshold}")
        rows.append(
            {
                "threshold": threshold,
                "score": score,
                "node_recall": recall,
                "datasets": datasets,
                "path": str(path),
                "sha256": sha256(path),
            }
        )
    dataset_sets = {tuple(row["datasets"]) for row in rows}
    if len(dataset_sets) != 1:
        raise ValueError("source datasets differ across threshold arms")
    selected = max(
        rows,
        key=lambda row: (
            row["score"],
            -abs(row["threshold"] - args.parent_threshold),
            row["threshold"],
        ),
    )
    output = {
        "status": "FROZEN_SOURCE_ONLY_THRESHOLD_SELECTION",
        "arm": args.arm,
        "parent_threshold": args.parent_threshold,
        "selection_rule": "maximum source score; tie by distance to parent threshold, then higher threshold",
        "source_grid": sorted(rows, key=lambda row: row["threshold"]),
        "selected_threshold": selected["threshold"],
        "selected_source_score": selected["score"],
        "target_data_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"{selected['threshold']:.12g}")


if __name__ == "__main__":
    main()
