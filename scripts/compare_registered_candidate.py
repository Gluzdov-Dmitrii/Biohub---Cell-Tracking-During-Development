"""Fail-closed paired gate for registered-linker candidate result artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(value: object, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite {label}: {value!r}")
    return result


def load_rows(payload: dict, arm: str, label: str) -> dict[str, dict]:
    try:
        rows = payload["per_movie_by_arm"][arm]
    except KeyError as error:
        raise KeyError(f"{label} missing arm {arm!r}") from error
    indexed: dict[str, dict] = {}
    for row in rows:
        dataset = str(row["dataset"])
        if dataset in indexed:
            raise ValueError(f"duplicate {label} dataset: {dataset}")
        finite(row["adj_edge_jaccard"], f"{label}.{dataset}.adj_edge_jaccard")
        finite(row["node_recall"], f"{label}.{dataset}.node_recall")
        indexed[dataset] = row
    if not indexed:
        raise ValueError(f"{label} has no per-movie rows")
    return indexed


def recompute_summary(rows: dict[str, dict], label: str) -> dict[str, float | int]:
    """Recompute the checked competition aggregation from sufficient statistics."""
    ordered = [rows[key] for key in sorted(rows)]
    count_names = ("edge_tp", "edge_fp", "edge_fn", "division_tp", "division_fp", "division_fn")
    totals: dict[str, float] = {}
    for name in count_names:
        values = [finite(row[name], f"{label}.{row['dataset']}.{name}") for row in ordered]
        if any(value < 0 or not value.is_integer() for value in values):
            raise ValueError(f"invalid {label} count field {name}: {values!r}")
        totals[name] = sum(values)
    weights = [finite(row["edge_tp"], "edge_tp") + finite(row["edge_fp"], "edge_fp") + finite(row["edge_fn"], "edge_fn") for row in ordered]
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError(f"{label} has zero aggregate edge denominator")
    adjusted = sum(
        weight * finite(row["adj_edge_jaccard"], f"{label}.{row['dataset']}.adj_edge_jaccard")
        for weight, row in zip(weights, ordered)
    ) / total_weight
    edge_denominator = totals["edge_tp"] + totals["edge_fp"] + totals["edge_fn"]
    edge_jaccard = totals["edge_tp"] / edge_denominator
    division_denominator = totals["division_tp"] + totals["division_fp"] + totals["division_fn"]
    division_jaccard = totals["division_tp"] / division_denominator if division_denominator else None
    score = adjusted if division_jaccard is None else adjusted + 0.1 * division_jaccard
    return {
        "n": len(ordered),
        "n_adj": len(ordered),
        "edge_jaccard": edge_jaccard,
        "adj_edge_jaccard": adjusted,
        "division_tp": int(totals["division_tp"]),
        "division_fp": int(totals["division_fp"]),
        "division_fn": int(totals["division_fn"]),
        "node_recall": sum(finite(row["node_recall"], "node_recall") for row in ordered) / len(ordered),
        "score": score,
    }


def validate_summary(payload: dict, arm: str, label: str, rows: dict[str, dict]) -> dict:
    try:
        claimed = payload["summary_by_arm"][arm]
    except KeyError as error:
        raise KeyError(f"{label} missing summary for arm {arm!r}") from error
    computed = recompute_summary(rows, label)
    for key, expected in computed.items():
        if key in ("n", "n_adj", "division_tp", "division_fp", "division_fn"):
            if int(claimed[key]) != expected:
                raise ValueError(f"inconsistent {label} summary {key}: {claimed[key]!r} != {expected!r}")
        elif not math.isclose(finite(claimed[key], f"{label}.summary.{key}"), float(expected), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"inconsistent {label} summary {key}: {claimed[key]!r} != {expected!r}")
    return computed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--arm", default="registered_hungarian")
    parser.add_argument("--absolute-tolerance", type=float, default=1e-12)
    args = parser.parse_args()

    if args.absolute_tolerance < 0.0:
        parser.error("--absolute-tolerance must be nonnegative")
    parent = json.loads(args.parent.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    parent_rows = load_rows(parent, args.arm, "parent")
    candidate_rows = load_rows(candidate, args.arm, "candidate")
    if set(parent_rows) != set(candidate_rows):
        raise ValueError(
            "dataset mismatch: "
            + json.dumps(
                {
                    "parent_only": sorted(set(parent_rows) - set(candidate_rows)),
                    "candidate_only": sorted(set(candidate_rows) - set(parent_rows)),
                },
                sort_keys=True,
            )
        )

    parent_summary = validate_summary(parent, args.arm, "parent", parent_rows)
    candidate_summary = validate_summary(candidate, args.arm, "candidate", candidate_rows)
    parent_score = finite(parent_summary["score"], "parent.score")
    candidate_score = finite(candidate_summary["score"], "candidate.score")
    parent_recall = finite(parent_summary["node_recall"], "parent.node_recall")
    candidate_recall = finite(candidate_summary["node_recall"], "candidate.node_recall")
    per_movie = []
    for dataset in sorted(parent_rows):
        old = finite(parent_rows[dataset]["adj_edge_jaccard"], f"parent.{dataset}.score")
        new = finite(candidate_rows[dataset]["adj_edge_jaccard"], f"candidate.{dataset}.score")
        per_movie.append(
            {
                "dataset": dataset,
                "parent_score": old,
                "candidate_score": new,
                "delta": new - old,
                "parent_node_recall": finite(
                    parent_rows[dataset]["node_recall"], f"parent.{dataset}.node_recall"
                ),
                "candidate_node_recall": finite(
                    candidate_rows[dataset]["node_recall"], f"candidate.{dataset}.node_recall"
                ),
            }
        )

    tolerance = args.absolute_tolerance
    checks = {
        "positive_pooled_score": candidate_score - parent_score > tolerance,
        "no_negative_movie_delta": all(row["delta"] >= -tolerance for row in per_movie),
        "no_pooled_node_recall_regression": candidate_recall - parent_recall >= -tolerance,
    }
    gate_pass = all(checks.values())
    result = {
        "experiment": args.experiment,
        "status": "PASS_PRIVATE_DEVELOPMENT_GATE" if gate_pass else "REJECT_PRIVATE_DEVELOPMENT_GATE",
        "arm": args.arm,
        "inputs": {
            "parent": str(args.parent),
            "parent_sha256": sha256(args.parent),
            "candidate": str(args.candidate),
            "candidate_sha256": sha256(args.candidate),
        },
        "dataset_count": len(per_movie),
        "parent_score": parent_score,
        "candidate_score": candidate_score,
        "pooled_delta": candidate_score - parent_score,
        "parent_node_recall": parent_recall,
        "candidate_node_recall": candidate_recall,
        "node_recall_delta": candidate_recall - parent_recall,
        "per_movie": per_movie,
        "checks": checks,
        "metric_self_consistency": {
            "status": "PASS_RECOMPUTED_FROM_PER_MOVIE_SUFFICIENT_STATISTICS",
            "absolute_tolerance": 1e-12,
        },
        "gate_pass": gate_pass,
        "locked_audit_opened": False,
        "kaggle_submission_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
