import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[1]/'scripts/prepare_exp213_honest_refit.py'
spec = importlib.util.spec_from_file_location('exp213_plan', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_source_validation_and_target_are_disjoint_and_reproducible():
    names = [f'44b6_{i}' for i in range(20)] + [f'6bba_{i}' for i in range(20)]
    fold = module.make_fold(names, '44b6', names)
    assert fold == module.make_fold(list(reversed(names)), '44b6', names)
    assert len(fold['validation']) == 2 and len(fold['train']) == 18
    assert len(fold['target_oof']) == 20


@pytest.mark.parametrize('mutation', ['same_movie', 'other_movie_same_embryo', 'contaminated_source'])
def test_rejects_movie_or_embryo_leakage(mutation):
    fold = {'source_embryo':'44b6', 'train':['44b6_a'], 'validation':['44b6_b'], 'target_oof':['6bba_c']}
    if mutation == 'same_movie':
        fold['validation'] = ['44b6_a']
    elif mutation == 'other_movie_same_embryo':
        fold['target_oof'] = ['44b6_d']
    else:
        fold['train'] += ['6bba_d']
    with pytest.raises(ValueError):
        module.validate_fold(fold)
