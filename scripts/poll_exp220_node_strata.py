import json,sys
from pathlib import Path
sys.path.insert(0,'scripts')
from monitor_exp213_job import ssh
source='''import json,time
from pathlib import Path
r=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp220_node_strata_20260921')
a=json.loads((r/'launch.json').read_text()); p=Path('/proc/'+str(a['pid'])+'/stat')
stat=p.read_text().split(') ')[1].split() if p.exists() else []
print(json.dumps({'alive':bool(stat and stat[0]!='Z' and stat[19]==a['start']),'elapsed':time.time()-a['started'],'log_tail':(r/'worker.log').read_text()[-2000:],'result':json.loads((r/'result.json').read_text()) if (r/'result.json').exists() else None}))
'''
r=ssh('nsu-quadro','python3 -',source)
Path('reports/exp220_status_20260921.json').write_text(json.dumps(r,indent=2))
if r['result']:
 Path('reports/exp220_result_20260921.json').write_text(json.dumps(r['result'],indent=2))
 r['result']={'status':r['result']['status'],'movies':len(r['result']['movies']),'strata':r['result']['strata']}
print(json.dumps(r,indent=2))
