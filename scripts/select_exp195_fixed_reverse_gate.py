"""Evaluate one fixed reverse inference-time gate with nested q75 thresholds."""
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
from select_nested_pooled_synthetic_gap import sha256, summarise


def direction_block(base_path: Path, gap_path: Path, gap_filtered_path: Path, direction: str) -> dict:
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    gap_payload = json.loads(gap_path.read_text(encoding="utf-8"))
    gap_filtered = json.loads(gap_filtered_path.read_text(encoding="utf-8"))
    base_arm, gap_arm = ("min8", "min8") if direction == "forward" else ("min3", "min6")
    raw_base = rows_by_name(base_payload, "no_filter")
    control = numeric_control(raw_base, rows_by_name(gap_payload, "registered_hungarian"))
    if control > TOLERANCE:
        raise ValueError(f"{direction}: baseline control failed")
    base = rows_by_name(base_payload, base_arm)
    gap = rows_by_name(gap_filtered, gap_arm)
    if sorted(base) != sorted(gap) or len(base) != 12:
        raise ValueError(f"{direction}: coverage mismatch")
    names = sorted(base)
    selected, selections = [], []
    features = build_features(base_payload, gap_payload, base_arm)
    for held_out in names:
        if direction == "forward":
            use_gap, threshold = False, None
        else:
            train = [features[name]["base_pruned_node_fraction"] for name in names if name != held_out]
            threshold = percentile(train, 0.75)
            use_gap = features[held_out]["base_pruned_node_fraction"] <= threshold
        selected.append(gap[held_out] if use_gap else base[held_out])
        selections.append({
            "dataset": held_out,
            "selected_graph": "gap" if use_gap else "base",
            "feature": features[held_out]["base_pruned_node_fraction"],
            "train_q75_threshold": threshold,
        })
    base_rows = [base[name] for name in names]
    return {
        "direction": direction,
        "baseline_control_maximum_absolute_error": control,
        "base_rows": base_rows,
        "selected_rows": selected,
        "selections": selections,
        "base_summary": summarise(base_rows),
        "nested_selected_summary": summarise(selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-forward", type=Path, required=True)
    parser.add_argument("--base-reverse", type=Path, required=True)
    parser.add_argument("--gap-forward", type=Path, required=True)
    parser.add_argument("--gap-forward-filtered", type=Path, required=True)
    parser.add_argument("--gap-reverse", type=Path, required=True)
    parser.add_argument("--gap-reverse-filtered", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    forward = direction_block(args.base_forward, args.gap_forward, args.gap_forward_filtered, "forward")
    reverse = direction_block(args.base_reverse, args.gap_reverse, args.gap_reverse_filtered, "reverse")
    all_base = forward["base_rows"] + reverse["base_rows"]
    all_selected = forward["selected_rows"] + reverse["selected_rows"]
    base_summary, selected_summary = summarise(all_base), summarise(all_selected)
    result = {
        "status": "PASS_EXP195_FIXED_REVERSE_GATE",
        "protocol": "Forward always base; reverse gap iff held-out inference feature <= q75 from the other 11 reverse movies.",
        "directions": {"forward": forward, "reverse": reverse},
        "combined": {"base": base_summary, "nested_selected": selected_summary, "delta": selected_summary["score"] - base_summary["score"]},
        "inputs": {key: {"path": str(value), "sha256": sha256(value)} for key, value in vars(args).items() if key != "output"},
        "evidence_class": "Sequentially exploratory nested development OOF.",
        "eligible_for_kaggle_submission": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"directions": {name: block["nested_selected_summary"] for name, block in result["directions"].items()}, "combined": result["combined"]}, indent=2))


if __name__ == "__main__":
    main()
