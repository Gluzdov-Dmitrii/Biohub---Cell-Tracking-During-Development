"""Select a weak-linker weight using source-only official score."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for spec in args.result:
        weight_text, raw_path = spec.split("=", 1)
        payload = json.loads(Path(raw_path).read_text())
        parent = payload["summary_by_arm"]["registered_hungarian"]
        candidate = payload["summary_by_arm"]["external_weak_hungarian"]
        rows.append({
            "weight": float(weight_text),
            "path": raw_path,
            "parent_score": parent["score"],
            "candidate_score": candidate["score"],
            "score_delta": candidate["score"] - parent["score"],
            "recall_delta": candidate["node_recall"] - parent["node_recall"],
        })
    eligible = [row for row in rows if row["score_delta"] >= 0 and row["recall_delta"] >= 0]
    if not eligible:
        raise RuntimeError({"no_eligible_weight": rows})
    selected = max(eligible, key=lambda row: (row["candidate_score"], -row["weight"]))
    output = {
        "status": "FROZEN_FROM_SOURCE_ONLY_VALIDATION",
        "candidates": rows,
        "selected_weight": selected["weight"],
    }
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
