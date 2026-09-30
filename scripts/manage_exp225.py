"""Explicit, receipt-backed steps for EXP225. Never automatically retry a POST."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'work/exp225_20260922'
KERNEL = 'dmitriigluzdov/biohub-exp225-p26-research-and-frozen-inference'
COMP = 'biohub-cell-tracking-during-development'
DESCRIPTION = 'EXP225 P26 FIXED TIGHT55 GOLD_PUBLIC SLOT1 v2 20260922'
PARENT_CSV_SHA = 'd34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(name, value):
    WORK.mkdir(exist_ok=True)
    value = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), **value}
    (WORK / name).write_text(json.dumps(value, indent=2, default=str) + '\n', encoding='utf-8')
    return value


def api_client():
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()
    return api


def source_identity(api):
    from submit_code_file_once import get_current_kernel, validate_remote_kernel_identity
    remote = get_current_kernel(api, KERNEL)
    meta = remote.metadata
    source = remote.blob.source
    local_dir = ROOT / 'kaggle_notebooks/exp225_p26_research'
    local_meta = json.loads((local_dir / 'kernel-metadata.json').read_text())
    local = json.loads((local_dir / local_meta['code_file']).read_text(encoding='utf-8'))
    downloaded = json.loads(source)
    # Outputs and serialization may change; executable cells and prose must not.
    cells = lambda n: [(c['cell_type'], ''.join(c['source'])) for c in n['cells']]
    assert cells(local) == cells(downloaded), 'Remote notebook content drift'
    path = WORK / 'remote_source.ipynb'
    path.write_bytes(source.encode('utf-8'))
    digest = sha(path)
    version = int(meta.current_version_number)
    validate_remote_kernel_identity(remote, KERNEL, version, COMP, digest)
    assert meta.enable_internet is False, 'Internet must be off'
    assert meta.is_private is True, 'Notebook must remain private'
    record = save('source_identity.json', {
        'kernel': KERNEL, 'version': version, 'source_sha256': digest,
        'local_source_sha256': sha(local_dir / local_meta['code_file']),
        'executable_and_markdown_cells_equal': True,
        'internet': meta.enable_internet, 'private': meta.is_private,
        'metadata': meta.to_dict(),
    })
    return record


def status(api):
    result = api.kernels_status(KERNEL)
    record = save('kernel_status.json', {'status': str(result.status), 'response': result.to_dict()})
    print(json.dumps(record, default=str))


def download_audit(api):
    import requests
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelSessionOutputRequest
    from exp225_output_audit import audit_submission
    identity = source_identity(api)
    state = str(api.kernels_status(KERNEL).status)
    assert state.endswith('.COMPLETE'), state
    files, logs, seen = [], [], set()
    token = None
    while True:
        req = ApiListKernelSessionOutputRequest()
        req.user_name, req.kernel_slug = KERNEL.split('/')
        api._set_paging(req, 100, token)
        with api.build_kaggle_client() as client:
            response = client.kernels.kernels_api_client.list_kernel_session_output(req)
        files.extend(response.files or [])
        if response.log:
            logs.append(response.log)
        token = response.next_page_token
        if not token:
            break
        assert token not in seen, 'Repeated inventory cursor'
        seen.add(token)
    names = [f.file_name for f in files]
    assert len(names) == len(set(names))
    assert [n for n in names if PurePosixPath(n).name == 'submission.csv'] == ['submission.csv']
    out = ROOT / f"outputs/kaggle/exp225_p26_research_v{identity['version']}"
    out.mkdir(parents=True, exist_ok=True)
    (out / 'kernel.log').write_text('\n'.join(logs), encoding='utf-8')
    (out / 'output_inventory.json').write_text(json.dumps({'files': names, **identity}, indent=2), encoding='utf-8')
    required = ['submission.csv', 'exp225_runtime_audit.json']
    required += [n for n in names if n.endswith('.json') and PurePosixPath(n).parent == PurePosixPath('.') and n not in required]
    for name in required:
        assert name in names, name
        item = next(f for f in files if f.file_name == name)
        dest = out / name
        with requests.get(item.url, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            with dest.with_suffix(dest.suffix + '.partial').open('wb') as stream:
                for block in response.iter_content(1024 * 1024):
                    stream.write(block)
        dest.with_suffix(dest.suffix + '.partial').replace(dest)
    runtime = json.loads((out / 'exp225_runtime_audit.json').read_text())
    shapes = runtime['runtime_shapes']
    audit = audit_submission(out / 'submission.csv', shapes)
    assert runtime['submission_sha256'] == sha(out / 'submission.csv')
    assert audit['submission_sha256'] == runtime['submission_sha256']
    receipt = save('prepost.json', {
        'status': 'PASS_PREPOST', 'track': 'GOLD_PUBLIC', 'slot': 1,
        'hypothesis': 'Reproduce account-confirmed P26 .947 using its frozen tight55 final graph policy, without runtime train selection; make it inspectable and extensible.',
        'parent': 'P26 v1 ref56243810 scriptVersionId348873417 public.947',
        'hidden_test_dataflow': 'Runtime competition test Zarr -> pinned primary/secondary models -> TTA/association/ILP -> physical repairs/DeepCenter -> graph audit -> one root CSV',
        'expected_output': 'submission.csv', 'identity': identity, 'audit': audit,
        'runtime_receipt_sha256': sha(out / 'exp225_runtime_audit.json'),
        'output_inventory_sha256': sha(out / 'output_inventory.json'),
        'matches_parent_public_csv': audit['submission_sha256'] == PARENT_CSV_SHA,
        'promotion_gate': 'Complete nonempty account score, no API error, nonzero bytes; compare public .947. No unseen-embryo OOF claim.',
        'description': DESCRIPTION,
    })
    print(json.dumps({k: receipt[k] for k in ['status', 'matches_parent_public_csv', 'audit']}, default=str))


def submission_readback(api):
    items = api.competition_submissions(COMP)
    matches = [x for x in items if x.description == DESCRIPTION]
    rows = [{k: getattr(x, k, None) for k in ['ref', 'date', 'description', 'status', 'public_score', 'error_description', 'total_bytes', 'url']} for x in matches]
    anomalies = []
    for row in rows:
        row_status = str(row['status']).rsplit('.', 1)[-1].upper()
        if row_status == 'ERROR':
            anomalies.append({'ref': row['ref'], 'reason': 'Terminal submission ERROR'})
        if row['error_description']:
            anomalies.append({'ref': row['ref'], 'reason': str(row['error_description'])})
        if row_status == 'COMPLETE' and (
            row['public_score'] is None or not str(row['public_score']).strip()
            or not int(row['total_bytes'] or 0)
        ):
            anomalies.append({'ref': row['ref'], 'reason': 'Terminal COMPLETE without a score or output bytes'})
    state = 'ANOMALY_STOP_NO_RETRY' if anomalies else (
        'SCORED' if len(rows) == 1 and str(rows[0]['status']).rsplit('.', 1)[-1].upper() == 'COMPLETE' else 'PENDING_OR_NOT_FOUND'
    )
    record = save('submission_full_api.json', {'status': state, 'matches': rows, 'anomalies': anomalies,
                                              'quota': api.competition_get_submission_limits(COMP).to_dict()})
    print(json.dumps(record, default=str))
    return record


def submit(api):
    prepost = json.loads((WORK / 'prepost.json').read_text())
    assert prepost['status'] == 'PASS_PREPOST'
    identity = source_identity(api)
    assert identity['source_sha256'] == prepost['identity']['source_sha256']
    assert identity['version'] == prepost['identity']['version']
    tests = json.loads((WORK / 'required_tests.json').read_text())
    assert tests['status'] == 'PASS', 'Required tests failed'
    for path, digest in tests['files'].items():
        assert sha(ROOT / path) == digest, f'Rerun tests after changed file: {path}'
    with (WORK / 'submission_claim.json').open('x') as stream:
        json.dump({'description': DESCRIPTION, 'identity': identity, 'policy': 'exactly one POST; reconcile any ambiguous outcome; no automatic retry'}, stream, indent=2)
    command = [sys.executable, 'scripts/submit_code_file_once.py', '--competition', COMP,
               '--kernel', KERNEL, '--version', str(identity['version']), '--file-name', 'submission.csv',
               '--description', DESCRIPTION, '--source-file', str(WORK / 'remote_source.ipynb'),
               '--source-sha256', identity['source_sha256']]
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        chunks = [chunk.decode(errors='replace') if isinstance(chunk, bytes) else (chunk or '')
                  for chunk in (exc.stdout, exc.stderr)]
        (WORK / 'guarded_submit.log').write_text(''.join(chunks) + '\nHELPER_TIMEOUT: reconcile; never retry POST\n', encoding='utf-8')
        submission_readback(api)
        raise RuntimeError('Ambiguous helper timeout: full API reconciled; no automatic retry') from exc
    (WORK / 'guarded_submit.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    print(result.stdout)
    record = submission_readback(api)
    assert len(record['matches']) == 1, 'Reconcile submission; do not retry'
    assert not record['anomalies'], 'Submission anomaly; stop for today; no retry'
    if result.returncode:
        raise RuntimeError('Helper returned nonzero; read full receipt; no retry')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['identity', 'status', 'audit', 'submit', 'readback'])
    args = parser.parse_args()
    api = api_client()
    if args.action == 'identity':
        print(json.dumps(source_identity(api), default=str))
    elif args.action == 'status':
        status(api)
    elif args.action == 'audit':
        download_audit(api)
    elif args.action == 'submit':
        submit(api)
    else:
        submission_readback(api)
