"""Tiny fixture for the official-matched-endpoint FN partition."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = (Path(__file__).resolve().parents[1] / "work" /
          "source_inner_error_decomposition_20260927" / "audit_source_inner.py")


def test_endpoint_classes_are_mutually_exclusive():
    spec = spec_from_file_location("source_inner_audit", SCRIPT)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    gt_edges = {(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)}
    matched_gt_nodes = {0, 1, 2, 5, 8, 9}
    official_true_edges = {(0, 1)}
    assert module.classify_gt_edges(gt_edges, matched_gt_nodes, official_true_edges) == {
        "tp": 1,
        "fn_both_unmatched": 1,             # 6 -> 7
        "fn_source_unmatched": 1,           # 4 -> 5
        "fn_target_unmatched": 1,           # 2 -> 3
        "fn_both_matched_link_missing": 1,  # 8 -> 9
    }
