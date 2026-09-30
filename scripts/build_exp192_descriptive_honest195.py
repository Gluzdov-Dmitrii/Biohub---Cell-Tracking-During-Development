"""Combine frozen EXP192 confirmation with prior non-twin development rows."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_frozen_confirmation_results import PUBLIC_TWINS
from select_nested_pooled_synthetic_gap import sha256, summarise


def arm_rows(path: Path, arm: str, prefix: str) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = list(payload["per_movie_by_arm"][arm])
    rows = [row for row in values if str(row["dataset"]) not in PUBLIC_TWINS]
    names = [str(row["dataset"]) for row in rows]
    if len(rows) != 10 or len(set(names)) != 10 or any(not name.startswith(prefix + "_") for name in names):
        raise ValueError(f"{path}:{arm} must contain exactly 10 unique non-twin {prefix} movies")
    return sorted(rows, key=lambda row: str(row["dataset"]))


def confirmation_rows(path: Path) -> tuple[dict, dict[str, list[dict]], dict[str, list[dict]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS_FROZEN_CONFIRMATION_ASSEMBLY":
        raise ValueError(f"{path}: confirmation status did not pass")
    base, selected = {}, {}
    for direction, prefix, expected in (("forward", "6bba", 116), ("reverse", "44b6", 59)):
        block = payload["directions"][direction]
        base[direction] = list(block["base_rows"])
        selected[direction] = list(block["selected_rows"])
        for label, rows in (("base", base[direction]), ("selected", selected[direction])):
            names = [str(row["dataset"]) for row in rows]
            if len(rows) != expected or len(set(names)) != expected:
                raise ValueError(f"{path}:{direction}:{label} count mismatch")
            if any(not name.startswith(prefix + "_") or name in PUBLIC_TWINS for name in names):
                raise ValueError(f"{path}:{direction}:{label} cohort mismatch")
    return payload, base, selected


def build(
    confirmation_exp190: Path,
    confirmation_exp191: Path,
    development_forward: Path,
    development_reverse: Path,
    development_reverse_gap: Path,
) -> dict:
    exp190_payload, confirm_base190, confirm_selected190 = confirmation_rows(confirmation_exp190)
    exp191_payload, confirm_base191, confirm_selected191 = confirmation_rows(confirmation_exp191)
    if confirm_base190 != confirm_base191:
        raise ValueError("EXP190/191 confirmation baselines differ")
    if confirm_selected190["forward"] != confirm_selected191["forward"]:
        raise ValueError("EXP190/191 forward confirmation policies differ")

    dev_base = {
        "forward": arm_rows(development_forward, "no_filter", "6bba"),
        "reverse": arm_rows(development_reverse, "no_filter", "44b6"),
    }
    dev_selected190 = {
        "forward": arm_rows(development_forward, "min8", "6bba"),
        "reverse": arm_rows(development_reverse, "min3", "44b6"),
    }
    dev_selected191 = {
        "forward": dev_selected190["forward"],
        "reverse": arm_rows(development_reverse_gap, "gap_primary_min6", "44b6"),
    }

    experiments = {}
    for name, payload, confirm_selected, dev_selected in (
        ("EXP190", exp190_payload, confirm_selected190, dev_selected190),
        ("EXP191", exp191_payload, confirm_selected191, dev_selected191),
    ):
        directions = {}
        all_base, all_selected = [], []
        for direction in ("forward", "reverse"):
            base = sorted(confirm_base190[direction] + dev_base[direction], key=lambda row: str(row["dataset"]))
            selected = sorted(confirm_selected[direction] + dev_selected[direction], key=lambda row: str(row["dataset"]))
            if [row["dataset"] for row in base] != [row["dataset"] for row in selected]:
                raise ValueError(f"{name}:{direction} coverage mismatch")
            directions[direction] = {
                "movie_count": len(base),
                "base_summary": summarise(base),
                "frozen_selected_summary": summarise(selected),
            }
            all_base.extend(base)
            all_selected.extend(selected)
        names = [str(row["dataset"]) for row in all_base]
        if len(names) != 195 or len(set(names)) != 195 or set(names) & PUBLIC_TWINS:
            raise ValueError(f"{name}: expected 195 unique non-twin movies")
        base_summary = summarise(all_base)
        selected_summary = summarise(all_selected)
        experiments[name] = {
            "frozen_arms": {
                "forward": payload["directions"]["forward"]["frozen_arm"],
                "reverse": payload["directions"]["reverse"]["frozen_arm"],
            },
            "directions": directions,
            "combined": {
                "movie_count": 195,
                "base": base_summary,
                "frozen_selected": selected_summary,
                "delta": selected_summary["score"] - base_summary["score"],
            },
        }
    paths = [confirmation_exp190, confirmation_exp191, development_forward, development_reverse, development_reverse_gap]
    return {
        "status": "PASS_EXP192_DESCRIPTIVE_HONEST195",
        "evidence_class": "Secondary descriptive aggregate: 175 untouched confirmation movies plus 20 previously opened non-twin development movies.",
        "primary_result_remains": "The untouched 175-movie EXP192 confirmation; this report cannot change promotion decisions.",
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in paths],
        "experiments": experiments,
        "eligible_for_kaggle_submission": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmation-exp190", type=Path, required=True)
    parser.add_argument("--confirmation-exp191", type=Path, required=True)
    parser.add_argument("--development-forward", type=Path, required=True)
    parser.add_argument("--development-reverse", type=Path, required=True)
    parser.add_argument("--development-reverse-gap", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.confirmation_exp190, args.confirmation_exp191, args.development_forward, args.development_reverse, args.development_reverse_gap)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["experiments"], indent=2))


if __name__ == "__main__":
    main()
