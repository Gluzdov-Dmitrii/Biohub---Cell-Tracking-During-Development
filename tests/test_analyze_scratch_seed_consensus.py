import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "seed_consensus", ROOT / "scripts" / "analyze_scratch_seed_consensus.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def row(dataset: str, tp: int = 8) -> dict:
    return {
        "dataset": dataset, "edge_tp": tp, "edge_fp": 1, "edge_fn": 1,
        "division_tp": 0, "division_fp": 0, "division_fn": 0,
        "edge_jaccard": tp / (tp + 2), "adj_edge_jaccard": tp / (tp + 2),
        "node_recall": 0.9,
    }


def payload(arm: str, rows: list[dict]) -> dict:
    indexed = {item["dataset"]: item for item in rows}
    return {
        "per_movie_by_arm": {arm: rows},
        "summary_by_arm": {arm: MODULE.recompute_summary(indexed, "test")},
    }


def test_combine_parent_rejects_duplicate_movies(tmp_path: Path) -> None:
    paths = []
    for name in ("a", "b"):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload(MODULE.BASE_ARM, [row("same")])))
        paths.append(path)
    try:
        MODULE.combine_parent(paths, "fold")
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate movie was accepted")


def test_evaluate_fold_requires_twelve_matching_movies(tmp_path: Path) -> None:
    base = tmp_path / "base.json"
    seed = tmp_path / "seed.json"
    consensus = tmp_path / "consensus.json"
    base.write_text(json.dumps(payload(MODULE.BASE_ARM, [row("one")])))
    seed.write_text(json.dumps(payload(MODULE.BASE_ARM, [row("one")])))
    consensus.write_text(
        json.dumps(payload(MODULE.CONSENSUS_ARM["314159"], [row("one", 9)]))
    )
    try:
        MODULE.evaluate_fold("fold", "314159", [base], seed, consensus)
    except ValueError as error:
        assert "12" in str(error)
    else:
        raise AssertionError("short fold was accepted")


def test_evaluate_fold_returns_success_receipt_for_twelve_movies(tmp_path: Path) -> None:
    base_rows = [row(f"m{i}", 8) for i in range(12)]
    candidate_rows = [row(f"m{i}", 9) for i in range(12)]
    base = tmp_path / "base.json"
    seed = tmp_path / "seed.json"
    consensus = tmp_path / "consensus.json"
    base.write_text(json.dumps(payload(MODULE.BASE_ARM, base_rows)))
    seed.write_text(json.dumps(payload(MODULE.BASE_ARM, base_rows)))
    consensus.write_text(json.dumps(payload(
        MODULE.CONSENSUS_ARM["314159"], candidate_rows
    )))
    receipt = MODULE.evaluate_fold("fold", "314159", [base], seed, consensus)
    assert receipt["selected_topology_seed"] == "314159"
    assert receipt["delta"]["score"] > 0
    assert receipt["nonnegative_movies"] == 12


def test_quantile_interpolates_and_bootstrap_is_deterministic() -> None:
    assert MODULE.quantile([0.0, 10.0], 0.25) == 2.5
    fold_rows = []
    for index in range(12):
        parent = row(f"m{index}", 8)
        candidate = row(f"m{index}", 9)
        fold_rows.append({
            "dataset": f"m{index}", "parent": parent, "candidate": candidate,
            "score_delta": candidate["adj_edge_jaccard"] - parent["adj_edge_jaccard"],
            "node_recall_delta": 0.0,
        })
    folds = {"a": {"per_movie": fold_rows}, "b": {"per_movie": [
        {**item, "dataset": "b" + item["dataset"],
         "parent": {**item["parent"], "dataset": "b" + item["dataset"]},
         "candidate": {**item["candidate"], "dataset": "b" + item["dataset"]}}
        for item in fold_rows
    ]}}
    first = MODULE.uncertainty(folds, draws=20, seed=7)
    second = MODULE.uncertainty(folds, draws=20, seed=7)
    assert first == second
    assert first["probability_score_delta_positive"] == 1.0
