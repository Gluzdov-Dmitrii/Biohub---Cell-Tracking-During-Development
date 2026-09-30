"""Wait for all60epoch training, then finish eight fixed paired shards; no metrics/POST."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from monitor_exp213_job import ssh, QUEUE

LOCAL = Path(__file__).resolve().parents[1]
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
PYTHON = REMOTE + '/envs/prepost/py3.11-stdlib-v1/bin/python'
REPORT = LOCAL / 'reports/exp214_strong60_prediction_progress_20260912.json'
LANES = [[f'44b6_{i:02}' for i in range(5)], [f'6bba_{i:02}' for i in range(3)]]


def save(status, **values):
    result = {'status': status, 'updated': time.time(), **values}
    temp = REPORT.with_suffix('.partial')
    temp.write_text(json.dumps(result, indent=2) + '\n')
    temp.replace(REPORT)
    print(json.dumps(result), flush=True)


def main():
    with (LOCAL / 'reports/exp214_strong60_prediction_claim_20260912.json').open('x') as stream:
        json.dump({'started': time.time(), 'lanes': LANES, 'scope': 'Only eight frozen paired shards after all training/release; no target metrics or POST'}, stream, indent=2)
    configurations = {}
    for lane in LANES:
        for tag in lane:
            path = LOCAL / f'reports/exp214_strong60_paired_{tag}_config_20260912.json'
            config = json.loads(path.read_text())
            assert config['code'] == REMOTE + '/code/exp214_inference_v7_20260912'
            configurations[tag] = (path, config, hashlib.sha256(path.read_bytes()).hexdigest())
    deadline = datetime.datetime(2026, 9, 13, 17, 30, tzinfo=datetime.timezone.utc).timestamp()
    while time.time() < deadline:
        training = json.loads((LOCAL / 'reports/exp214_strong60_training_progress_20260912.json').read_text())
        if training['status'] == 'STOPPED_NEEDS_RECONCILIATION':
            raise RuntimeError('Training coordinator stopped; reconcile before prediction launch')
        if training['status'] == 'COMPLETE_THREE_STRONG60_MODELS':
            break
        save('WAITING_ALL_STRONG60_TRAINING_AND_RELEASE')
        time.sleep(45)
    else:
        raise TimeoutError('Training dependency exceeded inference deadline')
    bundle = ssh('nsu-quadro', PYTHON + ' ' + REMOTE + '/code/exp214_freeze_strong60_bundles_20260912.py')
    assert bundle['status'] == 'PASS_ALL_FOUR_STRONG60_MODELS_FROZEN'
    (LOCAL / 'reports/exp214_strong60_model_bundle_receipt_20260912.json').write_text(json.dumps(bundle, indent=2) + '\n')
    tags = [tag for lane in LANES for tag in lane]
    while time.time() < deadline:
        queue = ssh('nsu-quadro', 'python3 ' + QUEUE + ' status')['requests']
        active = [row for row in queue if row['state'] not in ('RELEASED', 'CANCELLED')]
        source = '''import json
from pathlib import Path
r=Path(ROOT);rows={}
for tag in TAGS:
 p=r/('runs/exp214_strong60_paired_'+tag+'_20260912')
 if not p.exists():continue
 row={'exists':True}
 for name,key in [('exit.json','exit'),('output/status.json','prediction')]:
  f=p/name
  if f.exists():row[key]=json.loads(f.read_text())
 rows[tag]=row
print(json.dumps(rows))
'''.replace('ROOT', repr(REMOTE)).replace('TAGS', repr(tags))
        rows = ssh('nsu-quadro', 'python3 -', source)
        completed, waiting, launched = [], [], []
        for lane in LANES:
            for tag in lane:
                path, config, digest = configurations[tag]
                assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Frozen inference config changed'
                row = rows.get(tag)
                if row:
                    if 'exit' in row:
                        assert row['exit']['returncode'] == 0 and not row['exit']['hard_timeout'], tag
                        assert row['prediction']['status'] == 'PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS'
                        monitor_path = Path(str(path).replace('_config_', '_monitor_'))
                        monitor = json.loads(monitor_path.read_text()) if monitor_path.exists() else {}
                        if monitor.get('monitor_status') == 'RELEASED_AFTER_VERIFIED_EXIT':
                            assert monitor['queue']['id'] == config['lease_id'] and monitor['queue']['state'] == 'RELEASED'
                            completed.append(tag)
                            continue
                    waiting.append(tag)
                    break
                own = [item for item in active if item['project'] == 'biohub-cell-tracking-during-development' and item['state'] in ('RUNNING', 'RESERVED')]
                others = [item for item in active if item['project'] != 'biohub-cell-tracking-during-development' and item['state'].startswith('WAITING')]
                if len(own) >= 2 or (own and others):
                    waiting.append(tag)
                    break
                process = subprocess.run([sys.executable, 'scripts/launch_exp214_job.py', '--config', str(path.relative_to(LOCAL)), '--mode', 'inference'], cwd=LOCAL, capture_output=True, text=True, timeout=120)
                log = path.with_name(path.stem + '_finite_launch.log')
                log.write_text(process.stdout + '\n' + process.stderr)
                if process.returncode:
                    raise RuntimeError('Launch stopped; reconcile any reserved lease: ' + str(log))
                active.append(json.loads(process.stdout)['lease'])
                launched.append(tag)
                break
        if len(completed) == 8:
            result = {'status': 'PASS_ALL_STRONG60_PAIRED_PREDICTIONS_RELEASED', 'shards': completed, 'movies': 175, 'target_metrics_read': False}
            source = "import json\nfrom pathlib import Path\np=Path(" + repr(REMOTE + '/code/exp214_strong60_evaluation_inputs_20260912/predictions_complete.json') + ")\nv=" + repr(result) + "\nwith p.open('x') as f:json.dump(v,f,indent=2)\nprint(json.dumps(v))\n"
            ssh('nsu-quadro', 'python3 -', source)
            save('COMPLETE_ALL_STRONG60_PREDICTIONS', completed=completed, movies=175)
            return
        save('RUNNING_FIXED_STRONG60_PREDICTIONS', completed=completed, waiting_or_running=waiting, launched=launched)
        time.sleep(45)
    raise TimeoutError('Finite inference deadline reached; existing jobs retain monitors')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('STOPPED_NEEDS_RECONCILIATION', error=str(error))
        traceback.print_exc()
        raise
