import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_native_guided_division import add_native_guided_divisions


def test_native_guided_division_adds_valid_continuing_second_child() -> None:
    coords = np.array([
        [0, 0, 0, 0],
        [1, 0, 1, 0],
        [1, 0, 2, 0],
        [2, 0, 4, 0],
        [2, 0, 0, 0],
    ], dtype=float)
    links = [(0, 1, 0.9, 1.0), (1, 3, 0.9, 3.0), (2, 4, 0.9, 2.0)]
    native = [(0, 2, 0.95, 2.0)]
    result, stats = add_native_guided_divisions(coords, links, native, np.ones(3))
    assert (0, 2, 0.95, 2.0) in result
    assert stats["accepted"] == 1
    assert stats["maximum_out_degree"] == 2


def test_native_guided_division_rejects_non_diverging_pair() -> None:
    coords = np.array([
        [0, 0, 0, 0],
        [1, 0, 1, 0],
        [1, 0, 2, 0],
        [2, 0, 2, 0],
        [2, 0, 3, 0],
    ], dtype=float)
    links = [(0, 1, 0.9, 1.0), (1, 3, 0.9, 1.0), (2, 4, 0.9, 1.0)]
    result, stats = add_native_guided_divisions(
        coords, links, [(0, 2, 0.95, 2.0)], np.ones(3)
    )
    assert result == links
    assert stats["accepted"] == 0
    assert stats["rejected"]["divergence"] == 1
