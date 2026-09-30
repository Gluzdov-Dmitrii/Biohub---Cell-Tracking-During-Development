"""One read-only status snapshot for current ensemble and warm-start runs."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from monitor_exp213_job import ssh

ROOT=Path(__file__).resolve().parents[1]
TARGETS=[('EXP228_chunk01','reports/exp228_quadro_chunk01_config_20260923.json'),
         ('EXP231','reports/exp231_warmstart_full2_config_20260923.json')]


def one(item):
    name,path=item;c=json.loads((ROOT/path).read_text())
    source='''import pathlib,json,time
r=pathlib.Path(__RUN__)
def read(n):
 p=r/n;return json.loads(p.read_text()) if p.exists() else None
launch=read('launch.json');alive=False
if launch:
 p=pathlib.Path('/proc',str(launch['pid']),'stat')
 if p.exists():
  raw=p.read_text();f=raw[raw.rfind(')')+2:].split();alive=f[0]!='Z' and f[19]==launch['start']
print(json.dumps({'at':time.time(),'alive':alive,'launch':launch,'exit':read('exit.json'),
 'release':read('supervision/complete.json'),'control':read('supervision/control.json'),
 'result':read('output/result.json'),'complete':read('output/complete.json'),
 'history':read('output/fold1/history.json'),'csv_count':len(list((r/'output').glob('*.csv'))),
 'tail':(r/'inference.log').read_text(errors='replace')[-1500:] if (r/'inference.log').exists() else ''}))
'''.replace('__RUN__',repr(c['run']))
    state=ssh(c['alias'],'python3 -',source)
    dest=ROOT/'work/horaz_development_20260923'/('exp231' if name=='EXP231' else 'exp228')
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'status.json').write_text(json.dumps(state,indent=2))
    result=state['result'] or state['complete'] or {}
    return {'experiment':name,'alive':state['alive'],'pid':(state['launch'] or {}).get('pid'),
            'queue':((state['control'] or {}).get('queue') or {}).get('state'),
            'exit':state['exit'],'release':(state['release'] or {}).get('status'),
            'result_status':result.get('status'),'epochs':len(state['history'] or []),
            'csv_count':state['csv_count'],'last_log_lines':state['tail'].splitlines()[-2:]}


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        for status in pool.map(one,TARGETS):print(json.dumps(status))
