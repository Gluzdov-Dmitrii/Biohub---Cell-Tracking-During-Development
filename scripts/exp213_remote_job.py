"""Run one bounded, preregistered source-only refit; no queue API on A100."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    root = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
    code, run = Path(config['code']), Path(config['run'])
    assert code.resolve().is_relative_to(root/'code')
    assert run.resolve().is_relative_to(root/'runs')
    run.mkdir(parents=True, exist_ok=True)
    # Exclusive ownership prevents duplicate launches after an ambiguous SSH reply.
    with (run/'job_claim.json').open('x') as stream:
        json.dump({'wrapper_pid':os.getpid(),'config':config},stream,indent=2)
    for name, expected in json.loads((code/'code_manifest.json').read_text()).items():
        assert hashlib.sha256((code/name).read_bytes()).hexdigest() == expected,name
    assert config['fold'] in ['44b6','6bba'] and config['seed'] in [2026,314159]
    assert 60 <= config['max_seconds'] <= 10800
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=config['gpu'], OMP_NUM_THREADS='8',
               MKL_NUM_THREADS='8', PYTHONDONTWRITEBYTECODE='1', CUBLAS_WORKSPACE_CONFIG=':4096:8',
               TMPDIR=str(run/'tmp'), XDG_CACHE_HOME=str(root/'cache/exp213'),
               TORCH_HOME=str(root/'cache/exp213/torch'))
    (run/'tmp').mkdir(exist_ok=True)
    command = ['taskset','-c',config.get('cpu_affinity','0-7'),str(root/'envs/prepost/py3.11-stdlib-v1/bin/python'),
        str(code/'train_exp213_detector.py'),'--plan',str(code/'plan.json'),
        '--fold',config['fold'],'--seed',str(config['seed']),'--repo',str(code/'tracking_repo'),
        '--data-dir',str(Path(config.get('data_dir',root/'data/exp213_source_view_20260912'))),'--output',str(run/'output'),
        '--precision','fp32','--max-seconds',str(config['max_seconds'])]
    for key in ('window_selection', 'image_cache', 'warm_start'):
        if config.get(key):
            value = Path(config[key])
            assert value.resolve().is_relative_to(root)
            command.extend(['--'+key.replace('_','-'), str(value)])
    if config.get('data_dir'):
        assert Path(config['data_dir']).resolve().is_relative_to(root/'data')
        assert config.get('image_cache'), 'Metadata-only input requires exact image cache'
    with (run/'training.log').open('a') as log:
        child = subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                                 env=env,start_new_session=True)
        start = Path(f'/proc/{child.pid}/stat').read_text().split()[21]
        launch = {'pid':child.pid,'start':start,'command':command,'started':time.time(),'config':config}
        (run/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
        timed_out = False
        try:
            result = child.wait(timeout=config['max_seconds']+3600)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(child.pid,signal.SIGTERM)
            try:
                result = child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL)
                result = child.wait()
        (run/'exit.json').write_text(json.dumps({'returncode':result,'hard_timeout':timed_out,
            'pid':child.pid,'start':start,'finished':time.time()},indent=2)+'\n')


if __name__ == '__main__':
    main()
