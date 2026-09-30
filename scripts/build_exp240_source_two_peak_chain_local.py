"""Seal EXP240's label-free CPU source19 bundle without remote access."""

import hashlib
import json
from pathlib import Path
import shutil

if not __debug__:
    raise RuntimeError("EXP240 preparation requires assertions")

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'work/exp240_source_two_peak_chain_v1_20260927'
PREREG = ROOT / 'reports/EXP240_SOURCE_TWO_PEAK_CHAIN_FEASIBILITY_PREREG_20260927.md'
PREREG_SHA = 'e2f9547dd3b3d874f53c03c93c90e663e04d1de1317eb0d668cabdec78e21e35'
AUDIT = ROOT / 'reports/exp238_source_peak_cpu_audit_verified_20260927.json'
AUDIT_SHA = '04cdb945f1b955ea2960b819706ea03a9c1c0a37f8ed4715052035f37111b3af'
SOURCE = ROOT / 'work/exp238_source_peak_cpu_audit_20260927/config.json'
SOURCE_GRAPHS = ROOT / 'work/source_inner_error_decomposition_v2_20260927/config.json'
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
OUTPUT = REMOTE + '/runs/exp240_source_two_peak_chain_v1_20260927/output'
RECEIPTS = {
    'source44': ('exp238_source44_peak_cache_verified_20260927.json',
                 '1b27c1db034c8849ed5221c590b3bf40f53a70e96cee96d8ab973558c9ce7695'),
    'source6': ('exp238_source6_peak_cache_verified_20260927.json',
                '9272f5f0574975ea8bd4ddc72e503ff2ccc2503a46a59c39f05ef7a2d2b37765'),
    'source44_guarded_recheck': ('exp238_source44_peak_cache_guarded_recheck_20260927.json',
                                 'ca95fc50ac24b4a2ccdc0429e6d6b2fd428e1eaecb85255f7eb7133397e53f7a'),
    'source44_optimization_correction': ('exp238_source44_peak_cache_verifier_optimization_correction_20260927.json',
                                          '9a797e6e9416c85325a0584493f9986497ec84b01898c110631643991c0d9510'),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert sha(PREREG) == PREREG_SHA and sha(AUDIT) == AUDIT_SHA
    assert BUNDLE.is_dir() and (BUNDLE / 'screen_exp240_chains.py').is_file()
    old = json.loads(SOURCE.read_text())
    graph_source = json.loads(SOURCE_GRAPHS.read_text())
    assert [c['cache_cohort'] for c in old['cohorts']] == ['source44', 'source6']
    assert [len(c['ids']) for c in old['cohorts']] == [8, 11]
    copy_dir = BUNDLE / 'verification'
    copy_dir.mkdir(exist_ok=True)
    for key, (filename, digest) in RECEIPTS.items():
        src = ROOT / 'reports' / filename
        assert sha(src) == digest
        dst = copy_dir / (key + '.json')
        if dst.exists():
            assert sha(dst) == digest
        else:
            shutil.copyfile(src, dst)
            assert sha(dst) == digest
    cohorts = []
    for row, graph_cohort in zip(old['cohorts'], graph_source['cohorts']):
        short = row['cache_cohort']
        plan_path = ROOT / 'work/exp238_source_peak_cache_local_20260927' / short / 'exp238_plan.json'
        assert sha(plan_path) == row['plan_sha256']
        plan = json.loads(plan_path.read_text())
        assert plan['parent_run'].startswith(REMOTE + '/runs/')
        assert [m['dataset'] for m in plan['movies']] == row['ids']
        assert [(m['dataset'], m['graph_csv_sha256'], m['graph_receipt_sha256'])
                for m in plan['movies']] == [
                    (m['dataset'], m['csv_sha256'], m['receipt_sha256'])
                    for m in graph_cohort['graph_hashes']]
        fields = ('cache_code', 'cache_run', 'checkpoint_sha256', 'manifest_sha256',
                  'plan_sha256', 'status_sha256', 'exit_sha256', 'complete_sha256',
                  'control_sha256', 'independent_receipt_sha256',
                  'guarded_recheck_receipt_sha256', 'optimization_correction_receipt_sha256')
        cohorts.append({'cohort': short, 'source_embryo': row['source_embryo'],
                        'ids': row['ids'], 'parent_run': plan['parent_run'],
                        **{key: row.get(key) for key in fields}})
        assert cohorts[-1]['independent_receipt_sha256'] == RECEIPTS[short][1]
    config = {'status': 'PREREGISTERED_EXP240_SOURCE19_LABEL_FREE',
              'prereg_sha256': PREREG_SHA, 'exp238_verified_audit_sha256_pin_only': AUDIT_SHA,
              'output': OUTPUT, 'floor': 0.075, 'radius_um': 7.0,
              'scale_zyx_um': [1.625, 0.40625, 0.40625], 'downsample_zyx': [1, 4, 4],
              'cohorts': cohorts, 'source_only': True, 'labels_read': False,
              'target_data_opened': False, 'graph_created': False, 'gpu_used': False,
              'metrics_computed': False, 'kaggle_post': False}
    config_path = BUNDLE / 'config.json'
    expected_config = json.dumps(config, indent=2) + '\n'
    if config_path.exists():
        assert config_path.read_text() == expected_config
    else:
        config_path.write_text(expected_config)
    files = {p.relative_to(BUNDLE).as_posix(): sha(p) for p in sorted(BUNDLE.rglob('*'))
             if p.is_file() and p.name != 'manifest.json'}
    assert set(files) == {'config.json', 'screen_exp240_chains.py',
                          'verification/source44.json', 'verification/source6.json',
                          'verification/source44_guarded_recheck.json',
                          'verification/source44_optimization_correction.json'}
    manifest = {'status': 'SEALED_EXP240_LABEL_FREE_CPU_BUNDLE', 'files': files}
    manifest_path = BUNDLE / 'manifest.json'
    content = json.dumps(manifest, indent=2) + '\n'
    if manifest_path.exists():
        assert manifest_path.read_text() == content
    else:
        manifest_path.write_text(content)
    print(json.dumps({'status': 'SEALED_EXP240_LABEL_FREE_CPU_BUNDLE',
                      'manifest_sha256': sha(manifest_path), 'config_sha256': sha(config_path),
                      'files': len(files), 'remote_mutation': False, 'labels_read': False}))


if __name__ == '__main__':
    main()
