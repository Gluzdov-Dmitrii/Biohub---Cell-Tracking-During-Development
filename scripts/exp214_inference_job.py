"""One leased, bounded inference job with immutable command and source receipts."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    config=json.loads(Path(sys.argv[1]).read_text())
    root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
    run=Path(config['run']);code=Path(config['code'])
    assert run.resolve().is_relative_to(root/'runs') and code.resolve().is_relative_to(root/'code')
    run.mkdir(parents=True,exist_ok=True)
    with (run/'job_claim.json').open('x') as f:json.dump(config,f,indent=2)
    for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
        assert hashlib.sha256((code/name).read_bytes()).hexdigest()==digest,name
    command=['taskset','-c',config['cpu_affinity'],str(root/'envs/prepost/py3.11-stdlib-v1/bin/python'),
             str(code/config['script']),*config['arguments']]
    assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')
    (run/'tmp').mkdir(exist_ok=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES=config['gpu'],OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',
             PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'),XDG_CACHE_HOME=str(root/'cache/exp214'),
             TORCH_HOME=str(root/'cache/exp214/torch'),PYTHONPATH=str(code))
    with (run/'inference.log').open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,env=env,start_new_session=True)
        start=Path(f'/proc/{child.pid}/stat').read_text().split()[21]
        (run/'launch.json').write_text(json.dumps({'pid':child.pid,'start':start,'command':command,'started':time.time(),'config':config},indent=2)+'\n')
        timeout=False
        try:result=child.wait(timeout=config['max_seconds'])
        except subprocess.TimeoutExpired:
            timeout=True;os.killpg(child.pid,signal.SIGTERM)
            try:result=child.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);result=child.wait()
        (run/'exit.json').write_text(json.dumps({'returncode':result,'hard_timeout':timeout,'pid':child.pid,'start':start,'finished':time.time()},indent=2)+'\n')


if __name__=='__main__':main()
