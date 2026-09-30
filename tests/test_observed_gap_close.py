import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_observed_gap_close import close_observed_single_frame_gaps
from select_observed_gap_gate import select_gate


class ObservedGapCloseTests(unittest.TestCase):
    def test_reuses_isolated_middle_node(self):
        coords = np.array([
            [0, 0, 0, 0],
            [1, 0, 0, 5],
            [2, 0, 0, 10],
        ], dtype=float)
        result, stats = close_observed_single_frame_gaps(
            coords, [], np.ones(3), adaptive=False
        )
        self.assertEqual(result, [(0, 1, 0.0, 5.0), (1, 2, 0.0, 5.0)])
        self.assertEqual(stats["observed_middle_reused"], 1)

    def test_does_not_synthesize_missing_middle(self):
        coords = np.array([[0, 0, 0, 0], [2, 0, 0, 9]], dtype=float)
        result, stats = close_observed_single_frame_gaps(
            coords, [], np.ones(3), adaptive=True
        )
        self.assertEqual(result, [])
        self.assertEqual(stats["rejected_no_observed_middle"], 1)

    def test_gate_requires_both_directions_and_each_movie(self):
        def payload(base, fixed, adaptive):
            rows = lambda values: [
                {"dataset": f"m{i}", "adj_edge_jaccard": value}
                for i, value in enumerate(values)
            ]
            return {
                "summary_by_arm": {
                    "registered_hungarian": {"score": base},
                    "fixed_observed_gap": {"score": fixed},
                    "adaptive_observed_gap": {"score": adaptive},
                },
                "per_movie_by_arm": {
                    "registered_hungarian": rows([base, base]),
                    "adaptive_observed_gap": rows([adaptive, adaptive]),
                },
                "telemetry": [{
                    "fixed": {"added_edges": 0},
                    "adaptive": {"added_edges": 2, "density_candidates_expanded": 1,
                                 "density_candidates_restricted": 0},
                }],
            }
        passed = select_gate({"a": payload(.5, .50, .51), "b": payload(.4, .405, .41)})
        self.assertTrue(passed["eligible_for_reciprocal_official24"])
        failed = select_gate({"a": payload(.5, .50, .51), "b": payload(.4, .405, .39)})
        self.assertFalse(failed["eligible_for_reciprocal_official24"])


if __name__ == "__main__":
    unittest.main()
