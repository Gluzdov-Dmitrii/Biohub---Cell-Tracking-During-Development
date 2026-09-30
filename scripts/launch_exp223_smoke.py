"""Launch exactly one prepared EXP214 job through the shared queue, then monitor it."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from monitor_exp213_job import ssh,QUEUE


def queue_request(args, request_id, token):
    command=shlex.join(args)
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','nsu-quadro',command],
        text=True,capture_output=True,timeout=45)
    if result.stdout.strip().startswith('{'):
        payload=json.loads(result.stdout)
        if payload.get('state')=='WAITING_RESOURCE':
            ssh('nsu-quadro',shlex.join(['python3',QUEUE,'cancel','--id',request_id,'--token',token]))
            raise RuntimeError('Queue returned WAITING_RESOURCE; cancelled unlaunched request '+request_id)
        if result.returncode==0:
            return payload
    if result.returncode:
        raise RuntimeError(f'nsu-quadro exit {result.returncode}: {result.stderr[-1000:]}')
    raise RuntimeError('Queue request did not return JSON object')


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True)
    p.add_argument('--mode',choices=['training','inference'],required=True);a=p.parse_args()
    c=json.loads(a.config.read_text());assert c['experiment'] == 'EXP223'
    root='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
    assert c['run'].startswith(root+'/runs/exp223_')
    assert c['code'].startswith(root+'/code/exp223_')
    state=ssh('nsu-quadro',shlex.join(['python3',QUEUE,'status']))
    for required in c.get('requires_released_runs', []):
        previous=[r for r in state['requests'] if r['run_path']==required]
        assert previous and any(r['state']=='RELEASED' for r in previous), 'Required predecessor has not been released: '+required
        assert all(r['state'] in ('RELEASED','CANCELLED') for r in previous), 'Required predecessor still active: '+required
    if c.get('resume_output'):
        parent=c['resume_output'].removesuffix('/output')
        previous=[r for r in state['requests'] if r['run_path']==parent]
        assert previous and any(r['state']=='RELEASED' for r in previous)
        assert all(r['state'] in ('RELEASED','CANCELLED') for r in previous), 'Original job has not been released'
    active=[r for r in state['requests'] if r['state'] in ('RUNNING','RESERVED')]
    others_waiting=[r for r in state['requests'] if r['project']!='biohub-cell-tracking-during-development' and r['state'].startswith('WAITING')]
    if others_waiting and any(r['project']=='biohub-cell-tracking-during-development' for r in active):
        raise RuntimeError('Other project waiting; do not start a second Biohub GPU job')
    resources=c['resources']
    args=['python3',QUEUE,'request','--id',c['lease_id'],'--owner','biohub-agent','--token',c['token'],
          '--project','biohub-cell-tracking-during-development','--run-path',c['run'],'--pool',c.get('pool','a100'),'--count','1',
          '--cpu',str(resources['cpu']),'--ram-gib',str(resources['ram_gib']),
          '--disk-gib',str(resources['disk_growth_gib']),'--minutes',str(c.get('lease_minutes',240))]
    lease=queue_request(args,c['lease_id'],c['token'])
    assert lease['state']=='RESERVED' and lease['health']=='CURRENT',lease
    if lease['gpus'] != [c['gpu']]:
        ssh('nsu-quadro',shlex.join(['python3',QUEUE,'release','--id',c['lease_id'],'--token',c['token'],'--verified-stopped']))
        raise AssertionError('Allocated GPU mismatch; released unlaunched lease: '+json.dumps(lease))
    assert a.mode == 'inference'
    wrapper='exp223_inference_job.py'
    source='''import subprocess,json
from pathlib import Path
c=CONFIG
r=Path(c['run']); assert not r.exists(), 'Existing run: reconcile, never duplicate launch'
assert c['gpu'] not in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
r.mkdir(); config=r/'config.json';config.write_text(json.dumps(c,indent=2)+'\\n')
if c.get('resume_output'):
 original=Path(c['resume_output']).resolve()
 assert original.is_relative_to(Path(ROOT)/'runs') and original.name=='output'
 assert (original.parent/'exit.json').is_file(), 'Original wrapper has not recorded exit'
 previous=json.loads((original.parent/'launch.json').read_text())
 stat=Path('/proc')/str(previous['pid'])/'stat'
 assert not stat.exists() or stat.read_text().split()[21]!=previous['start'], 'Original PID identity is still alive'
 contract=json.loads((original/'contract.json').read_text())
 assert contract['fold']==c['fold'] and contract['seed']==c['seed']
 assert (original/'checkpoint_last.pth').is_file()
 (r/'output').symlink_to(original,target_is_directory=True)
with (r/'wrapper.log').open('w') as log:
 p=subprocess.Popen([ROOT+'/envs/prepost/py3.11-stdlib-v1/bin/python',str(Path(c['code'])/WRAPPER),str(config)],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'wrapper_pid':p.pid,'run':str(r)}))
'''.replace('CONFIG',repr(c)).replace('ROOT',repr(root)).replace('WRAPPER',repr(wrapper))
    assert lease['alias']==c.get('alias','nsu-a100')
    launch=ssh(c.get('alias','nsu-a100'),'python3 -',source)
    stem=a.config.stem.removesuffix('_config')+'_monitor'
    receipt=a.config.parent/(stem+'.json')
    with (a.config.parent/(stem+'.log')).open('a') as out,(a.config.parent/(stem+'.err')).open('a') as err:
        monitor=subprocess.Popen([sys.executable,str(Path(__file__).with_name('monitor_exp213_job.py')),
            '--config',str(a.config.resolve()),'--receipt',str(receipt.resolve())],stdout=out,stderr=err,
            stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    record={'lease':lease,'launch':launch,'monitor_pid':monitor.pid,'monitor_receipt':str(receipt)}
    a.config.with_name(a.config.stem+'_launch.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
