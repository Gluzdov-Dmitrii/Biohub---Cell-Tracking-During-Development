"""Verify that EXP187 no-filter arms exactly reproduce frozen EXP152 rows."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def compare(observed_path: Path, parent_path: Path) -> dict:
    observed = json.loads(observed_path.read_text(encoding="utf-8"))["per_movie_by_arm"]["no_filter"]
    parent = json.loads(parent_path.read_text(encoding="utf-8"))["per_movie_by_arm"]["registered_hungarian"]
    observed_rows = {row["dataset"]: row for row in observed}
    parent_rows = {row["dataset"]: row for row in parent}
    if sorted(observed_rows) != sorted(parent_rows):
        raise AssertionError("dataset coverage mismatch")
    maximum_error = 0.0
    for dataset in sorted(parent_rows):
        if set(observed_rows[dataset]) != set(parent_rows[dataset]):
            raise AssertionError((dataset, sorted(observed_rows[dataset]), sorted(parent_rows[dataset])))
        for metric in sorted(set(parent_rows[dataset]) - {"dataset"}):
            a, b = observed_rows[dataset][metric], parent_rows[dataset][metric]
            if isinstance(a, int) and isinstance(b, int):
                if a != b:
                    raise AssertionError((dataset, metric, a, b))
            elif math.isnan(float(a)) and math.isnan(float(b)):
                continue
            else:
                error = abs(float(a) - float(b))
                maximum_error = max(maximum_error, error)
                if error > 1e-12:
                    raise AssertionError((dataset, metric, a, b, error))
    return {"movies": len(parent_rows), "maximum_absolute_error": maximum_error}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--forward-parent", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--reverse-parent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "status": "PASS_EXACT_EXP152_CONTROL_REPRODUCTION",
        "tolerance": 1e-12,
        "forward": compare(args.forward, args.forward_parent),
        "reverse": compare(args.reverse, args.reverse_parent),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
