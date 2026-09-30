import pathlib,json,hashlib,base64,sys
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
code='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp223_official_scorer_v1_20260921'
files={'score_exp223_official.py':pathlib.Path('scripts/score_exp223_official.py').read_bytes(),'score_config.json':pathlib.Path('reports/exp223_official_score_config_20260921.json').read_bytes()}
s='''import pathlib,json,base64,hashlib
p=pathlib.Path(CODE);p.mkdir(exist_ok=True)
for n,b64 in FILES.items():
 b=base64.b64decode(b64);q=p/n
 if q.exists():assert q.read_bytes()==b,'Immutable scorer version differs'
 else:q.write_bytes(b)
manifest={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in FILES};(p/'manifest.json').write_text(json.dumps(manifest,indent=2))
c=json.loads((p/'score_config.json').read_text())
for f,h in c['evaluator_files'].items():assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==h
print(json.dumps({'status':'STAGED_PINNED_SCORER_NOT_EXECUTED','code':str(p),'manifest':manifest,'target_labels_read':False}))
'''.replace('CODE',repr(code)).replace('FILES',repr({n:base64.b64encode(b).decode() for n,b in files.items()}))
r=ssh('nsu-quadro','python3 -',s);pathlib.Path('reports/exp223_official_scorer_staged_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
