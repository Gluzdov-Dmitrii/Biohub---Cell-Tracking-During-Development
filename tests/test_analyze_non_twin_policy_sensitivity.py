import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_non_twin_policy_sensitivity import build
from build_frozen_confirmation_results import PUBLIC_TWINS


def metric(name, tp):
    return {
        "dataset": name, "edge_tp": tp, "edge_fp": 2, "edge_fn": 3,
        "division_tp": 0, "division_fp": 0, "division_fn": 0,
        "num_pred_nodes": 20, "node_recall": 0.9, "total_node_ratio": 1.0,
        "edge_jaccard": tp / (tp + 5), "adj_edge_jaccard": tp / (tp + 5),
    }


def test_excludes_public_twins_and_preserves_fixed_composition():
    forward_name, reverse_name = "6bba_private.zarr", "44b6_private.zarr"
    forward_parent = [metric(forward_name, 10)]
    reverse_parent = [metric(reverse_name, 10)]
    forward = {"per_movie_by_arm": {
        "translation": forward_parent + [metric("6bba_05b6850b.zarr", 100)],
        "flow_k32_a050": [metric(forward_name, 11), metric("6bba_05b6850b.zarr", 200)],
    }}
    reverse = {"per_movie_by_arm": {
        "translation": reverse_parent + [metric("44b6_0113de3b.zarr", 100)],
        "flow_k16_a025": [metric(reverse_name, 11), metric("44b6_0113de3b.zarr", 200)],
    }}
    exp195 = {"directions": {
        "forward": {"selected_rows": forward_parent + [metric("6bba_05b6850b.zarr", 100)]},
        "reverse": {"selected_rows": [metric(reverse_name, 12), metric("44b6_0113de3b.zarr", 100)]},
    }}
    result = build(forward, reverse, exp195, expected_non_twin=1)
    assert result["movie_count"] == 2
    assert set(result["excluded_public_twins"]) == PUBLIC_TWINS
    assert result["deltas"]["exp201_vs_exp190"] > 0
    assert result["deltas"]["exp202_vs_exp195"] > 0
