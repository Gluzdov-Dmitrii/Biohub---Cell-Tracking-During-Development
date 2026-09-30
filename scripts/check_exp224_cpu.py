import json,pathlib,sys
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
c=json.loads(pathlib.Path('reports/exp224_cpu_launch_config_20260921.json').read_text())
s='''import json,pathlib,time
r=pathlib.Path(RUN)
out={'checked_at':time.time(),'run':str(r)}
for n in ['launch.json','exit.json','wrapper_launch.json','wrapper_exit.json','output/no_metric_gate.json','output/result.json']:
 p=r/n
 if p.exists():
  d=json.loads(p.read_text());out[n]={k:v for k,v in d.items() if k not in ['rows','provenance']} if n.endswith('result.json') else d
for name in ['worker.log','inference.log','wrapper.log']:
 p=r/name
 if p.exists():out[name]=p.read_text()[-1400:]
print(json.dumps(out))
'''.replace('RUN',repr(c['remote_run']))
r=ssh('nsu-quadro','python3 -',s);pathlib.Path('reports/exp224_live_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
