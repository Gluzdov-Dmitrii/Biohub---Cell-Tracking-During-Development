from scripts.select_synthetic_gap_target_gate import evaluate_gate


def _result(base_score=0.7, raw_score=0.71, gated_score=0.72, bad_movie=False):
    movies = [f"movie_{index:02d}.zarr" for index in range(12)]
    base_rows = [
        {"dataset": movie, "adj_edge_jaccard": base_score, "node_recall": 0.9}
        for movie in movies
    ]
    gated_rows = [
        {
            "dataset": movie,
            "adj_edge_jaccard": base_score + (-0.001 if bad_movie and index == 0 else 0.02),
            "node_recall": 0.9,
        }
        for index, movie in enumerate(movies)
    ]
    return {
        "summary_by_arm": {
            "registered_hungarian": {"n": 12, "score": base_score},
            "synthetic_gap_no_veto": {"n": 12, "score": raw_score},
            "synthetic_gap_deepcenter": {"n": 12, "score": gated_score},
        },
        "per_movie_by_arm": {
            "registered_hungarian": base_rows,
            "synthetic_gap_deepcenter": gated_rows,
        },
        "telemetry": [{"deepcenter": {"deepcenter_checked": 3, "synthetic_added": 2}}],
    }


def test_target_gate_passes_strict_two_embryo_case():
    result = evaluate_gate({"forward": _result(), "reverse": _result(0.6, 0.61, 0.62)})
    assert result["status"] == "PASS_TARGET_OOF_GATE"
    assert result["pooled"]["n_movies"] == 24
    assert result["eligible_for_kaggle_submission"] is False


def test_target_gate_rejects_single_movie_regression():
    result = evaluate_gate({"forward": _result(bad_movie=True), "reverse": _result(0.6, 0.61, 0.62)})
    assert result["status"] == "REJECT_TARGET_OOF_GATE"
    assert result["gates"]["nonnegative_score_each_movie"] is False


def test_target_gate_rejects_veto_worse_than_no_veto():
    result = evaluate_gate({"forward": _result(raw_score=0.73), "reverse": _result(0.6, 0.61, 0.62)})
    assert result["status"] == "REJECT_TARGET_OOF_GATE"
    assert result["gates"]["veto_not_worse_than_no_veto_each_embryo"] is False
