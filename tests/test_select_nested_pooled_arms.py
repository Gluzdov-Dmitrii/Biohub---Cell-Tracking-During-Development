import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from select_nested_pooled_arms import select


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


class NestedPooledArmTests(unittest.TestCase):
    def test_held_out_movie_does_not_select_its_own_arm(self):
        names = ["m1", "m2", "m3"]
        payload = {"per_movie_by_arm": {
            "base": [row(name, 0.5) for name in names],
            "spiky": [row(name, value) for name, value in zip(names, [0.9, 0.4, 0.4])],
            "stable": [row(name, 0.6) for name in names],
        }}
        result = select(payload, "test", "base", ["spiky", "stable"])
        selected = {item["held_out_dataset"]: item["selected_arm"] for item in result["selections"]}
        self.assertEqual(selected["m1"], "stable")
        self.assertEqual(selected["m2"], "spiky")
        self.assertEqual(selected["m3"], "spiky")


if __name__ == "__main__":
    unittest.main()
