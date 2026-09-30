import json,sys
from pathlib import Path
sys.path.insert(0,'scripts')
from monitor_exp213_job import ssh
src='''import json,subprocess
from pathlib import Path
r=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
print(json.dumps({'metrics':[str(p) for p in (r/'runs').glob('*gapfix*/*/new90/metrics.json')], 'exp216':[str(p) for p in (r/'runs/exp216_submission_failure_attribution_20260915').iterdir()], 'gpus':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True)}))
'''
print(json.dumps(ssh('nsu-quadro','python3 -',src),indent=2))
print(json.dumps(ssh('nsu-a100','python3 -',"import json,subprocess,os; print(json.dumps({'host':os.uname().nodename,'gpus':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True)}))"),indent=2))
