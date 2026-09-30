"""First five full Horaz epochs on 63 source movies; no external scoring or epoch choice."""
import argparse
import json
import math
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, sha256
from run_exp226_source_pilot import write_training_report


def validate(plan):
    assert plan['experiment'] == 'EXP227' and plan['purpose'] == 'source_only_full_training_first_block'
    assert plan['source_embryo'] == '44b6' and plan['target_embryo'] == '6bba'
    assert plan['fold'] == 1 and plan['block_end_epoch'] == 5 and plan['planned_epochs'] == 50
    assert plan['resume'] is False and plan['checkpoint_selection'] == 'deferred_source_graph_10_20_30_40_50'
    train, inner = plan['train'], plan['inner_validation']
    assert len(train) == 63 and len(inner) == 8
    names = [r['dataset_id'] for r in train + inner]
    assert len(names) == len(set(names)) == 71, 'Source train/validation overlap'
    roots = []
    for row in train + inner:
        assert row['dataset_id'].startswith('44b6_')
        for key, suffix in [('zarr_path', '.zarr'), ('geff_path', '.geff')]:
            p = Path(row[key])
            assert p.name == row['dataset_id'] + suffix, 'Path mismatch'
            roots.append(p.resolve())
    assert len(set(roots)) == len(roots), 'Aliased records'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    assert sha256(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text()); validate(plan)
    code = Path(__file__).resolve().parent
    for name, digest in json.loads((code/'code_manifest.json').read_text()).items():
        assert sha256(code/name) == digest, name
    manifest = json.loads((code/'source44_manifest.json').read_text())
    assert sha256(code/'source44_manifest.json') == plan['source_manifest_sha256']
    assert plan['train'] == manifest['train'] and plan['inner_validation'] == manifest['inner_validation']
    out = Path(plan['output']); out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(code/'horaz/src/src'))
    guard = SourceAccessGuard(plan['train']+plan['inner_validation'], out, plan['data_root'])
    sys.addaudithook(guard)
    result = {'status':'RUNNING_FULL_SOURCE_BLOCK', 'plan_sha256':args.plan_sha256,
              'no_generalization_claim':True, 'checkpoint_selection':plan['checkpoint_selection']}
    (out/'contract.json').write_text(json.dumps(plan, indent=2))
    started = time.time()
    try:
        import torch
        reporting = ModuleType('training_report'); reporting.write_training_report = write_training_report
        sys.modules['training_report'] = reporting
        import train
        from engine import load_checkpoint
        assert torch.cuda.is_available(); torch.set_num_threads(8)
        resolved = json.loads((code/'horaz/resolved_config.json').read_text())
        resolved.update(seed=3407, deterministic=False, epochs=50, num_workers=0,
                        torch_compile=False, max_iterations_per_epoch=None, batch_size=4,
                        max_frames=None, output_root=str(out))
        # Store the complete 50-epoch recipe in checkpoints; only this invocation ends at5.
        cfg = SimpleNamespace(**resolved); cfg.epochs = plan['block_end_epoch']
        train.PERIODIC_EPOCHS = tuple(range(1, cfg.epochs+1))
        checkpoint = train.train_fold(cfg, 1, plan['train'], plan['inner_validation'], out, resolved, resume=False)
        history = json.loads((out/'fold1/history.json').read_text())
        assert [r['epoch'] for r in history] == [1,2,3,4,5]
        assert all(r['training_iterations'] > 8 for r in history), 'Unexpected pilot-sized training'
        assert all(math.isfinite(v) for row in history for v in row.values() if isinstance(v,(int,float)))
        model, _ = load_checkpoint(checkpoint, torch.device('cpu'))
        assert all(torch.isfinite(v).all().item() for v in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        peak_gib = max(row[k] for row in history for k in ('training_peak_gpu_allocated_gb','validation_peak_gpu_allocated_gb'))
        result.update(status='PASS_FULL_SOURCE_BLOCK_5_OF_50', elapsed_seconds=time.time()-started,
                      checkpoint_sha256=sha256(checkpoint), checkpoint_reload='PASS_weights_only',
                      completed_epochs=5, planned_epochs=50, history=history, peak_cuda_allocated_gib=peak_gib)
    except BaseException as exc:
        result.update(status='FAILED_FULL_SOURCE_BLOCK',error=repr(exc),elapsed_seconds=time.time()-started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids),denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else 'attempt_blocked')
        (out/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)


if __name__=='__main__': main()
