import sys,json,pathlib
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
c=json.loads(pathlib.Path('reports/exp223_benchmark_config_20260921.json').read_text())
src="import pathlib,json;p=pathlib.Path("+repr(c['run'])+");print(json.dumps({n:json.loads((p/n).read_text()) if (p/n).exists() else None for n in ['exit.json','output/complete.json','supervision/complete.json','supervision/control.json']}))"
r=ssh('nsu-a100','python3 -',src);pathlib.Path('reports/exp223_benchmark_status_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
