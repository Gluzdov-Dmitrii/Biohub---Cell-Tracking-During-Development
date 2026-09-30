"""Freeze all four completed60epoch models together, retaining actual plan lineage."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
PLAN = ROOT / 'code/exp214_strong60_v1_20260912/plan.json'
OUTPUT = ROOT / 'code/exp214_strong60_evaluation_inputs_20260912'
PLAN_SHA = '44f507d749bc1885e4aa9349e2e611f3359ebfc1e439d94c9823f62eab3495ee'
OLD_PLAN_SHA = '9b1fd764a4571669d0ed7c51ea4e8f4a3cdd49d455ae8af957413b45c9e398e3'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_or_verify(path, value):
    if path.exists():
        assert json.loads(path.read_text()) == value, 'Existing frozen bundle differs'
    else:
        with path.open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')


def main():
    assert sha(PLAN) == PLAN_SHA
    plan = json.loads(PLAN.read_text())
    previous = json.loads((ROOT / 'code/exp214_equal_time_v1_20260912/plan.json').read_text())
    assert plan['folds'] == previous['folds']
    for key in ('epochs', 'lr', 'batch_size', 'layers', 'downsample', 'window_size', 'pool_kernel_um', 'det_loss_weight', 'det_neg_weight', 'selection'):
        assert plan['detector'][key] == previous['detector'][key], key
    bundles = {}
    for fold in ('44b6', '6bba'):
        models = {}
        for role, seed in (('primary', 2026), ('secondary', 314159)):
            reused = fold == '44b6' and seed == 2026
            directory = ROOT / ('runs/exp214_equal_time44b6_s2026_20260912/output' if reused else f'runs/exp214_strong60_{fold}_s{seed}_p01_20260912/output')
            status_path = directory / 'status.json'
            status = json.loads(status_path.read_text())
            assert status['status'] == 'COMPLETE_SOURCE_REFIT' and status['epoch'] == status['total_epochs'] == 60
            assert status['target_data_opened'] is False
            assert status['contract']['fold'] == fold and status['contract']['seed'] == seed
            expected_plan = OLD_PLAN_SHA if reused else PLAN_SHA
            assert status['contract']['plan_sha256'] == expected_plan
            model = directory / 'edge_predictor_best.pth'
            assert sha(model) == status['best_sha256'] and sha(directory / 'checkpoint_last.pth') == status['checkpoint_sha256']
            if reused:
                assert status['best_sha256'] == '6dfa9cbfc5f298c6680a63353314d9bf353466a4aec5756aa188e4e0b2bd8bba'
            history = json.loads((directory / 'history.json').read_text())
            assert [row['epoch'] for row in history] == list(range(1, 61))
            models[role] = {'path': str(model), 'sha256': status['best_sha256'], 'actual_training_plan_sha256': expected_plan, 'source_status_sha256': sha(status_path), 'seed': seed, 'selected_epoch': max(history, key=lambda row: row['selection_score'])['epoch'], 'source_only_selection': True}
        center = ROOT / f'runs/exp180_reciprocal_deepcenter_training_20260910/output/{fold}/best.pt'
        center_sha = plan['center']['source' + fold + '_sha256']
        assert sha(center) == center_sha
        bundles[fold] = {'purpose': 'STRONG60_PAIRED175_DEVELOPMENT_COMPARISON', 'source_embryo': fold, 'training_plan_sha256': PLAN_SHA, **models, 'center': {'path': str(center), 'sha256': center_sha}, 'scope': 'All roles clean for the opposite embryo; actual per-role training plans retained, including reused prospective60epoch control. Not exact400epoch public-weight OOF.'}
    OUTPUT.mkdir(exist_ok=True)
    for fold, bundle in bundles.items():
        save_or_verify(OUTPUT / (fold + '_bundle.json'), bundle)
    result = {'status': 'PASS_ALL_FOUR_STRONG60_MODELS_FROZEN', 'comparison_plan_sha256': PLAN_SHA, 'bundles': bundles}
    save_or_verify(OUTPUT / 'model_bundle_receipt.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
