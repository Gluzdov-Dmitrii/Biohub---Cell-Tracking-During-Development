import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_cached_native_ilp import degrees


def test_degrees_counts_divisions_and_constraints() -> None:
    edges = [(0, 1, 0.9, 1.0), (0, 2, 0.8, 1.2), (1, 3, 0.9, 1.0)]
    assert degrees(edges) == (1, 2, 1)


def test_degrees_detects_duplicate_incoming() -> None:
    edges = [(0, 2, 0.9, 1.0), (1, 2, 0.8, 1.2)]
    assert degrees(edges) == (2, 1, 0)
