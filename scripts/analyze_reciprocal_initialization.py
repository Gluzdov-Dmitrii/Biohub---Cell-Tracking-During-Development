"""Fail-closed reciprocal development gate for model-initialization experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from compare_registered_candidate import load_rows, recompute_summary, validate_summary


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pair(parent_path: Path, candidate_path: Path, arm: str, fold: str) -> dict:
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    parent_rows = load_rows(parent, arm, f"{fold}.parent")
    candidate_rows = load_rows(candidate, arm, f"{fold}.candidate")
    if set(parent_rows) != set(candidate_rows):
        raise ValueError(f"{fold} parent/candidate dataset mismatch")
    parent_summary = validate_summary(parent, arm, f"{fold}.parent", parent_rows)
    candidate_summary = validate_summary(candidate, arm, f"{fold}.candidate", candidate_rows)
    return {
        "fold": fold,
        "parent_path": parent_path,
        "candidate_path": candidate_path,
        "parent_sha256": sha256(parent_path),
        "candidate_sha256": sha256(candidate_path),
        "parent_rows": parent_rows,
        "candidate_rows": candidate_rows,
        "parent_summary": parent_summary,
        "candidate_summary": candidate_summary,
    }


def delta(candidate: dict, parent: dict) -> dict:
    return {
        "score": float(candidate["score"]) - float(parent["score"]),
        "node_recall": float(candidate["node_recall"]) - float(parent["node_recall"]),
        "division_tp": int(candidate["division_tp"]) - int(parent["division_tp"]),
        "division_fp": int(candidate["division_fp"]) - int(parent["division_fp"]),
        "division_fn": int(candidate["division_fn"]) - int(parent["division_fn"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forward-parent", type=Path, required=True)
    parser.add_argument("--forward-candidate", type=Path, required=True)
    parser.add_argument("--reverse-parent", type=Path, required=True)
    parser.add_argument("--reverse-candidate", type=Path, required=True)
    parser.add_argument("--repeat-gate", type=Path)
    parser.add_argument("--require-repeat", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", default="registered_hungarian")
    parser.add_argument("--experiment", default="EXP137")
    parser.add_argument("--stage", choices=("development", "locked_audit"), default="development")
    args = parser.parse_args()

    pairs = [
        load_pair(args.forward_parent, args.forward_candidate, args.arm, "44b6_to_6bba"),
        load_pair(args.reverse_parent, args.reverse_candidate, args.arm, "6bba_to_44b6"),
    ]
    all_parent_rows: dict[str, dict] = {}
    all_candidate_rows: dict[str, dict] = {}
    fold_receipts = {}
    for pair in pairs:
        overlap = set(all_parent_rows) & set(pair["parent_rows"])
        if overlap:
            raise ValueError(f"duplicate datasets across reciprocal folds: {sorted(overlap)}")
        all_parent_rows.update(pair["parent_rows"])
        all_candidate_rows.update(pair["candidate_rows"])
        fold_delta = delta(pair["candidate_summary"], pair["parent_summary"])
        movie_deltas = [
            {
                "dataset": dataset,
                "score_delta": float(pair["candidate_rows"][dataset]["adj_edge_jaccard"])
                - float(pair["parent_rows"][dataset]["adj_edge_jaccard"]),
                "node_recall_delta": float(pair["candidate_rows"][dataset]["node_recall"])
                - float(pair["parent_rows"][dataset]["node_recall"]),
            }
            for dataset in sorted(pair["parent_rows"])
        ]
        fold_receipts[pair["fold"]] = {
            "inputs": {
                "parent": str(pair["parent_path"]),
                "parent_sha256": pair["parent_sha256"],
                "candidate": str(pair["candidate_path"]),
                "candidate_sha256": pair["candidate_sha256"],
            },
            "parent": pair["parent_summary"],
            "candidate": pair["candidate_summary"],
            "delta": fold_delta,
            "per_movie": movie_deltas,
            "positive_movies": sum(row["score_delta"] > 0.0 for row in movie_deltas),
            "negative_movies": sum(row["score_delta"] < 0.0 for row in movie_deltas),
        }

    pooled_parent = recompute_summary(all_parent_rows, "pooled.parent")
    pooled_candidate = recompute_summary(all_candidate_rows, "pooled.candidate")
    pooled_delta = delta(pooled_candidate, pooled_parent)
    if args.require_repeat and args.repeat_gate is None:
        parser.error("--require-repeat requires --repeat-gate")
    repeat_pass = None
    repeat_receipt = None
    if args.repeat_gate is not None:
        repeat = json.loads(args.repeat_gate.read_text(encoding="utf-8"))
        if repeat.get("metric_self_consistency", {}).get("status") != "PASS_RECOMPUTED_FROM_PER_MOVIE_SUFFICIENT_STATISTICS":
            raise ValueError("repeat gate lacks exact metric self-consistency receipt")
        repeat_pass = repeat.get("gate_pass") is True
        repeat_receipt = {
            "path": str(args.repeat_gate),
            "sha256": sha256(args.repeat_gate),
            "gate_pass": repeat_pass,
        }

    checks = {
        "nonnegative_score_delta_each_embryo": all(
            row["delta"]["score"] >= 0.0 for row in fold_receipts.values()
        ),
        "positive_pooled_score_delta": pooled_delta["score"] > 0.0,
        "no_node_recall_regression_each_embryo": all(
            row["delta"]["node_recall"] >= 0.0 for row in fold_receipts.values()
        ),
        "no_division_tp_loss_each_embryo": all(
            row["delta"]["division_tp"] >= 0 for row in fold_receipts.values()
        ),
    }
    if args.require_repeat:
        checks["independent_seed_direction_repeated"] = repeat_pass is True
    gate_pass = all(checks.values())
    stage_label = "DEVELOPMENT_GATE" if args.stage == "development" else "LOCKED_AUDIT"
    receipt = {
        "experiment": args.experiment,
        "stage": args.stage,
        "status": f"PASS_RECIPROCAL_{stage_label}" if gate_pass else f"REJECT_RECIPROCAL_{stage_label}",
        "arm": args.arm,
        "folds": fold_receipts,
        "pooled": {"parent": pooled_parent, "candidate": pooled_candidate, "delta": pooled_delta},
        "worst_candidate_fold_score": min(
            row["candidate"]["score"] for row in fold_receipts.values()
        ),
        "candidate_fold_score_gap": abs(
            fold_receipts["44b6_to_6bba"]["candidate"]["score"]
            - fold_receipts["6bba_to_44b6"]["candidate"]["score"]
        ),
        "repeat_required": args.require_repeat,
        "repeat_evidence": repeat_receipt,
        "checks": checks,
        "metric_self_consistency": "PASS_RECOMPUTED_FROM_PER_MOVIE_SUFFICIENT_STATISTICS",
        "gate_pass": gate_pass,
        "locked_audit_authority": gate_pass if args.stage == "development" else False,
        "locked_audit_opened": args.stage == "locked_audit",
        "kaggle_submission_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
