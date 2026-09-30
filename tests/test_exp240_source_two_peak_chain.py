"""Focused EXP240 label-free geometry and source-boundary tests."""

import csv
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/exp240_source_two_peak_chain_v1_20260927/screen_exp240_chains.py'
spec = importlib.util.spec_from_file_location('exp240_screen', SOURCE)
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def peaks(*rows):
    return np.asarray(list(rows), dtype=screen.PEAK_DTYPE)


def test_two_seeds_compete_for_same_exact_chain():
    nodes = {0: (0, 0, 4, 4), 1: (1, 0, 8, 8),
             2: (0, 0, 4, 5), 3: (1, 0, 8, 9)}
    edges = [(0, 1), (2, 3)]
    values = peaks((2, 0, 3, 3, 0.2), (3, 0, 4, 4, 0.3))
    got = screen.select_chains(nodes, edges, values)
    assert got['seed_count'] == 2
    assert got['offgraph_peak_count'] == 2
    assert got['legal_pair_count'] == 2
    assert got['distinct_legal_seed_count'] == 2
    assert got['selected_conflict_free_chain_count'] == 1
    assert got['selected_chains'][0]['seed_id'] == 1
    assert got == screen.select_chains(nodes, edges, values)


def test_fourth_motion_residual_rejects_pair_even_when_first_three_pass():
    nodes = {0: (0, 0, 48, 0), 1: (1, 0, 64, 0)}
    values = peaks((2, 0, 24, 0, 0.2), (3, 0, 20, 0, 0.2))
    got = screen.select_chains(nodes, [(0, 1)], values)
    assert got['offgraph_peak_count'] == 2
    assert got['legal_pair_count'] == 0
    assert got['distinct_legal_seed_count'] == 0


def test_offgraph_boundary_is_strict():
    # A peak 6.5 um from an existing node is excluded from the off-graph set.
    nodes = {0: (0, 0, 0, 0), 1: (1, 0, 0, 0),
             2: (2, 0, 0, 0)}
    values = peaks((2, 4, 0, 0, 0.2), (3, 4, 0, 0, 0.2))
    got = screen.select_chains(nodes, [(0, 1)], values)
    assert got['offgraph_peak_count'] == 1
    assert got['legal_pair_count'] == 0


def test_geff_and_image_access_guarded():
    with pytest.raises(PermissionError):
        screen.deny_data_and_geff('open', (str(screen.DATA / 'exp213_source_view_20260912/44b6_996155de.geff'), 'r'))
    with pytest.raises(PermissionError):
        screen.deny_data_and_geff('os.scandir', (str(screen.DATA / 'target_6bba.zarr'),))
    screen.deny_data_and_geff('open', (str(screen.ROOT / 'runs/exp238_source44_peak_cache_v1_20260927/output/graph__44b6_996155de.csv'), 'r'))


def test_graph_reader_rejects_non_adjacent_original_edge(tmp_path):
    path = tmp_path / 'graph.csv'
    rows = [
        [0, '44b6_996155de', 'node', 0, 0, 0, 0, 0, -1, -1],
        [1, '44b6_996155de', 'node', 1, 2, 0, 0, 0, -1, -1],
        [2, '44b6_996155de', 'edge', -1, -1, -1, -1, -1, 0, 1],
    ]
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(screen.COLUMNS)
        writer.writerows(rows)
    with pytest.raises(AssertionError):
        screen.load_graph(path, '44b6_996155de')
