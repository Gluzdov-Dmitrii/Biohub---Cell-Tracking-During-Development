"""Freeze all ensemble chunks and reference inputs for independent CPU graph work."""
import base64
import hashlib
import json
from pathlib import Path
from monitor_exp213_job import ssh

LOCAL=Path(__file__).resolve().parents[1]
WORK=LOCAL/'work/horaz_parallel_20260923';WORK.mkdir(exist_ok=True)
ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE=ROOT+'/code/exp228_horaz_ensemble_v1_20260923'
files={name:(LOCAL/'scripts'/name).read_bytes() for name in ('run_exp228_ensemble.py','run_exp223_inference.py','exp223_supervisor.py','monitor_exp213_job.py')}
wrapper=(LOCAL/'scripts/exp214_inference_job.py').read_text()
old="assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
assert wrapper.count(old)==1
files['exp228_job.py']=wrapper.replace(old,"assert config['script'] == 'run_exp228_ensemble.py'").encode()
source='''import pathlib,json,hashlib,shutil,base64
root=pathlib.Path(ROOT);old=root/'code/exp223_horaz0_inference_v3_20260921';code=pathlib.Path(CODE)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old/'code_manifest.json')=='037dc7fb367948cd1253f7ac44dab95f2c23c686e259462b8b446f2ea37da8cd'
assert not code.exists();code.mkdir()
needed={'selected/resolved_config.json','selected/fold1_selected.pt','fixed_last/fold1_last.pt'}
manifest={}
for name,digest in json.loads((old/'code_manifest.json').read_text()).items():
 if name.startswith('selected/src/src/') or name in needed:
  p=old/name;assert sha(p)==digest,name;target=code/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);manifest[name]=digest
for name,value in FILES.items():
 b=base64.b64decode(value);(code/name).write_bytes(b);manifest[name]=sha(code/name)
cohort=old/'heldout175_manifest.json';assert sha(cohort)=='001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4'
shutil.copyfile(cohort,code/cohort.name);manifest[cohort.name]=sha(cohort)
rows=json.loads(cohort.read_text())['rows'];selected=sorted([r for r in rows if r['fold']==1],key=lambda r:hashlib.sha256(('EXP228-chunks-v1:'+r['dataset']).encode()).hexdigest());assert len(selected)==116
plans=[]
for i in range(4):
 run=root/f'runs/exp228_horaz_ensemble_chunk{i:02d}_20260923'
 plan={'experiment':'EXP228','mode':'heldout_same_fold_ensemble','chunk':i,'rows':selected[i::4],'mixture':[.5,.5],'weights':{n:manifest[n] for n in sorted(needed) if n.endswith('.pt')},'cohort_sha256':sha(cohort),'output':str(run/'output')}
 path=code/f'plan_chunk{i:02d}.json';path.write_text(json.dumps(plan,indent=2));manifest[path.name]=sha(path);plans.append({'chunk':i,'run':str(run),'plan':str(path),'sha256':sha(path)})
# Freeze the already-scored selected reference files without reading labels or metrics.
assert sha(old/'rollout.json')=='230a9dbbf0921a7a8c02c3df96252d9fd1d946d20eb6d72f3924e2692189675c'
rollout=json.loads((old/'rollout.json').read_text());refs={}
weight_hash={0:'8c202a657567309a15e0b254236b2d730b4a4942b54408608d3b1895fc45ff08',1:'009c105cc3d745c3fa7e90fdf4c81d041627235274a37003631085c3c929ec53'}
for chunk in rollout['chunks']:
 run=pathlib.Path(chunk['run']);exit=json.loads((run/'exit.json').read_text());assert exit['returncode']==0 and not exit['hard_timeout'];sup=json.loads((run/'supervision/complete.json').read_text());assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT'
 assert sha(pathlib.Path(chunk['plan']))==chunk['sha256']
 original_plan=json.loads(pathlib.Path(chunk['plan']).read_text())
 for ds in original_plan['movies']:
  receipt=run/'output'/('selected50_20__'+ds+'.json');r=json.loads(receipt.read_text());contract=r['contract'];fold=0 if ds.startswith('44b6_') else 1
  assert contract['dataset']==ds and contract['arm']=='selected50_20' and contract['mode']=='heldout' and contract['fold']==fold and contract['weight_sha256']==weight_hash[fold]
  assert contract['code_sha256']==sha(old/'code_manifest.json') and contract['decoder_sha256']==sha(old/'selected/resolved_config.json') and contract['manifest_sha256']==sha(cohort)
  row=next(x for x in rows if x['dataset']==ds);csv=receipt.with_suffix('.csv');assert csv.is_file()
  assert ds not in refs;refs[ds]={'dataset':ds,'shape':row['shape'],'reference_csv':str(csv),'reference_sha256':r['csv_sha256'],'receipt_path':str(receipt),'receipt_sha256':sha(receipt),'zarr':row['zarr']}
assert len(refs)==175
reference={'rows':[refs[n] for n in sorted(refs)],'cohort_sha256':sha(cohort),'reference':'EXP223 selected heldout175','all_prior_runs_released':True}
(code/'reference_manifest.json').write_text(json.dumps(reference,indent=2));manifest['reference_manifest.json']=sha(code/'reference_manifest.json')
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'code':str(code),'code_manifest_sha256':sha(code/'code_manifest.json'),'plans':plans,'reference':reference}))
'''.replace('ROOT',repr(ROOT)).replace('CODE',repr(CODE)).replace('FILES',repr({k:base64.b64encode(v).decode() for k,v in files.items()}))
result=ssh('nsu-quadro','python3 -',source)
(WORK/'ensemble_staging.json').write_text(json.dumps({k:v for k,v in result.items() if k!='reference'},indent=2))
(WORK/'reference_manifest.json').write_text(json.dumps(result['reference'],indent=2))
for plan in result['plans']:
    config={'experiment':'EXP228','lease_id':f"exp228-horaz-ensemble-chunk{plan['chunk']:02d}-20260923",'token':f"exp228_horaz_ensemble_chunk{plan['chunk']:02d}_20260923",'code':CODE,'run':plan['run'],'max_seconds':10800,'cpu_affinity':'8-15','script':'run_exp228_ensemble.py','arguments':[plan['plan'],'--plan-sha256',plan['sha256']]}
    (LOCAL/f"reports/exp228_chunk{plan['chunk']:02d}_config_20260923.json").write_text(json.dumps(config,indent=2))
print(json.dumps({'status':'STAGED_IMMUTABLE_4x29','code':CODE,'code_manifest_sha256':result['code_manifest_sha256'],'reference_movies':len(result['reference']['rows']),'plans':result['plans']}))
