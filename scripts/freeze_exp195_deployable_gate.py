"""Freeze the EXP195 reverse q75 gate on all 12 development movies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_exp194_nested_inference_gate import (
    TOLERANCE,
    build_features,
    numeric_control,
    percentile,
    rows_by_name,
)
from select_nested_pooled_synthetic_gap import sha256


def freeze(base_path: Path, gap_path: Path) -> dict:
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    gap_payload = json.loads(gap_path.read_text(encoding="utf-8"))
    control = numeric_control(
        rows_by_name(base_payload, "no_filter"),
        rows_by_name(gap_payload, "registered_hungarian"),
    )
    if control > TOLERANCE:
        raise ValueError("registered baseline control failed")
    features = build_features(base_payload, gap_payload, "min3")
    if len(features) != 12 or any(not name.startswith("44b6_") for name in features):
        raise ValueError("expected 12 reverse-development movies")
    values = [row["base_pruned_node_fraction"] for row in features.values()]
    threshold = percentile(values, 0.75)
    return {
        "status": "PASS_EXP195_DEPLOYABLE_GATE_FREEZE",
        "trained_on": "12 previously opened reverse-development 44b6 target movies",
        "feature": "base_pruned_node_fraction",
        "feature_definition": "EXP190 min3 nodes_removed / max(base no-filter num_pred_nodes, 1)",
        "operator": "less_than_or_equal",
        "threshold_method": "linear-interpolated q75 over all 12 development feature values",
        "threshold": threshold,
        "when_true": "choose g45_t20 synthetic-gap graph followed by min6",
        "when_false": "choose base graph followed by min3",
        "forward_policy": "always base graph followed by min8",
        "baseline_control_maximum_absolute_error": control,
        "development_movies": 12,
        "inputs": {
            "base_reverse": {"path": str(base_path), "sha256": sha256(base_path)},
            "gap_reverse": {"path": str(gap_path), "sha256": sha256(gap_path)},
        },
        "anti_adaptation": "Threshold is frozen before any EXP192 target inference or metric is available.",
        "eligible_for_kaggle_submission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-reverse", type=Path, required=True)
    parser.add_argument("--gap-reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.base_reverse, args.gap_reverse)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
