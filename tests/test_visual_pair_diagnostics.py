from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from diagnose_visual_pair_errors import geometry_bins, selected_parent_keys, top_parent_rows


def test_top_parent_rows_tracks_positive_rank():
    keys = [("a", 1), ("a", 1), ("a", 1), ("b", 2)]
    rows = top_parent_rows(keys, [0, 1, 0, 0], [0.9, 0.8, 0.1, 0.5])
    assert rows[("a", 1)]["top_label"] == 0
    assert rows[("a", 1)]["positive_rank"] == 2
    assert rows[("b", 2)]["positive_rank"] is None


def test_selected_parent_keys_uses_precision_gate():
    rows = {
        ("a", 1): {"top_score": 0.9, "top_label": 1},
        ("b", 2): {"top_score": 0.8, "top_label": 0},
        ("c", 3): {"top_score": 0.7, "top_label": 1},
    }
    assert selected_parent_keys(rows, 2) == set(rows)


def test_geometry_bins_are_complete():
    rows = [
        {"positive_sister_um": 1.0, "scratch_positive_rank": 1,
         "feature_positive_rank": 2, "ensemble_positive_rank": 1},
        {"positive_sister_um": 9.0, "scratch_positive_rank": 2,
         "feature_positive_rank": 1, "ensemble_positive_rank": 1},
    ]
    bins = geometry_bins(rows)
    assert sum(row["division_parents"] for row in bins) == 2
    assert bins[0]["scratch_top_pair_recall"] == 1.0
