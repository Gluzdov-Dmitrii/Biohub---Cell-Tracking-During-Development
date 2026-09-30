"""Stage sealed EXP241 CPU graph code; default is local review only."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh

if not __debug__:
    raise RuntimeError('EXP241 stage requires PYTHONOPTIMIZE=0')

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'work/exp241_fixed_two_peak_source_candidate_v1_20260927'
MANIFEST = BUNDLE / 'manifest.json'
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE = REMOTE + '/code/exp241_fixed_two_peak_source_candidate_v1_20260927'
RUN = REMOTE + '/runs/exp241_fixed_two_peak_source_candidate_v1_20260927'
PREREG = ROOT / 'reports/EXP241_FIXED_TWO_PEAK_SOURCE_CANDIDATE_PREREG_20260927.md'
EXP240_RECEIPT = ROOT / 'reports/exp240_source_two_peak_chain_verified_20260927.json'
EXP240_BUNDLE = ROOT / 'work/exp240_source_two_peak_chain_v1_20260927/manifest.json'
PREREG_SHA = '6e602f1374f74282493541cfaa214de6bdff82396e22eec8995674e48bd4fe0f'
EXP240_RECEIPT_SHA = '68ea60bc71f0dbca5b0c8664515b027a195a73d11a5bd88be18850c72c6dc161'
EXP240_MANIFEST_SHA = '5bd3fd540e6df6a9b357965d0fd7c37556fe8afc2844274537cc94fb1873c370'
INTENT = ROOT / 'reports/exp241_fixed_two_peak_source_candidate_stage_intent_20260927.json'
RECEIPT = ROOT / 'reports/exp241_fixed_two_peak_source_candidate_stage_20260927.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exclusive_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def local_gate() -> tuple[dict, dict]:
    assert sha(PREREG) == PREREG_SHA
    assert sha(EXP240_RECEIPT) == EXP240_RECEIPT_SHA
    assert sha(EXP240_BUNDLE) == EXP240_MANIFEST_SHA
    prior = json.loads(EXP240_RECEIPT.read_text())
    assert prior['status'] == 'PASS_EXP240_LABEL_FREE_CPU_INDEPENDENT_VERIFICATION'
    assert prior['source_manifest_sha256'] == EXP240_MANIFEST_SHA
    assert prior['remote']['result_sha256'] == '696c951c11a68817ee45505c98173f1a9d89e200477016de992d4504425961b2'
    assert [c['selected_conflict_free_chain_count'] for c in prior['remote']['cohorts']] == [835, 358]
    assert prior['source_labels_read'] is False and prior['target_data_opened'] is False
    manifest = json.loads(MANIFEST.read_text())
    cfg = json.loads((BUNDLE / 'config.json').read_text())
    assert manifest['status'] == 'SEALED_EXP241_LABEL_FREE_CPU_GRAPH_BUNDLE'
    assert cfg['status'] == 'PREREGISTERED_EXP241_FIXED_SOURCE19_LABEL_FREE_GRAPH'
    assert cfg['prereg_sha256'] == PREREG_SHA
    assert cfg['exp240_verified_receipt_sha256'] == EXP240_RECEIPT_SHA
    assert cfg['exp240_manifest_sha256'] == EXP240_MANIFEST_SHA
    assert cfg['output'] == RUN + '/output'
    assert cfg['expected_chains'] == {'source44': 835, 'source6': 358}
    assert cfg['source_only'] and not any(cfg[k] for k in
        ('source_labels_read', 'target_data_opened', 'metric_computed', 'gpu_used', 'kaggle_post'))
    files = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob('*') if p.is_file()}
    assert files == set(manifest['files']) | {'manifest.json'}
    for rel, digest in manifest['files'].items():
        path = (BUNDLE / rel).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and sha(path) == digest
    return manifest, cfg


def remote_preflight() -> dict:
    source = r'''import json,os,pathlib
if not __debug__:raise RuntimeError('EXP241 stage requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
assert os.environ.get('PYTHONOPTIMIZE')=='0' and os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
print(json.dumps({'status':'PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS',
 'code_absent':True,'run_absent':True,'source_labels_read':False}))
'''.replace('@@CODE@@', repr(CODE)).replace('@@RUN@@', repr(RUN))
    assert '@@' not in source
    return ssh('nsu-quadro', 'env PYTHONOPTIMIZE=0 python3 -B -', source)


def remote_stage(manifest: dict, manifest_sha: str) -> dict:
    bodies = {rel: base64.b64encode((BUNDLE / rel).read_bytes()).decode('ascii')
              for rel in manifest['files']}
    bodies['manifest.json'] = base64.b64encode(MANIFEST.read_bytes()).decode('ascii')
    expected = {**manifest['files'], 'manifest.json': manifest_sha}
    source = r'''import ast,base64,hashlib,json,os,pathlib
if not __debug__:raise RuntimeError('EXP241 remote stage requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
bodies=@@BODIES@@;expected=@@EXPECTED@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.environ.get('PYTHONOPTIMIZE')=='0' and os.uname().nodename=='prepost'
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
print(json.dumps({'status':'STAGED_EXP241_LABEL_FREE_CPU_GRAPH_BUNDLE',
 'code':str(code),'manifest_sha256':sha(code/'manifest.json'),
 'files':len(observed),'run_absent':True,'source_labels_read':False}))
'''
    for token, value in {'@@CODE@@': CODE, '@@RUN@@': RUN,
                         '@@BODIES@@': bodies, '@@EXPECTED@@': expected}.items():
        source = source.replace(token, repr(value))
    assert '@@' not in source
    compile(source, 'exp241_remote_stage', 'exec')
    return ssh('nsu-quadro', 'env PYTHONOPTIMIZE=0 python3 -B -', source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    manifest, _ = local_gate()
    if not args.execute:
        print(json.dumps({'status': 'EXP241_STAGE_LOCAL_REVIEW_ONLY',
                          'manifest_sha256': sha(MANIFEST), 'files': len(manifest['files']),
                          'remote_mutation': False, 'source_labels_read': False}))
        return
    assert not INTENT.exists() and not RECEIPT.exists()
    preflight = remote_preflight()
    assert preflight['status'] == 'PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS'
    manifest_sha = sha(MANIFEST)
    exclusive_json(INTENT, {'status': 'INTENT_EXP241_CPU_STAGE',
                            'manifest_sha256': manifest_sha,
                            'preflight': preflight, 'source_labels_read': False})
    staged = remote_stage(manifest, manifest_sha)
    assert staged['status'] == 'STAGED_EXP241_LABEL_FREE_CPU_GRAPH_BUNDLE'
    assert staged['manifest_sha256'] == manifest_sha
    exclusive_json(RECEIPT, {'status': staged['status'],
                             'manifest_sha256': manifest_sha,
                             'config_sha256': sha(BUNDLE / 'config.json'),
                             'intent_sha256': sha(INTENT), 'remote': staged,
                             'run_started': False, 'source_labels_read': False})
    print(json.dumps({'status': staged['status'], 'manifest_sha256': manifest_sha}))


if __name__ == '__main__':
    main()
