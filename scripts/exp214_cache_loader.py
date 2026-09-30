"""Exact replacement of the public trainer's strided image read."""
import ast
import inspect
from pathlib import Path
import textwrap


def cached_dataset_class(upstream, cache_path):
    import numpy as np
    import zarr
    arrays = {}

    def cache_raw(vm, t_start, count):
        name = Path(vm.zarr_path).name
        if name not in arrays:
            group = zarr.open_group(str(cache_path / name), mode='r')
            assert group.attrs['spatial_stride'] == list(vm.downsample)
            arrays[name] = (group['0'], set(group.attrs['available_frames']))
        array, available = arrays[name]
        assert set(range(t_start, t_start + count)) <= available, (name, t_start)
        return np.asarray(array[t_start:t_start + count], dtype=np.float32)

    tree = ast.parse(textwrap.dedent(inspect.getsource(upstream.FrameWindowDataset.__getitem__)))
    body = tree.body[0].body
    removed = [n for n in body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'z']
    assert len(removed) == 1
    body.remove(removed[0])
    node = next(n for n in body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == 'raw')
    node.value = ast.parse('cache_raw(vm,t_start,W)', mode='eval').body
    ast.fix_missing_locations(tree)
    namespace = {**upstream.__dict__, 'cache_raw': cache_raw}
    exec(compile(tree, '<exact_xy4_training_cache>', 'exec'), namespace)
    return type('ExactCachedDataset', (upstream.FrameWindowDataset,), {'__getitem__': namespace['__getitem__']})
