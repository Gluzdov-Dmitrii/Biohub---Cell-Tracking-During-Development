"""Reliability tests for the official-data integrity audit."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/build_official24_private_splits.py"
SPEC = importlib.util.spec_from_file_location("build_official24_private_splits", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OfficialDataAuditTests(unittest.TestCase):
    def test_manifest_path_is_scoped_and_traversal_safe(self):
        self.assertEqual(
            MODULE.safe_manifest_path("train/6bba_demo.zarr/zarr.json"),
            Path("train/6bba_demo.zarr/zarr.json"),
        )
        for unsafe in ("../secret", "test/file", "train/../secret", "/train/file"):
            with self.assertRaises(ValueError):
                MODULE.safe_manifest_path(unsafe)

    def test_content_hash_binds_path_size_and_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "train/6bba_demo.zarr/0/c/0"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"abc")
            entries = [{"name": "train/6bba_demo.zarr/0/c/0", "size": 3}]
            first = MODULE.content_tree_sha256(root, entries)
            path.write_bytes(b"abd")
            second = MODULE.content_tree_sha256(root, entries)
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
