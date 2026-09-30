"""Operational state only; no prediction content or target metrics are opened."""
import json
from pathlib import Path
import sys
from monitor_exp213_job import ssh,QUEUE

def main():
    queue=ssh('nsu-quadro','python3 '+QUEUE+' status')
    active=[r for r in queue['requests'] if r['state'] not in ('RELEASED','CANCELLED')]
    code='''import json,time
from pathlib import Path
root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
rows=[]
for run in sorted((root/'runs').glob('exp214_*20260912')):
 if not any(k in run.name for k in ('reduced','paired','equal_time','control_')):continue
 row={'run':run.name}
 for filename,key in (('exit.json','exit'),('output/status.json','training')):
  p=run/filename
  if p.exists():
   v=json.loads(p.read_text());row[key]={k:v[k] for k in ('returncode','status','epoch','total_epochs','elapsed_seconds','best_sha256') if k in v}
 history=run/'output/history.json'
 if history.exists():
  h=json.loads(history.read_text());row['last_completed_epoch']=h[-1]['epoch'] if h else 0
 row['candidate_movies']=len(list((run/'output/public/candidates').glob('*.npz')))+len(list((run/'output/candidates').glob('*.npz')))
 row['public_receipt']=(run/'output/public/inference_receipt.json').exists() or (run/'output/inference_receipt.json').exists()
 row['local_receipt']=(run/'output/local/inference_receipt.json').exists()
 rows.append(row)
print(json.dumps({'utc_epoch':time.time(),'runs':rows}))
'''
    result=ssh('nsu-quadro','python3 -',code);result['queue']=active
    Path('reports/exp214_progress_snapshot_20260912.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
