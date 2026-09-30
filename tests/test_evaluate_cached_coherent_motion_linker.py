import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_coherent_motion_linker import (  # noqa: E402
    coherent_links,
    fit_transform,
)
from evaluate_coordinate_consensus import registered_links  # noqa: E402


def test_fit_transform_recovers_rigid_row_transform():
    source = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3], [2, 1, 1]], dtype=float
    )
    theta = np.deg2rad(8.0)
    rotation = np.array(
        [[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]],
        dtype=float,
    )
    target = source @ rotation + np.array([1.0, -0.5, 0.25])
    fitted_rotation, offset, fitted_scale = fit_transform(source, target, "rigid")
    np.testing.assert_allclose(source @ fitted_rotation + offset, target, atol=1e-10)
    assert fitted_scale == 1.0


def test_similarity_scale_is_recovered_inside_guardrail():
    source = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3], [2, 1, 1]], dtype=float
    )
    target = 1.02 * source + np.array([0.3, -0.2, 0.1])
    rotation, offset, fitted_scale = fit_transform(source, target, "similarity")
    np.testing.assert_allclose(fitted_scale * (source @ rotation) + offset, target, atol=1e-10)
    assert abs(fitted_scale - 1.02) < 1e-10


def test_zero_blend_edges_equal_registered_translation():
    frame0 = np.array([[0, 0, 0], [0, 10, 0], [0, 0, 10], [5, 5, 5]], dtype=float)
    frame1 = frame0 + np.array([0.5, 0.2, -0.1])
    coords = np.vstack(
        [
            np.column_stack([np.zeros(len(frame0)), frame0]),
            np.column_stack([np.ones(len(frame1)), frame1]),
        ]
    )
    expected = registered_links(coords, np.ones(3))
    actual, telemetry = coherent_links(coords, np.ones(3), "rigid", 0.0)
    assert actual == expected
    assert telemetry[0]["accepted_edges"] == 4
