"""Source-only BF16 numerical check on the identical materialized batch.

This is not a tracking metric, an epoch-speed benchmark, or a promoted model.
"""
import argparse
import ast
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import random
import sys
import time

def main():
    p=argparse.ArgumentParser()
    for k in ('repo','plan','selection','cache','data','helpers','output'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();sys.path[:0]=[str(a.helpers),str(a.repo/'src'),str(a.repo/'scripts')]
    os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    import train_unet_transformer as upstream
    from biohub_tracking.models import TemporalUNet3D
    from exp214_cache_loader import cached_dataset_class
    torch.set_num_threads(8)
    torch.backends.cuda.enable_flash_sdp(False);torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True);torch.backends.cudnn.benchmark=False
    torch.use_deterministic_algorithms(True,warn_only=True)
    assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    plan=json.loads(a.plan.read_text());cfg=plan['detector']
    assert hashlib.sha256(a.plan.read_bytes()).hexdigest()=='983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a'
    name=plan['folds']['44b6']['train'][0];assert name.startswith('44b6_')
    selection=json.loads(a.selection.read_text())
    row=next(r for r in selection['folds']['44b6']['4']['movies'] if r['dataset']==name)
    starts=sorted(row['selected_starts'])[:8];assert len(starts)==8
    vm,windows=upstream.load_dataset_windows(a.data/(name+'.zarr'),window_size=2,downsample=(1,4,4))
    windows=[w for w in windows if w.t_start in starts];assert len(windows)==8
    dataset=cached_dataset_class(upstream,a.cache)([(vm,windows)],max_nodes=16,augmentations=[])
    batch=next(iter(DataLoader(dataset,batch_size=8,shuffle=False,num_workers=0)))
    def batch_sha():
        h=hashlib.sha256()
        for key,value in sorted(batch.items()):
            h.update(key.encode());h.update(str(value.dtype).encode());h.update(str(tuple(value.shape)).encode())
            h.update(value.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()
    frozen_sha=batch_sha()
    original_tqdm=upstream.tqdm
    upstream.tqdm=lambda *args,**kwargs:original_tqdm(*args,**{**kwargs,'disable':True})
    tree=ast.parse(inspect.getsource(upstream.train_epoch))
    loop=next(n for n in tree.body[0].body if isinstance(n,ast.For))
    begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='(unet_out, det_logits)')
    end=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='loss')
    context=ast.parse("with torch.autocast(device_type='cuda', dtype=torch.bfloat16):\n    pass").body[0]
    context.body=loop.body[begin:end+1];loop.body[begin:end+1]=[context];ast.fix_missing_locations(tree)
    namespace=dict(upstream.__dict__)
    def fp32_loss(operation):
        @functools.wraps(operation)
        def wrapped(*values,**kwargs):
            def cast(v):return v.float() if isinstance(v,torch.Tensor) and v.is_floating_point() else v
            with torch.autocast(device_type='cuda',enabled=False):return operation(*(cast(v) for v in values),**{k:cast(v) for k,v in kwargs.items()})
        return wrapped
    namespace['compute_batch_loss']=fp32_loss(upstream.compute_batch_loss)
    namespace['compute_detection_loss']=fp32_loss(upstream.compute_detection_loss)
    exec(compile(tree,'<frozen_batch_bf16>','exec'),namespace)
    random.seed(2026);np.random.seed(2026);torch.manual_seed(2026);torch.cuda.manual_seed_all(2026)
    model=upstream.UNetNodeTransformer(unet=TemporalUNet3D(in_channels=1,out_channels=32,layers=cfg['layers']),
        unet_out_channels=32,pos_feat_dim=4*upstream._POS_EMBED_DIM).cuda()
    initial={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    records={};updates={}
    for label,operation in (('fp32_a',upstream.train_epoch),('fp32_b',upstream.train_epoch),('bf16',namespace['train_epoch'])):
        model.load_state_dict(initial);optimizer=torch.optim.AdamW(model.parameters(),lr=cfg['lr'])
        random.seed(1002029);np.random.seed(1002029);torch.manual_seed(1002029);torch.cuda.manual_seed_all(1002029)
        assert batch_sha()==frozen_sha
        torch.cuda.synchronize();start=time.monotonic()
        e,d=operation(model,[batch],optimizer,torch.device('cuda'),det_loss_weight=cfg['det_loss_weight'],
            det_neg_weight=cfg['det_neg_weight'],max_iters=1,pool_kernel_um=cfg['pool_kernel_um'])
        torch.cuda.synchronize()
        updates[label]=torch.cat([(v.detach().cpu()-initial[k]).flatten() for k,v in model.named_parameters()])
        assert torch.isfinite(updates[label]).all() and batch_sha()==frozen_sha
        records[label]={'edge_loss':e,'detection_loss':d,'loss':e+cfg['det_loss_weight']*d,'step_seconds_including_warmup':time.monotonic()-start,'input_sha256':frozen_sha}
    repeat=float(torch.nn.functional.cosine_similarity(updates['fp32_a'],updates['fp32_b'],dim=0))
    cosine=float(torch.nn.functional.cosine_similarity(updates['fp32_a'],updates['bf16'],dim=0))
    relative=abs(records['bf16']['loss']-records['fp32_a']['loss'])/max(abs(records['fp32_a']['loss']),1e-8)
    result={'status':'COMPLETE_IDENTICAL_SOURCE_BATCH_PRECISION_CHECK','source_movie':name,'source_starts':starts,
        'augmentation':'disabled in this numerical probe only','target_labels_read':False,'input_sha256':frozen_sha,
        'fp32_repeat_update_cosine':repeat,'bf16_update_cosine':cosine,'bf16_relative_loss_difference':relative,
        'passes_previous_numerical_thresholds':repeat>.99 and cosine>.90 and relative<.05,
        'records':records,'device':torch.cuda.get_device_name(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'One source-only numerical probe; not end-to-end training equivalence, epoch speed, or OOF. Main FP32 models unchanged.'}
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'status.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
