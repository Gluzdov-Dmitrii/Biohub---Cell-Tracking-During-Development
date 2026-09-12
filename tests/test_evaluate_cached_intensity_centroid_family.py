import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_intensity_centroid_family import (
    parse_radius,
    radius_label,
    refine_movie_family,
)


class CountingImage:
    def __init__(self, array: np.ndarray):
        self.array = array
        self.reads = 0

    def __getitem__(self, index: int) -> np.ndarray:
        self.reads += 1
        return self.array[index]


def test_family_loads_each_frame_once_and_keeps_arms_independent() -> None:
    array = np.zeros((2, 5, 9, 9), dtype=np.float32)
    array[0, 2, 4, 5] = 10.0
    array[1, 3, 5, 4] = 10.0
    image = CountingImage(array)
    coords = np.asarray([[0.0, 2.0, 4.0, 4.0], [1.0, 2.0, 4.0, 4.0]])
    refined, telemetry = refine_movie_family(
        image, coords, np.asarray([2.0, 1.0, 1.0]), [(1, 1, 1), (2, 2, 2)]
    )
    assert image.reads == 2
    assert set(refined) == {"intensity_centroid_r1_1_1", "intensity_centroid_r2_2_2"}
    np.testing.assert_array_equal(coords[:, 1:4], [[2.0, 4.0, 4.0], [2.0, 4.0, 4.0]])
    np.testing.assert_allclose(refined["intensity_centroid_r1_1_1"][:, 1:4], [[2, 4, 5], [3, 5, 4]])
    assert telemetry["intensity_centroid_r2_2_2"]["frames"] == 2


def test_radius_parser_and_duplicate_guard() -> None:
    assert parse_radius("2,5,5") == (2, 5, 5)
    assert radius_label((2, 5, 5)) == "intensity_centroid_r2_5_5"
    try:
        refine_movie_family(np.zeros((1, 2, 2, 2)), np.empty((0, 4)), np.ones(3), [(1, 1, 1), (1, 1, 1)])
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate radii must fail")


def test_empty_family_does_not_read_frames() -> None:
    image = CountingImage(np.zeros((2, 3, 3, 3), dtype=np.float32))
    coords = np.asarray([[0.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]])
    refined, telemetry = refine_movie_family(image, coords, np.ones(3), [])
    assert refined == {}
    assert telemetry == {}
    assert image.reads == 0
