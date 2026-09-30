"""Apply the frozen reciprocal target-OOF gate for EXP183."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def evaluate_gate(results: dict[str, dict]) -> dict:
    directions: dict[str, dict] = {}
    all_score_deltas: list[float] = []
    all_recall_deltas: list[float] = []
    weighted_base = 0.0
    weighted_gated = 0.0
    total_movies = 0

    for direction, result in results.items():
        summary = result["summary_by_arm"]
        base = summary["registered_hungarian"]
        raw = summary["synthetic_gap_no_veto"]
        gated = summary["synthetic_gap_deepcenter"]
        n_movies = int(gated["n"])
        if int(base["n"]) != n_movies or int(raw["n"]) != n_movies:
            raise ValueError(f"arm movie-count mismatch in {direction}")

        base_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["registered_hungarian"]}
        gated_rows = {row["dataset"]: row for row in result["per_movie_by_arm"]["synthetic_gap_deepcenter"]}
        if set(base_rows) != set(gated_rows) or len(base_rows) != n_movies:
            raise ValueError(f"per-movie coverage mismatch in {direction}")

        movie_score_delta: dict[str, float] = {}
        movie_recall_delta: dict[str, float] = {}
        for movie in sorted(base_rows):
            score_delta = float(gated_rows[movie]["adj_edge_jaccard"]) - float(
                base_rows[movie]["adj_edge_jaccard"]
            )
            recall_delta = float(gated_rows[movie]["node_recall"]) - float(
                base_rows[movie]["node_recall"]
            )
            movie_score_delta[movie] = score_delta
            movie_recall_delta[movie] = recall_delta
            all_score_deltas.append(score_delta)
            all_recall_deltas.append(recall_delta)

        base_score = float(base["score"])
        raw_score = float(raw["score"])
        gated_score = float(gated["score"])
        checked = sum(int(row["deepcenter"]["deepcenter_checked"]) for row in result["telemetry"])
        accepted = sum(int(row["deepcenter"]["synthetic_added"]) for row in result["telemetry"])
        weighted_base += n_movies * base_score
        weighted_gated += n_movies * gated_score
        total_movies += n_movies
        directions[direction] = {
            "n_movies": n_movies,
            "base_score": base_score,
            "no_veto_score": raw_score,
            "deepcenter_score": gated_score,
            "deepcenter_minus_base": gated_score - base_score,
            "deepcenter_minus_no_veto": gated_score - raw_score,
            "deepcenter_checked": checked,
            "synthetic_added": accepted,
            "positive_movie_count": sum(delta > 0 for delta in movie_score_delta.values()),
            "zero_movie_count": sum(delta == 0 for delta in movie_score_delta.values()),
            "worst_movie_score_delta": min(movie_score_delta.values()),
            "worst_movie_recall_delta": min(movie_recall_delta.values()),
            "per_movie_score_delta": movie_score_delta,
            "per_movie_recall_delta": movie_recall_delta,
        }

    pooled_base = weighted_base / total_movies
    pooled_gated = weighted_gated / total_movies
    gates = {
        "exactly_12_movies_each_embryo": all(row["n_movies"] == 12 for row in directions.values()),
        "model_exercised_each_embryo": all(row["deepcenter_checked"] > 0 for row in directions.values()),
        "synthetic_added_each_embryo": all(row["synthetic_added"] > 0 for row in directions.values()),
        "strict_score_gain_each_embryo": all(row["deepcenter_minus_base"] > 0 for row in directions.values()),
        "strict_pooled_score_gain": pooled_gated > pooled_base,
        "nonnegative_score_each_movie": all(delta >= 0 for delta in all_score_deltas),
        "nonnegative_recall_each_movie": all(delta >= 0 for delta in all_recall_deltas),
        "veto_not_worse_than_no_veto_each_embryo": all(
            row["deepcenter_minus_no_veto"] >= 0 for row in directions.values()
        ),
    }
    passed = all(gates.values())
    return {
        "status": "PASS_TARGET_OOF_GATE" if passed else "REJECT_TARGET_OOF_GATE",
        "eligible_for_private_robust_runtime_candidate": passed,
        "eligible_for_kaggle_submission": False,
        "pooled": {
            "n_movies": total_movies,
            "base_score": pooled_base,
            "deepcenter_score": pooled_gated,
            "deepcenter_minus_base": pooled_gated - pooled_base,
            "worst_movie_score_delta": min(all_score_deltas),
            "worst_movie_recall_delta": min(all_recall_deltas),
        },
        "directions": directions,
        "gates": gates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_gate(
        {
            "44b6_to_6bba_target": json.loads(args.forward.read_text(encoding="utf-8")),
            "6bba_to_44b6_target": json.loads(args.reverse.read_text(encoding="utf-8")),
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
