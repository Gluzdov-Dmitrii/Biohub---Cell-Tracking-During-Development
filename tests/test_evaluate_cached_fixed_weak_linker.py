from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_fixed_weak_linker import cached_edges


def test_cached_edges_preserve_ids_probabilities_and_distances() -> None:
    payload = {
        "edge_source": np.asarray([1, 4], dtype=np.int64),
        "edge_target": np.asarray([2, 5], dtype=np.int64),
        "edge_probability": np.asarray([0.25, 0.75], dtype=np.float32),
        "edge_distance": np.asarray([3.5, 1.25], dtype=np.float32),
    }
    assert cached_edges(payload) == [
        (1, 2, 0.25, 3.5),
        (4, 5, 0.75, 1.25),
    ]
