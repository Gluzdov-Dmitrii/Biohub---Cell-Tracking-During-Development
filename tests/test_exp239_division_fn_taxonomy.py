"""Label-free synthetic checks of the EXP239 stage ordering and access guard."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "scripts/audit_exp239_source_division_fn_taxonomy.py"
SPEC = importlib.util.spec_from_file_location("exp239_taxonomy", SOURCE)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class Graph:
    def __init__(self, edges):
        self.forward = {}
        self.backward = {}
        for source, target in edges:
            self.forward.setdefault(source, []).append(target)
            self.backward.setdefault(target, []).append(source)

    def successors(self, node):
        return self.forward.get(node, [])

    def predecessors(self, node):
        return self.backward.get(node, [])

    def out_degree(self, node):
        return len(self.successors(node))


GT = Graph([(0, 1), (1, 2), (1, 3), (2, 4), (3, 5)])


def directed_support(pred, fork, parents, daughters):
    """Independent small-graph oracle for distinct direct-child branches."""
    if not ({fork} | set(pred.predecessors(fork))) & parents:
        return False
    branches = [{child, *pred.successors(child)} for child in pred.successors(fork)]
    if len(branches) < 2:
        return False
    for first, matches_a in enumerate(daughters):
        for second, matches_b in enumerate(daughters):
            if first >= second:
                continue
            for a, branch_a in enumerate(branches):
                for b, branch_b in enumerate(branches):
                    if a != b and matches_a & branch_a and matches_b & branch_b:
                        return True
    return False


@pytest.mark.parametrize(
    "edges,matches,invalid,is_tp,category,subtype",
    [
        ([(10, 20), (10, 30)], {20: 2, 30: 3}, set(), False,
         "no_parent_side_match", None),
        ([(10, 20), (10, 30)], {10: 1, 20: 2}, set(), False,
         "fewer_than_two_daughter_lineages", None),
        ([(10, 20)], {10: 1, 20: 2, 30: 3}, set(), False,
         "no_local_fork", None),
        ([(10, 20), (10, 30), (20, 40)], {10: 1, 20: 2, 40: 3}, set(), False,
         "directed_branch_failure", None),
        ([(10, 20), (10, 30)], {10: 1, 20: 2, 30: 3}, {10}, False,
         "organizer_veto_or_pairing", "organizer_invalid_fork"),
        ([(10, 20), (10, 30)], {10: 1, 20: 2, 30: 3}, set(), False,
         "organizer_veto_or_pairing", "bipartite_collision"),
        ([(10, 20), (10, 30)], {10: 1, 20: 2, 30: 3}, set(), True,
         "recovered", None),
    ],
)
def test_synthetic_fork_windows(edges, matches, invalid, is_tp, category, subtype):
    result = audit.classify_window(
        Graph(edges), GT, 1, matches, invalid, is_tp, directed_support)
    assert (result["category"], result["subtype"]) == (category, subtype)
    if is_tp:
        assert result["valid_forks"] == 1


def test_geff_guard_is_closed_then_exact_source_allowlist():
    state = {"label_access_enabled": False}
    guard = audit.label_audit_hook({"44b6_example"}, state)
    source = audit.DATA / "44b6_example.geff" / "nodes.parquet"
    target = audit.DATA / "6bba_target.geff" / "nodes.parquet"
    with pytest.raises(PermissionError, match="remain sealed"):
        guard("open", (str(source),))
    state["label_access_enabled"] = True
    guard("open", (str(source),))
    with pytest.raises(PermissionError, match="outside source19"):
        guard("open", (str(target),))


def test_tp_without_valid_fork_fails_closed():
    with pytest.raises(AssertionError, match="no valid local fork"):
        audit.classify_window(Graph([(10, 20)]), GT, 1,
                              {10: 1, 20: 2}, set(), True, directed_support)
