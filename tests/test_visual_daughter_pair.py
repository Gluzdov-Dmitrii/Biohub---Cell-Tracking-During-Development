from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "train_visual_daughter_pair", ROOT / "scripts/train_visual_daughter_pair.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_model_is_exactly_daughter_swap_invariant():
    torch.manual_seed(2)
    model = MODULE.VisualDaughterPair().eval()
    parent = torch.randn(3, 1, 11, 11, 11)
    first = torch.randn_like(parent)
    second = torch.randn_like(parent)
    geometry = torch.randn(3, 5)
    with torch.no_grad():
        forward = model(parent, first, second, geometry)
        swapped = model(parent, second, first, geometry)
    assert torch.equal(forward, swapped)


def test_pair_enumeration_is_deterministic_and_labels_true_pair():
    coords = np.asarray([
        [0, 5, 5, 5],
        [0, 20, 20, 20],
        [1, 4, 5, 5],
        [1, 6, 5, 5],
        [1, 21, 20, 20],
        [1, 22, 20, 20],
    ], dtype=np.float32)
    edges = np.asarray([[0, 2], [0, 3], [1, 4]], dtype=np.int64)
    kwargs = dict(nearest_k=3, include_all_negatives=True, ordinary_parent_fraction=1.0, shard_key="x")
    first, stats = MODULE.enumerate_pair_examples(coords, edges, np.ones(3), **kwargs)
    second, _ = MODULE.enumerate_pair_examples(coords, edges, np.ones(3), **kwargs)
    assert first == second
    positives = [row for row in first if row.label]
    assert len(positives) == 1
    assert {positives[0].daughter_a, positives[0].daughter_b} == {2, 3}
    assert stats["division_parents"] == 1
    assert stats["division_pairs_covered"] == 1


def test_validation_discovery_rejects_non_external_patterns(tmp_path):
    with pytest.raises(ValueError, match="frozen external"):
        MODULE.discover_external_shards(tmp_path, "target_*.npz")


def test_parent_threshold_counts_only_top_pair_per_parent():
    rows = [
        ("a", 0, 1, 0.9),
        ("a", 0, 0, 0.8),
        ("a", 1, 0, 0.7),
        ("a", 2, 1, 0.6),
        ("a", 3, 0, 0.1),
    ]
    result = MODULE.select_parent_threshold(rows)
    assert result["true_parents"] == 2
    assert result["true_positive_parents"] == 2
    assert result["predicted_parents"] == 3
    assert result["precision"] == pytest.approx(2 / 3)
    assert result["recall"] == 1.0
