"""Compose frozen EXP206 forward centroid refinement with frozen EXP195 reverse gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_exp195_confirmation_result import build as build_exp195
from build_frozen_confirmation_results import policy_result, rows
from select_nested_pooled_synthetic_gap import sha256, summarise


NUMERIC_KEYS = (
    "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn",
    "num_pred_nodes", "node_recall", "total_node_ratio", "edge_jaccard", "adj_edge_jaccard",
)


def compose(exp195: dict, forward_centroid: dict, expected_forward: int = 116) -> dict:
    centroid_control = rows(forward_centroid, "translation", "6bba", expected_forward)
    centroid_selected = rows(
        forward_centroid, "intensity_centroid_r2_5_5", "6bba", expected_forward
    )
    parent_forward = list(exp195["directions"]["forward"]["selected_rows"])
    if [row["dataset"] for row in centroid_control] != [row["dataset"] for row in parent_forward]:
        raise ValueError("EXP206/EXP195 forward coverage mismatch")
    maximum_error = max(
        abs(float(control[key]) - float(parent[key]))
        for control, parent in zip(centroid_control, parent_forward)
        for key in NUMERIC_KEYS
    )
    if maximum_error > 1e-12:
        raise ValueError("EXP206 translation control does not reproduce EXP195 forward min8")
    result = policy_result(
        "EXP206_ON_EXP192_CONFIRMATION",
        list(exp195["directions"]["forward"]["base_rows"]),
        list(exp195["directions"]["reverse"]["base_rows"]),
        centroid_selected,
        list(exp195["directions"]["reverse"]["selected_rows"]),
        {"forward": "intensity_centroid_r2_5_5_min8", "reverse": "exp195_q75_inference_gate"},
        {},
    )
    parent_rows = parent_forward + list(exp195["directions"]["reverse"]["selected_rows"])
    parent_summary = summarise(parent_rows)
    result["forward_parent_control_maximum_absolute_error"] = maximum_error
    result["incremental_vs_exp195"] = {
        "parent_summary": parent_summary,
        "delta": result["combined"]["frozen_selected"]["score"] - parent_summary["score"],
    }
    result["selection_provenance"] = (
        "Forward-only arm selected on the already-open EXP205 development cohort and frozen "
        "before any EXP192 target inference; this 175-movie result is its first confirmation."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-centroid", type=Path, required=True)
    parser.add_argument("--forward-base", type=Path, required=True)
    parser.add_argument("--reverse-base-chunk", type=Path, action="append", required=True)
    parser.add_argument("--reverse-gap-chunk", type=Path, action="append", required=True)
    parser.add_argument("--reverse-gap-filtered-chunk", type=Path, action="append", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (len(args.reverse_base_chunk) == len(args.reverse_gap_chunk) == len(args.reverse_gap_filtered_chunk) == 3):
        parser.error("exactly three reverse chunks of each kind are required")
    exp195 = build_exp195(
        args.forward_base, args.reverse_base_chunk, args.reverse_gap_chunk,
        args.reverse_gap_filtered_chunk, args.policy,
    )
    centroid = json.loads(args.forward_centroid.read_text(encoding="utf-8"))
    result = compose(exp195, centroid)
    result["inputs"] = [
        {"path": str(path), "sha256": sha256(path)}
        for path in [
            args.forward_centroid, args.forward_base, args.policy,
            *args.reverse_base_chunk, *args.reverse_gap_chunk, *args.reverse_gap_filtered_chunk,
        ]
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "combined": result["combined"],
        "incremental_vs_exp195": result["incremental_vs_exp195"],
    }, indent=2))


if __name__ == "__main__":
    main()
