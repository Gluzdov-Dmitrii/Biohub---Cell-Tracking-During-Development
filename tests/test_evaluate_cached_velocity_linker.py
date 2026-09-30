import numpy as np

from scripts.evaluate_cached_velocity_linker import velocity_links


def edge_pairs(edges):
    return {(source, target) for source, target, *_ in edges}


def test_velocity_resolves_crossing_that_global_drift_swaps():
    coords = np.asarray(
        [
            [0, 0, 0, 0],
            [0, 0, 0, 10],
            [1, 0, 0, 4],
            [1, 0, 0, 6],
            [2, 0, 0, 8],
            [2, 0, 0, 2],
        ],
        dtype=float,
    )
    baseline = edge_pairs(velocity_links(coords, np.ones(3), alpha=0.0))
    velocity = edge_pairs(velocity_links(coords, np.ones(3), alpha=1.0))
    assert {(0, 2), (1, 3)} <= baseline
    assert {(2, 5), (3, 4)} <= baseline
    assert {(0, 2), (1, 3)} <= velocity
    assert {(2, 4), (3, 5)} <= velocity


def test_rejects_alpha_outside_unit_interval():
    try:
        velocity_links(np.empty((0, 4)), np.ones(3), alpha=1.1)
    except ValueError as error:
        assert "alpha" in str(error)
    else:
        raise AssertionError("invalid alpha accepted")
