"""Select one native-division probability threshold on source-only validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PARENT = "registered_hungarian"
CANDIDATE = "registered_plus_native_guided_division"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for spec in args.result:
        threshold_text, path_text = spec.split("=", 1)
        payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
        parent = payload["summary_by_arm"][PARENT]
        candidate = payload["summary_by_arm"][CANDIDATE]
        row = {
            "threshold": float(threshold_text),
            "path": path_text,
            "parent_score": float(parent["score"]),
            "candidate_score": float(candidate["score"]),
            "score_delta": float(candidate["score"] - parent["score"]),
            "division_tp_delta": int(candidate["division_tp"] - parent["division_tp"]),
            "division_fp": int(candidate["division_fp"]),
        }
        row["eligible"] = row["score_delta"] >= 0 and row["division_tp_delta"] >= 0
        rows.append(row)
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise RuntimeError("no source-validation threshold is non-regressing")
    selected = max(eligible, key=lambda row: (row["candidate_score"], row["threshold"]))
    result = {
        "status": "FROZEN_FROM_SOURCE_ONLY_VALIDATION",
        "selection_rule": "nonnegative score and division-TP deltas; highest score; tie chooses higher threshold",
        "candidates": sorted(rows, key=lambda row: row["threshold"], reverse=True),
        "selected_threshold": selected["threshold"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
