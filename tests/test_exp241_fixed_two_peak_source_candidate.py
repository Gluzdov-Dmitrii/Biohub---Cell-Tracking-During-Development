"""Focused EXP241 graph provenance, exact-row preservation and guard checks."""

import csv
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/exp241_fixed_two_peak_source_candidate_v1_20260927/build_exp241_graphs.py'
spec = importlib.util.spec_from_file_location('exp241_build', SOURCE)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def fixture(tmp_path):
    name = '44b6_996155de'
    nodes = {5: (0, 0, 0, 0), 7: (1, 0, 0, 0)}
    edges = [(5, 7)]
    dtype = np.dtype([('t', '<u2'), ('z', '<u2'), ('y', '<u2'),
                      ('x', '<u2'), ('probability', '<f4')])
    peaks = np.asarray([(2, 0, 0, 0, 0.2), (3, 0, 0, 0, 0.3)], dtype=dtype)
    chain = {'seed_id': 7, 'p1': [2, 0, 0, 0], 'p2': [3, 0, 0, 0],
             'rank_residual_sq': 0.0,
             'rank_negative_probability_sum': -float(peaks[0]['probability']) - float(peaks[1]['probability']),
             'seed_legal_pair_count': 1}
    row = {'selected_conflict_free_chain_count': 1, 'selected_chains': [chain],
           'original_nodes': 2, 'original_edges': 1, 'peak_count': 2}
    original = tmp_path / 'old.csv'
    with original.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(build.COLUMNS)
        writer.writerow([11, name, 'node', 5, 0, 0, 0, 0, -1, -1])
        writer.writerow([15, name, 'node', 7, 1, 0, 0, 0, -1, -1])
        writer.writerow([19, name, 'edge', -1, -1, -1, -1, -1, 5, 7])
    return name, nodes, edges, peaks, row, original


def test_fixed_chain_appends_exact_nodes_edges_and_keeps_old_bytes(tmp_path):
    name, nodes, edges, peaks, row, original = fixture(tmp_path)
    chains = build.checked_chains(nodes, edges, peaks, row)
    candidate = tmp_path / 'candidate.csv'
    receipt = build.append_graph(original, candidate, name, nodes, edges, chains)
    assert candidate.read_bytes().startswith(original.read_bytes())
    rows = list(csv.reader(candidate.open(newline='', encoding='utf-8')))
    assert rows[-4:] == [
        ['20', name, 'node', '8', '2', '0', '0', '0', '-1', '-1'],
        ['21', name, 'node', '9', '3', '0', '0', '0', '-1', '-1'],
        ['22', name, 'edge', '-1', '-1', '-1', '-1', '-1', '7', '8'],
        ['23', name, 'edge', '-1', '-1', '-1', '-1', '-1', '8', '9'],
    ]
    assert (receipt['first_new_node_id'], receipt['first_new_row_id']) == (8, 20)
    assert receipt['added_nodes'] == receipt['added_edges'] == 2


def test_selected_peak_must_match_sealed_peak_record(tmp_path):
    _, nodes, edges, peaks, row, _ = fixture(tmp_path)
    row['selected_chains'][0]['p2'] = [3, 0, 0, 1]
    with pytest.raises(AssertionError):
        build.checked_chains(nodes, edges, peaks, row)


def test_selected_seed_must_be_original_free_end(tmp_path):
    _, nodes, edges, peaks, row, _ = fixture(tmp_path)
    edges.append((7, 10))
    nodes[10] = (2, 0, 0, 0)
    row['original_nodes'] = 3
    row['original_edges'] = 2
    with pytest.raises(AssertionError):
        build.checked_chains(nodes, edges, peaks, row)


def test_no_label_guard_blocks_geff_and_data_tree():
    with pytest.raises(PermissionError):
        build.deny_labels('open', (str(build.DATA / 'source.geff'), 'r'))
    with pytest.raises(PermissionError):
        build.deny_labels('os.scandir', (str(build.DATA / 'source.zarr'),))
    build.deny_labels('open', (str(build.ROOT / 'runs/graph.csv'), 'r'))


def test_durable_gate_call_precedes_csv_and_npy_value_load():
    source = SOURCE.read_text()
    assert source.index("durable_json(OUTPUT / 'no_label_gate.json', gate)") < source.index('nodes, edges = old.load_graph')
    assert source.index("durable_json(OUTPUT / 'no_label_gate.json', gate)") < source.index('peaks = old.load_peaks')
    assert 'os.fsync(stream.fileno())' in source and 'os.fsync(fd)' in source
