"""Fail-closed tests for private-development candidate comparison."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/compare_registered_candidate.py"
SPEC = importlib.util.spec_from_file_location("compare_registered_candidate", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(dataset: str, tp: int, fp: int, fn: int, adjusted: float, recall: float) -> dict:
    return {
        "dataset": dataset,
        "edge_tp": tp,
        "edge_fp": fp,
        "edge_fn": fn,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "adj_edge_jaccard": adjusted,
        "node_recall": recall,
    }


class ComparatorReliabilityTests(unittest.TestCase):
    def test_exact_weighted_recomputation(self):
        rows = {"a": row("a", 2, 1, 1, 0.5, 0.8), "b": row("b", 8, 1, 1, 0.8, 1.0)}
        summary = MODULE.recompute_summary(rows, "candidate")
        self.assertAlmostEqual(summary["adj_edge_jaccard"], (4 * 0.5 + 10 * 0.8) / 14)
        self.assertAlmostEqual(summary["edge_jaccard"], 10 / 14)
        self.assertAlmostEqual(summary["node_recall"], 0.9)
        self.assertEqual(summary["score"], summary["adj_edge_jaccard"])

    def test_tampered_summary_is_rejected(self):
        rows = {"a": row("a", 2, 1, 1, 0.5, 0.8)}
        good = MODULE.recompute_summary(rows, "candidate")
        payload = {"summary_by_arm": {"registered": {**good, "score": good["score"] + 0.01}}}
        with self.assertRaisesRegex(ValueError, "inconsistent candidate summary score"):
            MODULE.validate_summary(payload, "registered", "candidate", rows)

    def test_negative_or_fractional_counts_are_rejected(self):
        for bad in (-1, 1.5):
            rows = {"a": row("a", bad, 1, 1, 0.5, 0.8)}
            with self.assertRaisesRegex(ValueError, "invalid candidate count field edge_tp"):
                MODULE.recompute_summary(rows, "candidate")


if __name__ == "__main__":
    unittest.main()
