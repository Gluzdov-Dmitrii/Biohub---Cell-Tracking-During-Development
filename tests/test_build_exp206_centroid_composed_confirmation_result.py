import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp206_centroid_composed_confirmation_result import compose


def metric(name, tp):
    return {
        "dataset": name, "edge_tp": tp, "edge_fp": 2, "edge_fn": 3,
        "division_tp": 0, "division_fp": 0, "division_fn": 0,
        "num_pred_nodes": 20, "node_recall": 0.9, "total_node_ratio": 1.0,
        "edge_jaccard": tp / (tp + 5), "adj_edge_jaccard": tp / (tp + 5),
    }


def test_composes_forward_centroid_with_reverse_gate():
    forward_base = [metric(f"6bba_{i:04x}.zarr", 9) for i in range(3)]
    forward_parent = [metric(f"6bba_{i:04x}.zarr", 10) for i in range(3)]
    reverse_base = [metric(f"44b6_{i:04x}.zarr", 9) for i in range(2)]
    reverse_parent = [metric(f"44b6_{i:04x}.zarr", 11) for i in range(2)]
    exp195 = {"directions": {
        "forward": {"base_rows": forward_base, "selected_rows": forward_parent},
        "reverse": {"base_rows": reverse_base, "selected_rows": reverse_parent},
    }}
    centroid = {"per_movie_by_arm": {
        "translation": forward_parent,
        "intensity_centroid_r2_5_5": [metric(f"6bba_{i:04x}.zarr", 12) for i in range(3)],
    }}
    result = compose(exp195, centroid, expected_forward=3)
    assert result["forward_parent_control_maximum_absolute_error"] == 0.0
    assert result["incremental_vs_exp195"]["delta"] > 0
    assert result["combined"]["frozen_selected"]["n"] == 5
    assert "first confirmation" in result["selection_provenance"]
