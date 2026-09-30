import sys,json
from pathlib import Path
sys.path.insert(0,'scripts')
from monitor_exp213_job import ssh
source=r'''import pathlib,json,hashlib,tarfile,sys,traceback
root=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
archive=root/'code/exp223_horaz0_package_20260921.tar'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='a9bdfef55bb09180a18e94d14d9420e840faa335efa65d8fd39e937c001282a8'
dst=root/'code/exp223_horaz0_v1_20260921';dst.mkdir(exist_ok=True)
with tarfile.open(archive) as t:
 for m in t.getmembers():
  assert m.isfile() and (dst/m.name).resolve().is_relative_to(dst.resolve())
  data=t.extractfile(m).read();p=dst/m.name;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==data
  else:p.write_bytes(data)
manifest=json.loads((dst/'package_manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((dst/name).read_bytes()).hexdigest()==digest
import torch
results=[]
for arm in ['selected','fixed_last']:
 for p in sorted((dst/arm).glob('*.pt')):
  c=torch.load(p,map_location='cpu',weights_only=True)
  results.append({'arm':arm,'file':p.name,'keys':list(c),'metadata':c.get('metadata'),'epoch':c.get('epoch'),'model_config':c.get('model_config'),'tensor_count':len(c.get('model',{})),'finite':all(torch.isfinite(v).all().item() for v in c.get('model',{}).values() if torch.is_tensor(v))})
sys.path.insert(0,str(dst/'selected/src/src'))
try:
 import engine,inference
 dependency={'status':'PASS_IMPORT','torch':torch.__version__}
except Exception as e: dependency={'status':'FAIL_IMPORT','type':type(e).__name__,'error':str(e),'trace':traceback.format_exc()}
result={'code':str(dst),'manifest_sha256':hashlib.sha256((dst/'package_manifest.json').read_bytes()).hexdigest(),'weights':results,'dependency':dependency}
(dst/'safe_load_probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
'''
result=ssh('nsu-quadro','/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/prepost/py3.11-stdlib-v1/bin/python -',source)
Path('reports/exp223_safe_load_probe_20260921.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
