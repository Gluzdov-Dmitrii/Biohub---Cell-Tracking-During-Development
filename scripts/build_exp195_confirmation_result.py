"""Apply the frozen EXP195 inference gate to untouched EXP192 chunk outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_exp194_nested_inference_gate import TOLERANCE, build_features, numeric_control, rows_by_name
from select_nested_pooled_synthetic_gap import sha256, summarise


EXPECTED_POLICY_SHA = "23c9d3553df6239d643be0261beba4bf8338fa123c6ea15a06bfbfdb1d57e439"


def merge_chunks(paths: list[Path]) -> dict:
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    arms = set(payloads[0]["per_movie_by_arm"])
    if any(set(payload["per_movie_by_arm"]) != arms for payload in payloads[1:]):
        raise ValueError("chunk arm sets differ")
    result = {"per_movie_by_arm": {arm: [] for arm in arms}, "telemetry": []}
    for payload in payloads:
        for arm in arms:
            result["per_movie_by_arm"][arm].extend(payload["per_movie_by_arm"][arm])
        result["telemetry"].extend(payload.get("telemetry", []))
    for arm, rows in result["per_movie_by_arm"].items():
        names = [str(row["dataset"]) for row in rows]
        if len(names) != len(set(names)):
            raise ValueError(f"{arm}: duplicate movie")
    telemetry_names = [str(row["dataset"]) for row in result["telemetry"]]
    if len(telemetry_names) != len(set(telemetry_names)):
        raise ValueError("duplicate telemetry movie")
    return result


def checked_rows(payload: dict, arm: str, prefix: str, count: int) -> dict[str, dict]:
    rows = rows_by_name(payload, arm)
    if len(rows) != count or any(not name.startswith(prefix + "_") for name in rows):
        raise ValueError(f"{arm}: expected {count} unique {prefix} movies")
    return rows


def apply_policy(feature: float, threshold: float) -> bool:
    return feature <= threshold


def build(
    forward_base_path: Path,
    reverse_base_paths: list[Path],
    reverse_gap_paths: list[Path],
    reverse_gap_filtered_paths: list[Path],
    policy_path: Path,
) -> dict:
    if sha256(policy_path) != EXPECTED_POLICY_SHA:
        raise ValueError("EXP195 policy hash mismatch")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("status") != "PASS_EXP195_DEPLOYABLE_GATE_FREEZE":
        raise ValueError("EXP195 policy status mismatch")
    threshold = float(policy["threshold"])
    forward_payload = json.loads(forward_base_path.read_text(encoding="utf-8"))
    reverse_base = merge_chunks(reverse_base_paths)
    reverse_gap = merge_chunks(reverse_gap_paths)
    reverse_gap_filtered = merge_chunks(reverse_gap_filtered_paths)

    forward_raw = checked_rows(forward_payload, "no_filter", "6bba", 116)
    forward_selected = checked_rows(forward_payload, "min8", "6bba", 116)
    reverse_raw = checked_rows(reverse_base, "no_filter", "44b6", 59)
    reverse_pruned = checked_rows(reverse_base, "min3", "44b6", 59)
    reverse_gap_registered = checked_rows(reverse_gap, "registered_hungarian", "44b6", 59)
    reverse_gap_pruned = checked_rows(reverse_gap_filtered, "min6", "44b6", 59)
    control = numeric_control(reverse_raw, reverse_gap_registered)
    if control > TOLERANCE:
        raise ValueError("reverse registered control mismatch")
    features = build_features(reverse_base, reverse_gap, "min3")
    selected_reverse = {}
    selections = []
    for name in sorted(reverse_pruned):
        value = features[name]["base_pruned_node_fraction"]
        use_gap = apply_policy(value, threshold)
        selected_reverse[name] = reverse_gap_pruned[name] if use_gap else reverse_pruned[name]
        selections.append({"dataset": name, "selected_graph": "gap" if use_gap else "base", "feature": value})

    forward_names = sorted(forward_raw)
    reverse_names = sorted(reverse_raw)
    directions = {
        "forward": {
            "base_rows": [forward_raw[name] for name in forward_names],
            "selected_rows": [forward_selected[name] for name in forward_names],
            "frozen_arm": "base_min8",
            "base_summary": summarise([forward_raw[name] for name in forward_names]),
            "frozen_selected_summary": summarise([forward_selected[name] for name in forward_names]),
        },
        "reverse": {
            "base_rows": [reverse_raw[name] for name in reverse_names],
            "selected_rows": [selected_reverse[name] for name in reverse_names],
            "frozen_arm": "exp195_q75_inference_gate",
            "threshold": threshold,
            "selections": selections,
            "base_summary": summarise([reverse_raw[name] for name in reverse_names]),
            "frozen_selected_summary": summarise([selected_reverse[name] for name in reverse_names]),
        },
    }
    all_base = directions["forward"]["base_rows"] + directions["reverse"]["base_rows"]
    all_selected = directions["forward"]["selected_rows"] + directions["reverse"]["selected_rows"]
    base_summary, selected_summary = summarise(all_base), summarise(all_selected)
    all_inputs = [forward_base_path, policy_path, *reverse_base_paths, *reverse_gap_paths, *reverse_gap_filtered_paths]
    return {
        "experiment": "EXP195_ON_EXP192_CONFIRMATION",
        "status": "PASS_FROZEN_CONFIRMATION_ASSEMBLY",
        "protocol": "Threshold frozen before target inference; one complete graph chosen from inference-only telemetry.",
        "primary_metric": "175-movie combined pooled adjusted-edge score",
        "reverse_registered_control_maximum_absolute_error": control,
        "directions": directions,
        "combined": {"base": base_summary, "frozen_selected": selected_summary, "delta": selected_summary["score"] - base_summary["score"]},
        "selection_counts": {
            "forward_base": 116,
            "reverse_base": sum(row["selected_graph"] == "base" for row in selections),
            "reverse_gap": sum(row["selected_graph"] == "gap" for row in selections),
        },
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in all_inputs],
        "eligible_for_kaggle_submission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-base", type=Path, required=True)
    parser.add_argument("--reverse-base-chunk", type=Path, action="append", required=True)
    parser.add_argument("--reverse-gap-chunk", type=Path, action="append", required=True)
    parser.add_argument("--reverse-gap-filtered-chunk", type=Path, action="append", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (len(args.reverse_base_chunk) == len(args.reverse_gap_chunk) == len(args.reverse_gap_filtered_chunk) == 3):
        parser.error("exactly three reverse chunks of each kind are required")
    result = build(args.forward_base, args.reverse_base_chunk, args.reverse_gap_chunk, args.reverse_gap_filtered_chunk, args.policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"combined": result["combined"], "selection_counts": result["selection_counts"]}, indent=2))


if __name__ == "__main__":
    main()
