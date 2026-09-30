"""Stage and launch one bounded CPU diagnostic on existing NSU inputs."""
import hashlib
import json
from pathlib import Path
from monitor_exp213_job import ssh

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
files = {name: (ROOT / 'scripts' / name).read_text() for name in ['analyze_exp220_node_strata.py', 'analyze_submission_edge_failure_modes.py', 'analyze_cached_edge_failure_modes.py']}
prereg = {'experiment': 'EXP220', 'status': 'PREREGISTERED', 'hypothesis': 'Frozen missed annotated nodes concentrate by physical neighbor distance, array depth, time, or spatial boundary, motivating source-only data sampling changes.', 'evidence': 'development-adapted diagnostic; no new OOF/model selection', 'resources': {'host':'nsu-quadro', 'cpu':4,'ram_gib':32,'disk_growth_gib':0.02,'gpu':0,'timeout_seconds':7200},'no_kaggle_post': True, 'sources': {k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}}
(ROOT/'reports/exp220_preregistration_20260921.json').write_text(json.dumps(prereg,indent=2)+'\n')
source = r'''
import json, os, resource, subprocess, time
from pathlib import Path
root=Path(ROOT_VALUE)
run=root/'runs/exp220_node_strata_20260921'
assert not run.exists(), 'Existing run requires reconciliation'
run.mkdir()
(run/'tmp').mkdir()
for name,value in FILES_VALUE.items(): (run/name).write_text(value)
(run/'run.json').write_text(json.dumps(PREREG_VALUE,indent=2))
repo=root/'code/exp214_honest_refit_v4_20260912/tracking_repo'
python=root/'envs/prepost/py3.11-stdlib-v1/bin/python'
command=[str(python),str(run/'analyze_exp220_node_strata.py'),'--repo',str(repo),'--data',str(root/'data/exp213_source_view_20260912'),'--metrics',str(root/'runs/exp214_gapfix_score175_20260914/output/new90/metrics.json'),'--output',str(run/'result.json')]
def limits():
 os.sched_setaffinity(0,set(range(4)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',POLARS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
with (run/'worker.log').open('x') as log:
 p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','7200',*command],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
identity=Path('/proc/'+str(p.pid)+'/stat').read_text().split(') ')[1].split()[19]
receipt={'pid':p.pid,'start':identity,'command':command,'started':time.time(),'run':str(run),'timeout_seconds':7200}
(run/'launch.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
'''.replace('ROOT_VALUE',repr(REMOTE)).replace('FILES_VALUE',repr(files)).replace('PREREG_VALUE',repr(prereg))
result=ssh('nsu-quadro','python3 -',source)
(ROOT/'reports/exp220_launch_20260921.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
