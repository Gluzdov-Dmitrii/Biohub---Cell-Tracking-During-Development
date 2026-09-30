"""Verify a finished ensemble chunk before starting the next one."""
import argparse
import json
from pathlib import Path
from monitor_exp213_job import ssh


def main():
    p=argparse.ArgumentParser();p.add_argument('config',type=Path);args=p.parse_args()
    c=json.loads(args.config.read_text())
    assert c['experiment']=='EXP228' and c['pool']=='quadro'
    source='''import pathlib,json,hashlib
r=pathlib.Path(__RUN__);plan=pathlib.Path(__PLAN__)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads(plan.read_text());comp=json.loads((r/'output/complete.json').read_text())
ex=json.loads((r/'exit.json').read_text());sup=json.loads((r/'supervision/complete.json').read_text())
ctl=json.loads((r/'supervision/control.json').read_text())
assert sha(plan)==__PLAN_SHA__ and len(p['rows'])==len(comp['records'])==comp['n_movies']
assert comp['status']=='PASS_EXP228_NO_LABEL_CHUNK' and comp['no_target_labels'] is True
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and ctl['queue']['state']=='RELEASED'
assert [x['dataset'] for x in comp['records']]==[x['dataset'] for x in p['rows']]
files=set(x.name for x in (r/'output').iterdir());expected={'complete.json'}
for rec in comp['records']:
 n=rec['dataset'];csv=r/'output'/('ensemble__'+n+'.csv');js=r/'output'/('ensemble__'+n+'.json')
 assert sha(csv)==rec['csv_sha256'] and json.loads(js.read_text())==rec
 assert rec['plan_sha256']==__PLAN_SHA__ and rec['fold']==1 and rec['mixture']==[0.5,0.5]
 expected.update((csv.name,js.name))
assert files==expected,(len(files),len(expected))
print(json.dumps({'status':'PASS_EXP228_CHUNK_FULL_AUDIT','chunk':p['chunk'],'n_movies':len(p['rows']),
 'plan_sha256':sha(plan),'complete_sha256':sha(r/'output/complete.json'),
 'lease':ctl['queue']['state'],'exit':ex['returncode']}))
'''.replace('__RUN__',repr(c['run'])).replace('__PLAN__',repr(c['arguments'][0])).replace('__PLAN_SHA__',repr(c['arguments'][2]))
    result=ssh('nsu-quadro','python3 -',source)
    dest=args.config.with_name(args.config.stem+'_full_audit.json')
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
