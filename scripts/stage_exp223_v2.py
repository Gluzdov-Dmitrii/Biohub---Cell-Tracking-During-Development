import pathlib,json,base64,sys,hashlib
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
root='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development';code=root+'/code/exp223_horaz0_inference_v2_20260921'
wrapper=pathlib.Path('scripts/exp214_inference_job.py').read_text().replace("assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')","assert config['script'] == 'run_exp223_inference.py'")
files={n:pathlib.Path('scripts',n).read_bytes() for n in ['run_exp223_inference.py','exp223_supervisor.py','monitor_exp213_job.py']};files['exp223_inference_job.py']=wrapper.encode()
source='''import pathlib,json,base64,hashlib,shutil
root=pathlib.Path(ROOT);old=root/'code/exp223_horaz0_v1_20260921';code=pathlib.Path(CODE)
if not code.exists():shutil.copytree(old,code)
manifest=json.loads((code/'package_manifest.json').read_text())
for name,val in FILES.items():
 data=base64.b64decode(val);p=code/name
 if name in ['run_exp223_inference.py','exp223_supervisor.py','monitor_exp213_job.py'] and p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
 manifest[name]=hashlib.sha256(data).hexdigest()
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
rows=json.loads((code/'heldout175_manifest.json').read_text())['rows']
# Larger representative source: highest image-volume6bba,source fold0; target labels forbidden.
row=max([r for r in rows if r['dataset'].startswith('6bba_')],key=lambda r:r['shape'][1]*r['shape'][2]*r['shape'][3])
plan={'code':str(code),'output':str(root/'runs/exp223_larger_source_benchmark_20260921/output'),'manifest_sha256':hashlib.sha256((code/'heldout175_manifest.json').read_bytes()).hexdigest(),'mode':'source_benchmark','arms':['selected50_20'],'movies':[row['dataset']]}
(code/'benchmark_plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps({'code':str(code),'plan':plan,'row':row,'code_manifest_sha256':hashlib.sha256((code/'code_manifest.json').read_bytes()).hexdigest()}))
'''.replace('ROOT',repr(root)).replace('CODE',repr(code)).replace('FILES',repr({k:base64.b64encode(v).decode() for k,v in files.items()}))
r=ssh('nsu-quadro','python3 -',source);pathlib.Path('reports/exp223_v2_staging_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
