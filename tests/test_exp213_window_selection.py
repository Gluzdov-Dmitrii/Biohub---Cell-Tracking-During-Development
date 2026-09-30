import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('selection',Path(__file__).parents[1]/'scripts/audit_exp213_training_reduction.py')
selection=importlib.util.module_from_spec(spec); spec.loader.exec_module(selection)


def test_divisions_and_neighbours_survive_high_stride():
    starts=list(range(31))
    kept=selection.select_windows(starts,[0,15,30],8,'example')
    assert set([0,1,2,13,14,15,16,17,28,29,30])<=set(kept)
    assert set(kept)<=set(starts)
    assert kept==selection.select_windows(starts,[0,15,30],8,'example')


def test_missing_windows_are_not_invented():
    starts=[0,1,4,9,21]
    assert set(selection.select_windows(starts,[9],4,'example'))<=set(starts)
