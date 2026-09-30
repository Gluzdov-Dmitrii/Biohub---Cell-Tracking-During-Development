import csv
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('gate',Path(__file__).parents[1]/'scripts/score_exp214_paired.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)


def write(tmp_path,edges):
    p=tmp_path/'submission.csv'
    with p.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(gate.COLUMNS)
        for i,t in enumerate((0,1,1)):w.writerow([i,'movie','node',i,t,1,1,1,-1,-1])
        for i,(s,t) in enumerate(edges,3):w.writerow([i,'movie','edge',-1,-1,-1,-1,-1,s,t])
    return p


def test_valid_division(tmp_path):
    assert len(gate.read_graphs(write(tmp_path,[(0,1),(0,2)]))['movie']['edges'])==2


@pytest.mark.parametrize('edges',[[(0,1),(0,1)],[(1,2)],[(0,9)]])
def test_invalid_graph_blocks_metric(tmp_path,edges):
    with pytest.raises(AssertionError):gate.read_graphs(write(tmp_path,edges))
