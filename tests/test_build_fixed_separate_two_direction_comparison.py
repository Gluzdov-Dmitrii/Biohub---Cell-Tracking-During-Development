import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_fixed_separate_two_direction_comparison import build


def payload(prefix: str, arm: str, fp: int) -> dict:
    return {
        "per_movie_by_arm": {
            arm: [
                {
                    "dataset": f"{prefix}_{index}",
                    "edge_tp": 10 + index,
                    "edge_fp": fp,
                    "edge_fn": 2,
                    "division_tp": 0,
                    "division_fp": 0,
                    "division_fn": 0,
                    "num_pred_nodes": 20,
                    "node_recall": 0.8,
                    "total_node_ratio": 0.0,
                    "edge_jaccard": (10 + index) / (12 + index + fp),
                    "adj_edge_jaccard": (10 + index) / (12 + index + fp),
                }
                for index in range(2)
            ]
        }
    }


def test_builds_fixed_comparison_from_four_files() -> None:
    result = build(
        payload("6bba", "base", 3),
        payload("6bba", "candidate", 1),
        payload("44b6", "base", 3),
        payload("44b6", "candidate", 1),
        "base",
        "candidate",
        expected_forward=2,
        expected_reverse=2,
    )
    assert result["combined"]["delta"] > 0
    assert result["selection"] == "none"


def test_rejects_unpaired_coverage() -> None:
    candidate = payload("6bba", "candidate", 1)
    candidate["per_movie_by_arm"]["candidate"][0]["dataset"] = "6bba_other"
    with pytest.raises(ValueError, match="paired coverage mismatch"):
        build(
            payload("6bba", "base", 3),
            candidate,
            payload("44b6", "base", 3),
            payload("44b6", "candidate", 1),
            "base",
            "candidate",
            expected_forward=2,
            expected_reverse=2,
        )


def test_supports_direction_specific_arm_names() -> None:
    result = build(
        payload("6bba", "base_f", 3),
        payload("6bba", "candidate_f", 1),
        payload("44b6", "base_r", 3),
        payload("44b6", "candidate_r", 1),
        "base_f",
        "candidate_f",
        expected_forward=2,
        expected_reverse=2,
        base_reverse_arm="base_r",
        candidate_reverse_arm="candidate_r",
    )
    assert result["directions"]["reverse"]["base_arm"] == "base_r"
    assert result["combined"]["delta"] > 0
