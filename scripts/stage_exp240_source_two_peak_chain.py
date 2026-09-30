"""One-shot EXP240 immutable CPU code stage. Default is local review only."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh

if not __debug__:
    raise RuntimeError('EXP240 staging requires assertions; PYTHONOPTIMIZE must be 0')

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'work/exp240_source_two_peak_chain_v1_20260927'
MANIFEST = BUNDLE / 'manifest.json'
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE = REMOTE + '/code/exp240_source_two_peak_chain_v1_20260927'
RUN = REMOTE + '/runs/exp240_source_two_peak_chain_v1_20260927'
INTENT = ROOT / 'reports/exp240_source_two_peak_chain_stage_intent_20260927.json'
RECEIPT = ROOT / 'reports/exp240_source_two_peak_chain_stage_20260927.json'
PREREG = ROOT / 'reports/EXP240_SOURCE_TWO_PEAK_CHAIN_FEASIBILITY_PREREG_20260927.md'
AUDIT = ROOT / 'reports/exp238_source_peak_cpu_audit_verified_20260927.json'
PREREG_SHA = 'e2f9547dd3b3d874f53c03c93c90e663e04d1de1317eb0d668cabdec78e21e35'
AUDIT_SHA = '04cdb945f1b955ea2960b819706ea03a9c1c0a37f8ed4715052035f37111b3af'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_json(path: Path, payload: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(payload, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def local_gate() -> tuple[dict, dict]:
    assert sha(PREREG) == PREREG_SHA and sha(AUDIT) == AUDIT_SHA
    manifest = json.loads(MANIFEST.read_text())
    config = json.loads((BUNDLE / 'config.json').read_text())
    assert manifest['status'] == 'SEALED_EXP240_LABEL_FREE_CPU_BUNDLE'
    assert config['status'] == 'PREREGISTERED_EXP240_SOURCE19_LABEL_FREE'
    assert config['prereg_sha256'] == PREREG_SHA
    assert config['exp238_verified_audit_sha256_pin_only'] == AUDIT_SHA
    assert config['output'] == RUN + '/output'
    assert config['floor'] == 0.075 and config['radius_um'] == 7.0
    assert [len(c['ids']) for c in config['cohorts']] == [8, 11]
    assert [c['cohort'] for c in config['cohorts']] == ['source44', 'source6']
    assert config['source_only'] and not any(config[k] for k in
           ('labels_read', 'target_data_opened', 'graph_created', 'gpu_used',
            'metrics_computed', 'kaggle_post'))
    files = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob('*') if p.is_file()}
    assert files == set(manifest['files']) | {'manifest.json'}
    for relative, digest in manifest['files'].items():
        path = (BUNDLE / relative).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and sha(path) == digest
    for cohort in config['cohorts']:
        short = cohort['cohort']
        assert sha(BUNDLE / 'verification' / (short + '.json')) == cohort['independent_receipt_sha256']
        receipt = json.loads((BUNDLE / 'verification' / (short + '.json')).read_text())
        assert receipt['status'] == 'PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION'
        assert receipt['ordered_ids'] == cohort['ids'] and receipt['cohort'] == short
        assert receipt['exit0'] and receipt['released'] and receipt['all_graph_hashes_exact']
        assert receipt['source_only'] and not receipt['labels_read']
    first = config['cohorts'][0]
    assert sha(BUNDLE / 'verification/source44_guarded_recheck.json') == first['guarded_recheck_receipt_sha256']
    assert sha(BUNDLE / 'verification/source44_optimization_correction.json') == first['optimization_correction_receipt_sha256']
    return manifest, config


def remote_preflight() -> dict:
    source = r'''import json,os,pathlib
if not __debug__:raise RuntimeError('EXP240 stage preflight requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
assert os.environ.get('PYTHONOPTIMIZE')=='0'
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
print(json.dumps({'status':'PASS_EXP240_STAGE_PREFLIGHT_NO_LABELS',
 'code_absent':True,'run_absent':True,'source_labels_read':False,'target_data_opened':False}))
'''.replace('@@CODE@@', repr(CODE)).replace('@@RUN@@', repr(RUN))
    assert '@@' not in source
    return ssh('nsu-quadro', 'env PYTHONOPTIMIZE=0 python3 -B -', source)


def remote_stage(manifest: dict, manifest_sha: str) -> dict:
    bodies = {relative: base64.b64encode((BUNDLE / relative).read_bytes()).decode('ascii')
              for relative in manifest['files']}
    bodies['manifest.json'] = base64.b64encode(MANIFEST.read_bytes()).decode('ascii')
    expected = {**manifest['files'], 'manifest.json': manifest_sha}
    source = r'''import ast,base64,hashlib,json,os,pathlib
if not __debug__:raise RuntimeError('EXP240 remote stage requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
bodies=@@BODIES@@;expected=@@EXPECTED@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.environ.get('PYTHONOPTIMIZE')=='0'
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
code.mkdir(parents=True,exist_ok=False)
for name,encoded in bodies.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(encoded,validate=True))
 assert sha(path)==expected[name],name
 if name.endswith('.py'):ast.parse(path.read_text(),filename=name)
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
print(json.dumps({'status':'STAGED_EXP240_LABEL_FREE_CPU_BUNDLE','code':str(code),
 'manifest_sha256':sha(code/'manifest.json'),'files':len(observed),
 'run_absent':True,'source_labels_read':False,'target_data_opened':False}))
'''
    for token, value in {'@@CODE@@': CODE, '@@RUN@@': RUN,
                         '@@BODIES@@': bodies, '@@EXPECTED@@': expected}.items():
        source = source.replace(token, repr(value))
    assert '@@' not in source
    compile(source, 'exp240_remote_stage', 'exec')
    return ssh('nsu-quadro', 'env PYTHONOPTIMIZE=0 python3 -B -', source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    manifest, config = local_gate()
    if not args.execute:
        print(json.dumps({'status': 'EXP240_STAGE_LOCAL_REVIEW_ONLY',
                          'manifest_sha256': sha(MANIFEST), 'files': len(manifest['files']),
                          'remote_mutation': False, 'source_labels_read': False}))
        return
    assert not INTENT.exists() and not RECEIPT.exists()
    preflight = remote_preflight()
    assert preflight['status'] == 'PASS_EXP240_STAGE_PREFLIGHT_NO_LABELS'
    manifest_sha = sha(MANIFEST)
    exclusive_json(INTENT, {'status': 'INTENT_EXP240_CPU_STAGE',
                            'manifest_sha256': manifest_sha, 'config_sha256': sha(BUNDLE / 'config.json'),
                            'preflight': preflight, 'source_labels_read': False})
    staged = remote_stage(manifest, manifest_sha)
    assert staged['status'] == 'STAGED_EXP240_LABEL_FREE_CPU_BUNDLE'
    assert staged['manifest_sha256'] == manifest_sha
    exclusive_json(RECEIPT, {'status': staged['status'], 'manifest_sha256': manifest_sha,
                             'config_sha256': sha(BUNDLE / 'config.json'),
                             'intent_sha256': sha(INTENT), 'remote': staged,
                             'run_started': False, 'source_labels_read': False})
    print(json.dumps({'status': staged['status'], 'manifest_sha256': manifest_sha}))


if __name__ == '__main__':
    main()
