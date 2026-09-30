import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp210_centroid_safety_veto import CENTROID_ARM, build


def row(name, edge_tp):
    return {
        "dataset": name, "edge_tp": edge_tp, "edge_fp": 1, "edge_fn": 2,
        "division_tp": 0, "division_fp": 0, "division_fn": 1,
        "num_pred_nodes": 10, "node_recall": 0.8, "total_node_ratio": 1.0,
        "edge_jaccard": edge_tp / (edge_tp + 3), "adj_edge_jaccard": edge_tp / (edge_tp + 3),
    }


def confirmation(forward_base, reverse_base, forward_selected, reverse_selected, score=0.0):
    return {
        "directions": {
            "forward": {"base_rows": forward_base, "selected_rows": forward_selected},
            "reverse": {"base_rows": reverse_base, "selected_rows": reverse_selected},
        },
        "combined": {"frozen_selected": {"score": score}},
    }


def test_uses_translation_only_above_frozen_fragmentation_threshold():
    names = [f"6bba_{i:04x}.zarr" for i in range(116)]
    translation = [row(name, 10) for name in names]
    centroid = [row(name, 11) for name in names]
    telemetry = []
    for index, name in enumerate(names):
        added = 6 if index == 0 else 5
        telemetry.append({
            "dataset": name,
            "nodes": 1000,
            "translation_filter": {"nodes_removed": 100},
            f"{CENTROID_ARM}_filter": {"nodes_removed": 100 + added},
        })
    chunk = {
        "status": "PASS_FIXED_INTENSITY_CENTROID_REFINEMENT",
        "per_movie_by_arm": {"translation": translation, CENTROID_ARM: centroid},
        "telemetry": telemetry,
    }
    reverse = [row(f"44b6_{i:04x}.zarr", 10) for i in range(59)]
    exp195 = confirmation(translation, reverse, translation, reverse)
    exp206 = confirmation(translation, reverse, centroid, reverse, score=0.5)
    result = build([chunk], exp195, exp206, 0.005, {})
    assert result["safety_veto"]["translation_movies"] == 1
    assert result["safety_veto"]["centroid_movies"] == 115
    assert result["safety_veto"]["decisions"][0]["selected_arm"] == "translation"
    assert result["control_maximum_absolute_error"] == 0
    assert result["centroid_parent_maximum_absolute_error"] == 0
