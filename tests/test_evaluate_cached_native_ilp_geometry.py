import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_cached_native_ilp_geometry import geometry_filter


def test_geometry_filter_keeps_two_valid_ranked_edges() -> None:
    coords = np.array(
        [[0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 2, 0], [1, 0, 3, 0]],
        dtype=float,
    )
    edges = [(0, 1, 0.8, 1.0), (0, 2, 0.9, 2.0), (0, 3, 0.7, 3.0)]
    kept, stats = geometry_filter(coords, edges, np.ones(3))
    assert {(edge[0], edge[1]) for edge in kept} == {(0, 1), (0, 2)}
    assert stats == {
        "multi_source_count": 1,
        "valid_division_count": 1,
        "bad_division_to_single_count": 0,
        "dropped_edges": 1,
    }


def test_geometry_filter_bad_pair_falls_back_to_top_probability() -> None:
    coords = np.array(
        [[0, 0, 0, 0], [1, 0, 1, 0], [1, 0, 20, 0]],
        dtype=float,
    )
    edges = [(0, 1, 0.8, 1.0), (0, 2, 0.9, 20.0)]
    kept, stats = geometry_filter(coords, edges, np.ones(3))
    assert kept == [(0, 2, 0.9, 20.0)]
    assert stats["bad_division_to_single_count"] == 1
    assert stats["dropped_edges"] == 1
