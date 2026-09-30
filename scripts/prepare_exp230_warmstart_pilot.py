"""Freeze and stage a tiny Horaz selected20 warm-start pilot on source44."""
import base64
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from run_exp230_warmstart_pilot import PARENT_SHA, validate

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/horaz_development_20260923/exp230';WORK.mkdir(parents=True,exist_ok=True)
REMOTE='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE=REMOTE+'/code/exp230_horaz_warmstart_pilot_v1_20260923'
RUN=REMOTE+'/runs/exp230_horaz_warmstart_pilot_v1_20260923'
PARENT_REMOTE=REMOTE+'/code/exp228_horaz_ensemble_quadro_v2_20260923/selected/fold1_selected.pt'

pilot=json.loads((ROOT/'work/horaz_development_20260922/pilot_plan.json').read_text())
source_manifest=ROOT/'work/horaz_development_20260922/source44_manifest.json'
manifest=json.loads(source_manifest.read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
plan={'experiment':'EXP230','purpose':'warmstart_source_only_feasibility',
      'source_embryo':'44b6','target_embryo':'6bba','fold':1,'parent_sha256':PARENT_SHA,
      'parent_epoch':20,'learning_rate':0.00002,'epochs':2,'iterations_per_epoch':8,
      'seed':3407,'resume':False,'checkpoint_selection':'none_feasibility_only',
      'num_workers':0,'torch_compile':False,
      'train':pilot['train'],'inner_validation':pilot['inner_validation'],
      'source_manifest_sha256':sha(source_manifest.read_bytes()),
      'data_root':REMOTE+'/data/exp213_source_view_20260912','output':RUN+'/output'}
validate(plan,manifest)
files={}
package=ROOT/'outputs/research/exp223_horaz0_package_20260921'
for name,digest in json.loads((package/'package_manifest.json').read_text()).items():
    if name.startswith('selected/') and (name.endswith('.py') or name=='selected/resolved_config.json'):
        blob=(package/name).read_bytes();assert sha(blob)==digest
        files['horaz/'+name.removeprefix('selected/')]=blob
for name in ['run_exp230_warmstart_pilot.py','run_exp226_source_pilot.py','exp226_protocol.py',
             'exp223_supervisor.py','monitor_exp213_job.py']:
    files[name]=(ROOT/'scripts'/name).read_bytes()
wrapper=(ROOT/'scripts/exp214_inference_job.py').read_text()
old="assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
assert wrapper.count(old)==1
files['exp230_job.py']=wrapper.replace(old,"assert config['script'] == 'run_exp230_warmstart_pilot.py'").encode()
files['source44_manifest.json']=source_manifest.read_bytes()
files['plan.json']=json.dumps(plan,indent=2).encode()
hashes={name:sha(blob) for name,blob in files.items()}
hashes['horaz/fold1_selected.pt']=PARENT_SHA
files['code_manifest.json']=json.dumps(hashes,indent=2).encode()
source='''import base64,hashlib,json,pathlib,shutil
code=pathlib.Path(__CODE__);assert not code.exists();code.mkdir()
for name,value in __FILES__.items():
 p=code/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(value))
parent=pathlib.Path(__PARENT__)
assert hashlib.sha256(parent.read_bytes()).hexdigest()==__PARENT_SHA__
shutil.copyfile(parent,code/'horaz/fold1_selected.pt')
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 assert hashlib.sha256((code/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({'status':'STAGED_HASH_VERIFIED','code':str(code),
 'code_manifest_sha256':hashlib.sha256((code/'code_manifest.json').read_bytes()).hexdigest(),
 'parent_sha256':__PARENT_SHA__}))
'''.replace('__CODE__',repr(CODE)).replace('__FILES__',repr({n:base64.b64encode(b).decode() for n,b in files.items()})).replace('__PARENT__',repr(PARENT_REMOTE)).replace('__PARENT_SHA__',repr(PARENT_SHA))
receipt=ssh('nsu-quadro','python3 -',source)
config={'experiment':'EXP230','lease_id':'exp230-horaz-warmstart-pilot-20260923',
        'token':'exp230_horaz_warmstart_pilot_20260923','code':CODE,'run':RUN,
        'max_seconds':1800,'cpu_affinity':'0-7','script':'run_exp230_warmstart_pilot.py',
        'arguments':[CODE+'/plan.json','--plan-sha256',hashes['plan.json']]}
for name,data in [('plan.json',plan),('code_manifest.json',hashes),('staging.json',receipt)]:
    (WORK/name).write_text(json.dumps(data,indent=2))
(ROOT/'reports/exp230_warmstart_pilot_config_20260923.json').write_text(json.dumps(config,indent=2))
print(json.dumps({'staging':receipt,'plan_sha256':hashes['plan.json'],
                  'training_movies':4,'inner_movies':2,'epochs':2,'batches_per_epoch':8}))
