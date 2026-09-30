"""Paired stratified bootstrap and leave-one-movie-out stability for nested OOF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from select_nested_pooled_synthetic_gap import summarise


def delta(base: list[dict], selected: list[dict]) -> float:
    return summarise(selected)["score"] - summarise(base)["score"]


def paired_direction(direction: dict) -> tuple[list[dict], list[dict]]:
    base = {row["dataset"]: row for row in direction["base_rows"]}
    selected = {row["dataset"]: row for row in direction["selected_rows"]}
    if sorted(base) != sorted(selected):
        raise ValueError("paired dataset coverage mismatch")
    names = sorted(base)
    return [base[name] for name in names], [selected[name] for name in names]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nested-result", type=Path, required=True)
    parser.add_argument("--reference-nested", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=314159)
    args = parser.parse_args()
    payload = json.loads(args.nested_result.read_text(encoding="utf-8"))
    pairs = {
        name: paired_direction(payload["directions"][name]) for name in ("forward", "reverse")
    }
    reference_label = "embedded base rows"
    if args.reference_nested is not None:
        reference = json.loads(args.reference_nested.read_text(encoding="utf-8"))
        reference_label = str(args.reference_nested)
        for name in ("forward", "reverse"):
            reference_base, reference_selected = paired_direction(reference["directions"][name])
            current_base, current_selected = pairs[name]
            if [row["dataset"] for row in reference_selected] != [row["dataset"] for row in current_selected]:
                raise ValueError("reference/current dataset coverage mismatch")
            pairs[name] = (reference_selected, current_selected)
    rng = np.random.default_rng(args.seed)
    bootstrap = np.empty(args.draws, dtype=float)
    for draw in range(args.draws):
        sampled_base, sampled_selected = [], []
        for base, selected in pairs.values():
            indices = rng.integers(0, len(base), size=len(base))
            sampled_base.extend(base[int(index)] for index in indices)
            sampled_selected.extend(selected[int(index)] for index in indices)
        bootstrap[draw] = delta(sampled_base, sampled_selected)

    all_base = [row for pair in pairs.values() for row in pair[0]]
    all_selected = [row for pair in pairs.values() for row in pair[1]]
    leave_one_out = []
    for omitted in range(len(all_base)):
        keep = [index for index in range(len(all_base)) if index != omitted]
        leave_one_out.append({
            "omitted_dataset": all_base[omitted]["dataset"],
            "delta": delta([all_base[index] for index in keep], [all_selected[index] for index in keep]),
        })
    result = {
        "status": "PASS_PAIRED_STABILITY_ANALYSIS",
        "reference": reference_label,
        "observed_delta": delta(all_base, all_selected),
        "bootstrap": {
            "design": (
                "paired movie resampling, stratified independently within each embryo direction "
                f"(forward n={len(pairs['forward'][0])}, reverse n={len(pairs['reverse'][0])})"
            ),
            "draws": args.draws,
            "seed": args.seed,
            "probability_positive": float(np.mean(bootstrap > 0.0)),
            "q025": float(np.quantile(bootstrap, 0.025)),
            "median": float(np.quantile(bootstrap, 0.5)),
            "q975": float(np.quantile(bootstrap, 0.975)),
        },
        "direction_delta": {
            name: delta(base, selected) for name, (base, selected) in pairs.items()
        },
        "leave_one_movie_out": leave_one_out,
        "leave_one_movie_out_min_delta": min(row["delta"] for row in leave_one_out),
        "leave_one_movie_out_max_delta": max(row["delta"] for row in leave_one_out),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
