import base64,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'scripts')
from monitor_exp213_job import ssh
source='''import base64,hashlib,json
from pathlib import Path
r=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp220_node_strata_20260921')
a=json.loads((r/'launch.json').read_text()); live=[]
for p in Path('/proc').glob('[0-9]*/stat'):
 try:
  f=p.read_text().split(') ')[1].split()
  if f[0]!='Z' and int(f[2])==a['pid']:live.append(int(p.parent.name))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
files={k:base64.b64encode((r/k).read_bytes()).decode() for k in ['result.json','worker.log','run.json','launch.json']}
print(json.dumps({'live_process_group':live,'pid':a['pid'],'start':a['start'],'files':files,'sha256':{k:hashlib.sha256((r/k).read_bytes()).hexdigest() for k in files}}))
'''
r=ssh('nsu-quadro','python3 -',source)
out=Path('outputs/research/exp220_node_strata_20260921');out.mkdir(exist_ok=True,parents=True)
for k,v in r.pop('files').items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==r['sha256'][k];(out/k).write_bytes(b)
Path('reports/exp220_completion_20260921.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
