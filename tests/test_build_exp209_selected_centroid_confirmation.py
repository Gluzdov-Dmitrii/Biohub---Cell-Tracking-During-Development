import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_exp209_selected_centroid_confirmation import build


def row(name, value):
    return {
        "dataset": name, "edge_tp": value, "edge_fp": 1, "edge_fn": 2,
        "division_tp": 0, "division_fp": 0, "division_fn": 1,
        "num_pred_nodes": 10, "node_recall": 0.8, "total_node_ratio": 1.0,
        "edge_jaccard": value / (value + 3), "adj_edge_jaccard": value / (value + 3),
    }


def policy(forward_base, reverse_base, forward_selected, reverse_selected, score=0.0):
    return {
        "directions": {
            "forward": {"base_rows": forward_base, "selected_rows": forward_selected},
            "reverse": {"base_rows": reverse_base, "selected_rows": reverse_selected},
        },
        "combined": {"frozen_selected": {"score": score}},
    }


def test_builds_three_fixed_policies_and_reproduces_controls():
    fb = [row(f"6bba_{i:04x}.zarr", 10) for i in range(116)]
    rb = [row(f"44b6_{i:04x}.zarr", 10) for i in range(59)]
    fselected = [row(item["dataset"], 12) for item in fb]
    rselected = [row(item["dataset"], 11) for item in rb]
    forward = {"per_movie_by_arm": {"translation": fb, "intensity_centroid_r3_5_5": fselected}}
    reverse = {"per_movie_by_arm": {"translation": rb, "intensity_centroid_r2_3_3": rselected}}
    exp190 = policy(fb, rb, fb, rb)
    exp191 = policy(fb, rb, fb, rselected)
    exp195 = policy(fb, rb, fb, rb)
    exp206 = policy(fb, rb, fselected, rb, score=0.5)
    result = build(forward, reverse, exp190, exp191, exp195, exp206, {})
    assert set(result) == {"both_selected", "forward_plus_exp191", "forward_plus_exp195"}
    assert result["both_selected"]["directions"]["reverse"]["frozen_arm"].endswith("r2_3_3_min3")
    assert result["forward_plus_exp195"]["directions"]["forward"]["frozen_arm"].endswith("r3_5_5_min8")
    assert all(value["translation_control_maximum_absolute_error"] == 0 for value in result.values())
