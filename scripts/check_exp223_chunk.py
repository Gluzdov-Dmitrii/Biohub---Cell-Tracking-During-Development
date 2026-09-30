import pathlib,json,sys
sys.path.insert(0,'scripts');from monitor_exp213_job import ssh
index=int(sys.argv[1]);c=json.loads(pathlib.Path(f'reports/exp223_chunk{index:02d}_config_20260921.json').read_text())
src="""import pathlib,json,time
p=pathlib.Path(RUN)
result={n:json.loads((p/n).read_text()) if (p/n).exists() else None for n in ['launch.json','exit.json','supervision/control.json','supervision/complete.json']}
files=list((p/'output').glob('*.json')) if (p/'output').exists() else [];result['receipt_count']=sum(f.name!='complete.json' for f in files)
result['tail']=(p/'inference.log').read_text()[-1800:] if (p/'inference.log').exists() else ''
print(json.dumps(result))
""".replace('RUN',repr(c['run']))
r=ssh('nsu-a100','python3 -',src);pathlib.Path(f'reports/exp223_chunk{index:02d}_status_20260921.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
