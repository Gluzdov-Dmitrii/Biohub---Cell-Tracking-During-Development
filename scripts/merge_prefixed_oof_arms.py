"""Merge arm families from several result JSONs under immutable prefixes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, metavar="PREFIX=PATH")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    merged: dict[str, list[dict]] = {}
    sources = []
    for spec in args.source:
        prefix, raw_path = spec.split("=", 1)
        path = Path(raw_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        for arm, rows in payload["per_movie_by_arm"].items():
            label = f"{prefix}_{arm}"
            if label in merged:
                raise ValueError(f"duplicate arm {label}")
            merged[label] = rows
        sources.append({"prefix": prefix, "path": str(path)})
    coverage = {label: sorted(row["dataset"] for row in rows) for label, rows in merged.items()}
    first = next(iter(coverage.values()))
    if any(names != first for names in coverage.values()):
        raise ValueError("dataset coverage mismatch")
    result = {"status": "PASS_MERGED_PREFIXED_ARMS", "sources": sources, "per_movie_by_arm": merged}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
