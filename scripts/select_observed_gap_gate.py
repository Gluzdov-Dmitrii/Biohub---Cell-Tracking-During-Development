"""Apply the frozen two-embryo source gate for EXP179."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def select_gate(results: dict[str, dict]) -> dict:
    directions = {}
    all_movie_deltas = []
    changed = False
    for direction, result in results.items():
        summaries = result["summary_by_arm"]
        base = float(summaries["registered_hungarian"]["score"])
        fixed = float(summaries["fixed_observed_gap"]["score"])
        adaptive = float(summaries["adaptive_observed_gap"]["score"])
        base_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["registered_hungarian"]}
        adaptive_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["adaptive_observed_gap"]}
        movie_deltas = {
            name: float(adaptive_rows[name]["adj_edge_jaccard"]) - float(row["adj_edge_jaccard"])
            for name, row in base_rows.items()
        }
        all_movie_deltas.extend(movie_deltas.values())
        changed = changed or any(
            int(item["adaptive"]["added_edges"]) != int(item["fixed"]["added_edges"])
            or int(item["adaptive"]["density_candidates_expanded"]) > 0
            or int(item["adaptive"]["density_candidates_restricted"]) > 0
            for item in result["telemetry"]
        )
        directions[direction] = {
            "base_score": base,
            "fixed_score": fixed,
            "adaptive_score": adaptive,
            "adaptive_minus_base": adaptive - base,
            "adaptive_minus_fixed": adaptive - fixed,
            "per_movie_adaptive_minus_base": movie_deltas,
        }
    passed = (
        changed
        and all(row["adaptive_minus_base"] > 0.0 for row in directions.values())
        and all(row["adaptive_minus_fixed"] >= 0.0 for row in directions.values())
        and all(delta >= 0.0 for delta in all_movie_deltas)
    )
    return {
        "status": "PASS_SOURCE_GATE" if passed else "REJECT_SOURCE_GATE",
        "eligible_for_reciprocal_official24": passed,
        "density_rule_changed_candidates": changed,
        "directions": directions,
        "gate": {
            "adaptive_positive_each_embryo": True,
            "adaptive_nonnegative_each_movie": True,
            "adaptive_not_worse_than_fixed_each_embryo": True,
            "density_rule_must_change_candidates": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = {
        "44b6_source": json.loads(args.forward.read_text(encoding="utf-8")),
        "6bba_source": json.loads(args.reverse.read_text(encoding="utf-8")),
    }
    selected = select_gate(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(selected, indent=2))


if __name__ == "__main__":
    main()
