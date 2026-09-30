from scripts.select_count_calibrated_graph import select


def row(dataset, ratio, tp):
    return {
        "dataset": dataset,
        "edge_tp": tp,
        "edge_fp": 1,
        "edge_fn": 1,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "node_recall": 0.9,
        "total_node_ratio": ratio,
        "adj_edge_jaccard": tp / (tp + 2),
    }


def payload(prefix, baseline_ratio, candidate_ratio):
    names = [f"{prefix}_{index:02d}.zarr" for index in range(12)]
    return {
        "per_movie_by_arm": {
            "base": [row(name, baseline_ratio, 5) for name in names],
            "candidate": [row(name, candidate_ratio, 6) for name in names],
        }
    }


def test_selects_closest_count_without_scores():
    result = select(payload("6bba", -0.2, 0.01), payload("44b6", 0.1, -0.02), "base", "base")
    assert result["status"] == "PASS_COUNT_CALIBRATED_GAIN"
    assert len(result["directions"]["forward"]["selected_rows"]) == 12
    assert {x["selected_arm"] for x in result["directions"]["forward"]["selections"]} == {"candidate"}
    assert {x["selected_arm"] for x in result["directions"]["reverse"]["selections"]} == {"candidate"}


def test_tie_prefers_baseline():
    result = select(payload("6bba", -0.1, 0.1), payload("44b6", -0.1, 0.1), "base", "base")
    assert {x["selected_arm"] for x in result["directions"]["forward"]["selections"]} == {"base"}
