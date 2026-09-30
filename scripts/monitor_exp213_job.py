"""Windows-side monitor of ONE existing reserved job, never starts a new job."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

QUEUE = '/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py'


def ssh(alias, command, source=None):
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',alias,command],
        input=source,text=True,capture_output=True,timeout=45)
    if result.returncode:
        raise RuntimeError(f'{alias} exit {result.returncode}: {result.stderr[-1000:]}')
    return json.loads(result.stdout)


def releasable(state):
    # Unknown state, a live process group, or any process on our GPU retains lease.
    return (state.get('exit') is not None and state.get('identity_alive') is False
            and state.get('group_alive') is False and state.get('gpu_pids') == [])


def probe(config):
    source = '''import json, subprocess
from pathlib import Path
c=CONFIG
r=Path(c['run'])
def read(name):
 p=r/name
 return json.loads(p.read_text()) if p.exists() else None
launch=read('launch.json')
pid=launch['pid'] if launch else None
identity=False
group=False
for path in Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=path.read_text(); fields=raw[raw.rfind(')')+2:].split()
  if pid is not None and fields[0]!='Z':
   if int(path.parent.name)==pid and fields[19]==launch['start']: identity=True
   if int(fields[2])==pid: group=True
 except (FileNotFoundError,ProcessLookupError,PermissionError): pass
gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader'],capture_output=True,text=True,check=True)
pids=[int(line.split(',')[0]) for line in gpu.stdout.splitlines() if c['gpu'] in line]
print(json.dumps({'launch':launch,'exit':read('exit.json'),'identity_alive':identity,'group_alive':group,'gpu_pids':pids,'status':read('output/status.json')}))
'''.replace('CONFIG',repr(config))
    return ssh(config.get('alias','nsu-a100'),'python3 -',source)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    config=json.loads(args.config.read_text())
    registered=False
    errors=0
    while True:
        try:
            state=probe(config)
            common=['--id',config['lease_id'],'--token',config['token']]
            if state['launch'] and not registered:
                launch=state['launch']
                ssh('nsu-quadro',shlex.join(['python3',QUEUE,'started',*common,
                    '--pid',str(launch['pid']),'--process-start',launch['start']]))
                registered=True
            if releasable(state):
                state['queue']=ssh('nsu-quadro',shlex.join(['python3',QUEUE,'release',*common,'--verified-stopped']))
                state['monitor_status']='RELEASED_AFTER_VERIFIED_EXIT'
            else:
                state['queue']=ssh('nsu-quadro',shlex.join(['python3',QUEUE,'heartbeat',*common]))
                state['monitor_status']='MONITORING'
            state['checked_at']=time.time()
            temporary=args.receipt.with_suffix('.tmp')
            temporary.write_text(json.dumps(state,indent=2)+'\n')
            temporary.replace(args.receipt)
            print(json.dumps({'time':state['checked_at'],'state':state['monitor_status']}),flush=True)
            errors=0
            if state['monitor_status']=='RELEASED_AFTER_VERIFIED_EXIT': return
        except Exception as exc:
            errors+=1
            print(json.dumps({'time':time.time(),'error':str(exc),'consecutive_errors':errors}),flush=True)
            # A connectivity failure never releases an uncertain allocation.
            if errors>=20: raise
        time.sleep(45)


if __name__=='__main__':
    main()
