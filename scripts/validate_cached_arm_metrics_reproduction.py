"""Fail closed unless two fixed per-movie metric arms reproduce exactly."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256


NUMERIC_FIELDS = (
    "edge_tp",
    "edge_fp",
    "edge_fn",
    "division_tp",
    "division_fp",
    "division_fn",
    "num_pred_nodes",
    "node_recall",
    "total_node_ratio",
    "edge_jaccard",
    "adj_edge_jaccard",
)


def arm_rows(payload: dict, arm: str) -> dict[str, dict]:
    try:
        rows = list(payload["per_movie_by_arm"][arm])
    except KeyError as error:
        raise ValueError(f"missing arm {arm}") from error
    result = {str(row["dataset"]): row for row in rows}
    if len(result) != len(rows) or not result:
        raise ValueError(f"{arm}: empty or duplicate movie rows")
    return result


def compare(reference: dict, candidate: dict, reference_arm: str, candidate_arm: str) -> dict:
    expected = arm_rows(reference, reference_arm)
    actual = arm_rows(candidate, candidate_arm)
    if sorted(expected) != sorted(actual):
        raise ValueError("movie coverage mismatch")
    maximum_error = 0.0
    for movie in sorted(expected):
        for field in NUMERIC_FIELDS:
            left = float(expected[movie][field])
            right = float(actual[movie][field])
            if not math.isfinite(left) or not math.isfinite(right):
                if not (math.isnan(left) and math.isnan(right)):
                    raise ValueError(f"{movie}/{field}: nonmatching nonfinite values")
                continue
            maximum_error = max(maximum_error, abs(left - right))
    if maximum_error > 1e-12:
        raise ValueError(f"maximum absolute metric error {maximum_error} exceeds 1e-12")
    return {
        "status": "PASS_EXACT_CACHED_ARM_METRIC_REPRODUCTION",
        "movies": len(expected),
        "reference_arm": reference_arm,
        "candidate_arm": candidate_arm,
        "maximum_absolute_error": maximum_error,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference-arm", required=True)
    parser.add_argument("--candidate-arm", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(
        json.loads(args.reference.read_text(encoding="utf-8")),
        json.loads(args.candidate.read_text(encoding="utf-8")),
        args.reference_arm,
        args.candidate_arm,
    )
    result["inputs"] = {
        "reference": {"path": str(args.reference), "sha256": sha256(args.reference)},
        "candidate": {"path": str(args.candidate), "sha256": sha256(args.candidate)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
