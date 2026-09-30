import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "reciprocal", ROOT / "scripts" / "analyze_reciprocal_initialization.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def row(dataset: str, tp: int, fp: int, fn: int, recall: float) -> dict:
    denominator = tp + fp + fn
    return {
        "dataset": dataset,
        "edge_tp": tp,
        "edge_fp": fp,
        "edge_fn": fn,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "edge_jaccard": tp / denominator,
        "adj_edge_jaccard": tp / denominator,
        "node_recall": recall,
    }


def payload(rows: list[dict]) -> dict:
    indexed = {item["dataset"]: item for item in rows}
    return {
        "per_movie_by_arm": {"registered_hungarian": rows},
        "summary_by_arm": {
            "registered_hungarian": MODULE.recompute_summary(indexed, "test")
        },
    }


def test_load_pair_rejects_dataset_mismatch(tmp_path: Path) -> None:
    parent = tmp_path / "parent.json"
    candidate = tmp_path / "candidate.json"
    parent.write_text(json.dumps(payload([row("a", 8, 1, 1, 0.8)])))
    candidate.write_text(json.dumps(payload([row("b", 9, 1, 0, 0.9)])))
    try:
        MODULE.load_pair(parent, candidate, "registered_hungarian", "fold")
    except ValueError as error:
        assert "dataset mismatch" in str(error)
    else:
        raise AssertionError("dataset mismatch was accepted")


def test_delta_reports_score_recall_and_divisions() -> None:
    parent = {
        "score": 0.5,
        "node_recall": 0.8,
        "division_tp": 2,
        "division_fp": 3,
        "division_fn": 4,
    }
    candidate = {
        "score": 0.6,
        "node_recall": 0.85,
        "division_tp": 3,
        "division_fp": 2,
        "division_fn": 4,
    }
    assert MODULE.delta(candidate, parent) == {
        "score": 0.09999999999999998,
        "node_recall": 0.04999999999999993,
        "division_tp": 1,
        "division_fp": -1,
        "division_fn": 0,
    }
