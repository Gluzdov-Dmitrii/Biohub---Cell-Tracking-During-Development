"""Freeze the three registered inference configurations; no training or metrics."""
import json
from pathlib import Path

ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'

def main():
    plan=json.loads(Path('reports/exp214_equal_time_plan_20260912.json').read_text())
    base=json.loads(Path('reports/exp214_paired_44b6_00_config_20260912.json').read_text())
    for short,arm in zip(('full12','reduced12','reduced60'),plan['equal_time_control']['arms']):
        c=json.loads(json.dumps(base))
        c['lease_id']=f'biohub-exp214-control-{short}-20260912'
        c['token']=f'exp214-control-{short}-v6'
        c['run']=ROOT+f'/runs/exp214_control_{short}_20260912'
        c['script']='run_exp214_public_fold.py'
        c['scope']=arm+'; all three 20-movie controls required before metrics'
        for flag,value in (('--bundle',ROOT+f'/code/exp214_evaluation_inputs_20260912/{short}_control_bundle.json'),('--output',c['run']+'/output')):
            c['arguments'][c['arguments'].index(flag)+1]=value
        p=Path(f'reports/exp214_control_{short}_config_20260912.json')
        with p.open('x') as f:json.dump(c,f,indent=2);f.write('\n')

if __name__=='__main__':main()
