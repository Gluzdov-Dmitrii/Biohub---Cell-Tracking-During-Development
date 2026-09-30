"""Finite remote NFS observer/controller for one leased EXP223 chunk."""
import json,sys,time,subprocess,socket
from pathlib import Path
import monitor_exp213_job as mon
mode=sys.argv[1];c=json.loads(Path(sys.argv[2]).read_text());run=Path(c['run']);state=run/'supervision';state.mkdir(exist_ok=True)
def atomic(name,value):
 p=state/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)
def local_probe(alias,command,source=None):
 assert alias=='nsu-a100' and command=='python3 -'
 return json.loads(subprocess.check_output(['python3','-'],input=source,text=True,timeout=30))
if mode=='observe':mon.ssh=local_probe
registered=False
for attempt in range(600):
 if (state/'complete.json').exists():break
 try:
  if mode=='observe':atomic('observation.json',{'at':time.time(),'state':mon.probe(c)})
  else:
   observation=json.loads((state/'observation.json').read_text());assert 0<=time.time()-observation['at']<90
   s=observation['state'];common=['--id',c['lease_id'],'--token',c['token']]
   if s['launch'] and not registered:
    subprocess.run(['python3',mon.QUEUE,'started',*common,'--pid',str(s['launch']['pid']),'--process-start',s['launch']['start']],check=True,capture_output=True);registered=True
   action='release' if mon.releasable(s) else 'heartbeat';args=['python3',mon.QUEUE,action,*common]
   if action=='release':args+=['--verified-stopped']
   q=json.loads(subprocess.check_output(args,text=True));atomic('control.json',{'at':time.time(),'action':action,'queue':q})
   if action=='release':atomic('complete.json',{'at':time.time(),'status':'RELEASED_AFTER_VERIFIED_EXIT','exit':s['exit']});break
 except Exception as e:
  with (state/(mode+'_errors.jsonl')).open('a') as f:f.write(json.dumps({'at':time.time(),'error':repr(e)})+'\n')
 time.sleep(20)
