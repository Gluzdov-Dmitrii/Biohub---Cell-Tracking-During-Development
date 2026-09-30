"""Require the EXP186 baseline variant to reproduce EXP185 exactly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def compare(reference_path: Path, candidate_path: Path) -> None:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    for arm in ("registered_hungarian", "synthetic_gap_no_veto", "synthetic_gap_deepcenter"):
        ref_rows = {row["dataset"]: row for row in reference["per_movie_by_arm"][arm]}
        new_rows = {row["dataset"]: row for row in candidate["per_movie_by_arm"][arm]}
        if set(ref_rows) != set(new_rows):
            raise ValueError(f"{arm}: dataset mismatch")
        for dataset in sorted(ref_rows):
            for key in (
                "edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp",
                "division_fn", "num_pred_nodes", "node_recall", "edge_jaccard",
                "adj_edge_jaccard",
            ):
                old = ref_rows[dataset][key]
                new = new_rows[dataset][key]
                if isinstance(old, int):
                    if int(new) != old:
                        raise ValueError(f"{arm}/{dataset}/{key}: {old} != {new}")
                elif abs(float(old) - float(new)) > 1e-12:
                    raise ValueError(f"{arm}/{dataset}/{key}: {old} != {new}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-forward", type=Path, required=True)
    parser.add_argument("--reference-reverse", type=Path, required=True)
    parser.add_argument("--candidate-forward", type=Path, required=True)
    parser.add_argument("--candidate-reverse", type=Path, required=True)
    args = parser.parse_args()
    compare(args.reference_forward, args.candidate_forward)
    compare(args.reference_reverse, args.candidate_reverse)
    print("PASS_EXACT_EXP185_BASELINE_REPRODUCTION")


if __name__ == "__main__":
    main()
