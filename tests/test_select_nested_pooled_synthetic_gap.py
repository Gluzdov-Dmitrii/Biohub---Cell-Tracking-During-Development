import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_nested_pooled_synthetic_gap import select_direction, summarise


def row(dataset: str, adjusted: float) -> dict:
    return {
        "dataset": dataset,
        "edge_tp": 5,
        "edge_fp": 3,
        "edge_fn": 2,
        "division_tp": 0,
        "division_fp": 0,
        "division_fn": 0,
        "node_recall": 0.8,
        "adj_edge_jaccard": adjusted,
    }


class NestedPooledSyntheticGapTests(unittest.TestCase):
    def test_summarise_uses_edge_mass_weighting(self):
        first = row("a", 0.4)
        second = row("b", 0.8)
        second.update(edge_tp=10, edge_fp=6, edge_fn=4)
        result = summarise([first, second])
        self.assertAlmostEqual(result["adj_edge_jaccard"], (0.4 * 10 + 0.8 * 20) / 30)

    def test_each_movie_is_excluded_from_its_parameter_selection(self):
        datasets = ["m1", "m2", "m3"]
        base = [row(name, 0.5) for name in datasets]

        def payload(values):
            return {
                "per_movie_by_arm": {
                    "registered_hungarian": base,
                    "synthetic_gap_deepcenter": [
                        row(name, value) for name, value in zip(datasets, values)
                    ],
                }
            }

        variants = {
            "a": {"payload": payload([0.9, 0.4, 0.4])},
            "b": {"payload": payload([0.6, 0.6, 0.6])},
        }
        result = select_direction(variants, "test")
        selected = {item["held_out_dataset"]: item["selected_variant"] for item in result["selections"]}
        self.assertEqual(selected["m1"], "b")
        self.assertEqual(selected["m2"], "a")
        self.assertEqual(selected["m3"], "a")


if __name__ == "__main__":
    unittest.main()
