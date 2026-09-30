import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from analyze_exp200_local_flow_mechanism import analyze_direction


def metric(name, tp, fp, fn):
    return {
        "dataset": name, "edge_tp": tp, "edge_fp": fp, "edge_fn": fn,
        "division_tp": 0, "division_fp": 0, "division_fn": 0,
        "num_pred_nodes": 20, "node_recall": 0.9, "total_node_ratio": 1.0,
        "edge_jaccard": tp / (tp + fp + fn),
        "adj_edge_jaccard": tp / (tp + fp + fn),
    }


def test_attributes_edge_changes_and_correlations():
    names = [f"6bba_{i}.zarr" for i in range(3)]
    base = [metric(name, 10, 2, 4) for name in names]
    candidate = [metric(name, 11 + i, 2, 3 - i) for i, name in enumerate(names)]
    flow = {
        "per_movie_by_arm": {"translation": base, "flow_k32_a050": candidate},
        "telemetry": [
            {"dataset": name, "variants": {"flow_k32_a050": {"frames": [
                {"median_correction_um": 0.2 + i, "mutual_pairs": 10 + i}
            ]}}}
            for i, name in enumerate(names)
        ],
    }
    attribution = {"per_movie": [
        {
            "dataset": name, "fn_missing_both_endpoints": 1,
            "fn_missing_source_endpoint": 1, "fn_missing_target_endpoint": 0,
            "fn_both_endpoints_matched_link_missing": 2,
        }
        for name in names
    ]}
    result = analyze_direction(flow, attribution, "flow_k32_a050", "6bba", 3)
    assert result["sufficient_stat_delta"] == {"edge_tp": 6, "edge_fp": 0, "edge_fn": -6}
    assert result["movie_counts"]["positive"] == 3
    assert result["correlation_with_delta_score"]["mean_mutual_pairs"]["pearson"] > 0
