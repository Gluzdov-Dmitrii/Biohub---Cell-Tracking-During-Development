"""Assemble one fixed paired comparison whose base and candidate are separate files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from select_nested_pooled_synthetic_gap import sha256, summarise


def rows(payload: dict, arm: str, prefix: str, expected: int) -> list[dict]:
    try:
        values = list(payload["per_movie_by_arm"][arm])
    except KeyError as error:
        raise ValueError(f"missing arm {arm}") from error
    names = [str(row["dataset"]) for row in values]
    if len(names) != expected or len(set(names)) != expected:
        raise ValueError(f"{arm}: expected {expected} unique movies")
    if any(not name.startswith(prefix + "_") for name in names):
        raise ValueError(f"{arm}: wrong embryo prefix")
    return sorted(values, key=lambda row: str(row["dataset"]))


def build(
    base_forward: dict,
    candidate_forward: dict,
    base_reverse: dict,
    candidate_reverse: dict,
    base_arm: str,
    candidate_arm: str,
    expected_forward: int = 12,
    expected_reverse: int = 12,
    base_reverse_arm: str | None = None,
    candidate_reverse_arm: str | None = None,
) -> dict:
    base_reverse_arm = base_reverse_arm or base_arm
    candidate_reverse_arm = candidate_reverse_arm or candidate_arm
    directions = {}
    for name, base_payload, candidate_payload, prefix, expected, current_base_arm, current_candidate_arm in (
        (
            "forward", base_forward, candidate_forward, "6bba", expected_forward,
            base_arm, candidate_arm,
        ),
        (
            "reverse", base_reverse, candidate_reverse, "44b6", expected_reverse,
            base_reverse_arm, candidate_reverse_arm,
        ),
    ):
        base = rows(base_payload, current_base_arm, prefix, expected)
        selected = rows(candidate_payload, current_candidate_arm, prefix, expected)
        if [row["dataset"] for row in base] != [row["dataset"] for row in selected]:
            raise ValueError(f"{name}: paired coverage mismatch")
        directions[name] = {
            "base_rows": base,
            "selected_rows": selected,
            "base_summary": summarise(base),
            "fixed_selected_summary": summarise(selected),
            "base_arm": current_base_arm,
            "fixed_arm": current_candidate_arm,
        }
    all_base = directions["forward"]["base_rows"] + directions["reverse"]["base_rows"]
    all_selected = (
        directions["forward"]["selected_rows"] + directions["reverse"]["selected_rows"]
    )
    base_summary = summarise(all_base)
    selected_summary = summarise(all_selected)
    return {
        "status": "PASS_FIXED_SEPARATE_TWO_DIRECTION_COMPARISON",
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
    parser.add_argument("--base-forward", type=Path, required=True)
    parser.add_argument("--candidate-forward", type=Path, required=True)
    parser.add_argument("--base-reverse", type=Path, required=True)
    parser.add_argument("--candidate-reverse", type=Path, required=True)
    parser.add_argument("--base-arm", required=True)
    parser.add_argument("--candidate-arm", required=True)
    parser.add_argument("--base-reverse-arm")
    parser.add_argument("--candidate-reverse-arm")
    parser.add_argument("--expected-forward", type=int, default=12)
    parser.add_argument("--expected-reverse", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "base_forward": args.base_forward,
        "candidate_forward": args.candidate_forward,
        "base_reverse": args.base_reverse,
        "candidate_reverse": args.candidate_reverse,
    }
    payloads = {
        key: json.loads(path.read_text(encoding="utf-8")) for key, path in paths.items()
    }
    result = build(
        payloads["base_forward"],
        payloads["candidate_forward"],
        payloads["base_reverse"],
        payloads["candidate_reverse"],
        args.base_arm,
        args.candidate_arm,
        args.expected_forward,
        args.expected_reverse,
        args.base_reverse_arm,
        args.candidate_reverse_arm,
    )
    result["inputs"] = {
        key: {"path": str(path), "sha256": sha256(path)} for key, path in paths.items()
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["combined"], indent=2))


if __name__ == "__main__":
    main()
