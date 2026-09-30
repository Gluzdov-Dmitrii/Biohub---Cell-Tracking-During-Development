"""Apply a frozen inference-observable pruning safety veto to EXP206."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from build_exp209_selected_centroid_confirmation import maximum_row_error
from build_frozen_confirmation_results import policy_result
from select_nested_pooled_synthetic_gap import sha256


CENTROID_ARM = "intensity_centroid_r2_5_5"


def build(chunks: list[dict], exp195: dict, exp206: dict, threshold: float, inputs: dict) -> dict:
    translation = {}
    centroid = {}
    telemetry = {}
    for payload in chunks:
        if payload.get("status") != "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT":
            raise ValueError("unexpected EXP206 chunk status")
        if set(payload.get("per_movie_by_arm", {})) != {"translation", CENTROID_ARM}:
            raise ValueError("unexpected EXP206 chunk arms")
        for row in payload["per_movie_by_arm"]["translation"]:
            name = str(row["dataset"])
            if name in translation:
                raise ValueError("duplicate translation movie")
            translation[name] = row
        for row in payload["per_movie_by_arm"][CENTROID_ARM]:
            name = str(row["dataset"])
            if name in centroid:
                raise ValueError("duplicate centroid movie")
            centroid[name] = row
        for item in payload.get("telemetry", []):
            name = str(item["dataset"])
            if name in telemetry:
                raise ValueError("duplicate telemetry movie")
            telemetry[name] = item
    names = sorted(translation)
    if len(names) != 116 or names != sorted(centroid) or names != sorted(telemetry):
        raise ValueError("expected exact paired 116-movie forward coverage")
    if any(not name.startswith("6bba_") for name in names):
        raise ValueError("wrong forward embryo prefix")

    decisions = []
    selected = []
    for name in names:
        item = telemetry[name]
        raw_nodes = int(item["nodes"])
        if raw_nodes <= 0:
            raise ValueError("raw candidate node count must be positive")
        base_removed = int(item["translation_filter"]["nodes_removed"])
        centroid_removed = int(item[f"{CENTROID_ARM}_filter"]["nodes_removed"])
        ratio = (centroid_removed - base_removed) / raw_nodes
        if not math.isfinite(ratio):
            raise ValueError("non-finite removal ratio")
        use_centroid = ratio <= threshold
        selected.append(centroid[name] if use_centroid else translation[name])
        decisions.append({
            "dataset": name,
            "raw_candidate_nodes": raw_nodes,
            "translation_nodes_removed": base_removed,
            "centroid_nodes_removed": centroid_removed,
            "added_removed_node_fraction": ratio,
            "selected_arm": CENTROID_ARM if use_centroid else "translation",
        })

    exp195_forward = list(exp195["directions"]["forward"]["selected_rows"])
    exp206_forward = list(exp206["directions"]["forward"]["selected_rows"])
    control_error = maximum_row_error([translation[name] for name in names], exp195_forward)
    centroid_error = maximum_row_error([centroid[name] for name in names], exp206_forward)
    if max(control_error, centroid_error) > 1e-12:
        raise ValueError("cached EXP206 rows do not reproduce frozen confirmations")

    result = policy_result(
        "EXP210_CENTROID_PRUNING_SAFETY_VETO_ON_EXP192_CONFIRMATION",
        list(exp195["directions"]["forward"]["base_rows"]),
        list(exp195["directions"]["reverse"]["base_rows"]),
        selected,
        list(exp195["directions"]["reverse"]["selected_rows"]),
        {"forward": "centroid_r2_5_5_with_added_removal_fraction_veto", "reverse": "exp195_q75_inference_gate"},
        inputs,
    )
    result["protocol"] = (
        "The 0.005 added-removed-node fraction threshold was frozen on 12 development movies "
        "before this gate was evaluated on the 116 confirmation movies. Selection uses only "
        "inference-observable graph-filter telemetry; reverse is unchanged from EXP195/EXP206."
    )
    result["safety_veto"] = {
        "threshold": threshold,
        "formula": "(centroid_nodes_removed - translation_nodes_removed) / raw_candidate_nodes",
        "centroid_movies": sum(item["selected_arm"] == CENTROID_ARM for item in decisions),
        "translation_movies": sum(item["selected_arm"] == "translation" for item in decisions),
        "decisions": decisions,
    }
    result["control_maximum_absolute_error"] = control_error
    result["centroid_parent_maximum_absolute_error"] = centroid_error
    result["incremental_vs_exp206_score"] = (
        result["combined"]["frozen_selected"]["score"]
        - float(exp206["combined"]["frozen_selected"]["score"])
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunk", type=Path, action="append", required=True)
    parser.add_argument("--exp195", type=Path, required=True)
    parser.add_argument("--exp206", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.005)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    chunks = [json.loads(path.read_text(encoding="utf-8")) for path in args.chunk]
    exp195 = json.loads(args.exp195.read_text(encoding="utf-8"))
    exp206 = json.loads(args.exp206.read_text(encoding="utf-8"))
    paths = {"chunks": args.chunk, "exp195": args.exp195, "exp206": args.exp206}
    inputs = {
        "chunks": [{"path": str(path), "sha256": sha256(path)} for path in args.chunk],
        "exp195": {"path": str(args.exp195), "sha256": sha256(args.exp195)},
        "exp206": {"path": str(args.exp206), "sha256": sha256(args.exp206)},
    }
    result = build(chunks, exp195, exp206, args.threshold, inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "combined": result["combined"],
        "safety_veto_counts": {
            "centroid": result["safety_veto"]["centroid_movies"],
            "translation": result["safety_veto"]["translation_movies"],
        },
        "incremental_vs_exp206_score": result["incremental_vs_exp206_score"],
    }, indent=2))


if __name__ == "__main__":
    main()
