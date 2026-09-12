import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_intensity_centroid_refinement import refine_movie, refine_points


def test_refine_points_finds_weighted_centroid_and_keeps_flat_crop():
    frame = np.zeros((7, 13, 13), dtype=np.float32)
    frame[4, 8, 7] = 10.0
    frame[4, 8, 8] = 30.0
    points = np.asarray([[3.0, 6.0, 6.0], [0.0, 0.0, 0.0]])
    refined, shifts, failed = refine_points(frame, points, (2, 5, 5))
    np.testing.assert_allclose(refined[0], [4.0, 8.0, 7.75])
    np.testing.assert_allclose(shifts[0], [1.0, 2.0, 1.75])
    np.testing.assert_allclose(refined[1], points[1])
    assert failed == 1


def test_refine_movie_preserves_time_and_reports_physical_shift():
    image = np.zeros((2, 5, 7, 7), dtype=np.float32)
    image[0, 2, 3, 4] = 5.0
    image[1, 3, 4, 3] = 5.0
    coords = np.asarray([[0.0, 2.0, 3.0, 3.0], [1.0, 2.0, 3.0, 3.0]])
    refined, telemetry = refine_movie(image, coords, np.asarray([2.0, 1.0, 1.0]), (1, 2, 2))
    np.testing.assert_array_equal(refined[:, 0], coords[:, 0])
    np.testing.assert_allclose(refined[:, 1:4], [[2.0, 3.0, 4.0], [3.0, 4.0, 3.0]])
    assert telemetry["nodes"] == 2
    assert telemetry["frames"] == 2
    assert telemetry["zero_weight_nodes"] == 0
    np.testing.assert_allclose(telemetry["max_shift_um"], np.sqrt(5.0))


def test_negative_radius_is_rejected():
    frame = np.ones((2, 2, 2), dtype=np.float32)
    try:
        refine_points(frame, np.asarray([[0.0, 0.0, 0.0]]), (-1, 1, 1))
    except ValueError as error:
        assert "radii" in str(error)
    else:
        raise AssertionError("negative radius must fail")
