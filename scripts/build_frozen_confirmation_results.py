"""Assemble frozen EXP190/191 policies without selecting on confirmation scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


PUBLIC_TWINS = {
    "44b6_0113de3b.zarr",
    "44b6_0b24845f.zarr",
    "6bba_05b6850b.zarr",
    "6bba_05db0fb1.zarr",
}


def rows(payload: dict, arm: str, expected_prefix: str, expected_count: int) -> list[dict]:
    try:
        values = list(payload["per_movie_by_arm"][arm])
    except KeyError as exc:
        raise ValueError(f"missing frozen arm {arm}") from exc
    names = [str(row["dataset"]) for row in values]
    if len(names) != expected_count or len(set(names)) != expected_count:
        raise ValueError(f"{arm}: expected {expected_count} unique movies, got {len(set(names))}")
    if any(not name.startswith(expected_prefix + "_") for name in names):
        raise ValueError(f"{arm}: wrong target prefix")
    if set(names) & PUBLIC_TWINS:
        raise ValueError(f"{arm}: public twin leaked into confirmation")
    return sorted(values, key=lambda row: str(row["dataset"]))


def policy_result(
    experiment: str,
    forward_base: list[dict],
    reverse_base: list[dict],
    forward_selected: list[dict],
    reverse_selected: list[dict],
    labels: dict[str, str],
    inputs: dict,
) -> dict:
    combined_base = summarise(forward_base + reverse_base)
    combined_selected = summarise(forward_selected + reverse_selected)
    directions = {}
    for name, base, selected in (
        ("forward", forward_base, forward_selected),
        ("reverse", reverse_base, reverse_selected),
    ):
        if [row["dataset"] for row in base] != [row["dataset"] for row in selected]:
            raise ValueError(f"{name}: frozen policy coverage mismatch")
        directions[name] = {
            "base_rows": base,
            "selected_rows": selected,
            "base_summary": summarise(base),
            "frozen_selected_summary": summarise(selected),
            "frozen_arm": labels[name],
            "per_movie_delta": [
                {
                    "dataset": base_row["dataset"],
                    "delta_adj_edge_jaccard": float(selected_row["adj_edge_jaccard"])
                    - float(base_row["adj_edge_jaccard"]),
                }
                for base_row, selected_row in zip(base, selected)
            ],
        }
    return {
        "experiment": experiment,
        "status": "PASS_FROZEN_CONFIRMATION_ASSEMBLY",
        "protocol": "No arm selection: policies were frozen before all 175 confirmation movies were downloaded or inferred.",
        "primary_metric": "175-movie combined pooled adjusted-edge score",
        "inputs": inputs,
        "directions": directions,
        "combined": {
            "base": combined_base,
            "frozen_selected": combined_selected,
            "delta": combined_selected["score"] - combined_base["score"],
            "negative_movie_count": sum(
                item["delta_adj_edge_jaccard"] < 0
                for direction in directions.values()
                for item in direction["per_movie_delta"]
            ),
        },
        "eligible_for_kaggle_submission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-base", type=Path, required=True)
    parser.add_argument("--reverse-base", type=Path, required=True)
    parser.add_argument("--reverse-gap", type=Path, required=True)
    parser.add_argument("--exp190-output", type=Path, required=True)
    parser.add_argument("--exp191-output", type=Path, required=True)
    args = parser.parse_args()
    forward_payload = json.loads(args.forward_base.read_text(encoding="utf-8"))
    reverse_payload = json.loads(args.reverse_base.read_text(encoding="utf-8"))
    gap_payload = json.loads(args.reverse_gap.read_text(encoding="utf-8"))
    forward_base = rows(forward_payload, "no_filter", "6bba", 116)
    reverse_base = rows(reverse_payload, "no_filter", "44b6", 59)
    forward_min8 = rows(forward_payload, "min8", "6bba", 116)
    reverse_min3 = rows(reverse_payload, "min3", "44b6", 59)
    reverse_gap_min6 = rows(gap_payload, "min6", "44b6", 59)
    inputs = {
        "forward_base": {"path": str(args.forward_base), "sha256": sha256(args.forward_base)},
        "reverse_base": {"path": str(args.reverse_base), "sha256": sha256(args.reverse_base)},
        "reverse_gap": {"path": str(args.reverse_gap), "sha256": sha256(args.reverse_gap)},
    }
    exp190 = policy_result(
        "EXP190_ON_EXP192_CONFIRMATION", forward_base, reverse_base,
        forward_min8, reverse_min3,
        {"forward": "base_min8", "reverse": "base_min3"}, inputs,
    )
    exp191 = policy_result(
        "EXP191_ON_EXP192_CONFIRMATION", forward_base, reverse_base,
        forward_min8, reverse_gap_min6,
        {"forward": "base_min8", "reverse": "gap_g45_t20_min6"}, inputs,
    )
    for path, payload in ((args.exp190_output, exp190), (args.exp191_output, exp191)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exp190": exp190["combined"], "exp191": exp191["combined"]}, indent=2))


if __name__ == "__main__":
    main()
