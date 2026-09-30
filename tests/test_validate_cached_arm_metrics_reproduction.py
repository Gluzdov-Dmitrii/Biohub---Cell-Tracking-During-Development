import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_cached_arm_metrics_reproduction import compare


def payload(arm: str) -> dict:
    return {
        "per_movie_by_arm": {
            arm: [
                {
                    "dataset": "6bba_a.zarr",
                    "edge_tp": 3,
                    "edge_fp": 1,
                    "edge_fn": 2,
                    "division_tp": 0,
                    "division_fp": 0,
                    "division_fn": 1,
                    "num_pred_nodes": 5,
                    "node_recall": 0.8,
                    "total_node_ratio": -0.1,
                    "edge_jaccard": 0.5,
                    "adj_edge_jaccard": 0.55,
                }
            ]
        }
    }


def test_accepts_exact_metrics_under_different_arm_names() -> None:
    result = compare(payload("raw"), payload("cached"), "raw", "cached")
    assert result["maximum_absolute_error"] == 0.0


def test_rejects_metric_drift() -> None:
    candidate = copy.deepcopy(payload("cached"))
    candidate["per_movie_by_arm"]["cached"][0]["edge_tp"] = 4
    with pytest.raises(ValueError, match="exceeds"):
        compare(payload("raw"), candidate, "raw", "cached")
