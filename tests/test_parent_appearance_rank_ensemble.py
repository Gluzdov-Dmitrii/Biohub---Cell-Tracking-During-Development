import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from train_parent_appearance_rank_ensemble import apply_threshold, percentile_ranks, select_threshold


def test_percentile_ranks_preserve_order():
    scores = np.array([0.2, 0.9, 0.4])
    ranks = percentile_ranks(scores)
    assert list(np.argsort(ranks)) == [0, 2, 1]


def test_threshold_is_selected_on_calibration_and_applied_verbatim():
    labels = np.array([1, 0, 1, 0], dtype=np.float32)
    scores = np.array([0.9, 0.8, 0.7, 0.1])
    selected = select_threshold(labels, scores, true_parents=2)
    assert selected["threshold"] == 0.7
    measured = apply_threshold(labels, scores, selected["threshold"], true_parents=2)
    assert measured["true_positive_parents"] == 2
    assert measured["predicted_parents"] == 3
