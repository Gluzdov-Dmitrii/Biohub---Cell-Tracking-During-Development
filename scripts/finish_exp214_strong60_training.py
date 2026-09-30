"""Finite continuation of exactly three clean models to60 epochs; no inference/POST."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from monitor_exp213_job import ssh, QUEUE

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/exp214_strong60_training_progress_20260912.json'
LANES = [[('44b6', 314159), ('6bba', 2026)], [('6bba', 314159)]]


def save(status, **values):
    result = {'status': status, 'updated': time.time(), **values}
    temporary = REPORT.with_suffix('.partial')
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.replace(REPORT)
    print(json.dumps(result), flush=True)


def main():
    with (ROOT / 'reports/exp214_strong60_training_claim_20260912.json').open('x') as stream:
        json.dump({'started': time.time(), 'lanes': LANES, 'scope': 'Only prepared60epoch continuations; no model/graph tuning, metrics or POST'}, stream, indent=2)
    configurations = {}
    for lane in LANES:
        for fold, seed in lane:
            for part in range(1, 2 if fold == '44b6' else 4):
                path = ROOT / f'reports/exp214_strong60_{fold}_s{seed}_p{part:02}_config_20260912.json'
                config = json.loads(path.read_text())
                assert config['fold'] == fold and config['seed'] == seed
                assert config['code'].endswith('/exp214_strong60_v1_20260912')
                configurations[(fold, seed, part)] = (path, config, hashlib.sha256(path.read_bytes()).hexdigest())
    deadline = datetime.datetime(2026, 9, 13, 14, tzinfo=datetime.timezone.utc).timestamp()
    while time.time() < deadline:
        queue = ssh('nsu-quadro', 'python3 ' + QUEUE + ' status')['requests']
        active = [row for row in queue if row['state'] not in ('RELEASED', 'CANCELLED')]
        completed, waiting, launched = [], [], []
        for lane in LANES:
            lane_blocked = False
            for fold, seed in lane:
                model_done = False
                for part in range(1, 2 if fold == '44b6' else 4):
                    path, config, digest = configurations[(fold, seed, part)]
                    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Frozen training configuration changed'
                    monitor_path = Path(str(path).replace('_config_', '_monitor_'))
                    monitor = json.loads(monitor_path.read_text()) if monitor_path.exists() else {}
                    if monitor.get('monitor_status') == 'RELEASED_AFTER_VERIFIED_EXIT':
                        assert monitor['exit']['returncode'] == 0 and not monitor['exit']['hard_timeout'], config['run']
                        assert monitor['queue']['id'] == config['lease_id'] and monitor['queue']['state'] == 'RELEASED'
                        status = monitor['status']
                        if status['status'] == 'COMPLETE_SOURCE_REFIT':
                            assert status['epoch'] == status['total_epochs'] == 60
                            completed.append({'fold': fold, 'seed': seed, 'best_sha256': status['best_sha256']})
                            model_done = True
                            break
                        assert status['status'] == 'CHECKPOINTED_CONTINUATION_REQUIRED' and status['epoch'] < 60
                        continue
                    started = path.with_name(path.stem + '_launch.json').exists()
                    known = [row for row in active if row['id'] == config['lease_id']]
                    if started or monitor or known:
                        waiting.append(config['lease_id'])
                        lane_blocked = True
                        break
                    own = [row for row in active if row['project'] == 'biohub-cell-tracking-during-development' and row['state'] in ('RESERVED', 'RUNNING')]
                    others = [row for row in active if row['project'] != 'biohub-cell-tracking-during-development' and row['state'].startswith('WAITING')]
                    if len(own) >= 2 or (own and others):
                        waiting.append(config['lease_id'])
                        lane_blocked = True
                        break
                    process = subprocess.run([sys.executable, 'scripts/launch_exp214_job.py', '--config', str(path.relative_to(ROOT)), '--mode', 'training'], cwd=ROOT, capture_output=True, text=True, timeout=120)
                    log = path.with_name(path.stem + '_finite_launch.log')
                    log.write_text(process.stdout + '\n' + process.stderr)
                    if process.returncode:
                        raise RuntimeError('Launch stopped; reconcile any reserved lease before retry: ' + str(log))
                    result = json.loads(process.stdout)
                    active.append(result['lease'])
                    launched.append(config['lease_id'])
                    lane_blocked = True
                    break
                if lane_blocked:
                    break
                assert model_done, f'Prepared chunk capacity exhausted for {fold}/{seed}; no automatic expansion'
        if len(completed) == 3:
            save('COMPLETE_THREE_STRONG60_MODELS', completed=completed, reused_source44_seed2026=True)
            return
        save('RUNNING_FIXED_STRONG60_TRAINING', completed=completed, waiting_or_running=waiting, launched=launched)
        time.sleep(45)
    raise TimeoutError('Strong60 training deadline reached; existing jobs retain independent monitors, no successors')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('STOPPED_NEEDS_RECONCILIATION', error=str(error))
        traceback.print_exc()
        raise
