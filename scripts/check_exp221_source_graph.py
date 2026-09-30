"""One compact read-only poll of the remote source8 gate and scorer."""
import json
from pathlib import Path
from monitor_exp213_job import ssh
from prepare_exp221_source_graph import ROOT,RUN
from migrate_exp221_source_supervision import SUP


def main():
    source='''import json,time
from pathlib import Path
r=Path(RUN);s=Path(SUP)/'state'
out={'checked_at':time.time(),'source8_only':True}
for key,path in [('inference_exit',r/'exit.json'),('prediction_gate',r/'output/status.json'),('remote_control',s/'control_status.json'),('score_exit',s/'score_exit.json'),('supervision_complete',s/'complete.json')]:
 if path.exists(): out[key]=json.loads(path.read_text())
out['candidate_movies']={arm:len(list((r/'output'/arm/'candidates').glob('*.npz'))) for arm in ['control','domain']}
out['errors']={p.name:p.read_text().splitlines()[-2:] for p in s.glob('*errors.jsonl')}
p=r/'score/metrics.json'
if p.exists():
 data=json.loads(p.read_text());out['metrics']={key:data[key] for key in ['status','scope','summary']}
print(json.dumps(out))
'''.replace('RUN',repr(RUN)).replace('SUP',repr(SUP))
    result=ssh('nsu-quadro','python3 -',source)
    Path('reports/exp221_source_graph8_live_20260921.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
