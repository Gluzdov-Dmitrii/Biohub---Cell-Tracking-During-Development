"""Packaging/model smoke only; no labels, OOF metrics, or policy tuning."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys

root = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
bundle = root / 'code/exp212_production_v4_20260912'
artifacts = bundle / 'models'
repo = root / 'code/support_repo'
run = root / 'runs/exp212_rtx_smoke_20260912'
for line in (artifacts / 'SHA256SUMS').read_text().splitlines():
    expected, relative = line.split('  ', 1)
    assert hashlib.sha256((artifacts / relative).read_bytes()).hexdigest() == expected
sys.path[:0] = [str(artifacts), str(repo / 'src'), str(repo / 'scripts')]
import numpy as np
import scipy
import torch
import numba
import polars as pl
import zarr
import tracksdata
from predict_unet_transformer import load_model
from evaluate_cached_intensity_centroid_refinement import refine_movie
from evaluate_cached_short_track_family import filter_family
from evaluate_coordinate_consensus import registered_links
from evaluate_synthetic_gap_deepcenter import load_bundle

assert hasattr(pl, 'Float16')
assert torch.cuda.is_available()
torch.set_num_threads(8)
torch.manual_seed(314159)
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)
results = {}
for arm in ('forward_44b6_model', 'reverse_6bba_model'):
    model, window, downsample = load_model(artifacts / arm / 'edge_predictor_best.pth', torch.device('cuda'))
    with torch.inference_mode():
        features = model.unet(torch.zeros((1, window, 1, 16, 16, 16), device='cuda'))
    assert torch.isfinite(features).all()
    results[arm] = {'shape': list(features.shape), 'finite': True, 'window': window, 'downsample': downsample}
    del model, features
    torch.cuda.empty_cache()
deep = load_bundle(artifacts / 'reverse_6bba_model/deepcenter_best.pt', 'ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e')
with torch.inference_mode():
    output = deep['model'](torch.zeros((1, 1, 16, 16, 16), device='cuda'))
assert torch.isfinite(output).all()
results['deepcenter'] = {'shape': list(output.shape), 'finite': True}
receipt = {'status': 'PASS_GPU_MODEL_AND_IMPORT_SMOKE', 'scope': 'Synthetic tensors only; not full runtime inference or OOF', 'device': torch.cuda.get_device_name(), 'versions': {name: importlib.metadata.version(name) for name in ('numpy','scipy','torch','numba','llvmlite','polars','zarr','tracksdata')}, 'models': results, 'all_model_manifest_hashes_match': True}
(run / 'smoke_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt), flush=True)
