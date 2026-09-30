import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_short_track_family import filter_family


class ShortTrackFamilyTests(unittest.TestCase):
    def setUp(self):
        self.coords = np.asarray([[i, i, 0, 0] for i in range(9)], dtype=float)
        self.edges = [
            (0, 1, 1.0, 1.0), (1, 2, 1.0, 1.0), (2, 3, 1.0, 1.0), (3, 4, 1.0, 1.0),
            (5, 6, 1.0, 1.0), (6, 7, 1.0, 1.0),
        ]

    def test_minimum_length_filters_short_component_and_isolate(self):
        coords, edges, stats = filter_family(self.coords, self.edges, {}, 5, False)
        self.assertEqual(len(coords), 5)
        self.assertEqual(len(edges), 4)
        self.assertEqual(stats["nodes_removed"], 4)

    def test_public_rescue_requires_probability_and_distance(self):
        coords_in = np.asarray([[i, i, 0, 0] for i in range(1011)], dtype=float)
        edges_in = [
            (0, 1, 1.0, 1.0), (1, 2, 1.0, 1.0), (2, 3, 1.0, 1.0), (3, 4, 1.0, 1.0),
            (5, 6, 1.0, 1.0), (6, 7, 1.0, 1.0), (7, 8, 1.0, 1.0),
            (8, 9, 1.0, 1.0), (9, 10, 1.0, 1.0),
        ]
        probs = {(s, t): 0.95 for s, t, *_ in edges_in}
        coords, edges, stats = filter_family(coords_in, edges_in, probs, 6, True)
        self.assertEqual(len(coords), 11)
        self.assertEqual(len(edges), 9)
        self.assertEqual(stats["components_rescued"], 1)

    def test_control_is_exact(self):
        coords, edges, stats = filter_family(self.coords, self.edges, {}, 1, False)
        np.testing.assert_array_equal(coords, self.coords)
        self.assertEqual(edges, self.edges)
        self.assertEqual(stats["nodes_removed"], 0)


if __name__ == "__main__":
    unittest.main()
