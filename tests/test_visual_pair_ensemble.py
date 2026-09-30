from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "evaluate_visual_pair_ensemble", ROOT / "scripts/evaluate_visual_pair_ensemble.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_percentile_ranks_are_stable_and_monotone():
    scores = np.asarray([0.2, 0.1, 0.9, 0.4])
    ranks = MODULE.percentile_ranks(scores)
    assert ranks.tolist() == [1 / 3, 0.0, 1.0, 2 / 3]


def test_percentile_ranks_single_value():
    assert MODULE.percentile_ranks(np.asarray([0.2])).tolist() == [1.0]
