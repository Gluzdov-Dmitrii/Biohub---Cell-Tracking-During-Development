"""Read-only compact checks for the two registered remote EXP221 arms."""
import argparse
import json
from pathlib import Path
from monitor_exp213_job import ssh, probe, QUEUE


def main():
    p=argparse.ArgumentParser(); p.add_argument('--smoke',action='store_true'); a=p.parse_args()
    results={}
    for arm in ['control','domain']:
        c=json.loads(Path(f'reports/exp221_{arm}_44b6_s2026_20260921_config.json').read_text())
        if a.smoke:
            c['run']+='_smoke'; c['lease_id']+='-smoke'; c['token']+='_smoke'
        state=probe(c)
        source='''import json
from pathlib import Path
r=Path(RUN)
out={}
for key in ['benchmark','status','history']:
 p=r/'output'/(key+'.json')
 if p.exists(): out[key]=json.loads(p.read_text())
p=r/'training.log'
lines=p.read_text().splitlines() if p.exists() else []
out['log_tail']=lines[-4:]
out['ready']=[json.loads(line) for line in lines if line.startswith('{') and '"stage": "ready"' in line]
print(json.dumps(out))
'''.replace('RUN',repr(c['run']))
        results[arm]={'process':state,'outputs':ssh('nsu-a100','python3 -',source)}
    results['queue']=ssh('nsu-quadro',f'python3 {QUEUE} status')
    results['queue']['requests']=[v for v in results['queue']['requests'] if v['id'].startswith('exp221-')]
    Path('reports/exp221_'+('smoke' if a.smoke else 'training')+'_live_20260921.json').write_text(json.dumps(results,indent=2)+'\n')
    compact={arm:{'alive':v['process'].get('identity_alive'), 'exit':v['process'].get('exit'),
             'outputs':v['outputs']} for arm,v in results.items() if arm!='queue'}
    compact['leases']=[{'id':v['id'],'state':v['state']} for v in results['queue']['requests']]
    for arm in ['control','domain']:
        outputs=compact[arm]['outputs']
        if 'history' in outputs: outputs['history']=outputs['history'][-1:]
    print(json.dumps(compact,indent=2))


if __name__=='__main__': main()
