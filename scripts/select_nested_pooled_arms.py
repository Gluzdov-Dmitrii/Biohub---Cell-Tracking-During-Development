"""Nested leave-one-movie-out selection among arms in reciprocal OOF JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


def select(payload: dict, direction: str, base_arm: str, candidate_arms: list[str]) -> dict:
    all_arms = payload["per_movie_by_arm"]
    labels = sorted(candidate_arms)
    if base_arm not in all_arms or any(label not in all_arms for label in labels):
        raise ValueError(f"{direction}: missing requested arm")
    rows = {label: {row["dataset"]: row for row in all_arms[label]} for label in labels}
    base = {row["dataset"]: row for row in all_arms[base_arm]}
    datasets = sorted(base)
    if len(datasets) < 3 or any(sorted(rows[label]) != datasets for label in labels):
        raise ValueError(f"{direction}: invalid dataset coverage")
    selected_rows, selections = [], []
    for held_out in datasets:
        development = [name for name in datasets if name != held_out]
        scores = {
            label: summarise([rows[label][name] for name in development])["score"]
            for label in labels
        }
        chosen = max(labels, key=lambda label: (scores[label], label))
        selected = rows[chosen][held_out]
        selected_rows.append(selected)
        selections.append({
            "held_out_dataset": held_out,
            "selected_arm": chosen,
            "development_scores": scores,
            "held_out_delta": float(selected["adj_edge_jaccard"]) - float(base[held_out]["adj_edge_jaccard"]),
        })
    return {
        "direction": direction,
        "base_rows": [base[name] for name in datasets],
        "selected_rows": selected_rows,
        "selections": selections,
        "base_summary": summarise([base[name] for name in datasets]),
        "nested_selected_summary": summarise(selected_rows),
        "full_data_arm_scores_diagnostic_only": {
            label: summarise([rows[label][name] for name in datasets])["score"] for label in labels
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--base-arm", required=True)
    parser.add_argument("--candidate-arm", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    forward_payload = json.loads(args.forward.read_text(encoding="utf-8"))
    reverse_payload = json.loads(args.reverse.read_text(encoding="utf-8"))
    forward = select(forward_payload, "44b6_to_6bba", args.base_arm, args.candidate_arm)
    reverse = select(reverse_payload, "6bba_to_44b6", args.base_arm, args.candidate_arm)
    base = summarise(forward["base_rows"] + reverse["base_rows"])
    selected = summarise(forward["selected_rows"] + reverse["selected_rows"])
    result = {
        "status": "PASS_NESTED_POOLED_GAIN" if selected["score"] > base["score"] else "REJECT_NESTED_POOLED_GAIN",
        "protocol": "Exploratory leave-one-movie-out arm selection within each reciprocal target direction.",
        "primary_metric": "combined_nested_pooled_score",
        "inputs": {
            "forward": {"path": str(args.forward), "sha256": sha256(args.forward)},
            "reverse": {"path": str(args.reverse), "sha256": sha256(args.reverse)},
        },
        "base_arm": args.base_arm,
        "candidate_arms": sorted(args.candidate_arm),
        "directions": {"forward": forward, "reverse": reverse},
        "combined": {
            "base": base,
            "nested_selected": selected,
            "delta": selected["score"] - base["score"],
            "negative_movie_count": sum(
                item["held_out_delta"] < 0
                for direction in (forward, reverse)
                for item in direction["selections"]
            ),
        },
        "eligible_for_kaggle_submission": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "combined": result["combined"]}, indent=2))


if __name__ == "__main__":
    main()
