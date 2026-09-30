import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_safe_division_repair import add_safe_divisions


def test_adds_one_divergent_orphan_as_second_daughter() -> None:
    coords = np.asarray([
        [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, -1, 0],
        [2, 0, 3, 0], [2, 0, -3, 0],
    ], dtype=float)
    links = [(0, 1, 1.0, 1.0), (1, 3, 1.0, 2.0), (2, 4, 1.0, 2.0)]
    result, stats = add_safe_divisions(coords, links, np.ones(3), min_divergence_growth_um=1.0)
    assert len(result) == 4
    assert (0, 2) == result[-1][:2]
    assert stats["accepted"] == 1


def test_rejects_nondivergent_orphan() -> None:
    coords = np.asarray([
        [0, 0, 0, 0], [1, 0, 1, 0], [1, 0, -1, 0],
        [2, 0, 1.5, 0], [2, 0, -1.5, 0],
    ], dtype=float)
    links = [(0, 1, 1.0, 1.0), (1, 3, 1.0, 0.5), (2, 4, 1.0, 0.5)]
    result, stats = add_safe_divisions(coords, links, np.ones(3))
    assert result == links
    assert stats["accepted"] == 0
