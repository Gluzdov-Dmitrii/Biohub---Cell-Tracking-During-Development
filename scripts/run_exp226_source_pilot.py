"""EXP226: fresh Horaz training feasibility only; no target scoring or model selection."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, invoke_source_training, sha256, validate_plan


def write_training_report(path, fold, history):
    """Preserve numeric reports without adding plotting dependencies to the training env."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix('.report.json').write_text(json.dumps({'fold': fold, 'history': history}, indent=2))
    with path.with_suffix('.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(history[0]) if history else ['epoch'])
        writer.writeheader()
        writer.writerows(history)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    assert sha256(args.plan) == args.plan_sha256, 'Plan changed'
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    code = Path(__file__).resolve().parent
    for name, digest in json.loads((code / 'code_manifest.json').read_text()).items():
        assert sha256(code / name) == digest, name
    out = Path(plan['output'])
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(code / 'horaz/src/src'))
    guard = SourceAccessGuard(plan['train'] + plan['inner_validation'], out, plan['data_root'])
    sys.addaudithook(guard)
    started = time.time()
    result = {'status': 'RUNNING_SOURCE_ONLY_PILOT', 'plan_sha256': args.plan_sha256,
              'purpose': plan['purpose'], 'checkpoint_selection': plan['checkpoint_selection']}
    (out / 'contract.json').write_text(json.dumps(plan, indent=2))
    try:
        import torch
        report_module = ModuleType('training_report')
        report_module.write_training_report = write_training_report
        sys.modules['training_report'] = report_module
        import train
        from engine import load_checkpoint
        assert torch.cuda.is_available()
        torch.set_num_threads(8)
        cfg_values = json.loads((code / 'horaz/resolved_config.json').read_text())
        cfg_values.update(seed=plan['seed'], deterministic=False, epochs=plan['epochs'],
                          num_workers=0, torch_compile=False, max_iterations_per_epoch=8,
                          batch_size=4, max_frames=None, output_root=str(out))
        cfg = SimpleNamespace(**cfg_values)
        # Capture initialization to prove fresh build and actual optimizer updates.
        original_build = train.build_model
        initial = {}
        def build(config):
            model = original_build(config)
            initial['parameters'] = {name: value.detach().cpu().clone()
                                     for name, value in model.named_parameters()}
            return model
        train.build_model = build
        checkpoint = invoke_source_training(train, cfg, plan, out, cfg_values)
        history = json.loads((out / 'fold1/history.json').read_text())
        assert [row['epoch'] for row in history] == [1, 2]
        assert all(row['training_iterations'] == 8 for row in history)
        assert all(math.isfinite(value) for row in history for value in row.values()
                   if isinstance(value, (int, float)))
        # Official inference loader must consume our own saved checkpoint safely.
        model, model_config = load_checkpoint(checkpoint, torch.device('cpu'))
        changed = sum(not torch.equal(value.detach(), initial['parameters'][name])
                      for name, value in model.named_parameters())
        assert changed > 0, 'No optimizer updates reached saved model'
        assert all(torch.isfinite(value).all().item() for value in model.parameters())
        assert guard.opened_ids == guard.allowed_ids and not guard.denied
        result.update(status='PASS_SOURCE_ONLY_TRAINING_PILOT', elapsed_seconds=time.time()-started,
                      checkpoint_sha256=sha256(checkpoint), checkpoint_bytes=checkpoint.stat().st_size,
                      changed_parameter_tensors=changed, checkpoint_reload='PASS_weights_only',
                      peak_cuda_bytes=torch.cuda.max_memory_allocated(), history=history,
                      torch_version=str(torch.__version__), gpu=torch.cuda.get_device_name(0),
                      model_config=model_config.to_dict(), no_generalization_claim=True)
    except BaseException as exc:
        result.update(status='FAILED_SOURCE_ONLY_PILOT', error=repr(exc), elapsed_seconds=time.time()-started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids), denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else 'attempt_blocked',
                      access_control='explicit records plus reviewed Python I/O audit; not OS isolation')
        (out / 'result.json').write_text(json.dumps(result, indent=2))
        print(json.dumps({k: v for k, v in result.items() if k != 'history'}), flush=True)


if __name__ == '__main__':
    main()
