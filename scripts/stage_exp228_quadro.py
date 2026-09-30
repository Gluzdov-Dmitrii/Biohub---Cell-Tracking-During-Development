"""Repartition the unchanged ensemble for an idle Quadro; original failed launch retained."""
import base64
import json
from pathlib import Path
from monitor_exp213_job import ssh

ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
LOCAL=Path(__file__).resolve().parents[1]
files={n:(LOCAL/'scripts'/n).read_bytes() for n in ['run_exp228_ensemble.py']}
supervisor=(LOCAL/'scripts/exp223_supervisor.py').read_text()
old="assert alias=='nsu-a100' and command=='python3 -'"
assert supervisor.count(old)==1
files['exp223_supervisor.py']=supervisor.replace(old,"assert alias==c['alias'] and command=='python3 -'").encode()
source='''import pathlib,json,shutil,hashlib,base64
root=pathlib.Path(ROOT);old=root/'code/exp228_horaz_ensemble_v1_20260923';code=root/'code/exp228_horaz_ensemble_quadro_v2_20260923'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old/'code_manifest.json')=='d60550bffa95dfede0121707cfb2d5e64f35ea14b2783eba8d7b16b24d5d1e40'
assert not code.exists();code.mkdir();manifest={}
for name,digest in json.loads((old/'code_manifest.json').read_text()).items():
 assert sha(old/name)==digest,name
 if name.startswith('plan_chunk'):continue
 dest=code/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,dest);manifest[name]=digest
for name,value in FILES.items():(code/name).write_bytes(base64.b64decode(value));manifest[name]=sha(code/name)
cohort=code/'heldout175_manifest.json';rows=json.loads(cohort.read_text())['rows'];selected=sorted([r for r in rows if r['fold']==1],key=lambda r:hashlib.sha256(('EXP228-chunks-v1:'+r['dataset']).encode()).hexdigest())
plans=[]
for i in range(8):
 run=root/f'runs/exp228_horaz_ensemble_quadro_chunk{i:02d}_20260923'
 p={'experiment':'EXP228','mode':'heldout_same_fold_ensemble','chunk':i,'chunk_count':8,'rows':selected[i::8],'mixture':[.5,.5],'weights':{n:manifest[n] for n in ('selected/fold1_selected.pt','fixed_last/fold1_last.pt')},'cohort_sha256':sha(cohort),'output':str(run/'output')}
 path=code/f'plan_chunk{i:02d}.json';path.write_text(json.dumps(p,indent=2));manifest[path.name]=sha(path);plans.append({'chunk':i,'movies':len(p['rows']),'run':str(run),'plan':str(path),'sha256':sha(path)})
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'code':str(code),'code_manifest_sha256':sha(code/'code_manifest.json'),'plans':plans}))
'''.replace('ROOT',repr(ROOT)).replace('FILES',repr({n:base64.b64encode(b).decode() for n,b in files.items()}))
r=ssh('nsu-quadro','python3 -',source)
(LOCAL/'work/horaz_parallel_20260923/ensemble_quadro_staging.json').write_text(json.dumps(r,indent=2))
for p in r['plans']:
 c={'experiment':'EXP228','lease_id':f"exp228-horaz-quadro-chunk{p['chunk']:02d}-20260923",'token':f"exp228_horaz_quadro_chunk{p['chunk']:02d}_20260923",'pool':'quadro','code':r['code'],'run':p['run'],'max_seconds':10800,'cpu_affinity':'8-15','script':'run_exp228_ensemble.py','arguments':[p['plan'],'--plan-sha256',p['sha256']]}
 (LOCAL/f"reports/exp228_quadro_chunk{p['chunk']:02d}_config_20260923.json").write_text(json.dumps(c,indent=2))
print(json.dumps({'status':'STAGED_SAME_SCIENCE_QUADRO','code':r['code'],'code_manifest_sha256':r['code_manifest_sha256'],'first_plan':r['plans'][0],'total_movies':sum(p['movies'] for p in r['plans'])}))
