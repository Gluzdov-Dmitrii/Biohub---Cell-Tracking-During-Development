"""One read-only status snapshot; never launch, resume or submit anything."""
import json
from pathlib import Path
from monitor_exp213_job import ssh

root=Path(__file__).resolve().parents[1]
config=json.loads((root/'reports/exp227_source_block01_config_20260922.json').read_text())
source='''import pathlib,json,time,hashlib
r=pathlib.Path(RUN)
def read(name):
 p=r/name;return json.loads(p.read_text()) if p.exists() else None
launch=read('launch.json');alive=False
if launch:
 p=pathlib.Path('/proc')/str(launch['pid'])/'stat'
 if p.exists():
  raw=p.read_text();f=raw[raw.rfind(')')+2:].split();alive=f[0]!='Z' and f[19]==launch['start']
log=r/'inference.log';tail=log.read_text(errors='replace')[-3500:] if log.exists() else ''
s={'at':time.time(),'launch':launch,'identity_alive':alive,'exit':read('exit.json'),'result':read('output/result.json'),'history':read('output/fold1/history.json'),'release':read('supervision/complete.json'),'control':read('supervision/control.json'),'log_tail':tail}
checkpoint=r/'output/fold1/last.pt'
if s['exit'] and checkpoint.exists():s['checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
print(json.dumps(s))
'''.replace('RUN',repr(config['run']))
state=ssh(config['alias'],'python3 -',source)
receipt=root/'work/horaz_development_20260922/exp227/status.json'
receipt.write_text(json.dumps(state,indent=2))
result=state['result'] or {}
summary={'identity_alive':state['identity_alive'],'pid':(state['launch'] or {}).get('pid'),
         'epochs_completed':len(state['history'] or []),'exit':state['exit'],'result_status':result.get('status'),
         'error':result.get('error'),'released':state['release'],
         'queue_state':((state['control'] or {}).get('queue') or {}).get('state'),
         'control_age_seconds':state['at']-(state['control'] or {}).get('at',0),
         'last_log_lines':state['log_tail'].splitlines()[-4:]}
print(json.dumps(summary))
