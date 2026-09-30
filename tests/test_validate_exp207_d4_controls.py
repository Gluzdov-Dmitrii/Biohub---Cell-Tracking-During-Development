import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_exp207_d4_controls import compare_cache_dirs


def write_cache(path: Path, coords: np.ndarray, probability: float) -> None:
    np.savez_compressed(
        path,
        coords=coords,
        edge_source=np.asarray([0]),
        edge_target=np.asarray([1]),
        edge_probability=np.asarray([probability], dtype=np.float32),
        edge_distance=np.asarray([1.0], dtype=np.float32),
    )


def test_cache_control_accepts_equal_coordinates_and_changed_edges(tmp_path: Path) -> None:
    off, on = tmp_path / "off", tmp_path / "on"
    off.mkdir()
    on.mkdir()
    coords = np.asarray([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=np.float32)
    write_cache(off / "6bba_a.npz", coords, 0.2)
    write_cache(on / "6bba_a.npz", coords, 0.3)
    result = compare_cache_dirs(off, on, ["6bba_a.zarr"])
    assert result["changed_edge_movies"] == ["6bba_a.zarr"]


def test_cache_control_rejects_coordinate_drift(tmp_path: Path) -> None:
    off, on = tmp_path / "off", tmp_path / "on"
    off.mkdir()
    on.mkdir()
    coords = np.asarray([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=np.float32)
    write_cache(off / "6bba_a.npz", coords, 0.2)
    changed = coords.copy()
    changed[0, 1] += 1
    write_cache(on / "6bba_a.npz", changed, 0.3)
    with pytest.raises(ValueError, match="coordinate drift"):
        compare_cache_dirs(off, on, ["6bba_a.zarr"])
