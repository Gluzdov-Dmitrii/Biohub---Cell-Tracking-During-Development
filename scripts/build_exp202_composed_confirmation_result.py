"""Compose frozen EXP201 forward local flow with frozen EXP195 reverse gate."""
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


def compose(exp195: dict, forward_flow: dict, expected_forward: int = 116) -> dict:
    flow_control = rows(forward_flow, "translation", "6bba", expected_forward)
    flow_selected = rows(forward_flow, "fixed_local_flow", "6bba", expected_forward)
    parent_forward = list(exp195["directions"]["forward"]["selected_rows"])
    if [row["dataset"] for row in flow_control] != [row["dataset"] for row in parent_forward]:
        raise ValueError("EXP201/EXP195 forward coverage mismatch")
    maximum_error = max(
        abs(float(control[key]) - float(parent[key]))
        for control, parent in zip(flow_control, parent_forward)
        for key in NUMERIC_KEYS
    )
    if maximum_error > 1e-12:
        raise ValueError("EXP201 translation control does not reproduce EXP195 forward min8")
    result = policy_result(
        "EXP202_ON_EXP192_CONFIRMATION",
        list(exp195["directions"]["forward"]["base_rows"]),
        list(exp195["directions"]["reverse"]["base_rows"]),
        flow_selected,
        list(exp195["directions"]["reverse"]["selected_rows"]),
        {"forward": "exp201_flow_k32_a050_min8", "reverse": "exp195_q75_inference_gate"},
        {},
    )
    parent_rows = parent_forward + list(exp195["directions"]["reverse"]["selected_rows"])
    result["forward_parent_control_maximum_absolute_error"] = maximum_error
    result["incremental_vs_exp195"] = {
        "parent_summary": summarise(parent_rows),
        "delta": result["combined"]["frozen_selected"]["score"] - summarise(parent_rows)["score"],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-flow", type=Path, required=True)
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
    flow = json.loads(args.forward_flow.read_text(encoding="utf-8"))
    result = compose(exp195, flow)
    result["inputs"] = [
        {"path": str(path), "sha256": sha256(path)}
        for path in [
            args.forward_flow, args.forward_base, args.policy,
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
