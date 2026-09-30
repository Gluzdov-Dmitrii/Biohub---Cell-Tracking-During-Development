"""Exact reciprocal promotion gate for the frozen EXP147 division repair."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from compare_registered_candidate import load_rows, recompute_summary, validate_summary


PARENT_ARM = "registered_hungarian"
DEFAULT_CANDIDATE_ARM = "registered_plus_safe_division"
CANDIDATE_ARM = DEFAULT_CANDIDATE_ARM


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fold(
    path: Path,
    fold: str,
    candidate_arm: str = DEFAULT_CANDIDATE_ARM,
) -> tuple[dict[str, dict], dict[str, dict], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    parent_rows = load_rows(payload, PARENT_ARM, f"{fold}.parent")
    candidate_rows = load_rows(payload, candidate_arm, f"{fold}.candidate")
    if set(parent_rows) != set(candidate_rows) or len(parent_rows) != 12:
        raise ValueError(f"{fold} requires the same 12 movies")
    parent = validate_summary(payload, PARENT_ARM, f"{fold}.parent", parent_rows)
    candidate = validate_summary(payload, candidate_arm, f"{fold}.candidate", candidate_rows)
    movie = [{
        "dataset": name,
        "score_delta": candidate_rows[name]["adj_edge_jaccard"] - parent_rows[name]["adj_edge_jaccard"],
        "division_tp_delta": candidate_rows[name]["division_tp"] - parent_rows[name]["division_tp"],
        "division_fp_delta": candidate_rows[name]["division_fp"] - parent_rows[name]["division_fp"],
    } for name in sorted(parent_rows)]
    delta = {
        "score": candidate["score"] - parent["score"],
        "adjusted_edge_jaccard": candidate["adj_edge_jaccard"] - parent["adj_edge_jaccard"],
        "node_recall": candidate["node_recall"] - parent["node_recall"],
        "division_tp": candidate["division_tp"] - parent["division_tp"],
        "division_fp": candidate["division_fp"] - parent["division_fp"],
        "division_fn": candidate["division_fn"] - parent["division_fn"],
    }
    return parent_rows, candidate_rows, {
        "input": {"path": str(path), "sha256": sha256(path)},
        "parent": parent, "candidate": candidate, "delta": delta, "per_movie": movie,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-arm", default=DEFAULT_CANDIDATE_ARM)
    parser.add_argument("--experiment", default="EXP147")
    args = parser.parse_args()
    folds = {}
    all_parent = {}
    all_candidate = {}
    for name, path in (("44b6_to_6bba", args.forward), ("6bba_to_44b6", args.reverse)):
        parent_rows, candidate_rows, receipt = load_fold(path, name, args.candidate_arm)
        if set(all_parent) & set(parent_rows):
            raise ValueError("duplicate movies across embryo directions")
        all_parent.update(parent_rows)
        all_candidate.update(candidate_rows)
        folds[name] = receipt
    parent = recompute_summary(all_parent, "pooled.parent")
    candidate = recompute_summary(all_candidate, "pooled.candidate")
    delta = {
        "score": candidate["score"] - parent["score"],
        "adjusted_edge_jaccard": candidate["adj_edge_jaccard"] - parent["adj_edge_jaccard"],
        "node_recall": candidate["node_recall"] - parent["node_recall"],
        "division_tp": candidate["division_tp"] - parent["division_tp"],
        "division_fp": candidate["division_fp"] - parent["division_fp"],
        "division_fn": candidate["division_fn"] - parent["division_fn"],
    }
    division_precision = (
        candidate["division_tp"] / (candidate["division_tp"] + candidate["division_fp"])
        if candidate["division_tp"] + candidate["division_fp"] else 0.0
    )
    checks = {
        "positive_score_each_embryo": all(f["delta"]["score"] > 0 for f in folds.values()),
        "positive_pooled_score": delta["score"] > 0,
        "positive_pooled_division_tp": delta["division_tp"] > 0,
        "no_division_tp_loss_each_embryo": all(f["delta"]["division_tp"] >= 0 for f in folds.values()),
        "pooled_division_precision_at_least_0_25": division_precision >= 0.25,
        "adjusted_edge_loss_at_most_0_005_each_embryo": all(
            f["delta"]["adjusted_edge_jaccard"] >= -0.005 for f in folds.values()
        ),
        "no_node_recall_loss_each_embryo": all(f["delta"]["node_recall"] >= 0 for f in folds.values()),
    }
    gate_pass = all(checks.values())
    result = {
        "experiment": args.experiment,
        "status": "PASS_PROSPECTIVE_FULL_OOF_GATE" if gate_pass else "REJECT_PROSPECTIVE_FULL_OOF_GATE",
        "folds": folds,
        "pooled": {"parent": parent, "candidate": candidate, "delta": delta, "division_precision": division_precision},
        "checks": checks,
        "metric_self_consistency": "PASS_RECOMPUTED_FROM_PER_MOVIE_SUFFICIENT_STATISTICS",
        "gate_pass": gate_pass,
        "kaggle_submission_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
