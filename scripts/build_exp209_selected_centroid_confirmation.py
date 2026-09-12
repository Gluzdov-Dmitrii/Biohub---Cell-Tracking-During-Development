"""Assemble preregistered EXP209 selected-centroid confirmation policies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_frozen_confirmation_results import policy_result, rows
from select_nested_pooled_synthetic_gap import sha256


NUMERIC_KEYS = (
    "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn",
    "num_pred_nodes", "node_recall", "total_node_ratio", "edge_jaccard", "adj_edge_jaccard",
)


def maximum_row_error(left: list[dict], right: list[dict]) -> float:
    if [row["dataset"] for row in left] != [row["dataset"] for row in right]:
        raise ValueError("paired control coverage mismatch")
    return max(
        abs(float(a[key]) - float(b[key]))
        for a, b in zip(left, right)
        for key in NUMERIC_KEYS
    )


def build(forward, reverse, exp190, exp191, exp195, exp206, inputs):
    forward_control = rows(forward, "translation", "6bba", 116)
    forward_selected = rows(forward, "intensity_centroid_r3_5_5", "6bba", 116)
    reverse_control = rows(reverse, "translation", "44b6", 59)
    reverse_selected = rows(reverse, "intensity_centroid_r2_3_3", "44b6", 59)
    control_error = max(
        maximum_row_error(forward_control, list(exp190["directions"]["forward"]["selected_rows"])),
        maximum_row_error(reverse_control, list(exp190["directions"]["reverse"]["selected_rows"])),
    )
    if control_error > 1e-12:
        raise ValueError("EXP209 translation control does not reproduce EXP190 min8/min3")

    forward_base = list(exp190["directions"]["forward"]["base_rows"])
    reverse_base = list(exp190["directions"]["reverse"]["base_rows"])
    policies = {
        "both_selected": (forward_selected, reverse_selected, {
            "forward": "source_selected_centroid_r3_5_5_min8",
            "reverse": "source_selected_centroid_r2_3_3_min3",
        }),
        "forward_plus_exp191": (forward_selected, list(exp191["directions"]["reverse"]["selected_rows"]), {
            "forward": "source_selected_centroid_r3_5_5_min8",
            "reverse": "exp191_gap_g45_t20_min6",
        }),
        "forward_plus_exp195": (forward_selected, list(exp195["directions"]["reverse"]["selected_rows"]), {
            "forward": "source_selected_centroid_r3_5_5_min8",
            "reverse": "exp195_q75_inference_gate",
        }),
    }
    output = {}
    for key, (selected_forward, selected_reverse, labels) in policies.items():
        result = policy_result(
            f"EXP209_{key.upper()}_ON_EXP192_CONFIRMATION",
            forward_base, reverse_base, selected_forward, selected_reverse, labels, inputs,
        )
        result["protocol"] = (
            "Centroid radii were selected only on the two reciprocal source checkpoint-validation "
            "movies per direction in EXP208, then frozen before these radius arms were evaluated "
            "on the 175-movie confirmation cohort. The radius family itself is development-adapted."
        )
        result["selection_provenance"] = {
            "forward_radius_zyx_voxels": [3, 5, 5],
            "reverse_radius_zyx_voxels": [2, 3, 3],
            "selection_scope": "EXP208 source checkpoint-validation movies only",
            "confirmation_radius_metrics_open_before_freeze": False,
        }
        result["translation_control_maximum_absolute_error"] = control_error
        result["incremental_vs_exp206_score"] = (
            result["combined"]["frozen_selected"]["score"]
            - float(exp206["combined"]["frozen_selected"]["score"])
        )
        output[key] = result
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("forward", "reverse", "exp190", "exp191", "exp195", "exp206"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--both-output", type=Path, required=True)
    parser.add_argument("--exp191-output", type=Path, required=True)
    parser.add_argument("--exp195-output", type=Path, required=True)
    args = parser.parse_args()
    paths = {name: getattr(args, name) for name in ("forward", "reverse", "exp190", "exp191", "exp195", "exp206")}
    payloads = {key: json.loads(path.read_text(encoding="utf-8")) for key, path in paths.items()}
    inputs = {key: {"path": str(path), "sha256": sha256(path)} for key, path in paths.items()}
    results = build(*(payloads[name] for name in ("forward", "reverse", "exp190", "exp191", "exp195", "exp206")), inputs)
    outputs = {
        "both_selected": args.both_output,
        "forward_plus_exp191": args.exp191_output,
        "forward_plus_exp195": args.exp195_output,
    }
    for key, path in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(results[key], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: {
        "score": value["combined"]["frozen_selected"]["score"],
        "delta_vs_raw_base": value["combined"]["delta"],
        "delta_vs_exp206": value["incremental_vs_exp206_score"],
    } for key, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()
