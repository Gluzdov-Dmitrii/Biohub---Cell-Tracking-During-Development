"""Nested movie-level gate between pruning-only and gap-plus-pruning graphs."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


TOLERANCE = 1e-12
QUANTILES = (0.25, 0.5, 0.75)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def rows_by_name(payload: dict, arm: str) -> dict[str, dict]:
    rows = payload["per_movie_by_arm"][arm]
    return {str(row["dataset"]): row for row in rows}


def telemetry_by_name(payload: dict) -> dict[str, dict]:
    return {str(row["dataset"]): row for row in payload["telemetry"]}


def numeric_control(left: dict[str, dict], right: dict[str, dict]) -> float:
    if sorted(left) != sorted(right):
        raise ValueError("control movie coverage mismatch")
    maximum = 0.0
    for name in left:
        if set(left[name]) != set(right[name]):
            raise ValueError("control row schemas differ")
        for key in left[name]:
            if key != "dataset":
                maximum = max(maximum, abs(float(left[name][key]) - float(right[name][key])))
    return maximum


def build_features(base_payload: dict, gap_payload: dict, base_arm: str) -> dict[str, dict[str, float]]:
    base_rows = rows_by_name(base_payload, "no_filter")
    base_telemetry = telemetry_by_name(base_payload)
    gap_telemetry = telemetry_by_name(gap_payload)
    if set(base_rows) != set(base_telemetry) or set(base_rows) != set(gap_telemetry):
        raise ValueError("feature telemetry coverage mismatch")
    result = {}
    for name, row in base_rows.items():
        denominator = max(float(row["num_pred_nodes"]), 1.0)
        deep = gap_telemetry[name]["deepcenter"]
        checked = max(float(deep["deepcenter_checked"]), 1.0)
        values = {
            "synthetic_added_rate": float(deep["synthetic_added"]) / denominator,
            "deepcenter_accept_rate": float(deep["deepcenter_accepted"]) / checked,
            "endpoint_selected_rate": float(deep["endpoint_pairs_selected"]) / denominator,
            "base_pruned_node_fraction": float(base_telemetry[name]["variants"][base_arm]["nodes_removed"]) / denominator,
        }
        if any(not math.isfinite(value) or value < 0.0 for value in values.values()):
            raise ValueError(f"{name}: invalid inference feature")
        result[name] = values
    return result


def choose_rule(train_names: list[str], features: dict[str, dict[str, float]], base: dict, gap: dict) -> dict:
    candidates = [{"label": "always_base", "priority": 0, "feature": None, "operator": None, "threshold": None}]
    candidates.append({"label": "always_gap", "priority": 1, "feature": None, "operator": None, "threshold": None})
    for feature in sorted(next(iter(features.values()))):
        values = [features[name][feature] for name in train_names]
        for q in QUANTILES:
            threshold = percentile(values, q)
            for operator in ("le", "gt"):
                candidates.append({
                    "label": f"{feature}_{operator}_q{int(q * 100)}",
                    "priority": 2,
                    "feature": feature,
                    "operator": operator,
                    "threshold": threshold,
                })
    scored = []
    for rule in candidates:
        selected = []
        for name in train_names:
            use_gap = applies(rule, features[name])
            selected.append(gap[name] if use_gap else base[name])
        scored.append((summarise(selected)["score"], rule["priority"], rule["label"], rule))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    best = dict(scored[0][3])
    best["training_pooled_score"] = scored[0][0]
    return best


def applies(rule: dict, features: dict[str, float]) -> bool:
    if rule["label"] == "always_base":
        return False
    if rule["label"] == "always_gap":
        return True
    value = features[rule["feature"]]
    return value <= rule["threshold"] if rule["operator"] == "le" else value > rule["threshold"]


def select_direction(base_path: Path, gap_path: Path, gap_filtered_path: Path, base_arm: str, gap_arm: str, direction: str) -> dict:
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    gap_payload = json.loads(gap_path.read_text(encoding="utf-8"))
    gap_filtered = json.loads(gap_filtered_path.read_text(encoding="utf-8"))
    raw_base = rows_by_name(base_payload, "no_filter")
    gap_registered = rows_by_name(gap_payload, "registered_hungarian")
    control_error = numeric_control(raw_base, gap_registered)
    if control_error > TOLERANCE:
        raise ValueError(f"{direction}: baseline control failed {control_error}")
    base = rows_by_name(base_payload, base_arm)
    gap = rows_by_name(gap_filtered, gap_arm)
    if sorted(base) != sorted(gap) or len(base) != 12:
        raise ValueError(f"{direction}: expected 12 paired movies")
    features = build_features(base_payload, gap_payload, base_arm)
    selected_rows, selections = [], []
    names = sorted(base)
    for held_out in names:
        train = [name for name in names if name != held_out]
        rule = choose_rule(train, features, base, gap)
        use_gap = applies(rule, features[held_out])
        selected_rows.append(gap[held_out] if use_gap else base[held_out])
        selections.append({
            "dataset": held_out,
            "selected_graph": "gap" if use_gap else "base",
            "rule": rule,
            "held_out_features": features[held_out],
        })
    base_rows = [base[name] for name in names]
    return {
        "direction": direction,
        "baseline_control_maximum_absolute_error": control_error,
        "base_arm": base_arm,
        "gap_arm": gap_arm,
        "base_rows": base_rows,
        "selected_rows": selected_rows,
        "selections": selections,
        "base_summary": summarise(base_rows),
        "nested_selected_summary": summarise(selected_rows),
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
    forward = select_direction(args.base_forward, args.gap_forward, args.gap_forward_filtered, "min8", "min8", "forward")
    reverse = select_direction(args.base_reverse, args.gap_reverse, args.gap_reverse_filtered, "min3", "min6", "reverse")
    all_base = forward["base_rows"] + reverse["base_rows"]
    all_selected = forward["selected_rows"] + reverse["selected_rows"]
    base_summary, selected_summary = summarise(all_base), summarise(all_selected)
    result = {
        "status": "PASS_EXP194_NESTED_INFERENCE_GATE",
        "protocol": "Each held-out movie uses a rule trained only on the other 11 movies in its embryo direction; features require no ground truth.",
        "directions": {"forward": forward, "reverse": reverse},
        "combined": {
            "base": base_summary,
            "nested_selected": selected_summary,
            "delta": selected_summary["score"] - base_summary["score"],
        },
        "inputs": {key: {"path": str(value), "sha256": sha256(value)} for key, value in vars(args).items() if key != "output"},
        "evidence_class": "Exploratory nested development OOF; sequential family choice disclosed.",
        "eligible_for_kaggle_submission": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"directions": {name: block["nested_selected_summary"] for name, block in result["directions"].items()}, "combined": result["combined"]}, indent=2))


if __name__ == "__main__":
    main()
