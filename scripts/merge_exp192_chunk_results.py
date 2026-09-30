"""Merge immutable EXP192 chunk metrics after all chunks have completed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from select_nested_pooled_synthetic_gap import summarise


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge(paths: list[Path], expected_count: int, prefix: str) -> dict:
    if not paths:
        raise ValueError("no chunk inputs")
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    arm_sets = [set(payload["per_movie_by_arm"]) for payload in payloads]
    if any(arms != arm_sets[0] for arms in arm_sets[1:]):
        raise ValueError("chunk arm sets differ")
    merged = {arm: [] for arm in sorted(arm_sets[0])}
    for payload in payloads:
        for arm in merged:
            merged[arm].extend(payload["per_movie_by_arm"][arm])
    for arm, rows in merged.items():
        names = [str(row["dataset"]) for row in rows]
        if len(names) != expected_count or len(set(names)) != expected_count:
            raise ValueError(f"{arm}: expected {expected_count} unique movies")
        if any(not name.startswith(prefix + "_") for name in names):
            raise ValueError(f"{arm}: wrong prefix")
        merged[arm] = sorted(rows, key=lambda row: str(row["dataset"]))
    return {
        "status": "PASS_EXP192_CHUNK_MERGE",
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in paths],
        "per_movie_by_arm": merged,
        "summary_by_arm": {arm: summarise(rows) for arm, rows in merged.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    parser.add_argument("--prefix", choices=("44b6", "6bba"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = merge(args.input, args.expected_count, args.prefix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary_by_arm"], indent=2))


if __name__ == "__main__":
    main()
