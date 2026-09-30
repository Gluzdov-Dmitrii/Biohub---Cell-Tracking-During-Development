from scripts.analyze_cached_edge_failure_modes import decompose_edges, summarize


def test_decomposition_partitions_official_style_counts():
    # GT: 1->2, 3->4, 5->6, 7->8, 9->10.
    # First is recovered; next three lose both/source/target endpoints; fourth
    # mapped pair is fragmented.  Predicted non-TPs cover each FP category and
    # one sparse-GT edge that the official rule ignores.
    gt_edges = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10)]
    pred_to_gt = {101: 1, 102: 2, 104: 4, 105: 5, 109: 9, 110: 10, 111: 12}
    gt_to_pred = {gt: pred for pred, gt in pred_to_gt.items()}
    pred_edges = [
        (101, 102),  # TP
        (101, 104),  # both matched, wrong association
        (105, 999),  # source anchor, target unmatched
        (998, 102),  # target anchor, source unmatched
        (111, 997),  # ignored: matched source has no GT outgoing edge
    ]
    got = decompose_edges(pred_edges, gt_edges, pred_to_gt, gt_to_pred)
    assert got == {
        "edge_tp": 1,
        "fn_missing_both_endpoints": 1,
        "fn_missing_source_endpoint": 1,
        "fn_missing_target_endpoint": 1,
        "fn_both_endpoints_matched_link_missing": 1,
        "fp_both_endpoints_matched_wrong_association": 1,
        "fp_source_anchor_target_unmatched": 1,
        "fp_target_anchor_source_unmatched": 1,
        "ignored_pred_edges": 1,
    }


def test_summary_reports_endpoint_vs_association_fraction():
    row = {
        "dataset": "movie.zarr",
        "edge_tp": 3,
        "fn_missing_both_endpoints": 1,
        "fn_missing_source_endpoint": 2,
        "fn_missing_target_endpoint": 1,
        "fn_both_endpoints_matched_link_missing": 2,
        "fp_both_endpoints_matched_wrong_association": 2,
        "fp_source_anchor_target_unmatched": 1,
        "fp_target_anchor_source_unmatched": 1,
        "ignored_pred_edges": 7,
    }
    pooled = summarize([row])
    assert pooled["edge_fn"] == 6
    assert pooled["edge_fp"] == 4
    assert pooled["endpoint_limited_fn_fraction"] == 4 / 6
    assert pooled["association_limited_fn_fraction"] == 2 / 6
