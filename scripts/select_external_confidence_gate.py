"""Freeze a confidence-gated external linker configuration from source only."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for raw_path in args.result:
        payload = json.loads(Path(raw_path).read_text())
        parent = payload["summary_by_arm"]["registered_hungarian"]
        candidate = payload["summary_by_arm"]["external_confidence_gate"]
        rows.append({
            "probability_floor": payload["probability_floor"],
            "bonus_weight": payload["bonus_weight"],
            "path": raw_path,
            "parent_score": parent["score"],
            "candidate_score": candidate["score"],
            "score_delta": candidate["score"] - parent["score"],
            "recall_delta": candidate["node_recall"] - parent["node_recall"],
        })
    eligible = [row for row in rows if row["score_delta"] >= 0 and row["recall_delta"] >= 0]
    selected = max(
        eligible,
        key=lambda row: (
            row["candidate_score"], row["probability_floor"], -row["bonus_weight"]
        ),
    ) if eligible else None
    output = {
        "status": "FROZEN_FROM_SOURCE_ONLY_VALIDATION" if selected else "REJECT_SOURCE_ONLY_GATE",
        "candidates": rows,
        "selected": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
