"""Reviewed-file staging and explicit bounded CPU launch, never implicit at import."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from monitor_exp213_job import ssh

LOCAL=Path(__file__).resolve().parents[1]
REMOTE='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'


def payload(config,launch=False):
    assert config['experiment']=='EXP224'
    assert config['remote_code'].startswith(REMOTE+'/code/exp224_')
    assert config['remote_run'].startswith(REMOTE+'/runs/exp224_')
    assert '..' not in Path(config['remote_code']).parts and '..' not in Path(config['remote_run']).parts
    assert config['resources']=={'cpu':4,'ram_gib':32,'gpus':0,'timeout_seconds':7200}
    assert isinstance(config['arguments'],list) and all(isinstance(v,str) for v in config['arguments'])
    result={}
    for name,local in config['files'].items():
        assert name==Path(name).name and name not in ['config.json','code_manifest.json','exp224_cpu_wrapper.py']
        p=(LOCAL/local).resolve();assert p.is_relative_to(LOCAL) and p.is_file()
        value=p.read_bytes();digest=hashlib.sha256(value).hexdigest()
        if launch:assert config.get('reviewed_sources',{}).get(name)==digest,'Parent-reviewed SHA missing/mismatched: '+name
        result[name]=base64.b64encode(value).decode()
    assert config['entrypoint'] in result and config['entrypoint']=='run_exp224_fixed_nodes.py'
    assert 'input_package.json' in result,'Verified source8 input package must be included'
    package=json.loads(base64.b64decode(result['input_package.json']))
    assert package['status']=='PASS_FIXED_SOURCE8_HYBRID_INPUT_EXPORT' and len(package['datasets'])==8
    if launch:assert config.get('launch_approved_after_code_review') is True,'Parent has not approved reviewed Grok code'
    result['exp224_cpu_wrapper.py']=base64.b64encode((LOCAL/'scripts/exp224_cpu_wrapper.py').read_bytes()).decode()
    result['config.json']=base64.b64encode(json.dumps(config,indent=2).encode()).decode()
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--launch',action='store_true',help='Only after parent review; default stages only')
    a=parser.parse_args();config=json.loads(a.config.read_text());files=payload(config,a.launch)
    source='''import base64,hashlib,json,os,shutil,socket,subprocess,time
from pathlib import Path
assert socket.gethostname()=='prepost'
c=CONFIG;p=Path(c['remote_code']);run=Path(c['remote_run']);root=Path(ROOT)
assert p.resolve().is_relative_to(root/'code') and run.resolve().is_relative_to(root/'runs')
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
queue=json.loads(subprocess.check_output(['python3','/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py','status'],text=True))
active=[v for v in queue['requests'] if v['state'] in ['RUNNING','RESERVED'] and v.get('host')=='prepost']
assert mem['MemAvailable']>40*1024**3,'Insufficient RAM for32GiB worker + headroom'
assert sum(v['cpu'] for v in active)+4<=112
assert sum(v['ram_gib'] for v in active)+32<=240
assert os.getloadavg()[0]<100,'Host load too high for bounded CPU start'
assert shutil.disk_usage(root).free>20*1024**3
p.mkdir(exist_ok=True)
for name,value in FILES.items():
 b=base64.b64decode(value);dest=p/name
 if dest.exists():assert dest.read_bytes()==b,'Immutable staged payload differs: '+name
 else:dest.write_bytes(b)
manifest={name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in FILES}
(p/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
package=json.loads((p/'input_package.json').read_text())
for key in ['control_csv','control_receipt','source_graph_metrics','source_manifest']:
 info=package[key];assert hashlib.sha256(Path(info['path']).read_bytes()).hexdigest()==info['sha256'],key
result={'stage':'PASS_IMMUTABLE_SOURCE_INPUT_HASHES','code':str(p),'manifest':manifest,
        'cpu_policy':'CPU-only actual host preflight; GPU queue read-only, no fake GPU lease',
        'mem_available':mem['MemAvailable'],'active_prepost_leases':[v['id'] for v in active],'load':os.getloadavg()}
if LAUNCH:
 assert not run.exists(),'Existing run: reconcile, never duplicate'
 run.mkdir();(run/'preflight.json').write_text(json.dumps(result,indent=2))
 with (run/'wrapper.log').open('x') as log:
  child=subprocess.Popen(['python3',str(p/'exp224_cpu_wrapper.py'),str(p/'config.json')],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 raw=Path('/proc',str(child.pid),'stat').read_text()
 result['launch']={'wrapper_pid':child.pid,'wrapper_start':raw[raw.rfind(')')+2:].split()[19],'run':str(run),'at':time.time()}
 (run/'wrapper_launch.json').write_text(json.dumps(result['launch'],indent=2))
print(json.dumps(result))
'''.replace('CONFIG',repr(config)).replace('FILES',repr(files)).replace('ROOT',repr(REMOTE)).replace('LAUNCH',repr(a.launch))
    result=ssh('nsu-quadro','python3 -',source)
    receipt=a.config.with_name(a.config.stem+('_launch_receipt' if a.launch else '_stage_receipt')+'.json')
    receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
