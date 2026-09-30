"""Finite two-job NFS observation/control bridge; no launches, credentials or kills."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from monitor_exp213_job import probe, releasable, QUEUE
import monitor_exp213_job


def atomic(path, value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    temp.replace(path)


def queue(command, config=None):
    args=['python3',QUEUE,command]
    if config:
        args+=['--id',config['lease_id'],'--token',config['token']]
    if command=='release': args+=['--verified-stopped']
    r=subprocess.run(args,capture_output=True,text=True,timeout=30,check=True)
    return json.loads(r.stdout)


def local_probe(alias, command, source=None):
    assert alias=='nsu-a100' and command=='python3 -'
    return json.loads(subprocess.run(['python3','-'],input=source,capture_output=True,text=True,
                                    check=True,timeout=30).stdout)


def main():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['observe','control']); a=p.parse_args()
    home=Path(__file__).resolve().parent
    state=home/'state'; state.mkdir(exist_ok=True)
    assert socket.gethostname()==('ngpu01' if a.mode=='observe' else 'prepost')
    configs=[json.loads((home/f'{arm}.json').read_text()) for arm in ['control','domain']]
    assert {c['lease_id'] for c in configs}=={'exp221-control-44b6-s2026-20260921','exp221-domain-44b6-s2026-20260921'}
    with (state/(a.mode+'_claim.json')).open('x') as f:
        json.dump({'pid':os.getpid(),'host':socket.gethostname(),'started':time.time(),
                   'start_identity':Path(f'/proc/{os.getpid()}/stat').read_text().split()[21]},f)
    if a.mode=='observe': monitor_exp213_job.ssh=local_probe
    else:
        live=queue('status')
        for c in configs:
            found=[r for r in live['requests'] if r['id']==c['lease_id']]
            assert len(found)==1 and found[0]['token']==c['token'] and found[0]['state']=='RUNNING'
        atomic(state/'control_ready.json',{'checked_at':time.time(),'queue_read_pass':True,
               'release_rule':'fresh snapshot AND exit present AND no PID/group/GPU processes',
               'activation_required':True})
    deadline=time.monotonic()+4*3600
    released=set()
    while time.monotonic()<deadline:
        try:
            if a.mode=='observe':
                snapshots={c['lease_id']:probe(c) for c in configs}
                atomic(state/'observations.json',{'checked_at':time.time(),'host':socket.gethostname(),'jobs':snapshots})
                if (state/'complete.json').exists(): return
            elif (state/'activate.json').exists():
                snapshot=json.loads((state/'observations.json').read_text())
                assert snapshot['host']=='ngpu01' and 0<=time.time()-snapshot['checked_at']<120, 'Stale/invalid observation; keep leases'
                statuses={}
                for c in configs:
                    key=c['lease_id']
                    if key in released: continue
                    job=snapshot['jobs'][key]
                    assert job['launch']['config']['lease_id']==key
                    action='release' if releasable(job) else 'heartbeat'
                    result=queue(action,c)
                    if action=='release': released.add(key)
                    statuses[key]={'action':action,'queue':result}
                atomic(state/'control_status.json',{'checked_at':time.time(),'jobs':statuses,'released':sorted(released)})
                if len(released)==2:
                    atomic(state/'complete.json',{'status':'BOTH_RELEASED_AFTER_VERIFIED_EXIT','checked_at':time.time()})
                    return
        except Exception as exc:
            # Unknown/stale/network state never frees an allocation.
            with (state/(a.mode+'_errors.jsonl')).open('a') as f:
                f.write(json.dumps({'at':time.time(),'error':repr(exc)})+'\n')
        time.sleep(45)
    atomic(state/(a.mode+'_deadline.json'),{'status':'BOUNDED_MONITOR_DEADLINE_NO_FORCED_RELEASE','at':time.time()})


if __name__=='__main__': main()
