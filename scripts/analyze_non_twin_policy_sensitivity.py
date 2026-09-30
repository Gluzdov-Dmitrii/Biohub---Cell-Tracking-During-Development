"""Recompute fixed EXP201/202 development policies after excluding public twins."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_frozen_confirmation_results import PUBLIC_TWINS
from select_nested_pooled_synthetic_gap import summarise


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected(payload: dict, arm: str, prefix: str, keep_twins: bool) -> list[dict]:
    rows = list(payload["per_movie_by_arm"][arm])
    rows = [row for row in rows if (row["dataset"] in PUBLIC_TWINS) == keep_twins]
    if any(not row["dataset"].startswith(prefix + "_") for row in rows):
        raise ValueError("prefix mismatch")
    return sorted(rows, key=lambda row: row["dataset"])


def build(forward: dict, reverse: dict, exp195: dict, expected_non_twin: int = 10) -> dict:
    fb = selected(forward, "translation", "6bba", False)
    ff = selected(forward, "flow_k32_a050", "6bba", False)
    rb = selected(reverse, "translation", "44b6", False)
    rf = selected(reverse, "flow_k16_a025", "44b6", False)
    p_forward = [row for row in exp195["directions"]["forward"]["selected_rows"] if row["dataset"] not in PUBLIC_TWINS]
    p_reverse = [row for row in exp195["directions"]["reverse"]["selected_rows"] if row["dataset"] not in PUBLIC_TWINS]
    if not all(len(rows) == expected_non_twin for rows in (fb, ff, rb, rf, p_forward, p_reverse)):
        raise ValueError("expected exact non-twin coverage in both directions")
    if fb != sorted(p_forward, key=lambda row: row["dataset"]):
        raise ValueError("EXP201 forward translation does not reproduce EXP195 forward parent")
    policies = {
        "exp190_fixed_base": fb + rb,
        "exp201_fixed_local_flow": ff + rf,
        "exp195_fixed_reverse_gate": p_forward + p_reverse,
        "exp202_composed": ff + p_reverse,
    }
    summaries = {name: summarise(rows) for name, rows in policies.items()}
    deltas = {
        "exp201_vs_exp190": summaries["exp201_fixed_local_flow"]["score"] - summaries["exp190_fixed_base"]["score"],
        "exp195_vs_exp190": summaries["exp195_fixed_reverse_gate"]["score"] - summaries["exp190_fixed_base"]["score"],
        "exp202_vs_exp195": summaries["exp202_composed"]["score"] - summaries["exp195_fixed_reverse_gate"]["score"],
    }
    return {
        "status": "PASS_NON_TWIN_FIXED_POLICY_SENSITIVITY",
        "movie_count": 2 * expected_non_twin,
        "excluded_public_twins": sorted(PUBLIC_TWINS),
        "summaries": summaries,
        "deltas": deltas,
        "direction_flow_delta": {
            "forward": summarise(ff)["score"] - summarise(fb)["score"],
            "reverse": summarise(rf)["score"] - summarise(rb)["score"],
        },
        "interpretation_guard": "Post-hoc sensitivity only; cannot alter frozen EXP201/202 or replace the 175-movie confirmation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-flow", type=Path, required=True)
    parser.add_argument("--reverse-flow", type=Path, required=True)
    parser.add_argument("--exp195", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.forward_flow, args.reverse_flow, args.exp195]
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    result = build(*payloads)
    result["inputs"] = [{"path": str(path), "sha256": sha256(path)} for path in paths]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "movie_count": result["movie_count"],
        "deltas": result["deltas"],
        "direction_flow_delta": result["direction_flow_delta"],
    }, indent=2))


if __name__ == "__main__":
    main()
