import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluate_cached_local_flow_linker import local_flow_links, local_residual_field  # noqa: E402
from evaluate_coordinate_consensus import registered_links  # noqa: E402


def test_local_field_tracks_two_spatial_motion_regions():
    left = np.array([[-3, 0, 0], [-3, 1, 0], [-2, 0, 1], [-2, 1, 1]], dtype=float)
    right = np.array([[3, 0, 0], [3, 1, 0], [2, 0, 1], [2, 1, 1]], dtype=float)
    source = np.vstack([left, right])
    target = np.vstack([left + [0, -0.4, 0], right + [0, 0.4, 0]])
    correction, count = local_residual_field(source, target, np.zeros(3), neighbours=4)
    assert count == 8
    assert np.all(correction[:4, 1] < -0.3)
    assert np.all(correction[4:, 1] > 0.3)


def test_local_field_correction_is_clipped():
    source = np.array([[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 0]], dtype=float)
    target = source + np.array([0, 3, 0])
    correction, _ = local_residual_field(source, target, np.zeros(3), neighbours=4)
    assert np.max(np.linalg.norm(correction, axis=1)) <= 2.0 + 1e-12


def test_zero_blend_edges_equal_registered_translation():
    frame0 = np.array([[0, 0, 0], [0, 10, 0], [0, 0, 10], [5, 5, 5]], dtype=float)
    frame1 = frame0 + np.array([0.5, 0.2, -0.1])
    coords = np.vstack(
        [np.column_stack([np.zeros(4), frame0]), np.column_stack([np.ones(4), frame1])]
    )
    expected = registered_links(coords, np.ones(3))
    actual, telemetry = local_flow_links(coords, np.ones(3), neighbours=4, alpha=0.0)
    assert actual == expected
    assert telemetry[0]["accepted_edges"] == 4
