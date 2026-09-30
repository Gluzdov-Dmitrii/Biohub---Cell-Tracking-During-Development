import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_fixed_two_direction_comparison import build


def metric(dataset, tp):
    return {
        "dataset": dataset,
        "edge_tp": tp,
        "edge_fp": 2,
        "edge_fn": 3,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "node_recall": 0.9,
        "total_node_ratio": 1.0,
        "adj_edge_jaccard": tp / (tp + 5),
    }


def test_builds_fixed_paired_comparison_without_selection():
    forward = {"per_movie_by_arm": {
        "base": [metric("6bba_a.zarr", 10)],
        "candidate": [metric("6bba_a.zarr", 11)],
    }}
    reverse = {"per_movie_by_arm": {
        "base": [metric("44b6_a.zarr", 10)],
        "candidate": [metric("44b6_a.zarr", 12)],
    }}
    result = build(forward, reverse, "base", "candidate", 1, 1)
    assert result["selection"] == "none"
    assert result["combined"]["delta"] > 0
    assert result["directions"]["forward"]["fixed_arm"] == "candidate"


def test_rejects_wrong_direction_prefix():
    forward = {"per_movie_by_arm": {
        "base": [metric("44b6_wrong.zarr", 10)],
        "candidate": [metric("44b6_wrong.zarr", 11)],
    }}
    reverse = {"per_movie_by_arm": {
        "base": [metric("44b6_a.zarr", 10)],
        "candidate": [metric("44b6_a.zarr", 11)],
    }}
    try:
        build(forward, reverse, "base", "candidate", 1, 1)
    except ValueError as error:
        assert "prefix" in str(error)
    else:
        raise AssertionError("wrong prefix must fail")
