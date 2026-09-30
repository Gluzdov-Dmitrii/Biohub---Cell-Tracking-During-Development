"""Synthetic, label-free checks for the EXP241 paired scorer contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/exp241_source_paired_scorer_v1_20260927/score_exp241_source_paired.py"
SPEC = importlib.util.spec_from_file_location("exp241_source_paired", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row(row_id, name, kind, node=-1, t=-1, z=-1, y=-1, x=-1, source=-1, target=-1):
    return [row_id, name, kind, node, t, z, y, x, source, target]


def write_graph(path: Path, rows, mode="w"):
    with path.open(mode, newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        if mode == "w":
            writer.writerow(MODULE.CSV_COLUMNS)
        writer.writerows(rows)


def graph_pair(tmp_path):
    name = "44b6_996155de"
    original = tmp_path / "original.csv"
    candidate = tmp_path / "candidate.csv"
    parent_rows = [row(0, name, "node", 1, 0, 1, 2, 3),
                   row(1, name, "node", 2, 1, 1, 2, 3),
                   row(2, name, "edge", source=1, target=2)]
    write_graph(original, parent_rows)
    candidate.write_bytes(original.read_bytes())
    write_graph(candidate, [row(3, name, "node", 3, 2, 1, 2, 3),
                            row(4, name, "node", 4, 3, 1, 2, 3),
                            row(5, name, "edge", source=2, target=3),
                            row(6, name, "edge", source=3, target=4)], "a")
    receipt = {"dataset": name, "source_graph_sha256": digest(original),
               "candidate_csv_sha256": digest(candidate),
               "original_prefix_sha256": digest(original), "original_rows": 3,
               "selected_chains": 1, "added_nodes": 2, "added_edges": 2,
               "first_new_node_id": 3, "first_new_row_id": 3}
    parsed_original = {"nodes": {1: (0, 1.0, 2.0, 3.0),
                                 2: (1, 1.0, 2.0, 3.0)}, "edges": [(1, 2)]}
    return original, candidate, receipt, parsed_original


def test_exact_graph_extension_and_reject_modified_original(tmp_path):
    original, candidate, receipt, parsed_original = graph_pair(tmp_path)
    parsed = MODULE.check_graph_extension(original, candidate, receipt, parsed_original)
    assert parsed["added_node_ids"] == [3, 4]
    assert parsed["added_edges"] == [(2, 3), (3, 4)]
    tampered = candidate.read_bytes().replace(b"1,2,3", b"1,2,4", 1)
    candidate.write_bytes(tampered)
    receipt["candidate_csv_sha256"] = digest(candidate)
    with pytest.raises(AssertionError):
        MODULE.check_graph_extension(original, candidate, receipt, parsed_original)


def test_new_edge_must_advance_one_frame(tmp_path):
    original, candidate, receipt, parsed_original = graph_pair(tmp_path)
    text = candidate.read_text().replace(
        "4,44b6_996155de,node,4,3,1,2,3,-1,-1",
        "4,44b6_996155de,node,4,4,1,2,3,-1,-1")
    candidate.write_text(text)
    receipt["candidate_csv_sha256"] = digest(candidate)
    with pytest.raises(AssertionError):
        MODULE.check_graph_extension(original, candidate, receipt, parsed_original)


def test_two_chains_use_interleaved_node_edge_row_ids(tmp_path):
    name = "44b6_996155de"
    original = tmp_path / "original2.csv"
    candidate = tmp_path / "candidate2.csv"
    write_graph(original, [row(0, name, "node", 1, 0, 1, 2, 3),
                           row(1, name, "node", 2, 1, 1, 2, 3),
                           row(2, name, "node", 5, 0, 2, 4, 6),
                           row(3, name, "node", 6, 1, 2, 4, 6),
                           row(4, name, "edge", source=1, target=2),
                           row(5, name, "edge", source=5, target=6)])
    candidate.write_bytes(original.read_bytes())
    write_graph(candidate, [row(6, name, "node", 7, 2, 1, 2, 3),
                            row(7, name, "node", 8, 3, 1, 2, 3),
                            row(8, name, "edge", source=2, target=7),
                            row(9, name, "edge", source=7, target=8),
                            row(10, name, "node", 9, 2, 2, 4, 6),
                            row(11, name, "node", 10, 3, 2, 4, 6),
                            row(12, name, "edge", source=6, target=9),
                            row(13, name, "edge", source=9, target=10)], "a")
    receipt = {"dataset": name, "source_graph_sha256": digest(original),
               "candidate_csv_sha256": digest(candidate),
               "original_prefix_sha256": digest(original), "original_rows": 6,
               "selected_chains": 2, "added_nodes": 4, "added_edges": 4,
               "first_new_node_id": 7, "first_new_row_id": 6}
    parsed_original = {"nodes": {1: (0, 1.0, 2.0, 3.0), 2: (1, 1.0, 2.0, 3.0),
                                 5: (0, 2.0, 4.0, 6.0), 6: (1, 2.0, 4.0, 6.0)},
                       "edges": [(1, 2), (5, 6)]}
    parsed = MODULE.check_graph_extension(original, candidate, receipt, parsed_original)
    assert parsed["added_node_ids"] == [7, 8, 9, 10]
    assert parsed["added_edges"] == [(2, 7), (7, 8), (6, 9), (9, 10)]


def synthetic_summary(score, edge=0.8, division=0.5, recall=0.9, micro=0.91):
    return {"official": {"score": score, "adj_edge_jaccard": edge,
                         "division_jaccard": division, "node_recall": recall},
            "nodes": {"recall_micro": micro}}


def test_fixed_promotion_requires_score_and_each_nonregression_component():
    old = synthetic_summary(0.800)
    good = synthetic_summary(0.805, edge=0.805)
    assert MODULE.promotion_gate(old, good)["pass"]
    assert not MODULE.promotion_gate(old, synthetic_summary(0.8049))["pass"]
    assert not MODULE.promotion_gate(old, synthetic_summary(0.810, division=0.499))["pass"]
    assert not MODULE.promotion_gate(old, synthetic_summary(0.810, micro=0.899))["pass"]
    assert not MODULE.promotion_gate(old, synthetic_summary(0.810, recall=0.899))["pass"]


def test_nested_parent_replay_is_exact_to_one_e_minus_twelve():
    MODULE.require_close({"rows": [{"score": 0.8 + 5e-13}]},
                         {"rows": [{"score": 0.8}]}, "parent")
    with pytest.raises(AssertionError):
        MODULE.require_close({"rows": [{"score": 0.8 + 2e-12}]},
                             {"rows": [{"score": 0.8}]}, "parent")


def test_node_counts_pool_by_sufficient_statistics():
    rows = [{"baseline_nodes": {"tp": 1, "fp_annotated": 2, "fn": 1,
                                "gt": 2, "pred_all_frames": 30, "pred_annotated": 3}},
            {"baseline_nodes": {"tp": 9, "fp_annotated": 1, "fn": 1,
                                "gt": 10, "pred_all_frames": 50, "pred_annotated": 10}}]
    pooled = MODULE.pool_nodes(rows, "baseline")
    assert pooled["recall_micro"] == 10 / 12
    assert pooled["fp_annotated"] == 3
    assert pooled["pred_all_frames"] == 80
