import pathlib,json,sys,base64,hashlib
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
src="""import pathlib,json,base64,hashlib,time
r=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp223_official_score175_v2_20260922');names=['launch.json','child.json','exit.json','output/no_metric_gate.json','output/result.json'];files={n:base64.b64encode((r/n).read_bytes()).decode() for n in names if (r/n).exists()};live=[]
if (r/'child.json').exists():
 child=json.loads((r/'child.json').read_text())
 for p in pathlib.Path('/proc').glob('[0-9]*/stat'):
  try:
   f=p.read_text().split(') ')[1].split()
   if f[0]!='Z' and int(f[2])==child['pid']:live.append(int(p.parent.name))
  except (FileNotFoundError,ProcessLookupError,PermissionError):pass
print(json.dumps({'files':files,'hashes':{n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in files},'live_group':live,'log':(r/'worker.log').read_text()[-2000:] if (r/'worker.log').exists() else ''}))
"""
r=ssh('nsu-quadro','python3 -',src);out=pathlib.Path('outputs/research/exp223_official_score175_v2_20260922');out.mkdir(exist_ok=True,parents=True)
for n,v in r.pop('files').items():
 b=base64.b64decode(v);assert hashlib.sha256(b).hexdigest()==r['hashes'][n];p=out/n;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(b)
pathlib.Path('reports/exp223_official_score_v2_status_20260922.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if (out/'output/result.json').exists():print(json.dumps(json.loads((out/'output/result.json').read_text())['summary'],indent=2))
