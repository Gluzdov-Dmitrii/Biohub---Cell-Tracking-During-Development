"""Verify cached graph no-filter metrics exactly reproduce their source evaluation arm."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cached-result", type=Path, required=True)
    parser.add_argument("--source-result", type=Path, required=True)
    parser.add_argument("--source-arm", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cached = json.loads(args.cached_result.read_text(encoding="utf-8"))["per_movie_by_arm"]["no_filter"]
    source = json.loads(args.source_result.read_text(encoding="utf-8"))["per_movie_by_arm"][args.source_arm]
    cached_rows = {row["dataset"]: row for row in cached}
    source_rows = {row["dataset"]: row for row in source}
    if sorted(cached_rows) != sorted(source_rows):
        raise AssertionError("dataset coverage mismatch")
    maximum_error = 0.0
    for dataset in sorted(source_rows):
        if set(cached_rows[dataset]) != set(source_rows[dataset]):
            raise AssertionError((dataset, sorted(cached_rows[dataset]), sorted(source_rows[dataset])))
        for key in sorted(set(source_rows[dataset]) - {"dataset"}):
            a, b = cached_rows[dataset][key], source_rows[dataset][key]
            if isinstance(a, int) and isinstance(b, int):
                if a != b:
                    raise AssertionError((dataset, key, a, b))
            elif math.isnan(float(a)) and math.isnan(float(b)):
                continue
            else:
                error = abs(float(a) - float(b))
                maximum_error = max(maximum_error, error)
                if error > 1e-12:
                    raise AssertionError((dataset, key, a, b, error))
    result = {
        "status": "PASS_EXACT_CACHED_ARM_REPRODUCTION",
        "movies": len(source_rows),
        "source_arm": args.source_arm,
        "maximum_absolute_error": maximum_error,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
