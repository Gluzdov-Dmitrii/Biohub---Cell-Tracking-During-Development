import csv
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('bounds', Path(__file__).resolve().parents[1] / 'scripts/bound_exp214_submission.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
COLUMNS = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']


def make_csv(path, z='64', t='0'):
    rows = [dict(zip(COLUMNS, row)) for row in [
        ['0','movie','node','7',t,z,'255.5','12.25','-1','-1'],
        ['1','movie','node','8','1','63.5','10','12','-1','-1'],
        ['2','movie','edge','-1','-1','-1','-1','-1','7','8']]]
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def test_only_invalid_coordinate_changes_and_raw_graph_survives(tmp_path):
    path = tmp_path / 'submission.csv'
    before = make_csv(path)
    original = path.read_bytes()
    report = module.bound_submission(path, {'movie': (2,64,256,256)})
    with path.open(newline='') as stream:
        after = list(csv.DictReader(stream))
    assert (tmp_path / 'raw_predictions.csv').read_bytes() == original
    before[0]['z'] = '63'
    assert after == before
    assert report['changed_nodes'] == 1


def test_valid_fractional_boundary_is_byte_identical(tmp_path):
    path = tmp_path / 'submission.csv'
    make_csv(path, z='63.9')
    original = path.read_bytes()
    report = module.bound_submission(path, {'movie': (2,64,256,256)})
    assert path.read_bytes() == original and report['changed_nodes'] == 0
    assert not (tmp_path / 'raw_predictions.csv').exists()


def test_time_error_is_rejected_without_changing_original(tmp_path):
    path = tmp_path / 'submission.csv'
    make_csv(path, t='2')
    original = path.read_bytes()
    with pytest.raises(AssertionError, match='timepoint'):
        module.bound_submission(path, {'movie': (2,64,256,256)})
    assert path.read_bytes() == original
