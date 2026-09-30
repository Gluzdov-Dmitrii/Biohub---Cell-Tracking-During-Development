import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_exp193_mechanism_diversity import pearson, rank


def test_rank_uses_average_ties():
    assert rank([3.0, 1.0, 1.0, 2.0]) == [3.0, 0.5, 0.5, 2.0]


def test_correlations():
    assert abs(pearson([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-12
    assert abs(pearson([1, 2, 3], [6, 4, 2]) + 1.0) < 1e-12
    assert pearson([1, 1], [2, 3]) is None
