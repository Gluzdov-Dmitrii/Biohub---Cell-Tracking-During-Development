"""Freeze embryo-disjoint COMPACT47 refit and compare existing evidence."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_fold(names: list[str], source: str, evaluation: list[str]) -> dict:
    source_names = sorted(n for n in names if n.split('_')[0] == source)
    ordered = sorted(source_names, key=lambda n: hashlib.sha256(('EXP213-SOURCE-VAL-v1:' + n).encode()).hexdigest())
    validation = sorted(ordered[:math.ceil(len(ordered) * .1)])
    train = sorted(set(source_names) - set(validation))
    target = sorted(n for n in evaluation if n.split('_')[0] != source)
    result = {'source_embryo': source, 'train': train, 'validation': validation, 'target_oof': target}
    validate_fold(result)
    return result


def validate_fold(fold: dict) -> None:
    train, validation, target = (set(fold[k]) for k in ('train', 'validation', 'target_oof'))
    if not train or not validation or not target:
        raise ValueError('Empty split')
    if train & validation or train & target or validation & target:
        raise ValueError('Movie leakage')
    source = fold['source_embryo']
    if any(n.split('_')[0] != source for n in train | validation):
        raise ValueError('Source split contains held-out embryo')
    if any(n.split('_')[0] == source for n in target):
        raise ValueError('Target contains training embryo')


def main() -> None:
    secondary = ROOT / 'outputs/research/frontier_20260907/s14_clean_output/secondary_seed_weights/unet_transformer/split_0'
    snapshot = json.loads((secondary / 'SNAPSHOT_MANIFEST.json').read_text())
    for name in ('edge_predictor_best.pth', 'split_manifest.json', 'training_config.json'):
        assert digest(secondary / name) == snapshot['files'][name]['sha256']
    training = json.loads((secondary / 'split_manifest.json').read_text())
    names = sorted(training['train'])
    assert len(names) == len(set(names)) == 199
    evidence_dir = ROOT / 'outputs/research/exp209_selected_centroid_confirmation_20260912'
    for line in (evidence_dir / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        # The immutable manifest contains original remote absolute paths.
        assert digest(evidence_dir / Path(name).name) == expected
    old = json.loads((evidence_dir / 'forward_plus_exp191_confirmation.json').read_text())
    rows = [r for d in old['directions'].values() for r in d['selected_rows']]
    target = sorted(Path(r['dataset']).stem for r in rows)
    assert len(target) == len(set(target)) == 175
    weight = sum(r['edge_tp'] + r['edge_fp'] + r['edge_fn'] for r in rows)
    oof = sum(r['adj_edge_jaccard'] * (r['edge_tp'] + r['edge_fp'] + r['edge_fn']) for r in rows) / weight
    dtp, dfp, dfn = (sum(r[k] for r in rows) for k in ('division_tp', 'division_fp', 'division_fn'))
    oof += .1 * dtp / max(1, dtp + dfp + dfn)
    assert abs(oof - .6815218332750073) < 1e-12
    folds = {source: make_fold(names, source, target) for source in ('44b6', '6bba')}
    public = json.loads((ROOT / 'reports/exp213_all_submissions_20260912.json').read_text())
    scored = {r['ref']: r for r in public['submissions']}
    assert public['pagination_exhausted']
    best = max((r for r in scored.values() if r.get('publicScore')), key=lambda r: float(r['publicScore']))
    assert best['ref'] == 56177715
    our = scored[56181132]
    plan = {
        'experiment': 'EXP213', 'status': 'FROZEN_BEFORE_REFIT_OR_NEW_TARGET_METRICS',
        'authorization': 'User explicitly requested maximally reliable comparable OOF and authorized necessary full COMPACT47 retraining on 2026-09-12.',
        'comparator': {'submission': best, 'version': 20, 'source_sha256': '5389953eb7c2f68b6e3664985ceb252d0eac391b65821b0ced692693003cbcba'},
        'existing_local': {'submission': our, 'recomputed_oof': oof, 'lb_minus_oof': float(our['publicScore'])-oof, 'public_gap': float(best['publicScore'])-float(our['publicScore'])},
        'provenance_gate': {'exact_public_weights_oof': 'IMPOSSIBLE_ON_AVAILABLE_TRAIN', 'secondary_sha256': snapshot['files']['edge_predictor_best.pth']['sha256'], 'secondary_training_movies': len(names), 'target_overlap': sorted(set(names) & set(target)), 'secondary_best_epoch': snapshot['best_epoch'], 'new_refit_is_not_the_exact_public_checkpoint': True},
        'all_train_movies': names, 'evaluation_movies': target, 'folds': folds,
        'detector': {'seeds': [2026, 314159], 'epochs': 400, 'lr': .0001, 'batch_size': 8, 'workers': 0, 'layers': [32,64,128], 'feature_channels': 32, 'downsample': [1,4,4], 'window_size': 2, 'pool_kernel_um': 5.0, 'det_loss_weight': 1.0, 'det_neg_weight': .01, 'initialization': 'scratch; never public checkpoint', 'selection': 'maximum source-validation accuracy times node recall; earliest strict maximum; no target selection', 'primary_seed_note': 'Public primary RNG provenance not fully documented; 2026 is the prospectively fixed reproducible refit seed, not a claim of byte-exact historical retraining.'},
        'center': {'teacher': 'Train independent source-only DeepCenter per fold; no initialization from original teacher', 'epochs': 500, 'selection': 'source-validation loss only', 'seed': 2026, 'factorization': 'Same COMPACT47 SVD layers/ranks 96,96,64', 'adaptation_steps': 500, 'adaptation_selection': 'source-only teacher fidelity every 100 steps; same original acceptance thresholds; no target access', 'training_movies': 'fold train only', 'validation_movies': 'fold validation only'},
        'frozen_inference': 'COMPACT47 v20 detector fusion, feature consensus, bidirectional association, ILP, graph repair and center confirmation unchanged; only fold checkpoints and explicit paths differ.',
        'comparisons': ['Frozen historical EXP209 on exactly the same 175 movies', 'Refit COMPACT47 full pipeline', 'EXP209 graph/postprocessing on the same refit detector outputs with the same source-only center where applicable'],
        'reporting': ['Official pooled sufficient statistics; both embryo scores; TP/FP/FN and divisions', 'Paired embryo-stratified movie bootstrap and leave-one-movie influence; conditional on two embryos', 'Training and inference time, peak memory and all input/model/source hashes'],
        'no_metric_gate': 'Do not inspect any new target score until all required fold models, target predictions and exact 175-movie coverage/hashes pass. Source-only training/validation and operational benchmark data may be read.',
        'scope_limits': 'The cohort and EXP209 family were development-adapted historically. This is leakage-controlled refit comparison on known two-embryo data, not a new independent biological test. Unknown-embryo production selector is not assigned this OOF.',
        'resources': {'gpu_count': 1, 'pool': 'quadro', 'cpu_threads': 8, 'ram_gib': 64, 'extra_disk_gib': 5, 'strategy': 'Existing immutable environment and symlinked verified data; source-only benchmark first; checkpoint/resume bounded jobs through common queue; duration estimated only after benchmark'},
        'kaggle_submission_authorized_by_this_plan': False,
    }
    destination = ROOT / 'reports/exp213_honest_refit_preregistration_20260912.json'
    if destination.exists():
        raise FileExistsError('Do not overwrite preregistration')
    destination.write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'oof': oof, 'lb':our['publicScore'], 'best_lb':best['publicScore'], 'overlap': len(plan['provenance_gate']['target_overlap']), 'folds': {k: {a:len(v[a]) for a in ('train','validation','target_oof')} for k,v in folds.items()}}, indent=2))


if __name__ == '__main__':
    main()
