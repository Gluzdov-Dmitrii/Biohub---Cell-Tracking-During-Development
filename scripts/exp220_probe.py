import json, subprocess, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from monitor_exp213_job import ssh
src='''import json, os, shutil, subprocess
from pathlib import Path
r=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
q=json.loads(subprocess.check_output(['python3','/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py','status']))
print(json.dumps({'host':os.uname().nodename,'active':[x for x in q['requests'] if x['state'] not in ['RELEASED','CANCELLED']], 'mem':Path('/proc/meminfo').read_text().splitlines()[:3], 'disk_free':shutil.disk_usage(r).free,'load':os.getloadavg(),'runs':[str(x) for x in (r/'runs').glob('*exp216*')], 'io':(r/'code/exp214_honest_refit_v4_20260912/tracking_repo/src/biohub_tracking/io.py').read_text()[:12000]}))
'''
r=ssh('nsu-quadro','python3 -',src)
Path('reports/exp220_cluster_preflight_20260921.json').write_text(json.dumps(r,indent=2))
print(json.dumps(r,indent=2))
