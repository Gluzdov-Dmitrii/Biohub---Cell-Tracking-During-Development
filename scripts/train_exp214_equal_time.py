"""Resumable source-only detector refit using the existing public trainer math.

Only epoch orchestration, lazy metadata padding, receipts and resume are new.
Losses, augmentations, model architecture and per-batch optimizer math are reused.
"""
from __future__ import annotations

import argparse
import ast
import functools
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

from prepare_exp213_honest_refit import validate_fold


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--fold', choices=['44b6', '6bba'], required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--data-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--benchmark-steps', type=int, default=0)
    p.add_argument('--max-seconds', type=int, default=10800)
    p.add_argument('--precision', choices=['fp32','bf16'], default='fp32')
    p.add_argument('--window-selection', type=Path, default=None,
                   help='Source-only reduction receipt. Uses the frozen stride-4 cohort; validation stays full.')
    p.add_argument('--image-cache', type=Path, default=None)
    p.add_argument('--warm-start',type=Path,default=None)
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    fold = plan['folds'][args.fold]
    validate_fold(fold)
    cfg = plan['detector']
    assert args.seed in cfg['seeds']
    assert args.max_seconds > 0 and args.benchmark_steps >= 0
    sys.path[:0] = [str(args.repo/'src'), str(args.repo/'scripts')]
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    import train_unet_transformer as upstream
    from biohub_tracking.models import TemporalUNet3D
    torch.set_num_threads(8)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    assert torch.cuda.is_available(), 'Reserved GPU required'
    original_tqdm = upstream.tqdm
    upstream.tqdm = lambda *a, **kw: original_tqdm(*a, **{**kw, 'disable': True})
    train_epoch = upstream.train_epoch
    if args.precision == 'bf16':
        assert torch.cuda.is_bf16_supported()
        # Autocast only forward/loss; optimizer, parameters and backward remain FP32.
        import inspect
        tree = ast.parse(inspect.getsource(upstream.train_epoch))
        loop = next(node for node in tree.body[0].body if isinstance(node, ast.For))
        begin = next(i for i,node in enumerate(loop.body) if isinstance(node, ast.Assign)
                     and ast.unparse(node.targets[0]) == '(unet_out, det_logits)')
        end = next(i for i,node in enumerate(loop.body) if isinstance(node, ast.Assign)
                   and ast.unparse(node.targets[0]) == 'loss')
        context = ast.parse("with torch.autocast(device_type='cuda', dtype=torch.bfloat16):\n    pass").body[0]
        context.body = loop.body[begin:end+1]
        loop.body[begin:end+1] = [context]
        ast.fix_missing_locations(tree)
        namespace = dict(upstream.__dict__)
        def fp32_loss(operation):
            @functools.wraps(operation)
            def wrapped(*values, **kwargs):
                def cast(value):
                    return value.float() if isinstance(value,torch.Tensor) and value.is_floating_point() else value
                with torch.autocast(device_type='cuda', enabled=False):
                    return operation(*(cast(v) for v in values), **{k:cast(v) for k,v in kwargs.items()})
            return wrapped
        # The public edge loss applies BCE to probabilities, which requires FP32.
        # Preserve its exact formula; do not replace it with another loss.
        namespace['compute_batch_loss'] = fp32_loss(upstream.compute_batch_loss)
        namespace['compute_detection_loss'] = fp32_loss(upstream.compute_detection_loss)
        exec(compile(tree, '<exp213_bf16_forward_only>', 'exec'), namespace)
        train_epoch = namespace['train_epoch']

    def seed_all(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed % (2**32))
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    seed_all(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    contract = {'plan_sha256': sha(args.plan), 'trainer_sha256': sha(Path(__file__)),
                'upstream_sha256': sha(Path(upstream.__file__)), 'fold': args.fold,
                'seed': args.seed, 'benchmark_steps': args.benchmark_steps, 'precision':args.precision,
                'window_selection_sha256': sha(args.window_selection) if args.window_selection else None,
                'image_cache_manifest_sha256':sha(args.image_cache/'manifest.json') if args.image_cache else None,
                'warm_start_sha256':sha(args.warm_start) if args.warm_start else None}
    contract_path = args.output/'contract.json'
    if contract_path.exists():
        assert json.loads(contract_path.read_text()) == contract, 'Resume contract changed'
    else:
        assert not any(args.output.iterdir()), 'Nonempty unregistered output directory'
        contract_path.write_text(json.dumps(contract, indent=2)+'\n')
    started = time.monotonic()
    data = {}
    for key in ('train', 'validation'):
        data[key] = []
        for index, name in enumerate(fold[key]):
            path = args.data_dir / (name+'.zarr')
            assert path.is_dir() and path.with_suffix('.geff').is_dir(), name
            data[key].append(upstream.load_dataset_windows(path, window_size=2, downsample=(1,4,4)))
            if (index+1) % 10 == 0 or index+1 == len(fold[key]):
                print(json.dumps({'stage':'load_source_only','split':key,'loaded':index+1,'total':len(fold[key])}), flush=True)
    if args.window_selection:
        reduction = json.loads(args.window_selection.read_text())
        # Selection was audited against the original immutable split contract.
        expected_plan_sha = plan.get('parent_plan_sha256', sha(args.plan))
        assert reduction['plan_sha256'] == expected_plan_sha
        selected = {v['dataset']:set(v['selected_starts']) for v in reduction['folds'][args.fold]['4']['movies']}
        assert set(selected) == set(fold['train'])
        filtered = []
        for vm, windows in data['train']:
            names = Path(vm.zarr_path).name.removesuffix('.zarr')
            keep = selected[names]
            assert keep <= {w.t_start for w in windows}
            chosen = [w for w in windows if w.t_start in keep]
            assert chosen and all(w.n_frames == 2 for w in chosen)
            assert all(w.t_start in keep for w in windows if (w.targets[0].sum(dim=1)>1).any())
            filtered.append((vm, chosen))
        data['train'] = filtered
    max_nodes = max(max(w.node_counts) for dataset in data.values() for _, windows in dataset for w in windows)

    class LazyRows:
        def __init__(self, video_data):
            self.rows = [(w, vm) for vm, windows in video_data for w in windows]
        def __len__(self):
            return len(self.rows)
        def __getitem__(self, index):
            window, vm = self.rows[index]
            return upstream.pad_window(window, max_nodes), vm

    dataset_class = upstream.FrameWindowDataset
    if args.image_cache:
        from exp214_cache_loader import cached_dataset_class
        cache_manifest = json.loads((args.image_cache/'manifest.json').read_text())
        assert cache_manifest['status'] == 'PASS_ALL_RETAINED_PIXELS_EXACT'
        assert cache_manifest['movies'] == 199
        assert cache_manifest['contract']['plan_sha256'] == plan.get('parent_plan_sha256',sha(args.plan))
        dataset_class = cached_dataset_class(upstream, args.image_cache)

    def dataset(key):
        # Identical upstream __getitem__; defer global-max padding until sampled.
        result = object.__new__(dataset_class)
        result.max_nodes = max_nodes
        result.augmentations = upstream.DEFAULT_AUGMENTATIONS if key == 'train' else []
        result._data = LazyRows(data[key])
        return result

    train_ds, validation_ds = dataset('train'), dataset('validation')
    loading_seconds = time.monotonic()-started
    model = upstream.UNetNodeTransformer(
        unet=TemporalUNet3D(in_channels=1, out_channels=32, layers=cfg['layers']),
        unet_out_channels=32, pos_feat_dim=4*upstream._POS_EMBED_DIM,
    ).cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['lr'])
    precision_check = None
    if args.benchmark_steps and args.precision == 'bf16':
        initial = {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        checks, updates = {}, {}
        for label, operation in [('fp32',upstream.train_epoch),('bf16',train_epoch)]:
            model.load_state_dict(initial)
            optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['lr'])
            seed_all(args.seed+1000003)
            probe_loader = DataLoader(train_ds, batch_size=cfg['batch_size'], shuffle=True,
                num_workers=0, generator=torch.Generator().manual_seed(args.seed+1000003))
            e,d = operation(model, probe_loader, optimizer, torch.device('cuda'),
                det_loss_weight=cfg['det_loss_weight'], det_neg_weight=cfg['det_neg_weight'],
                max_iters=1, pool_kernel_um=cfg['pool_kernel_um'])
            checks[label] = {'edge_loss':e,'detection_loss':d,'loss':e+cfg['det_loss_weight']*d}
            updates[label] = torch.cat([(v.detach().cpu()-initial[k]).flatten() for k,v in model.named_parameters()])
            assert torch.isfinite(updates[label]).all()
        relative = abs(checks['bf16']['loss']-checks['fp32']['loss'])/max(abs(checks['fp32']['loss']),1e-8)
        cosine = float(torch.nn.functional.cosine_similarity(updates['fp32'],updates['bf16'],dim=0))
        precision_check = {'source_first_step':checks,'relative_loss_difference':relative,'parameter_update_cosine':cosine,
                           'gate':'relative loss difference <0.05 and parameter update cosine >0.90',
                           'pass':relative < .05 and cosine > .90}
        (args.output/'precision_check.json').write_text(json.dumps(precision_check,indent=2)+'\n')
        assert precision_check['pass'], precision_check
        model.load_state_dict(initial)
        optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['lr'])
        del initial,updates
    architecture = {'unet_out_channels':32, 'unet_layers':cfg['layers'], 'downsample':[1,4,4], 'window_size':2, 'pool_kernel_um':5.0}
    (args.output/'config.json').write_text(json.dumps(architecture, indent=2)+'\n')
    last = args.output/'checkpoint_last.pth'
    epoch, best_score, history = 0, -1., []
    if last.exists():
        checkpoint = torch.load(last, map_location='cpu', weights_only=False)
        assert checkpoint['contract'] == contract
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        epoch, best_score, history = checkpoint['epoch'], checkpoint['best_score'], checkpoint['history']
        del checkpoint
    if not last.exists() and args.warm_start:
        import shutil
        checkpoint=torch.load(args.warm_start,map_location='cpu',weights_only=False)
        parent_status=json.loads((args.warm_start.parent/'status.json').read_text())
        assert parent_status['status']=='COMPLETE_SOURCE_REFIT' and parent_status['epoch']==12
        assert parent_status['checkpoint_sha256']==sha(args.warm_start)
        assert checkpoint['contract']['plan_sha256']==plan['warm_start_plan_sha256']
        assert checkpoint['contract']['fold']==args.fold and checkpoint['contract']['seed']==args.seed
        assert checkpoint['contract']['window_selection_sha256']==contract['window_selection_sha256']
        assert checkpoint['contract']['image_cache_manifest_sha256']==contract['image_cache_manifest_sha256']
        assert sha(args.warm_start.parent/'edge_predictor_best.pth')==parent_status['best_sha256']
        model.load_state_dict(checkpoint['model']);optimizer.load_state_dict(checkpoint['optimizer'])
        epoch,best_score,history=checkpoint['epoch'],checkpoint['best_score'],checkpoint['history']
        shutil.copy2(args.warm_start.parent/'edge_predictor_best.pth',args.output/'edge_predictor_best.pth')
        del checkpoint
    print(json.dumps({'stage':'ready','train_windows':len(train_ds),'validation_windows':len(validation_ds),'max_nodes':max_nodes,'loading_seconds':loading_seconds,'resume_epoch':epoch}), flush=True)
    initial_epoch = epoch
    for epoch in range(epoch+1, cfg['epochs']+1):
        seed_all(args.seed+1000003*epoch)
        generator = torch.Generator().manual_seed(args.seed+1000003*epoch)
        train_loader = DataLoader(train_ds, batch_size=cfg['batch_size'], shuffle=True,
                                  num_workers=0, generator=generator)
        validation_loader = DataLoader(validation_ds, batch_size=cfg['batch_size'], shuffle=False, num_workers=0)
        torch.cuda.reset_peak_memory_stats()
        epoch_start = time.monotonic()
        edge_loss, detection_loss = train_epoch(model, train_loader, optimizer, torch.device('cuda'),
            det_loss_weight=cfg['det_loss_weight'], det_neg_weight=cfg['det_neg_weight'],
            max_iters=args.benchmark_steps or None, pool_kernel_um=cfg['pool_kernel_um'])
        training_seconds = time.monotonic()-epoch_start
        peak = torch.cuda.max_memory_allocated()
        if args.benchmark_steps:
            receipt = {'status':'PASS_SOURCE_ONLY_TRAINING_BENCHMARK','scope':'Not OOF; benchmark state never promoted',
                       'contract':contract,'steps':args.benchmark_steps,'batch_size':cfg['batch_size'],
                       'train_windows':len(train_ds),'validation_windows':len(validation_ds),'max_nodes':max_nodes,
                       'loading_seconds':loading_seconds,'train_seconds':training_seconds,'peak_cuda_bytes':peak,
                       'seconds_per_step':training_seconds/args.benchmark_steps,
                       'estimated_train_only_epoch_seconds':training_seconds/args.benchmark_steps*len(train_loader),
                       'device':torch.cuda.get_device_name(),'target_data_opened':False}
            receipt['precision_check'] = precision_check
            (args.output/'benchmark.json').write_text(json.dumps(receipt, indent=2)+'\n')
            print(json.dumps(receipt), flush=True)
            return
        loss, accuracy, recall = upstream.evaluate(model, validation_loader, torch.device('cuda'), pool_kernel_um=5.)
        score = accuracy*recall
        if not np.isfinite([loss,accuracy,recall,edge_loss,detection_loss]).all():
            raise RuntimeError('Nonfinite source training/validation metrics')
        if score > best_score:
            best_score = score
            best_tmp = args.output/'edge_predictor_best.pth.tmp'
            torch.save(model.state_dict(), best_tmp)
            best_tmp.replace(args.output/'edge_predictor_best.pth')
        record = {'epoch':epoch,'edge_loss':edge_loss,'det_loss':detection_loss,
                  'source_loss':loss,'source_accuracy':accuracy,'source_node_recall':recall,
                  'selection_score':score,'best_score':best_score,'train_seconds':training_seconds,
                  'epoch_seconds':time.monotonic()-epoch_start,'peak_cuda_bytes':torch.cuda.max_memory_allocated()}
        history.append(record)
        temporary = args.output/'checkpoint_last.pth.tmp'
        torch.save({'contract':contract,'model':model.state_dict(),'optimizer':optimizer.state_dict(),
                    'epoch':epoch,'best_score':best_score,'history':history}, temporary)
        temporary.replace(last)
        (args.output/'history.json').write_text(json.dumps(history, indent=2)+'\n')
        print(json.dumps(record), flush=True)
        if time.monotonic()-started >= args.max_seconds:
            break
    status = {'status':'COMPLETE_SOURCE_REFIT' if epoch == cfg['epochs'] else 'CHECKPOINTED_CONTINUATION_REQUIRED',
              'epoch':epoch,'total_epochs':cfg['epochs'],'invocation_initial_epoch':initial_epoch,
              'checkpoint_sha256':sha(last),'best_sha256':sha(args.output/'edge_predictor_best.pth'),
              'elapsed_seconds':time.monotonic()-started,'target_data_opened':False,'contract':contract}
    (args.output/'status.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status), flush=True)


if __name__ == '__main__':
    main()
