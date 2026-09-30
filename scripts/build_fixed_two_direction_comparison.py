"""Assemble a fixed two-direction paired comparison without arm selection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


def arm_rows(payload: dict, arm: str, prefix: str, expected_count: int) -> list[dict]:
    try:
        values = list(payload["per_movie_by_arm"][arm])
    except KeyError as error:
        raise ValueError(f"missing arm {arm}") from error
    names = [str(row["dataset"]) for row in values]
    if len(names) != expected_count or len(set(names)) != expected_count:
        raise ValueError(f"{arm}: expected {expected_count} unique movies")
    if any(not name.startswith(prefix + "_") for name in names):
        raise ValueError(f"{arm}: wrong direction prefix")
    return sorted(values, key=lambda row: str(row["dataset"]))


def build(
    forward: dict,
    reverse: dict,
    base_arm: str,
    candidate_arm: str,
    expected_forward: int = 12,
    expected_reverse: int = 12,
) -> dict:
    directions = {}
    for name, payload, prefix, count in (
        ("forward", forward, "6bba", expected_forward),
        ("reverse", reverse, "44b6", expected_reverse),
    ):
        base = arm_rows(payload, base_arm, prefix, count)
        selected = arm_rows(payload, candidate_arm, prefix, count)
        if [row["dataset"] for row in base] != [row["dataset"] for row in selected]:
            raise ValueError("paired coverage mismatch")
        directions[name] = {
            "base_rows": base,
            "selected_rows": selected,
            "base_summary": summarise(base),
            "fixed_selected_summary": summarise(selected),
            "base_arm": base_arm,
            "fixed_arm": candidate_arm,
        }
    all_base = directions["forward"]["base_rows"] + directions["reverse"]["base_rows"]
    all_selected = directions["forward"]["selected_rows"] + directions["reverse"]["selected_rows"]
    base_summary = summarise(all_base)
    selected_summary = summarise(all_selected)
    return {
        "status": "PASS_FIXED_TWO_DIRECTION_COMPARISON",
        "selection": "none",
        "directions": directions,
        "combined": {
            "base": base_summary,
            "fixed_selected": selected_summary,
            "delta": selected_summary["score"] - base_summary["score"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--base-arm", required=True)
    parser.add_argument("--candidate-arm", required=True)
    parser.add_argument("--expected-forward", type=int, default=12)
    parser.add_argument("--expected-reverse", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(
        json.loads(args.forward.read_text(encoding="utf-8")),
        json.loads(args.reverse.read_text(encoding="utf-8")),
        args.base_arm,
        args.candidate_arm,
        args.expected_forward,
        args.expected_reverse,
    )
    result["inputs"] = {
        "forward": {"path": str(args.forward), "sha256": sha256(args.forward)},
        "reverse": {"path": str(args.reverse), "sha256": sha256(args.reverse)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["combined"], indent=2))


if __name__ == "__main__":
    main()
