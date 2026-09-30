"""Prepare, launch and inspect exactly one bounded source-only Horaz pilot."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shlex
import sys

from exp226_protocol import deterministic_split, validate_plan
from launch_exp221_job import queue_request
from monitor_exp213_job import QUEUE, ssh

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'work/horaz_development_20260922'
WORK = BASE
REVISION = 1
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE = REMOTE + '/code/exp226_horaz_source_pilot_v1_20260922'
RUN = REMOTE + '/runs/exp226_horaz_source_pilot_v1_20260922'
CONFIG = ROOT / 'reports/exp226_source_pilot_config_20260922.json'


def save(path, value):
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def prepare():
    assert not CONFIG.exists(), 'Existing EXP226 config: reconcile instead of overwriting'
    data = json.loads((BASE / 'resource_data_probe.json').read_text())['data']
    records = [{k: r[k] for k in ('dataset_id', 'zarr_path', 'geff_path')} for r in data['rows']]
    assert len(records) == 71 and all(r['has_geff'] for r in data['rows'])
    training, inner = deterministic_split(records, '44b6', 8)
    manifest = {'source_embryo': '44b6', 'target_embryo': '6bba',
                'rule': 'SHA256(EXP226-inner-v1:dataset_id), first8 inner; remaining63 train',
                'grouping_limitation': 'same embryo; acquisition IDs absent in inspected Zarr metadata',
                'train': training, 'inner_validation': inner}
    save(WORK / 'source44_manifest.json', manifest)
    plan = {'experiment': 'EXP226', 'purpose': 'source_only_training_pilot',
            'source_embryo': '44b6', 'target_embryo': '6bba', 'fold': 1,
            'train': training[:4], 'inner_validation': inner[:2], 'epochs': 2,
            'iterations_per_epoch': 8, 'seed': 3407, 'resume': False,
            'checkpoint_selection': 'none_pilot_fixed_final', 'num_workers': 0,
            'torch_compile': False, 'data_root': REMOTE + '/data/exp213_source_view_20260912',
            'output': RUN + '/output',
            'source_manifest_sha256': hashlib.sha256((WORK/'source44_manifest.json').read_bytes()).hexdigest()}
    validate_plan(plan)
    if REVISION == 2:
        previous = json.loads((BASE / 'pilot_plan.json').read_text())
        assert {k:v for k,v in plan.items() if k!='output'} == {k:v for k,v in previous.items() if k!='output'}, 'Scientific pilot plan must remain identical'
    package = ROOT / 'outputs/research/exp223_horaz0_package_20260921'
    upstream = json.loads((package / 'package_manifest.json').read_text())
    files = {}
    for name, digest in upstream.items():
        if name.startswith('selected/') and (name.endswith('.py') or name == 'selected/resolved_config.json'):
            content = (package / name).read_bytes()
            assert hashlib.sha256(content).hexdigest() == digest, name
            files['horaz/' + name.removeprefix('selected/')] = content
    assert len(files) >= 20
    for name in ('run_exp226_source_pilot.py', 'exp226_protocol.py', 'exp223_supervisor.py', 'monitor_exp213_job.py'):
        files[name] = (ROOT / 'scripts' / name).read_bytes()
    wrapper = (ROOT / 'scripts/exp214_inference_job.py').read_text()
    old = "assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
    assert wrapper.count(old) == 1
    wrapper = wrapper.replace(old, "assert config['script'] == 'run_exp226_source_pilot.py'")
    files['exp226_job.py'] = wrapper.encode()
    files['pilot_plan.json'] = json.dumps(plan, indent=2).encode()
    files['source44_manifest.json'] = (WORK / 'source44_manifest.json').read_bytes()
    manifest_hashes = {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}
    files['code_manifest.json'] = json.dumps(manifest_hashes, indent=2).encode()
    source = '''import base64,json,pathlib,hashlib
code=pathlib.Path(CODE); assert not code.exists(), 'Immutable code exists; reconcile'; code.mkdir()
for name,content in FILES.items():
 p=code/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(content))
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((code/name).read_bytes()).hexdigest()==digest,name
plan=json.loads((code/'pilot_plan.json').read_text())
for row in plan['train']+plan['inner_validation']:
 for key in ('zarr_path','geff_path'):assert pathlib.Path(row[key]).is_dir(),row
print(json.dumps({'status':'STAGED_HASH_VERIFIED','code':str(code),'n_files':len(manifest),'code_manifest_sha256':hashlib.sha256((code/'code_manifest.json').read_bytes()).hexdigest()}))
'''.replace('CODE', repr(CODE)).replace('FILES', repr({n: base64.b64encode(b).decode() for n,b in files.items()}))
    receipt = ssh('nsu-quadro', 'python3 -', source)
    config = {'experiment': 'EXP226', 'lease_id': f'exp226-horaz-source-pilot-v{REVISION}-20260922',
              'token': f'exp226_horaz_source_pilot_v{REVISION}_20260922', 'code': CODE, 'run': RUN,
              'max_seconds': 7200, 'cpu_affinity': '0-7', 'script': 'run_exp226_source_pilot.py',
              'arguments': [CODE + '/pilot_plan.json', '--plan-sha256', manifest_hashes['pilot_plan.json']]}
    save(CONFIG, config)
    save(WORK / 'pilot_plan.json', plan)
    save(WORK / 'staging.json', receipt)
    save(WORK / 'code_manifest.json', manifest_hashes)
    print(json.dumps({'staging':receipt, 'train':[r['dataset_id'] for r in plan['train']],
                      'inner_validation':[r['dataset_id'] for r in plan['inner_validation']],
                      'config':str(CONFIG)}))


def launch():
    c = json.loads(CONFIG.read_text())
    assert c['experiment'] == 'EXP226' and c['max_seconds'] == 7200
    state = ssh('nsu-quadro', shlex.join(['python3', QUEUE, 'status']))
    assert not any(r['state'].startswith('WAITING') and r['project'] != 'biohub-cell-tracking-during-development' for r in state['requests'])
    assert not any(r['id'] == c['lease_id'] for r in state['requests']), 'Existing lease: reconcile'
    if REVISION == 2:
        previous = [r for r in state['requests'] if r['id']=='exp226-horaz-source-pilot-v1-20260922']
        assert len(previous)==1 and previous[0]['state']=='RELEASED', 'Previous process must be released before a retry'
    with (WORK/'launch_claim.json').open('x') as f:json.dump(c, f, indent=2)
    args = ['python3', QUEUE, 'request', '--id', c['lease_id'], '--owner', 'biohub-agent',
            '--token', c['token'], '--project', 'biohub-cell-tracking-during-development',
            '--run-path', c['run'], '--pool', 'a100', '--count', '1', '--cpu', '8',
            '--ram-gib', '32', '--disk-gib', '4', '--minutes', '130']
    lease = queue_request(args, c['lease_id'], c['token'])
    save(WORK/'reservation.json', lease)
    assert lease['state'] == 'RESERVED' and lease['health'] == 'CURRENT'
    c.update(gpu=lease['gpus'][0], alias=lease['alias'])
    assert c['alias'] == 'nsu-a100'
    save(CONFIG, c)
    source = '''import pathlib,json,subprocess
c=CONFIG;r=pathlib.Path(c['run']);assert not r.exists();r.mkdir();config=r/'config.json';config.write_text(json.dumps(c,indent=2))
assert c['gpu'] not in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True)
records={}
for name,args in [('wrapper',[PYTHON,c['code']+'/exp226_job.py',str(config)]),('observe',['python3',c['code']+'/exp223_supervisor.py','observe',str(config)])]:
 with (r/(name+'.log')).open('w') as f:p=subprocess.Popen(args,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 records[name]=p.pid
print(json.dumps(records))
'''.replace('CONFIG',repr(c)).replace('PYTHON',repr(REMOTE+'/envs/prepost/py3.11-stdlib-v1/bin/python'))
    started = ssh(c['alias'], 'python3 -', source)
    save(WORK/'partial_launch.json', {'lease':lease,'launch':started,'config':c})
    source = '''import pathlib,json,subprocess
c=CONFIG;r=pathlib.Path(c['run'])
with (r/'controller.log').open('w') as f:p=subprocess.Popen(['python3',c['code']+'/exp223_supervisor.py','control',str(r/'config.json')],stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
print(json.dumps({'controller_pid':p.pid}))
'''.replace('CONFIG',repr(c))
    control = ssh('nsu-quadro', 'python3 -', source)
    receipt = {'lease':lease,'launch':started,'control':control,'config':c}
    save(WORK/'launch.json',receipt)
    print(json.dumps(receipt))


def status():
    c = json.loads(CONFIG.read_text())
    source = '''import json,pathlib,time
r=pathlib.Path(RUN)
def read(name):
 p=r/name;return json.loads(p.read_text()) if p.exists() else None
s={'at':time.time(),'launch':read('launch.json'),'exit':read('exit.json'),'result':read('output/result.json'),'supervision':read('supervision/complete.json'),'control':read('supervision/control.json')}
log=r/'inference.log';s['log_tail']=log.read_text(errors='replace')[-4000:] if log.exists() else None
print(json.dumps(s))
'''.replace('RUN',repr(c['run']))
    s = ssh(c.get('alias','nsu-a100'),'python3 -',source)
    save(WORK/'status.json',s)
    if s['result'] and s['result']['status'].startswith('PASS'):
        save(WORK/'pilot_result.json',s['result'])
    print(json.dumps({'exit':s['exit'],'result':{k:v for k,v in (s['result'] or {}).items() if k!='history'},
                      'released':s['supervision'], 'log_tail':s['log_tail']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','launch','status'])
    parser.add_argument('--revision', type=int, choices=[1,2], default=1)
    args=parser.parse_args()
    REVISION=args.revision
    if REVISION == 2:
        WORK=BASE/'v2';WORK.mkdir(exist_ok=True)
        CODE=CODE.replace('_v1_', '_v2_')
        RUN=RUN.replace('_v1_', '_v2_')
        CONFIG=ROOT/'reports/exp226_source_pilot_v2_config_20260922.json'
    globals()[args.action]()
