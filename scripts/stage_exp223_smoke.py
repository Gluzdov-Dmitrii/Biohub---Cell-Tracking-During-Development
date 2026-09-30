import pathlib,json,base64,sys,hashlib
sys.path.insert(0,'scripts')
from monitor_exp213_job import ssh
src=pathlib.Path('scripts/run_exp223_smoke.py').read_bytes()
wrapper=pathlib.Path('scripts/exp214_inference_job.py').read_text().replace("assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')","assert config['script'] == 'run_exp223_smoke.py'")
files={'run_exp223_smoke.py':src,'exp223_inference_job.py':wrapper.encode()}
source='''import pathlib,json,hashlib,base64
code=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp223_horaz0_v1_20260921')
manifest=json.loads((code/'package_manifest.json').read_text())
for name,value in FILES.items():
 data=base64.b64decode(value);p=code/name
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
 manifest[name]=hashlib.sha256(data).hexdigest()
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'manifest':manifest,'code':str(code)}))
'''.replace('FILES',repr({k:base64.b64encode(v).decode() for k,v in files.items()}))
r=ssh('nsu-quadro','python3 -',source)
pathlib.Path('reports/exp223_smoke_staging_20260921.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'code':r['code'],'file_count':len(r['manifest'])}))
