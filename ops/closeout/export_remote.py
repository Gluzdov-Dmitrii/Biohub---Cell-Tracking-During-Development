import hashlib
import io
import json
import os
import socket
import sys
import tarfile
from pathlib import Path

root = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
assert root.resolve() == root and root.is_dir()
models = {
 'runs/horaz_full_all199_e10_09810798af58/output/fold0/epoch_010.pt',
 'runs/horaz_full_all199_e20_77f8cc7d0382/output/fold0/epoch_020.pt',
 'runs/exp227_horaz_source_block02_20260927/output/fold1/epoch_010.pt',
 'runs/exp236_horaz_source6bba_block04_v2_20260927/output/fold0/epoch_010.pt',
}
names = {'result.json','metrics.json','summary.json','config.json','launch.json','exit.json','run.json','complete.json','selection.json','model_config.json','manifest.json'}
files = []
for section in ('code','runs','plans','preflight'):
 for dp, ds, ns in os.walk(root / section):
  ds[:] = [d for d in ds if 'venv' not in d.lower() and d not in ('envs','site-packages','__pycache__','.git','node_modules','data','cache','tmp')]
  for n in ns:
   p = Path(dp) / n
   rel = p.relative_to(root).as_posix()
   if p.is_symlink() or not p.resolve().is_relative_to(root):
    continue
   if rel in models or (p.stat().st_size <= 2_000_000 and (p.suffix in ('.py','.md','.toml','.yaml','.yml','.sh','.ps1') or n in names or 'manifest' in n.lower() or n.startswith('requirements'))):
    files.append(p)
files.append(root / 'PROJECT_MANIFEST.json')
assert models.issubset({p.relative_to(root).as_posix() for p in files})
records = []
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|gz') as tf:
 for p in sorted(set(files)):
  rel = p.relative_to(root).as_posix()
  digest = hashlib.sha256(p.read_bytes()).hexdigest()
  records.append({'path':rel,'bytes':p.stat().st_size,'sha256':digest})
  tf.add(p, arcname=rel, recursive=False)
 data = json.dumps({'hostname':socket.gethostname(),'root':str(root),'files':records},indent=2).encode()
 ti = tarfile.TarInfo('EXPORT_MANIFEST.json'); ti.size = len(data)
 tf.addfile(ti,io.BytesIO(data))
