import sys,json,pathlib
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh,probe
c=json.loads(pathlib.Path('reports/exp223_source_smoke_config_20260921.json').read_text())
print(json.dumps(probe(c),indent=2))
src="import pathlib,json;p=pathlib.Path("+repr(c['run'])+");print(json.dumps({'log':(p/'inference.log').read_text()[-2500:],'result':json.loads((p/'output/result.json').read_text()) if (p/'output/result.json').exists() else None}))"
r=ssh('nsu-a100','python3 -',src);print(json.dumps(r,indent=2));pathlib.Path('reports/exp223_smoke_latest_20260921.json').write_text(json.dumps(r,indent=2))
