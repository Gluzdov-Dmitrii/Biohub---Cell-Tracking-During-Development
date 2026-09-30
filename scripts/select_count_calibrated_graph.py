"""Select a complete graph using only closeness to the provided node-count estimate."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


COUNT_KEYS = (
    "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarise(rows: list[dict]) -> dict:
    totals = {key: sum(int(row[key]) for row in rows) for key in COUNT_KEYS}
    edge_denominator = totals["edge_tp"] + totals["edge_fp"] + totals["edge_fn"]
    edge_jaccard = totals["edge_tp"] / edge_denominator if edge_denominator else math.nan
    division_denominator = (
        totals["division_tp"] + totals["division_fp"] + totals["division_fn"]
    )
    division_jaccard = (
        totals["division_tp"] / division_denominator if division_denominator else math.nan
    )
    weights = [int(row["edge_tp"]) + int(row["edge_fp"]) + int(row["edge_fn"]) for row in rows]
    total_weight = sum(weights)
    adjusted = (
        sum(weight * float(row["adj_edge_jaccard"]) for weight, row in zip(weights, rows))
        / total_weight
        if total_weight
        else math.nan
    )
    score = adjusted if math.isnan(division_jaccard) else adjusted + 0.1 * division_jaccard
    return {
        **totals,
        "n": len(rows),
        "edge_jaccard": edge_jaccard,
        "division_jaccard": division_jaccard,
        "node_recall": sum(float(row["node_recall"]) for row in rows) / len(rows),
        "adj_edge_jaccard": adjusted,
        "score": score,
    }


def select_direction(payload: dict, baseline_arm: str) -> dict:
    arms = payload["per_movie_by_arm"]
    if baseline_arm not in arms:
        raise ValueError(f"missing baseline arm {baseline_arm}")
    rows_by_arm = {
        arm: {str(row["dataset"]): row for row in rows}
        for arm, rows in arms.items()
    }
    datasets = set(rows_by_arm[baseline_arm])
    if len(datasets) != 12:
        raise ValueError("expected 12 baseline movies")
    for arm, rows in rows_by_arm.items():
        if set(rows) != datasets:
            raise ValueError(f"{arm}: movie set differs")
    selected_rows = []
    selections = []
    for dataset in sorted(datasets):
        ranked = sorted(
            rows_by_arm,
            key=lambda arm: (
                abs(float(rows_by_arm[arm][dataset]["total_node_ratio"])),
                arm != baseline_arm,
                arm,
            ),
        )
        selected_arm = ranked[0]
        selected_rows.append(rows_by_arm[selected_arm][dataset])
        selections.append(
            {
                "dataset": dataset,
                "selected_arm": selected_arm,
                "selected_total_node_ratio": float(
                    rows_by_arm[selected_arm][dataset]["total_node_ratio"]
                ),
                "baseline_total_node_ratio": float(
                    rows_by_arm[baseline_arm][dataset]["total_node_ratio"]
                ),
            }
        )
    base_rows = [rows_by_arm[baseline_arm][dataset] for dataset in sorted(datasets)]
    return {
        "base_rows": base_rows,
        "selected_rows": selected_rows,
        "selections": selections,
        "base_summary": summarise(base_rows),
        "nested_selected_summary": summarise(selected_rows),
    }


def select(forward: dict, reverse: dict, forward_base: str, reverse_base: str) -> dict:
    directions = {
        "forward": select_direction(forward, forward_base),
        "reverse": select_direction(reverse, reverse_base),
    }
    base = summarise(
        directions["forward"]["base_rows"] + directions["reverse"]["base_rows"]
    )
    selected = summarise(
        directions["forward"]["selected_rows"]
        + directions["reverse"]["selected_rows"]
    )
    delta = selected["score"] - base["score"]
    return {
        "status": "PASS_COUNT_CALIBRATED_GAIN" if delta > 0 else "REJECT_COUNT_CALIBRATED_GAIN",
        "policy": "Choose the complete graph whose total_node_ratio is closest to zero; ties prefer the registered baseline.",
        "directions": directions,
        "combined": {"base": base, "nested_selected": selected, "delta": delta},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--forward-base", required=True)
    parser.add_argument("--reverse-base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = select(
        json.loads(args.forward.read_text(encoding="utf-8")),
        json.loads(args.reverse.read_text(encoding="utf-8")),
        args.forward_base,
        args.reverse_base,
    )
    result["inputs"] = {
        "forward": {"path": str(args.forward), "sha256": sha256(args.forward)},
        "reverse": {"path": str(args.reverse), "sha256": sha256(args.reverse)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
