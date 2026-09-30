from scripts.summarize_exp196_attribution import combine


def payload(prefix: str, endpoint: int, association: int) -> dict:
    rows = []
    for index in range(12):
        rows.append(
            {
                "dataset": f"{prefix}_{index:02d}.zarr",
                "fn_missing_both_endpoints": endpoint,
                "fn_missing_source_endpoint": 0,
                "fn_missing_target_endpoint": 0,
                "fn_both_endpoints_matched_link_missing": association,
            }
        )
    return {
        "status": "PASS_OFFICIAL_MATCH_EDGE_FAILURE_DECOMPOSITION",
        "per_movie": rows,
    }


def test_combine_exact_balanced_direction_counts():
    result = combine(payload("6bba", 3, 1), payload("44b6", 1, 1), draws=100, seed=9)
    assert result["movies"] == 24
    assert result["directional"]["forward"]["endpoint_limited_fn_fraction"] == 0.75
    assert result["directional"]["reverse"]["endpoint_limited_fn_fraction"] == 0.5
    assert result["pooled"]["endpoint_limited_fn"] == 48
    assert result["pooled"]["association_limited_fn"] == 24
    assert result["pooled"]["endpoint_limited_fn_fraction"] == 2 / 3
    assert result["movie_stratified_bootstrap"]["endpoint_fraction_ci95"] == [2 / 3, 2 / 3]


def test_rejects_wrong_direction_prefix():
    forward = payload("44b6", 1, 1)
    reverse = payload("44b6", 1, 1)
    try:
        combine(forward, reverse, draws=10)
    except ValueError as error:
        assert "forward: wrong embryo prefix" in str(error)
    else:
        raise AssertionError("wrong prefix was accepted")
