"""Finite CPU-only official175 score after all frozen strong60 predictions/release."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
RUN = ROOT / 'runs/exp214_eval90_score175_20260913'
CODE = ROOT / 'code/exp214_inference_v7_20260912'
INPUT = ROOT / 'code/exp214_eval90_inputs_20260913'


def save(status, **values):
    result = {'status': status, 'updated': time.time(), **values}
    temp = RUN / 'status.partial'
    temp.write_text(json.dumps(result, indent=2) + '\n')
    temp.replace(RUN / 'status.json')


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    deadline = datetime.datetime(2026, 9, 14, 0, tzinfo=datetime.timezone.utc).timestamp()
    marker = INPUT / 'predictions_complete.json'
    while not marker.exists() and time.time() < deadline:
        save('WAITING_ALL_FROZEN_EVAL90_PREDICTIONS')
        time.sleep(45)
    assert marker.exists(), 'Finite readiness deadline reached'
    ready = json.loads(marker.read_text())
    assert ready['status'] == 'PASS_ALL_EVAL90_PAIRED_PREDICTIONS_RELEASED' and ready['movies'] == 175 and len(ready['shards']) == 8
    out = RUN / 'output'
    commands = [
        [CODE / 'score_exp214_paired.py', '--repo', ROOT / 'code/exp214_honest_refit_v4_20260912/tracking_repo', '--data', ROOT / 'data/exp213_source_view_20260912', '--manifest', INPUT / 'manifest.json', '--output', out],
        [INPUT / 'compare_exp214_60_90.py', '--metrics', out / 'metrics.json', '--baseline', ROOT / 'runs/exp214_strong60_score175_20260912/output/metrics.json', '--output', out / 'comparison.json'],
    ]
    for index, arguments in enumerate(commands):
        timeout = min(3600, int(deadline - time.time()))
        assert timeout > 0
        save('SCORING_FIXED_EVAL90_COMPARISON', step=index)
        command = [sys.executable, *map(str, arguments)]
        with (RUN / f'step{index}.log').open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = Path(f'/proc/{process.pid}/stat').read_text().split(') ')[1].split()[19]
            (RUN / f'step{index}_launch.json').write_text(json.dumps({'pid': process.pid, 'start': identity, 'command': command, 'started': time.time()}, indent=2) + '\n')
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise
        (RUN / f'step{index}_exit.json').write_text(json.dumps({'returncode': code, 'finished': time.time()}, indent=2) + '\n')
        assert code == 0, f'Score step{index} failed; no automatic retry'
    save('COMPLETE_EVAL90_PAIRED175_COMPARISON')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('STOPPED_NO_AUTOMATIC_RETRY', error=str(error))
        raise
