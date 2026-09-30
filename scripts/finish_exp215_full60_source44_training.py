"""Finite EXP215 full-cache source44 continuation to >=60 epochs; no inference/POST."""
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
REPORT = ROOT / 'reports/exp215_full60_source44_training_progress_20260914.json'
CLAIM = ROOT / 'reports/exp215_full60_source44_training_claim_20260914.json'
PARTS = [1, 2, 3, 4]
FOLD = '44b6'
SEED = 2026


def save(status, **values):
    result = {'status': status, 'updated': time.time(), **values}
    temporary = REPORT.with_suffix('.partial')
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.replace(REPORT)
    print(json.dumps(result), flush=True)


def claim_once():
    payload = {
        'started': time.time(),
        'parts': PARTS,
        'scope': 'EXP215 full-cache source44b6 seed2026 continuation to >=60 epochs; source-only training, no inference, metrics or POST',
    }
    if CLAIM.exists():
        current = json.loads(CLAIM.read_text())
        assert current['parts'] == PARTS
        assert 'source-only training' in current['scope']
        return
    with CLAIM.open('x') as stream:
        json.dump(payload, stream, indent=2)
        stream.write('\n')


def cluster_json(alias, command):
    last_error = None
    for attempt in range(5):
        try:
            return ssh(alias, command)
        except Exception as error:
            last_error = error
            time.sleep(5 + attempt * 5)
    raise last_error


def main():
    claim_once()
    configurations = {}
    for part in PARTS:
        path = ROOT / f'reports/exp215_full60_{FOLD}_s{SEED}_p{part:02}_config_20260914.json'
        config = json.loads(path.read_text())
        assert config['experiment'] == 'EXP215'
        assert config['fold'] == FOLD and config['seed'] == SEED
        assert config['code'].endswith('/exp215_full_source44_v1_20260914')
        configurations[part] = (path, config, hashlib.sha256(path.read_bytes()).hexdigest())
    deadline = datetime.datetime(2026, 9, 16, 23, 30, tzinfo=datetime.timezone.utc).timestamp()
    while time.time() < deadline:
        queue = cluster_json('nsu-quadro', 'python3 ' + QUEUE + ' status')['requests']
        active = [row for row in queue if row['state'] not in ('RELEASED', 'CANCELLED')]
        released_chunks, launched, waiting = [], [], []
        for part in PARTS:
            path, config, digest = configurations[part]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Frozen training configuration changed'
            monitor_path = Path(str(path).replace('_config_', '_monitor_'))
            monitor = json.loads(monitor_path.read_text()) if monitor_path.exists() else {}
            if monitor.get('monitor_status') == 'RELEASED_AFTER_VERIFIED_EXIT':
                assert monitor['exit']['returncode'] == 0 and not monitor['exit']['hard_timeout'], config['run']
                assert monitor['queue']['id'] == config['lease_id'] and monitor['queue']['state'] == 'RELEASED'
                status = monitor['status']
                released_chunks.append({'part': part, 'epoch': status['epoch'], 'best_sha256': status.get('best_sha256')})
                if status['status'] == 'CHECKPOINTED_CONTINUATION_REQUIRED' and status['epoch'] >= 60:
                    save('COMPLETE_EXP215_SOURCE44_FULL60_MODEL', released_chunks=released_chunks,
                         best_sha256=status['best_sha256'], completion_reason='minimum_epoch_reached')
                    return
                if status['status'] == 'COMPLETE_SOURCE_REFIT':
                    assert status['epoch'] == status['total_epochs'] and status['epoch'] >= 60
                    save('COMPLETE_EXP215_SOURCE44_FULL60_MODEL', released_chunks=released_chunks, best_sha256=status['best_sha256'])
                    return
                assert status['status'] == 'CHECKPOINTED_CONTINUATION_REQUIRED' and status['epoch'] < 60
                continue
            started = path.with_name(path.stem + '_launch.json').exists()
            known = [row for row in active if row['id'] == config['lease_id']]
            if started or monitor or known:
                waiting.append(config['lease_id'])
                break
            own = [row for row in active if row['project'] == 'biohub-cell-tracking-during-development' and row['state'] in ('RESERVED', 'RUNNING')]
            others_waiting = [row for row in active if row['project'] != 'biohub-cell-tracking-during-development' and row['state'].startswith('WAITING')]
            if own or others_waiting:
                waiting.append(config['lease_id'])
                break
            process = subprocess.run(
                [sys.executable, 'scripts/launch_exp214_job.py', '--config', str(path.relative_to(ROOT)), '--mode', 'training'],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=120,
            )
            log = path.with_name(path.stem + '_finite_launch.log')
            log.write_text(process.stdout + '\n' + process.stderr)
            if process.returncode:
                raise RuntimeError('Launch stopped; reconcile any reserved lease before retry: ' + str(log))
            result = json.loads(process.stdout)
            active.append(result['lease'])
            launched.append(config['lease_id'])
            break
        else:
            raise RuntimeError('Prepared EXP215 chunk capacity exhausted before epoch 60')
        save('RUNNING_EXP215_SOURCE44_FULL60_TRAINING', released_chunks=released_chunks, waiting_or_running=waiting, launched=launched)
        time.sleep(60)
    raise TimeoutError('EXP215 full60 training deadline reached; existing jobs retain independent monitors, no successors')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('STOPPED_NEEDS_RECONCILIATION', error=str(error))
        traceback.print_exc()
        raise
