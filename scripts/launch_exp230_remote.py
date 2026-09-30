"""Use the existing guarded GPU lease and process supervisor for EXP230."""
import json
from pathlib import Path
import shlex
import sys

from monitor_exp213_job import ssh,QUEUE
from launch_exp221_job import queue_request

p=Path(sys.argv[1]);c=json.loads(p.read_text())
assert c['experiment']=='EXP230' and c['max_seconds']==1800
state=ssh('nsu-quadro',shlex.join(['python3',QUEUE,'status']))
assert not any(r['state'].startswith('WAITING') and r['project']!='biohub-cell-tracking-during-development'
               for r in state['requests']),'Other project waiting; defer'
assert not any(r['id']==c['lease_id'] for r in state['requests']),'Existing lease reconcile'
args=['python3',QUEUE,'request','--id',c['lease_id'],'--owner','biohub-agent',
      '--token',c['token'],'--project','biohub-cell-tracking-during-development',
      '--run-path',c['run'],'--pool','a100','--count','1','--cpu','8','--ram-gib','32',
      '--disk-gib','4','--minutes','40']
lease=queue_request(args,c['lease_id'],c['token'])
p.with_name(p.stem+'_reservation.json').write_text(json.dumps({'lease':lease,'config':c},indent=2))
assert lease['state']=='RESERVED'
c['gpu']=lease['gpus'][0];c['alias']=lease['alias'];p.write_text(json.dumps(c,indent=2))
source='''import pathlib,json,subprocess
c=__CONFIG__;r=pathlib.Path(c['run']);assert not r.exists();r.mkdir()
config=r/'config.json';config.write_text(json.dumps(c,indent=2))
assert c['gpu'] not in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
records={}
for name,args in [('wrapper',['/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python',c['code']+'/exp230_job.py',str(config)]),('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(config)])]:
 with (r/(name+'.log')).open('w') as f:q=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=q.pid
print(json.dumps(records))
'''.replace('__CONFIG__',repr(c))
launch=ssh(c['alias'],'python3 -',source)
p.with_name(p.stem+'_partial_launch.json').write_text(json.dumps({'lease':lease,'launch':launch,'config':c},indent=2))
source='''import pathlib,json,subprocess
c=__CONFIG__;r=pathlib.Path(c['run'])
with (r/'controller.log').open('w') as f:p=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(r/'config.json')],stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':p.pid}))
'''.replace('__CONFIG__',repr(c))
control=ssh('nsu-quadro','python3 -',source)
receipt={'lease':lease,'launch':launch,'control':control,'config':c}
p.with_name(p.stem+'_launch.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'lease_id':lease['id'],'state':lease['state'],'gpu':c['gpu'],
                  'wrapper_pid':launch['wrapper'],'observer_pid':launch['observe'],
                  'controller_pid':control['controller_pid']}))
