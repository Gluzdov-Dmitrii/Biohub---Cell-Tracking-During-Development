from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from train_parent_calibrated_pair import (
    choose_top_candidates,
    select_parent_operating,
    shard_time,
    symmetric_pair_features,
)


def test_shard_time():
    assert shard_time(Path("train_0476.npz")) == 476


def test_choose_top_candidates_reports_margin_and_label():
    vector = np.asarray([1.0, 2.0], dtype=np.float32)
    rows = [(2, 0, 0.3, vector), (1, 0, 0.4, vector), (1, 1, 0.9, vector)]
    chosen = choose_top_candidates(rows)
    assert chosen[0][0:4] == (1, 1, 0.9, 0.5)


def test_symmetric_features_ignore_daughter_order():
    parent = torch.randn(3, 32)
    a = torch.randn(3, 32)
    b = torch.randn(3, 32)
    geometry = torch.randn(3, 5)
    first = symmetric_pair_features(parent, a, b, geometry)
    second = symmetric_pair_features(parent, b, a, geometry)
    assert first.shape == (3, 101)
    assert torch.equal(first, second)


def test_operating_recall_uses_all_covered_divisions():
    result = select_parent_operating(
        [("a", 1), ("b", 2), ("c", 3)],
        np.asarray([1, 0, 1]),
        np.asarray([0.9, 0.8, 0.7]),
        true_parent_count=4,
    )
    assert result["true_positive_parents"] == 2
    assert result["recall"] == 0.5
    assert result["true_parents"] == 4
