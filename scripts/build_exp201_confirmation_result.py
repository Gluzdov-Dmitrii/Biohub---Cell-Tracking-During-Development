"""Assemble the fixed EXP201 policy on untouched EXP192 confirmation movies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_frozen_confirmation_results import policy_result, rows
from select_nested_pooled_synthetic_gap import sha256


def build(
    forward_path: Path,
    reverse_path: Path,
    expected_forward: int = 116,
    expected_reverse: int = 59,
) -> dict:
    forward = json.loads(forward_path.read_text(encoding="utf-8"))
    reverse = json.loads(reverse_path.read_text(encoding="utf-8"))
    forward_base = rows(forward, "translation", "6bba", expected_forward)
    reverse_base = rows(reverse, "translation", "44b6", expected_reverse)
    forward_selected = rows(forward, "fixed_local_flow", "6bba", expected_forward)
    reverse_selected = rows(reverse, "fixed_local_flow", "44b6", expected_reverse)
    inputs = {
        "forward": {"path": str(forward_path), "sha256": sha256(forward_path)},
        "reverse": {"path": str(reverse_path), "sha256": sha256(reverse_path)},
    }
    return policy_result(
        "EXP201_ON_EXP192_CONFIRMATION",
        forward_base,
        reverse_base,
        forward_selected,
        reverse_selected,
        {"forward": "flow_k32_a050_min8", "reverse": "flow_k16_a025_min3"},
        inputs,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.forward, args.reverse)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["combined"], indent=2))


if __name__ == "__main__":
    main()
