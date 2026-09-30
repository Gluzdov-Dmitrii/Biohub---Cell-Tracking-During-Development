"""Freeze a source8-only paired graph gate; reuse fixed public graph unchanged."""
import base64
import hashlib
import json
from pathlib import Path
from monitor_exp213_job import ssh
from exp221_source_scope import MOVIES

ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'
CODE=ROOT+'/code/exp221_source_graph_v1_20260921'
RUN=ROOT+'/runs/exp221_source_graph8_20260921'


def main():
    audit=json.loads(Path('reports/exp221_source_graph_input_audit_20260921.json').read_text())
    assert set(audit['validation'])==MOVIES
    assert not MOVIES.intersection(x.removesuffix('.zarr') for x in audit['center_split'][0]['train']+audit['center_split'][0]['test'])
    assert not MOVIES.intersection(audit['secondary_plan']['train'])
    assert set(audit['secondary_plan']['validation'])==MOVIES
    protocol={'experiment':'EXP221_SOURCE_GRAPH8','movies':sorted(MOVIES),'primary_selected_epochs':{'control':13,'domain':23},
              'scope':'Source-validation development graph diagnostic; not opposite-embryo OOF or private estimate',
              'graph':'Frozen COMPACT47-v20 public graph, unchanged secondary60/center, no overrides',
              'rule':'All16movie predictions complete before official labels; no other checkpoints; no POST or retraining'}
    digest=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    bundles={}
    for arm in ['control','domain']:
        status=audit['models'][arm]
        b=dict(audit['bundle']);b['primary']={'path':ROOT+f'/runs/exp221_{arm}_44b6_s2026_20260921/output/edge_predictor_best.pth',
            'sha256':status['best_sha256'],'selected_epoch':protocol['primary_selected_epochs'][arm],
            'actual_training_plan_sha256':status['contract']['plan_sha256']}
        b.update(evaluation_mode='EXP221_SOURCE_VALIDATION_FIXED8',source_validation_movies=sorted(MOVIES),
                 source_train_movies=audit['secondary_plan']['train'],training_plan_sha256=digest,
                 scope=protocol['scope'])
        bundles[arm]=b
    public=Path('scripts/run_exp214_public_fold.py').read_text()
    old="        assert all(not name.startswith(bundle['source_embryo']+'_') for name in movies),'Target is source embryo'"
    assert public.count(old)==1
    public=public.replace(old,"        from exp221_source_scope import validate_scope\n        validate_scope(bundle,movies)")
    score=Path('scripts/score_exp214_paired.py').read_text()
    score=score.replace("len(movies) in (40,175)","set(movies)==__import__('exp221_source_scope').MOVIES")
    old="            expected=set(part['movies']); assert all(not n.startswith(source+'_') for n in expected)"
    assert old in score
    score=score.replace(old,"            expected=set(part['movies'])\n            from exp221_source_scope import validate_scope\n            validate_scope(receipt['bundle'],part['movies'])")
    score=score.replace("'PASS_HONEST_PAIRED_CV'","'PASS_SOURCE_VALIDATION_PAIRED_GRAPH8'")
    score=score.replace("for prefix in ('44b6','6bba')","for prefix in ('44b6',)")
    driver='''import json,subprocess,sys
from pathlib import Path
c=Path(__file__).parent;r=Path(RUN);out=r/'output';out.mkdir(exist_ok=False)
for arm in ['control','domain']:
 subprocess.check_call([sys.executable,str(c/'run_exp214_public_fold.py'),'--notebook',NOTEBOOK,'--repo',REPO,'--bundle',str(c/(arm+'_bundle.json')),'--data-dir',DATA,'--movies',str(c/'movies.json'),'--output',str(out/arm)])
receipts=[json.loads((out/arm/'inference_receipt.json').read_text()) for arm in ['control','domain']]
assert all(not item['target_labels_read'] for item in receipts)
assert receipts[0]['movies']==receipts[1]['movies']
(out/'status.json').write_text(json.dumps({'status':'PASS_BOTH_SOURCE8_PREDICTIONS_NO_METRICS','target_labels_read':False}))
'''.replace('RUN',repr(RUN)).replace('NOTEBOOK',repr(ROOT+'/code/exp214_inference_v7_20260912/compact47_v20.ipynb')).replace('REPO',repr(ROOT+'/code/exp214_honest_refit_v4_20260912/tracking_repo')).replace('DATA',repr(ROOT+'/data/exp213_source_view_20260912'))
    files={'run_exp214_public_fold.py':public,'run_exp214_paired_fold.py':driver,'score_exp221_source_graph.py':score,
           'exp221_source_scope.py':Path('scripts/exp221_source_scope.py').read_text(),
           'exp214_inference_job.py':Path('scripts/exp214_inference_job.py').read_text(),
           'bound_exp214_submission.py':Path('scripts/bound_exp214_submission.py').read_text(),
           'movies.json':json.dumps(sorted(MOVIES)),'protocol.json':json.dumps(protocol,indent=2)}
    for arm,bundle in bundles.items(): files[arm+'_bundle.json']=json.dumps(bundle,indent=2)
    manifest={'movies':sorted(MOVIES),'training_plan_sha256':digest,'scope':protocol['scope'],
      'arms':{arm:[{'csv':RUN+f'/output/{arm}/submission.csv','receipt':RUN+f'/output/{arm}/inference_receipt.json','movies':sorted(MOVIES)}] for arm in bundles}}
    files['score_manifest.json']=json.dumps(manifest,indent=2)
    src='''import json,hashlib
from pathlib import Path
p=Path(CODE);p.mkdir(exist_ok=False)
for name,source in FILES.items(): (p/name).write_text(source)
manifest={name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in FILES}
(p/'code_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'code':str(p),'manifest':manifest}))
'''.replace('CODE',repr(CODE)).replace('FILES',repr(files))
    result=ssh('nsu-quadro','python3 -',src)
    cfg={'experiment':'EXP221','lease_id':'exp221-source-graph8-20260921','token':'exp221-source-graph8-20260921',
      'gpu':'GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46','cpu_affinity':'0-7','code':CODE,'run':RUN,
      'script':'run_exp214_paired_fold.py','arguments':[],'max_seconds':3600,'lease_minutes':70,
      'remote_monitor':True,'resources':{'cpu':8,'ram_gib':64,'disk_growth_gib':2,'gpus':1},'scope':protocol['scope']}
    Path('reports/exp221_source_graph8_20260921_config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    result.update(protocol=protocol,bundles=bundles,score_manifest=manifest)
    Path('reports/exp221_source_graph8_prepare_20260921.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PREPARED','code':CODE,'primary_hashes':{k:v['primary']['sha256'] for k,v in bundles.items()}}))


if __name__=='__main__':main()
