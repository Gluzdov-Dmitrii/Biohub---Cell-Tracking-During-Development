"""Source-only Horaz contracts, independent of torch and cluster libraries."""
import hashlib
import os
import re
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deterministic_split(records, source_embryo, inner_count=8):
    records = list(records)
    assert len(records) > inner_count > 0
    assert len({r['dataset_id'] for r in records}) == len(records)
    assert all(r['dataset_id'].startswith(source_embryo + '_') for r in records)
    ordered = sorted(records, key=lambda r: hashlib.sha256(
        ('EXP226-inner-v1:' + r['dataset_id']).encode()).hexdigest())
    return ordered[inner_count:], ordered[:inner_count]


def validate_plan(plan):
    assert plan['experiment'] == 'EXP226' and plan['purpose'] == 'source_only_training_pilot'
    assert plan['source_embryo'] == '44b6' and plan['target_embryo'] == '6bba'
    assert plan['fold'] == 1 and plan['epochs'] == 2 and plan['iterations_per_epoch'] == 8
    assert plan['resume'] is False and plan['checkpoint_selection'] == 'none_pilot_fixed_final'
    assert plan['num_workers'] == 0 and plan['torch_compile'] is False
    train, validation = plan['train'], plan['inner_validation']
    assert len(train) == 4 and len(validation) == 2
    ids = [r['dataset_id'] for r in train + validation]
    assert len(ids) == len(set(ids)), 'Train/inner-validation overlap'
    roots = []
    for record in train + validation:
        name = record['dataset_id']
        assert name.startswith(plan['source_embryo'] + '_'), 'Target row in source manifest'
        for key, suffix in [('zarr_path', '.zarr'), ('geff_path', '.geff')]:
            path = Path(record[key])
            assert path.name == name + suffix, 'Dataset/path mismatch'
            roots.append(path.resolve())
    assert len(roots) == len(set(roots)), 'Aliased source records'
    return roots


class SourceAccessGuard:
    """Python I/O audit plus explicit manifest routing; not an OS sandbox."""
    def __init__(self, records, output, data_root):
        self.output = Path(output).resolve()
        self.data_root = Path(data_root).resolve()
        self.allowed_ids = {r['dataset_id'] for r in records}
        self.roots = [Path(r[key]).resolve() for r in records for key in ('zarr_path', 'geff_path')]
        self.opened_ids = set()
        self.denied = []

    def check(self, path):
        if not isinstance(path, (str, bytes, os.PathLike)):
            return  # File descriptors do not encode a new pathname.
        path = Path(os.fsdecode(path)).absolute()
        resolved = path.resolve()
        if path.suffix.lower() in ('.pt', '.pth') and not resolved.is_relative_to(self.output):
            raise PermissionError('EXP226 forbids loading external/pretrained checkpoints')
        names = re.findall(r'(?:44b6|6bba)_[A-Za-z0-9]+(?=\.(?:zarr|geff)(?:[/\\]|$))', str(path))
        if any(name not in self.allowed_ids for name in names):
            raise PermissionError('EXP226 dataset outside the source allowlist')
        is_data = path.is_relative_to(self.data_root) or resolved.is_relative_to(self.data_root)
        if (is_data or names) and not any(resolved.is_relative_to(root) for root in self.roots):
            raise PermissionError('EXP226 data access outside explicit source roots')
        self.opened_ids.update(names)

    def __call__(self, event, args):
        if event in ('open', 'os.listdir', 'os.scandir') and args:
            try:
                self.check(args[0])
            except PermissionError as exc:
                self.denied.append({'event': event, 'path': str(args[0]), 'reason': str(exc)})
                raise


def invoke_source_training(module, cfg, plan, output, resolved_config):
    """Avoid upstream main()/run_periodic_cv(), both of which select on outer folds."""
    validate_plan(plan)
    module.PERIODIC_EPOCHS = (1, 2)
    return module.train_fold(cfg, plan['fold'], plan['train'], plan['inner_validation'],
                             Path(output), resolved_config, resume=False)
