"""Stage exact source and bounded CPU-only classical pilot on existing NSU data."""
import base64
import json
from pathlib import Path
from monitor_exp213_job import ssh

LOCAL=Path(__file__).resolve().parents[1]
files={name:base64.b64encode((LOCAL/path).read_bytes()).decode() for name,path in {
    'exp002_exact.py':'kaggle_notebooks/exp002_rule_based/biohub-rule-based-baseline.py',
    'run_exp222_classical_pilot.py':'scripts/run_exp222_classical_pilot.py',
    'analyze_submission_edge_failure_modes.py':'scripts/analyze_submission_edge_failure_modes.py',
    'preregistration.json':'reports/exp222_preregistration_20260921.json',
}.items()}
source=r'''
import base64,json,os,resource,shutil,subprocess,time
from pathlib import Path
root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
assert os.uname().nodename=='prepost'
memory={line.split(':')[0]:int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if len(line.split())>=2 and line.split()[1].isdigit()}
assert memory['MemAvailable']>40*1024**2
assert shutil.disk_usage(root).free>20*1024**3
queue=json.loads(subprocess.check_output(['python3','/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py','status']))
active=[r for r in queue['requests'] if r['state'] not in ['RELEASED','CANCELLED']]
run=root/'runs/exp222_classical_pilot_stdlib_20260921'
assert not run.exists(), 'Existing run must be reconciled'
run.mkdir();(run/'tmp').mkdir()
for name,value in FILES_VALUE.items():(run/name).write_bytes(base64.b64decode(value))
spec=json.loads((run/'preregistration.json').read_text())
for movie in spec['movies']:assert (root/'data/exp213_source_view_20260912'/(movie+'.zarr')/'0/zarr.json').exists()
def limits():
 os.sched_setaffinity(0,set(range(4)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',POLARS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
command=[str(root/'envs/prepost/py3.11-stdlib-v1/bin/python'),str(run/'run_exp222_classical_pilot.py')]
with (run/'worker.log').open('x') as log:
 p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','3600',*command],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
identity=Path('/proc/'+str(p.pid)+'/stat').read_text().split(') ')[1].split()[19]
receipt={'pid':p.pid,'start':identity,'command':command,'started':time.time(),'run':str(run),'timeout_seconds':3600,'host':os.uname().nodename,'mem_available_kib':memory['MemAvailable'],'active_allocations':[{'id':r['id'],'pool':r['pool'],'cpu':r['cpu']} for r in active]}
(run/'launch.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
'''.replace('FILES_VALUE',repr(files))
r=ssh('nsu-quadro','python3 -',source)
(LOCAL/'reports/exp222_stdlib_launch_20260921.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
