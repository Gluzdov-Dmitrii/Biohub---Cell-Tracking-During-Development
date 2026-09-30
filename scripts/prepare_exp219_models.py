"""Package the verified90/60 frontier for one new production diagnostic."""
import json
from pathlib import Path
from monitor_exp213_job import ssh
L=Path(__file__).resolve().parents[1]
R='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
def main():
    source='''import hashlib,json,shutil,tarfile
from pathlib import Path
r=Path(ROOT);out=r/'models/exp219_frontier90_20260916';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={};folds={};lineage={}
for fold in ('44b6','6bba'):
 b=json.loads((r/('code/exp214_eval90_inputs_20260913/'+fold+'_bundle.json')).read_text());folds[fold]={};lineage[fold]=b
 for role in ('primary','secondary','center'):
  p=Path(b[role]['path']);assert sha(p)==b[role]['sha256']
  name=f'models/{fold}/{role}/'+p.name;dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);files[name]=sha(dest);folds[fold][role]=name
  if role!='center':
   for aux in ('config.json','status.json','history.json'):
    dest=out/f'models/{fold}/{role}/{aux}';shutil.copy2(p.parent/aux,dest);files[str(dest.relative_to(out))]=sha(dest)
code=r/'code/exp214_inference_v8_20260914';cm=json.loads((code/'code_manifest.json').read_text())
for name,digest in cm.items():
 assert sha(code/name)==digest
 dest=out/'code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(code/name,dest);files['code/'+name]=sha(dest)
m={'status':'PASS_FROZEN90_60_FRONTIER_MODELS','training_plan_sha256':lineage['44b6']['training_plan_sha256'],'files':files,'folds':folds,'lineage':lineage,'oof_reference':0.7427291486246141,'scope':'175 reciprocal two-embryo development CV reference, not unseen-embryo routing score. Primary90 secondary60, source-only checkpoints.'}
(out/'artifact_manifest.json').write_text(json.dumps(m,indent=2)+'\\n')
archive=r/'models/exp219_frontier90_20260916.tar'
with tarfile.open(archive,'w') as f:
 for p in sorted(out.rglob('*')):
  if p.is_file():f.add(p,arcname=str(p.relative_to(out)),recursive=False)
print(json.dumps({'archive':str(archive),'archive_sha256':sha(archive),'manifest_sha256':sha(out/'artifact_manifest.json'),'bytes':archive.stat().st_size}))
'''.replace('ROOT',repr(R))
    result=ssh('nsu-quadro','python3 -',source)
    (L/'reports/exp219_remote_model_pack_20260916.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
