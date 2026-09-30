"""Fail-closed gate for the source-selected reciprocal scratch-seed consensus."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from compare_registered_candidate import load_rows, recompute_summary, validate_summary


BASE_ARM = "registered_hungarian"
CONSENSUS_ARM = {
    "314159": "scratch_topology_consensus_coords",
    "271828": "zebrahub_topology_consensus_coords",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def combine_parent(paths: list[Path], label: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for path in paths:
        payload = read(path)
        part = load_rows(payload, BASE_ARM, f"{label}:{path.name}")
        validate_summary(payload, BASE_ARM, f"{label}:{path.name}", part)
        overlap = set(rows) & set(part)
        if overlap:
            raise ValueError(f"duplicate {label} datasets: {sorted(overlap)}")
        rows.update(part)
    return rows


def evaluate_fold(
    fold: str,
    selected_seed: str,
    seed314_parts: list[Path],
    seed271_path: Path,
    consensus_path: Path,
) -> dict:
    if selected_seed not in CONSENSUS_ARM:
        raise ValueError(f"unsupported selected seed for {fold}: {selected_seed}")
    if selected_seed == "314159":
        parent_rows = combine_parent(seed314_parts, f"{fold}.seed314159")
        parent_paths = seed314_parts
    else:
        parent_payload = read(seed271_path)
        parent_rows = load_rows(parent_payload, BASE_ARM, f"{fold}.seed271828")
        validate_summary(parent_payload, BASE_ARM, f"{fold}.seed271828", parent_rows)
        parent_paths = [seed271_path]

    candidate_payload = read(consensus_path)
    candidate_arm = CONSENSUS_ARM[selected_seed]
    candidate_rows = load_rows(candidate_payload, candidate_arm, f"{fold}.consensus")
    candidate_summary = validate_summary(
        candidate_payload, candidate_arm, f"{fold}.consensus", candidate_rows
    )
    if set(parent_rows) != set(candidate_rows) or len(parent_rows) != 12:
        raise ValueError(f"{fold} expected the same 12 parent/candidate movies")
    parent_summary = recompute_summary(parent_rows, f"{fold}.parent")
    movie_deltas = [
        {
            "dataset": dataset,
            "parent": parent_rows[dataset],
            "candidate": candidate_rows[dataset],
            "score_delta": float(candidate_rows[dataset]["adj_edge_jaccard"])
            - float(parent_rows[dataset]["adj_edge_jaccard"]),
            "node_recall_delta": float(candidate_rows[dataset]["node_recall"])
            - float(parent_rows[dataset]["node_recall"]),
        }
        for dataset in sorted(parent_rows)
    ]
    delta = {
        "score": candidate_summary["score"] - parent_summary["score"],
        "node_recall": candidate_summary["node_recall"] - parent_summary["node_recall"],
        "division_tp": candidate_summary["division_tp"] - parent_summary["division_tp"],
    }
    return {
        "selected_topology_seed": selected_seed,
        "parent_inputs": [
            {"path": str(path), "sha256": sha256(path)} for path in parent_paths
        ],
        "candidate_input": {"path": str(consensus_path), "sha256": sha256(consensus_path)},
        "parent": parent_summary,
        "candidate": candidate_summary,
        "delta": delta,
        "per_movie": movie_deltas,
        "nonnegative_movies": sum(row["score_delta"] >= 0.0 for row in movie_deltas),
        "worst_movie_score_delta": min(row["score_delta"] for row in movie_deltas),
    }


def resampled_summary(rows: list[dict], indices: list[int], label: str) -> dict:
    duplicated = {}
    for draw, index in enumerate(indices):
        item = dict(rows[index])
        item["dataset"] = f"{item['dataset']}#draw{draw}"
        duplicated[item["dataset"]] = item
    return recompute_summary(duplicated, label)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def uncertainty(folds: dict, draws: int = 10_000, seed: int = 146) -> dict:
    rng = random.Random(seed)
    bootstrap_deltas = []
    for draw in range(draws):
        parent_sample = []
        candidate_sample = []
        for fold in folds.values():
            rows = fold["per_movie"]
            indices = [rng.randrange(len(rows)) for _ in rows]
            for local_draw, index in enumerate(indices):
                parent = dict(rows[index]["parent"])
                candidate = dict(rows[index]["candidate"])
                suffix = f"#boot{draw}-{local_draw}"
                parent["dataset"] += suffix
                candidate["dataset"] += suffix
                parent_sample.append(parent)
                candidate_sample.append(candidate)
        parent = recompute_summary(
            {row["dataset"]: row for row in parent_sample}, "bootstrap.parent"
        )
        candidate = recompute_summary(
            {row["dataset"]: row for row in candidate_sample}, "bootstrap.candidate"
        )
        bootstrap_deltas.append(candidate["score"] - parent["score"])

    all_rows = [row for fold in folds.values() for row in fold["per_movie"]]
    loo = []
    for omitted in all_rows:
        kept = [row for row in all_rows if row["dataset"] != omitted["dataset"]]
        parent = recompute_summary(
            {row["dataset"]: row["parent"] for row in kept}, "loo.parent"
        )
        candidate = recompute_summary(
            {row["dataset"]: row["candidate"] for row in kept}, "loo.candidate"
        )
        loo.append({"omitted": omitted["dataset"], "score_delta": candidate["score"] - parent["score"]})
    return {
        "method": "stratified movie bootstrap within each of the two observed embryo domains",
        "draws": draws,
        "seed": seed,
        "score_delta_percentile_95": [
            quantile(bootstrap_deltas, 0.025), quantile(bootstrap_deltas, 0.975)
        ],
        "probability_score_delta_positive": sum(value > 0 for value in bootstrap_deltas) / draws,
        "leave_one_movie_out": loo,
        "worst_leave_one_movie_out_delta": min(row["score_delta"] for row in loo),
        "scope_warning": "Conditional finite-movie sensitivity for 44b6 and 6bba only; not a population interval for unseen embryos or the post-close private leaderboard."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--forward-seed314-development", type=Path, required=True)
    parser.add_argument("--forward-seed314-locked", type=Path, required=True)
    parser.add_argument("--forward-seed271", type=Path, required=True)
    parser.add_argument("--forward-consensus", type=Path, required=True)
    parser.add_argument("--reverse-seed314-development", type=Path, required=True)
    parser.add_argument("--reverse-seed314-locked", type=Path, required=True)
    parser.add_argument("--reverse-seed271", type=Path, required=True)
    parser.add_argument("--reverse-consensus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    selection = read(args.selection)
    if selection.get("status") != "FROZEN_FROM_SOURCE_ONLY_BEFORE_TARGET_INFERENCE":
        raise ValueError("source-only selection receipt is missing or invalid")
    selected = selection.get("selected_topology_seed", {})
    folds = {
        "44b6_to_6bba": evaluate_fold(
            "44b6_to_6bba", selected.get("44b6_to_6bba"),
            [args.forward_seed314_development, args.forward_seed314_locked],
            args.forward_seed271, args.forward_consensus,
        ),
        "6bba_to_44b6": evaluate_fold(
            "6bba_to_44b6", selected.get("6bba_to_44b6"),
            [args.reverse_seed314_development, args.reverse_seed314_locked],
            args.reverse_seed271, args.reverse_consensus,
        ),
    }
    all_parent = {}
    all_candidate = {}
    for fold in folds.values():
        parent_paths = [Path(item["path"]) for item in fold["parent_inputs"]]
        if fold["selected_topology_seed"] == "314159":
            parent_rows = combine_parent(parent_paths, "pooled.parent")
        else:
            payload = read(parent_paths[0])
            parent_rows = load_rows(payload, BASE_ARM, "pooled.parent")
        candidate_payload = read(Path(fold["candidate_input"]["path"]))
        candidate_rows = load_rows(
            candidate_payload, CONSENSUS_ARM[fold["selected_topology_seed"]], "pooled.candidate"
        )
        if set(all_parent) & set(parent_rows):
            raise ValueError("duplicate datasets across reciprocal folds")
        all_parent.update(parent_rows)
        all_candidate.update(candidate_rows)
    pooled_parent = recompute_summary(all_parent, "pooled.parent")
    pooled_candidate = recompute_summary(all_candidate, "pooled.candidate")
    pooled_delta = {
        "score": pooled_candidate["score"] - pooled_parent["score"],
        "node_recall": pooled_candidate["node_recall"] - pooled_parent["node_recall"],
        "division_tp": pooled_candidate["division_tp"] - pooled_parent["division_tp"],
    }
    checks = {
        "positive_score_each_embryo": all(f["delta"]["score"] > 0 for f in folds.values()),
        "positive_pooled_score": pooled_delta["score"] > 0,
        "nonnegative_recall_each_embryo": all(
            f["delta"]["node_recall"] >= 0 for f in folds.values()
        ),
        "at_least_8_of_12_nonnegative_movies_each_embryo": all(
            f["nonnegative_movies"] >= 8 for f in folds.values()
        ),
        "worst_movie_delta_at_least_minus_0_01_each_embryo": all(
            f["worst_movie_score_delta"] >= -0.01 for f in folds.values()
        ),
        "no_division_tp_loss_each_embryo": all(
            f["delta"]["division_tp"] >= 0 for f in folds.values()
        ),
    }
    gate_pass = all(checks.values())
    receipt = {
        "experiment": "EXP146",
        "status": "PASS_PROSPECTIVE_FULL_OOF_GATE" if gate_pass else "REJECT_PROSPECTIVE_FULL_OOF_GATE",
        "selection": {
            "path": str(args.selection), "sha256": sha256(args.selection),
            "selected_topology_seed": selected,
        },
        "folds": folds,
        "pooled": {"parent": pooled_parent, "candidate": pooled_candidate, "delta": pooled_delta},
        "checks": checks,
        "uncertainty": uncertainty(folds),
        "metric_self_consistency": "PASS_RECOMPUTED_FROM_PER_MOVIE_SUFFICIENT_STATISTICS",
        "former_locked_warning": "EXP144 already opened 16 movies for a different hypothesis; this is candidate-specific prospective full OOF, not an untouched locked audit.",
        "gate_pass": gate_pass,
        "kaggle_submission_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
