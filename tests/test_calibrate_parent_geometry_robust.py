from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from calibrate_parent_geometry_robust import select_robust_threshold, wilson_lower


def test_wilson_lower_is_below_observed_precision():
    lower = wilson_lower(np.asarray([8]), np.asarray([10]))[0]
    assert 0.5 < lower < 0.8


def test_robust_threshold_requires_statistical_precision_margin():
    labels = np.asarray([1] * 20 + [0] * 5 + [1] + [0] * 20)
    scores = np.linspace(1.0, 0.0, len(labels))
    selected = select_robust_threshold(labels, scores, true_parents=21)
    assert selected["precision_wilson_lower"] >= 0.5
    assert selected["threshold"] > 0.0
