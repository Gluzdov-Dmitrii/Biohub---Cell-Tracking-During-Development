"""Freeze controlled primary90/secondary60 versus existing60/60 comparison."""
import hashlib,json
from pathlib import Path
from monitor_exp213_job import ssh
L=Path(__file__).resolve().parents[1]
R='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
def save(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    plan={'experiment':'EXP214','stage':'eval90','hypothesis':'Continuing primary detector60->90 improves paired175 tracking score; secondary60, center, graph and cohort fixed.', 'roles':{'primary':{'seed':2026,'epochs':90},'secondary':{'seed':314159,'epochs':60}},'target_metrics_gate':'All175 both arms predictions and all models frozen before metrics','scope':'Development-adapted reciprocal two-embryo OOF; not pristine holdout; no POST; no implicit further training','baseline':'exp214_strong60_score175_20260912','deadline_utc':'2026-09-14T00:00:00Z'}
    p=L/'reports/exp214_eval90_plan_20260913.json';save(p,plan)
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    remote='''import json,hashlib
from pathlib import Path
r=Path(ROOT);out=r/'code/exp214_eval90_inputs_20260913';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bundles={}
for fold in ('44b6','6bba'):
 old=json.loads((r/('code/exp214_strong60_evaluation_inputs_20260912/'+fold+'_bundle.json')).read_text())
 parent=r/('runs/exp214_continue90_'+fold+'_s2026_20260913/output')
 status=json.loads((parent/'status.json').read_text());history=json.loads((parent/'history.json').read_text())
 assert status['status']=='COMPLETE_SOURCE_REFIT' and status['epoch']==90 and status['target_data_opened'] is False
 assert status['contract']['fold']==fold and status['contract']['seed']==2026
 assert [x['epoch'] for x in history]==list(range(1,91))
 assert sha(parent/'checkpoint_last.pth')==status['checkpoint_sha256']
 assert sha(parent/'edge_predictor_best.pth')==status['best_sha256']
 old['primary']={'path':str(parent/'edge_predictor_best.pth'),'sha256':status['best_sha256'],'actual_training_plan_sha256':status['contract']['plan_sha256'],'source_status_sha256':sha(parent/'status.json'),'seed':2026,'selected_epoch':max(history,key=lambda x:x['selection_score'])['epoch'],'source_only_selection':True,'total_epochs':90}
 for role in ('secondary','center'):assert sha(Path(old[role]['path']))==old[role]['sha256']
 old.update(training_plan_sha256=DIGEST,purpose='CONTROLLED_PRIMARY90_SECONDARY60_PAIRED175',scope='Only primary detector advanced60->90; secondary60 and clean center unchanged. Two embryos, development-adapted.')
 bundles[fold]=old
 (out/(fold+'_bundle.json')).write_text(json.dumps(old,indent=2)+'\\n')
result={'status':'PASS_FROZEN_90_60_MODELS','plan_sha256':DIGEST,'bundles':bundles}
(out/'model_bundle_receipt.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
'''.replace('ROOT',repr(R)).replace('DIGEST',repr(digest))
    bundle=ssh('nsu-quadro','python3 -',remote)
    save(L/'reports/exp214_eval90_bundle_receipt_20260913.json',bundle)
    for fold,n in [('44b6',5),('6bba',3)]:
        for i in range(n):
            tag=f'{fold}_{i:02}'
            c=json.loads((L/f'reports/exp214_strong60_paired_{tag}_config_20260912.json').read_text())
            c.update(lease_id=f'biohub-exp214-eval90-{tag}-20260913',token=f'exp214-eval90-{tag}',run=R+f'/runs/exp214_eval90_paired_{tag}_20260913',scope=plan['hypothesis'])
            for flag,val in [('--bundle',R+f'/code/exp214_eval90_inputs_20260913/{fold}_bundle.json'),('--output',c['run']+'/output')]:c['arguments'][c['arguments'].index(flag)+1]=val
            save(L/f'reports/exp214_eval90_paired_{tag}_config_20260913.json',c)
    m=json.loads((L/'reports/exp214_strong60_score175_manifest_20260912.json').read_text())
    m.update(training_plan_sha256=digest,training_epochs={'primary':90,'secondary':60},scope=plan['hypothesis'])
    for arm in m['arms'].values():
        for part in arm:
            for k in ('csv','receipt'):part[k]=part[k].replace('exp214_strong60_paired_','exp214_eval90_paired_').replace('_20260912/','_20260913/')
    save(L/'reports/exp214_eval90_manifest_20260913.json',m)
    ssh('nsu-quadro','python3 -',"import json\nfrom pathlib import Path\np=Path("+repr(R+'/code/exp214_eval90_inputs_20260913/manifest.json')+")\np.write_text(json.dumps("+repr(m)+",indent=2))\nprint('{}')")
    src=(L/'scripts/finish_exp214_strong60_predictions.py').read_text()
    start=src.index('    while time.time() < deadline:')
    end=src.index('    tags = ',start)
    src=src[:start]+"    assert json.loads((LOCAL / 'reports/exp214_eval90_bundle_receipt_20260913.json').read_text())['status']=='PASS_FROZEN_90_60_MODELS'\n"+src[end:]
    src=src.replace('exp214_strong60','exp214_eval90').replace('STRONG60','EVAL90').replace('_20260912','_20260913')
    src=src.replace('exp214_inference_v7_20260913','exp214_inference_v7_20260912').replace('exp214_eval90_evaluation_inputs_20260913','exp214_eval90_inputs_20260913')
    src=src.replace('datetime.datetime(2026, 9, 13, 17, 30','datetime.datetime(2026, 9, 13, 23, 30')
    path=L/'scripts/finish_exp214_eval90_predictions.py'
    with path.open('x') as f:f.write(src)
    print(json.dumps({'plan_sha256':digest,'bundles':bundle['status'],'configs':8}))
if __name__=='__main__':main()
