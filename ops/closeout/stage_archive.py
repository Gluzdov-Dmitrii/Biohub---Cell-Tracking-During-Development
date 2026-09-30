import hashlib
import json
import shutil
from pathlib import Path

source = Path(r'C:/Users/Dmitry/Desktop/Kaggle/Biohub - Cell Tracking During Development')
archive = Path(r'C:/Users/Dmitry/Desktop/Kaggle/.archive/Biohub - Cell Tracking During Development')
assert source.resolve() == source and archive.resolve() == archive
assert (archive / '.git/config').is_file()
inventory = json.loads((source / 'work/closeout-20260930/local_inventory.json').read_text())
core = {'docs','scripts','tests','reports','research','notebooks','kaggle_notebooks','kaggle_datasets','.cursor','external'}
extensions = {'.py','.ps1','.sh','.md','.mdc','.ipynb','.json','.toml','.yaml','.yml','.txt','.diff','.patch','.docx','.svg','.png'}
badparts = {'site-packages','node_modules','__pycache__','.git','Lib','Scripts','Include','.venv','envs','wheels'}
records = []
for row in inventory['files']:
 rel = Path(row['path']); parts = rel.parts; p = source / rel
 if parts[0].startswith('.') and parts[0] != '.cursor':
  if len(parts) > 1: continue
 if any('pytest' in x.lower() or 'tmp' in x.lower() or x.lower() in {'temp','temporary'} for x in parts[:-1]): continue
 if any(x in badparts or 'venv' in x.lower() or x.startswith('.pytest') for x in parts): continue
 if p.name in ('kaggle.json','.env','access_token','goals-log.txt'): continue
 top = parts[0]
 eligible = (len(parts) == 1 and p.suffix in {'.md','.gitignore','.gitattributes'}) or p.name in {'.gitignore','.gitattributes'}
 if top in core and p.suffix in extensions and row['bytes'] <= 3_000_000: eligible = True
 if top in {'work','publication','outputs'} and p.suffix in extensions and row['bytes'] <= 2_000_000:
  if not any(x in {'external_inputs','support_pack','tracking_repo','public_notebooks','snapshots','teacher','training','train','test'} for x in parts): eligible = True
 if not eligible: continue
 if p.is_symlink(): continue
 target = archive / rel
 long_target = Path('\\\\?\\' + str(target))
 long_target.parent.mkdir(parents=True,exist_ok=True)
 try:
  long_target.write_bytes(p.read_bytes())
 except OSError as exc:
  raise RuntimeError(f'COPY_FAILED source={p} target={target} source_exists={p.exists()} parent_exists={target.parent.exists()}') from exc
 digest = hashlib.sha256(p.read_bytes()).hexdigest()
 assert hashlib.sha256(long_target.read_bytes()).hexdigest() == digest
 records.append({'path':rel.as_posix(),'bytes':row['bytes'],'sha256':digest})
for rel in ('reports/PUBLIC_FINAL_WRITEUPS_20260930.md','work/closeout-20260930/live_submissions.json'):
 p = source/rel; target = archive/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
shutil.copy2(source/'goals-log.txt',archive/'goals-log.txt')
model_records = []
for p in sorted((source/'kaggle_datasets/exp219_frontier90_models/models').rglob('*')):
 if p.is_file() and p.suffix in {'.pth','.pt'}:
  digest = hashlib.sha256(p.read_bytes()).hexdigest()
  target = archive/'local-artifacts/models'/f'{digest}{p.suffix}'
  target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists(): shutil.copy2(p,target)
  assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
  model_records.append({'source':str(p),'archive':str(target.relative_to(archive)),'bytes':p.stat().st_size,'sha256':digest})
out = archive/'reports/CLOSEOUT_COPY_MANIFEST_20260930.json'
out.write_text(json.dumps({'source':str(source),'archive':str(archive),'files':records,'local_models':model_records},indent=2),encoding='utf-8')
print(json.dumps({'copied_files':len(records),'copied_MiB':round(sum(x['bytes'] for x in records)/2**20,2),'local_models':len(model_records),'archive':str(archive)}))
