"""Apply the frozen two-embryo source gate for EXP181."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_gate(results: dict[str, dict]) -> dict:
    directions = {}
    all_score_deltas = []
    all_recall_deltas = []
    for direction, result in results.items():
        summary = result["summary_by_arm"]
        base_score = float(summary["registered_hungarian"]["score"])
        raw_score = float(summary["synthetic_gap_no_veto"]["score"])
        gated_score = float(summary["synthetic_gap_deepcenter"]["score"])
        base_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["registered_hungarian"]}
        gated_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["synthetic_gap_deepcenter"]}
        movie_score_delta = {}
        movie_recall_delta = {}
        for movie, base in base_rows.items():
            gated = gated_rows[movie]
            score_delta = float(gated["adj_edge_jaccard"]) - float(base["adj_edge_jaccard"])
            recall_delta = float(gated["node_recall"]) - float(base["node_recall"])
            movie_score_delta[movie] = score_delta
            movie_recall_delta[movie] = recall_delta
            all_score_deltas.append(score_delta)
            all_recall_deltas.append(recall_delta)
        checked = sum(int(row["deepcenter"]["deepcenter_checked"]) for row in result["telemetry"])
        accepted = sum(int(row["deepcenter"]["synthetic_added"]) for row in result["telemetry"])
        directions[direction] = {
            "base_score": base_score,
            "no_veto_score": raw_score,
            "deepcenter_score": gated_score,
            "deepcenter_minus_base": gated_score - base_score,
            "deepcenter_minus_no_veto": gated_score - raw_score,
            "deepcenter_checked": checked,
            "synthetic_added": accepted,
            "per_movie_score_delta": movie_score_delta,
            "per_movie_recall_delta": movie_recall_delta,
        }
    gates = {
        "model_exercised_each_embryo": all(row["deepcenter_checked"] > 0 for row in directions.values()),
        "synthetic_added_each_embryo": all(row["synthetic_added"] > 0 for row in directions.values()),
        "strict_score_gain_each_embryo": all(row["deepcenter_minus_base"] > 0 for row in directions.values()),
        "nonnegative_score_each_movie": all(delta >= 0 for delta in all_score_deltas),
        "nonnegative_recall_each_movie": all(delta >= 0 for delta in all_recall_deltas),
        "veto_not_worse_than_no_veto_each_embryo": all(
            row["deepcenter_minus_no_veto"] >= 0 for row in directions.values()
        ),
    }
    passed = all(gates.values())
    return {
        "status": "PASS_SOURCE_GATE" if passed else "REJECT_SOURCE_GATE",
        "eligible_for_reciprocal_target_oof": passed,
        "eligible_for_kaggle_submission": False,
        "directions": directions,
        "gates": gates,
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
    result = evaluate_gate(results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
