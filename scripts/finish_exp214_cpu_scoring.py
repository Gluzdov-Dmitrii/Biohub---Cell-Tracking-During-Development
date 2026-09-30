"""Finite CPU-only evaluation of the two frozen EXP214 manifests after readiness."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
CODE = ROOT / 'code/exp214_inference_v6_20260912'
INPUT = ROOT / 'code/exp214_evaluation_inputs_20260912'
REPO = ROOT / 'code/exp214_honest_refit_v4_20260912/tracking_repo'
DATA = ROOT / 'data/exp213_source_view_20260912'
RUN = ROOT / 'runs/exp214_final_cpu_scoring_20260912'


def write(name, value):
    path = RUN / name
    temp = path.with_suffix('.partial')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def ready(manifest):
    spec = json.loads(manifest.read_text())
    for parts in spec['arms'].values():
        if isinstance(parts, dict):
            parts = [parts]
        for part in parts:
            if not all(Path(part[k]).is_file() for k in ('receipt', 'csv')):
                return False
    return True


def execute(label, commands):
    for number, command in enumerate(commands):
        with (RUN / f'{label}_{number}.log').open('x') as log:
            process = subprocess.Popen([sys.executable, *map(str, command)], stdout=log, stderr=subprocess.STDOUT)
            try:
                code = process.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise
        write(f'{label}_{number}_exit.json', {'returncode': code, 'command': list(map(str, command)), 'finished': time.time()})
        if code:
            raise RuntimeError(f'{label} step {number} failed; inspect log, no automatic retry')


def main():
    assert not os.environ.get('CUDA_VISIBLE_DEVICES'), 'CPU-only worker'
    manifests = {
        'paired175': INPUT / 'exp214_score175_manifest_20260912.json',
        'data_control': INPUT / 'exp214_data_control_score_manifest_20260912.json',
    }
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in manifests.items()}
    commands = {}
    out = RUN / 'paired175'
    commands['paired175'] = [
        [CODE / 'score_exp214_paired.py', '--repo', REPO, '--data', DATA, '--manifest', manifests['paired175'], '--output', out],
        [CODE / 'compare_exp214_results.py', '--metrics', out / 'metrics.json', '--baseline', INPUT / 'exp214_frozen_exp209_baseline_rows_20260912.json', '--output', out / 'comparison.json'],
    ]
    out = RUN / 'data_control'
    commands['data_control'] = [
        [ROOT / 'code/exp214_score_data_control.py', '--plan', ROOT / 'code/exp214_equal_time_v1_20260912/plan.json', '--manifest', manifests['data_control'], '--repo', REPO, '--inference-code', CODE, '--data', DATA, '--output', out],
        [ROOT / 'code/exp214_compare_data_control.py', '--metrics', out / 'metrics.json', '--full-receipt', ROOT / 'models/exp214_full_control_12epoch_20260912/receipt.json', '--reduced12-history', ROOT / 'runs/exp214_reduced44b6_s2026_20260912/output/history.json', '--reduced60-history', ROOT / 'runs/exp214_equal_time44b6_s2026_20260912/output/history.json', '--inference-code', CODE, '--output', out / 'comparison.json'],
    ]
    completed = []
    deadline = time.monotonic() + 6 * 3600
    while time.monotonic() < deadline:
        for label, manifest in manifests.items():
            assert hashlib.sha256(manifest.read_bytes()).hexdigest() == hashes[label], 'Manifest changed'
            if label not in completed and ready(manifest):
                write('status.json', {'status': 'SCORING_AFTER_PREDICTION_READINESS', 'active': label, 'completed': completed, 'updated': time.time()})
                execute(label, commands[label])
                completed.append(label)
        if len(completed) == 2:
            write('status.json', {'status': 'COMPLETE_BOTH_CPU_COMPARISONS', 'completed': completed, 'updated': time.time()})
            return
        write('status.json', {'status': 'WAITING_FROZEN_PREDICTIONS', 'completed': completed, 'updated': time.time()})
        time.sleep(45)
    raise TimeoutError('Six-hour finite scoring readiness budget reached')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        write('status.json', {'status': 'STOPPED_NO_AUTOMATIC_RETRY', 'error': str(error), 'updated': time.time()})
        raise
