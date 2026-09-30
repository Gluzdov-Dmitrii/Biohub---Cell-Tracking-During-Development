"""Read-only provenance/compatibility gate for source-validation graph evaluation."""
import json
from pathlib import Path
from monitor_exp213_job import ssh


def main():
    source='''import json,hashlib
from pathlib import Path
r=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
def read(p):return json.loads((r/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read('code/exp221_control_v1_20260921/plan.json')
out={'validation':plan['folds']['44b6']['validation'],'models':{}}
for arm in ['control','domain']:
 p=r/('runs/exp221_'+arm+'_44b6_s2026_20260921/output')
 s=json.loads((p/'status.json').read_text()); assert s['status']=='COMPLETE_SOURCE_REFIT' and s['epoch']==24
 assert sha(p/'edge_predictor_best.pth')==s['best_sha256'] and sha(p/'checkpoint_last.pth')==s['checkpoint_sha256']
 out['models'][arm]=s
out['supervision']=read('code/exp221_supervision_v1_20260921/state/complete.json')
out['center_split']=read('runs/exp180_reciprocal_deepcenter_training_20260910/trainer_44b6_source.json')
out['bundle']=read('code/exp214_strong60_evaluation_inputs_20260912/44b6_bundle.json')
out['center_sha_actual']=sha(Path(out['bundle']['center']['path']))
out['secondary_sha_actual']=sha(Path(out['bundle']['secondary']['path']))
secondary_status=Path(out['bundle']['secondary']['path']).parent/'status.json'
out['secondary_status']=json.loads(secondary_status.read_text())
out['secondary_plan']=read('code/exp214_strong60_v1_20260912/plan.json')['folds']['44b6']
print(json.dumps(out))
'''
    out=ssh('nsu-quadro','python3 -',source)
    Path('reports/exp221_source_graph_input_audit_20260921.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['models','secondary_plan']},indent=2))


if __name__=='__main__':main()
