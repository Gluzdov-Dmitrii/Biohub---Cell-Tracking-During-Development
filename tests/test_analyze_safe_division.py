import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "safe_gate", ROOT / "scripts" / "analyze_safe_division.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def row(dataset: str, tp: int, div_tp: int = 0, div_fp: int = 0, div_fn: int = 1) -> dict:
    denominator = tp + 2
    return {
        "dataset": dataset,
        "edge_tp": tp, "edge_fp": 1, "edge_fn": 1,
        "division_tp": div_tp, "division_fp": div_fp, "division_fn": div_fn,
        "edge_jaccard": tp / denominator, "adj_edge_jaccard": tp / denominator,
        "node_recall": 0.9,
    }


def test_load_fold_recomputes_both_arms(tmp_path: Path) -> None:
    parent = [row(f"m{i}", 8) for i in range(12)]
    candidate = [row(f"m{i}", 9, div_tp=1, div_fn=0) for i in range(12)]
    payload = {
        "per_movie_by_arm": {
            MODULE.PARENT_ARM: parent,
            MODULE.CANDIDATE_ARM: candidate,
        },
        "summary_by_arm": {
            MODULE.PARENT_ARM: MODULE.recompute_summary({r["dataset"]: r for r in parent}, "p"),
            MODULE.CANDIDATE_ARM: MODULE.recompute_summary({r["dataset"]: r for r in candidate}, "c"),
        },
    }
    path = tmp_path / "fold.json"
    path.write_text(json.dumps(payload))
    parent_rows, candidate_rows, receipt = MODULE.load_fold(path, "fold")
    assert len(parent_rows) == len(candidate_rows) == 12
    assert receipt["delta"]["division_tp"] == 12
    assert receipt["delta"]["score"] > 0


def test_load_fold_rejects_short_movie_set(tmp_path: Path) -> None:
    rows = [row("only", 8)]
    summary = MODULE.recompute_summary({"only": rows[0]}, "one")
    payload = {
        "per_movie_by_arm": {MODULE.PARENT_ARM: rows, MODULE.CANDIDATE_ARM: rows},
        "summary_by_arm": {MODULE.PARENT_ARM: summary, MODULE.CANDIDATE_ARM: summary},
    }
    path = tmp_path / "short.json"
    path.write_text(json.dumps(payload))
    try:
        MODULE.load_fold(path, "fold")
    except ValueError as error:
        assert "12" in str(error)
    else:
        raise AssertionError("short fold was accepted")
