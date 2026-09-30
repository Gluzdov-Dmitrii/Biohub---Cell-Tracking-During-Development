from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from extract_manifest_from_archive import safe_relative, selected_entries


def test_selection_is_prefix_scoped_and_sorted():
    manifest = {"files": [
        {"name": "train/6bba_b.zarr/x", "size": 2},
        {"name": "train/44b6_a.zarr/x", "size": 1},
        {"name": "train/6bba_a.geff/x", "size": 3},
    ]}
    assert selected_entries(manifest, "6bba") == [
        {"name": "train/6bba_a.geff/x", "size": 3},
        {"name": "train/6bba_b.zarr/x", "size": 2},
    ]


def test_safe_relative_rejects_traversal():
    for bad in ("../train/x", "/train/x", "test/x", "train/../x"):
        try:
            safe_relative(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted unsafe path {bad}")
