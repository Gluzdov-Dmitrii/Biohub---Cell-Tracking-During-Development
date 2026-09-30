"""Bounded CPU-only operational wrapper; contains no scoring or model logic."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import sys
import time

ROOT=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')


def save(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def process_identity(pid):
    raw=Path(f'/proc/{pid}/stat').read_text();return raw[raw.rfind(')')+2:].split()[19]


def main():
    assert socket.gethostname()=='prepost'
    config_path=Path(sys.argv[1]);config=json.loads(config_path.read_text())
    code=Path(config['remote_code']).resolve();run=Path(config['remote_run']).resolve()
    assert code.is_relative_to(ROOT/'code') and run.is_relative_to(ROOT/'runs')
    assert code.name.startswith('exp224_') and run.name.startswith('exp224_')
    assert config['resources']=={'cpu':4,'ram_gib':32,'gpus':0,'timeout_seconds':7200}
    manifest=json.loads((code/'code_manifest.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((code/name).read_bytes()).hexdigest()==digest,name
    with (run/'wrapper_claim.json').open('x') as f:json.dump({'pid':os.getpid(),'at':time.time()},f)
    entry=code/config['entrypoint'];assert entry.is_file() and entry.parent==code
    args=[value.replace('{code}',str(code)).replace('{run}',str(run)).replace('{root}',str(ROOT)) for value in config['arguments']]
    command=[str(ROOT/'envs/prepost/py3.11-stdlib-v1/bin/python'),str(entry),*args]
    (run/'tmp').mkdir(exist_ok=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',
             POLARS_MAX_THREADS='4',NUMEXPR_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'),
             PYTHONPATH=str(code),XDG_CACHE_HOME=str(ROOT/'cache/exp224'))
    def limits():
        os.sched_setaffinity(0,{0,1,2,3})
        resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
    started=time.time()
    with (run/'worker.log').open('x') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                               start_new_session=True,env=env,preexec_fn=limits)
        identity=process_identity(child.pid)
        save(run/'launch.json',{'pid':child.pid,'start':identity,'started':started,'command':command,
             'wrapper_pid':os.getpid(),'wrapper_start':process_identity(os.getpid()),'config':config})
        timed_out=False
        try: result=child.wait(timeout=7200)
        except subprocess.TimeoutExpired:
            timed_out=True
            os.killpg(child.pid,signal.SIGTERM)
            try: result=child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);result=child.wait()
        # Clean only descendants in this exact session/process group, even if
        # a worker spawned a helper that survived its normal exit.
        group_remaining=[]
        for stat in Path('/proc').glob('[0-9]*/stat'):
            try:
                raw=stat.read_text();fields=raw[raw.rfind(')')+2:].split()
                if fields[0]!='Z' and int(fields[2])==child.pid:group_remaining.append(int(stat.parent.name))
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
        if group_remaining:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            time.sleep(2)
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        save(run/'exit.json',{'returncode':result,'hard_timeout':timed_out,'pid':child.pid,'start':identity,
             'started':started,'finished':time.time(),'orphan_group_cleanup':group_remaining})


if __name__=='__main__':main()
