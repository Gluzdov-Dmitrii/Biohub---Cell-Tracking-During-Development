import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from train_deepcenter_explicit_split import explicit_split_samples


class ExplicitDeepCenterSplitTests(unittest.TestCase):
    def test_exact_order_and_suffix_normalization(self):
        samples = [{"name": name} for name in ("a", "b", "c")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.json"
            path.write_text(json.dumps([{"train": ["b.zarr", "a.zarr"], "test": ["c.zarr"]}]))
            train, val, manifest = explicit_split_samples(samples, path, 0, "train", "test")
        self.assertEqual([row["name"] for row in train], ["b", "a"])
        self.assertEqual([row["name"] for row in val], ["c"])
        self.assertEqual(manifest["mode"], "explicit_predeclared")

    def test_overlap_rejected(self):
        samples = [{"name": "a"}, {"name": "b"}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.json"
            path.write_text(json.dumps({"train": ["a"], "test": ["a", "b"]}))
            with self.assertRaisesRegex(ValueError, "overlap"):
                explicit_split_samples(samples, path, 0, "train", "test")

    def test_unregistered_data_rejected(self):
        samples = [{"name": "a"}, {"name": "b"}, {"name": "extra"}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "split.json"
            path.write_text(json.dumps({"train": ["a"], "test": ["b"]}))
            with self.assertRaisesRegex(ValueError, "extra"):
                explicit_split_samples(samples, path, 0, "train", "test")


if __name__ == "__main__":
    unittest.main()
