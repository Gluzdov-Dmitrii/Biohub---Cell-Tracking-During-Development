"""Stage an immutable first full training block after verified EXP226 completion."""
import base64
import hashlib
import json
from pathlib import Path
import sys

from monitor_exp213_job import ssh
from run_exp227_source_block import validate

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/horaz_development_20260922/exp227';WORK.mkdir(exist_ok=True)
REMOTE='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE=REMOTE+'/code/exp227_horaz_source_block01_20260922'
RUN=REMOTE+'/runs/exp227_horaz_source_block01_20260922'
pilot=json.loads((WORK.parent/'v2/status.json').read_text())
assert pilot['result']['status']=='PASS_SOURCE_ONLY_TRAINING_PILOT'
assert pilot['exit']['returncode']==0 and pilot['supervision']['status']=='RELEASED_AFTER_VERIFIED_EXIT'
source_manifest=WORK.parent/'source44_manifest.json'
m=json.loads(source_manifest.read_text())
plan={'experiment':'EXP227','purpose':'source_only_full_training_first_block',
      'source_embryo':'44b6','target_embryo':'6bba','fold':1,'block_end_epoch':5,'planned_epochs':50,
      'resume':False,'checkpoint_selection':'deferred_source_graph_10_20_30_40_50',
      'train':m['train'],'inner_validation':m['inner_validation'],
      'source_manifest_sha256':hashlib.sha256(source_manifest.read_bytes()).hexdigest(),
      'data_root':REMOTE+'/data/exp213_source_view_20260912','output':RUN+'/output'}
validate(plan)
files={}
package=ROOT/'outputs/research/exp223_horaz0_package_20260921'
for name,digest in json.loads((package/'package_manifest.json').read_text()).items():
    if name.startswith('selected/') and (name.endswith('.py') or name=='selected/resolved_config.json'):
        b=(package/name).read_bytes();assert hashlib.sha256(b).hexdigest()==digest
        files['horaz/'+name.removeprefix('selected/')]=b
for name in ['run_exp227_source_block.py','run_exp226_source_pilot.py','exp226_protocol.py','exp223_supervisor.py','monitor_exp213_job.py']:
    files[name]=(ROOT/'scripts'/name).read_bytes()
wrapper=(ROOT/'scripts/exp214_inference_job.py').read_text()
old="assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
assert wrapper.count(old)==1
files['exp227_job.py']=wrapper.replace(old,"assert config['script'] == 'run_exp227_source_block.py'").encode()
files['source44_manifest.json']=source_manifest.read_bytes()
files['plan.json']=json.dumps(plan,indent=2).encode()
hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
files['code_manifest.json']=json.dumps(hashes,indent=2).encode()
source='''import pathlib,json,base64,hashlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir()
for name,value in FILES.items():
 p=code/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(value))
for n,h in json.loads((code/'code_manifest.json').read_text()).items():assert hashlib.sha256((code/n).read_bytes()).hexdigest()==h
print(json.dumps({'code':str(code),'code_manifest_sha256':hashlib.sha256((code/'code_manifest.json').read_bytes()).hexdigest(),'status':'STAGED_HASH_VERIFIED'}))
'''.replace('CODE',repr(CODE)).replace('FILES',repr({n:base64.b64encode(b).decode() for n,b in files.items()}))
receipt=ssh('nsu-quadro','python3 -',source)
config={'experiment':'EXP227','lease_id':'exp227-horaz-source-block01-20260922','token':'exp227_horaz_source_block01_20260922',
        'code':CODE,'run':RUN,'max_seconds':10800,'cpu_affinity':'0-7','script':'run_exp227_source_block.py',
        'arguments':[CODE+'/plan.json','--plan-sha256',hashes['plan.json']]}
for name,data in [('plan.json',plan),('code_manifest.json',hashes),('staging.json',receipt)]:
    (WORK/name).write_text(json.dumps(data,indent=2))
(ROOT/'reports/exp227_source_block01_config_20260922.json').write_text(json.dumps(config,indent=2))
print(json.dumps({'staging':receipt,'plan_sha256':hashes['plan.json'],'training_movies':63,'inner_validation_movies':8,'block_epochs':5,'hard_timeout_seconds':10800}))
