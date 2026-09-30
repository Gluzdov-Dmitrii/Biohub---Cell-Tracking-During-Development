"""Exercise generated cache-loader AST with real upstream item/augmentation code."""
import ast
import importlib.util
import json
from pathlib import Path
import sys
import types
import numpy as np
import torch
import torch.nn.functional as F

from exp221_domain_augmentation import test_contract, domain_augment


def main():
    directory = Path('publication/biohub-lite/20260910T094500Z-code-master/silver_20260912/official_evaluator/scripts')
    spec = importlib.util.spec_from_file_location('exp221_original_augmentations', Path('outputs/research/exp221_domain_pilot_code_20260921/upstream_augmentations_readonly.py'))
    augment = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(augment)
    # Preserve real function source in a temporary module for inspect.getsource.
    parsed = ast.parse((directory/'train_unet_transformer.py').read_text())
    cls = next(n for n in parsed.body if isinstance(n, ast.ClassDef) and n.name == 'FrameWindowDataset')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__getitem__')
    text = 'import numpy as np\nimport torch\nimport torch.nn.functional as F\nimport zarr\nclass FrameWindowDataset:\n'
    text += '\n'.join('    '+line for line in ast.unparse(method).splitlines())+'\n'
    module_path = Path('outputs/research/exp221_domain_pilot_code_20260921/item_test_fixture.py')
    module_path.write_text(text)
    raw = np.linspace(.1, 2., 2*3*5*7, dtype=np.float32).reshape(2, 3, 5, 7)
    class FakeGroup:
        attrs = {'spatial_stride':[1,1,1], 'available_frames':[0,1]}
        def __getitem__(self, key):
            assert key == '0'
            return raw
    sys.modules['zarr'] = types.SimpleNamespace(open_group=lambda *a, **kw: FakeGroup())
    spec = importlib.util.spec_from_file_location('exp221_item_test_fixture', module_path)
    upstream = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(upstream)
    spec = importlib.util.spec_from_file_location('exp221_generated_loader', module_path.parent/'exp214_cache_loader.py')
    cache = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cache)
    dataset_type = cache.cached_dataset_class(upstream, Path('/unused'))
    meta = {'t_start':0, 'n_frames':2, 'coords':torch.zeros(2, 4, 3), 'masks':torch.ones(2,4,dtype=torch.bool)}
    vm = types.SimpleNamespace(zarr_path='44b6_source.zarr', downsample=(1,1,1), image_shape=(2,3,5,7), voxel_size=(4,1,1), q_low=0., q_high=1.)
    def make(augs):
        ds=dataset_type(); ds._data=[(meta,vm)]; ds.augmentations=augs
        return ds
    def run(arm):
        draws=[]
        def record(imgs,coords,masks,*,rng):
            draws.append(float(rng.random()))
            return imgs,coords,masks
        augs=[record, augment.brightness_augment, augment.flip_augment]
        if arm=='domain': augs.append(domain_augment)
        ds=make(augs)
        np.random.seed(2026)
        values=[ds[0] for _ in range(4)]
        return draws, values, np.random.get_state()
    cd, cv, cs=run('control'); dd, dv, ds=run('domain')
    assert cd==dd, 'Per-item RNG draws must remain matched after candidate augmentation'
    assert np.array_equal(cs[1], ds[1]) and cs[2:]==ds[2:]
    for c,d in zip(cv,dv):
        assert torch.equal(c['coords'],d['coords']) and torch.equal(c['masks'],d['masks'])
        assert torch.isfinite(d['imgs']).all() and d['imgs'].shape==c['imgs'].shape
        assert not torch.equal(c['imgs'],d['imgs'])
    validation=make([])
    np.random.seed(1); a=validation[0]
    np.random.seed(99); b=validation[0]
    assert torch.equal(a['imgs'],b['imgs'])
    expected=torch.from_numpy(raw/(1.+1e-6)).half()
    assert torch.equal(a['imgs'],expected), 'Validation must remain exact original normalization'
    assert torch.equal(meta['coords'],torch.zeros(2,4,3)), 'Original coordinates mutated'
    result={'unit':test_contract(), 'integration':'PASS_REAL_UPSTREAM_ITEM_AST_PAIRED_RNG_VALIDATION_UNCHANGED',
            'source_validation_metric':'accuracy*recall selection proxy, not official graph score'}
    Path('reports/exp221_test_results_20260921.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
