import pathlib,json,base64,sys
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
root='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development';code=root+'/code/exp223_horaz0_inference_v3_20260921'
runner=pathlib.Path('scripts/run_exp223_inference.py').read_bytes()
source='''import pathlib,json,hashlib,shutil,base64
root=pathlib.Path(ROOT);old=root/'code/exp223_horaz0_inference_v2_20260921';code=pathlib.Path(CODE)
assert not code.exists(),'Immutable version already staged'
shutil.copytree(old,code)
(code/'run_exp223_inference.py').write_bytes(base64.b64decode(RUNNER))
manifest=json.loads((code/'code_manifest.json').read_text());manifest['run_exp223_inference.py']=hashlib.sha256((code/'run_exp223_inference.py').read_bytes()).hexdigest();(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
codehash=hashlib.sha256((code/'code_manifest.json').read_bytes()).hexdigest();cohort=code/'heldout175_manifest.json';cohorthash=hashlib.sha256(cohort.read_bytes()).hexdigest();rows=json.loads(cohort.read_text())['rows']
# Deterministic strided cohorts balance embryo composition; both arms per chunk.
plans=[]
for i in range(8):
 names=[r['dataset'] for r in rows[i::8]];run=root/f'runs/exp223_horaz0_pair_chunk{i:02d}_20260921'
 plan={'code':str(code),'code_manifest_sha256':codehash,'output':str(run/'output'),'manifest_sha256':cohorthash,'mode':'heldout','arms':['selected50_20','fixedlast50_same_decoder'],'movies':names}
 p=code/f'plan_chunk{i:02d}.json';p.write_text(json.dumps(plan,indent=2));plans.append({'chunk':i,'n_movies':len(names),'plan':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'run':str(run)})
rollout={'experiment':'EXP223','arms':['selected50_20','fixedlast50_same_decoder'],'movies':175,'predictions':350,'chunks':plans,'max_seconds_each':10800,'total_hard_cap_gpu_hours':24,'no_auto_retry':True,'score_gate':'ALL350_RECEIPTS_BEFORE_ANY_LABEL_ACCESS','code_manifest_sha256':codehash}
(code/'rollout.json').write_text(json.dumps(rollout,indent=2));print(json.dumps(rollout))
'''.replace('ROOT',repr(root)).replace('CODE',repr(code)).replace('RUNNER',repr(base64.b64encode(runner).decode()))
r=ssh('nsu-quadro','python3 -',source);pathlib.Path('reports/exp223_full_rollout_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
for x in r['chunks']:
 c={'experiment':'EXP223','lease_id':f"exp223-horaz0-pair-chunk{x['chunk']:02d}-20260921",'token':f"exp223_horaz0_pair_chunk{x['chunk']:02d}_20260921",'code':code,'run':x['run'],'max_seconds':10800,'cpu_affinity':'8-15','script':'run_exp223_inference.py','arguments':[x['plan'],'--plan-sha256',x['sha256']]}
 pathlib.Path(f"reports/exp223_chunk{x['chunk']:02d}_config_20260921.json").write_text(json.dumps(c,indent=2))
