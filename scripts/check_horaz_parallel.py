"""One read-only snapshot of EXP227/228/229. No launch, timer or submission."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from monitor_exp213_job import ssh

LOCAL=Path(__file__).resolve().parents[1]
CONFIGS=['reports/exp227_source_block01_config_20260922.json',
         'reports/exp228_quadro_chunk00_config_20260923.json',
         'reports/exp229_cpu_config_20260923.json']


def probe(config_path):
    c=json.loads((LOCAL/config_path).read_text())
    source='''import json,pathlib,time
r=pathlib.Path(RUN)
def read(n):
 p=r/n;return json.loads(p.read_text()) if p.exists() else None
launch=read('launch.json');alive=False
if launch:
 p=pathlib.Path('/proc',str(launch['pid']),'stat')
 if p.exists():
  raw=p.read_text();f=raw[raw.rfind(')')+2:].split();alive=f[0]!='Z' and f[19]==launch['start']
result=read('output/result.json');complete=read('output/complete.json')
log=r/LOG
print(json.dumps({'at':time.time(),'run':str(r),'launch':launch,'alive':alive,'exit':read('exit.json'),
 'release':read('supervision/complete.json'),'control':read('supervision/control.json'),
 'history':read('output/fold1/history.json'),'prediction_progress':read('predictions/progress.json'),
 'score_progress':read('output/progress.json'),'csv_count':len(list((r/'output').glob('*.csv'))),
 'complete':complete,'result':result,'log_tail':log.read_text(errors='replace')[-2000:] if log.exists() else ''}))
'''.replace('RUN',repr(c.get('run',c.get('remote_run')))).replace('LOG',repr('worker.log' if c['experiment']=='EXP229' else 'inference.log'))
    state=ssh(c.get('alias','nsu-quadro'),'python3 -',source)
    dest=LOCAL/'work/horaz_parallel_20260923'/(c['experiment'].lower()+'_status.json')
    dest.write_text(json.dumps(state,indent=2))
    return {'experiment':c['experiment'],'alive':state['alive'],'pid':(state['launch'] or {}).get('pid'),
            'exit':state['exit'],'queue':((state['control'] or {}).get('queue') or {}).get('state'),
            'epochs_completed':len(state['history'] or []),'csv_count':state['csv_count'],
            'prediction_progress':state['prediction_progress'],'score_progress':state['score_progress'],
            'result_status':(state['result'] or state['complete'] or {}).get('status'),
            'summary':(state['result'] or {}).get('summary'),'last_log':state['log_tail'].splitlines()[-1:]}


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(probe,CONFIGS):print(json.dumps(result))
