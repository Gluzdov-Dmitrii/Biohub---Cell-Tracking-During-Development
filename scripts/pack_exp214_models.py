"""Package only four completed clean refits, two clean centers and verified inference code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for k in ('root','plan','code','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();assert a.output.resolve().is_relative_to(a.root/'models')
    plan=json.loads(a.plan.read_text());plan_sha=sha(a.plan);inputs={};folds={}
    for fold in ('44b6','6bba'):
        folds[fold]={}
        for role,seed in (('primary',2026),('secondary',314159)):
            run=a.root/f'runs/exp214_reduced{fold}_s{seed}_20260912/output'
            status=json.loads((run/'status.json').read_text())
            assert status['status']=='COMPLETE_SOURCE_REFIT' and status['epoch']==status['total_epochs']==12
            assert status['target_data_opened'] is False
            assert status['contract']['plan_sha256']==plan_sha and status['contract']['fold']==fold and status['contract']['seed']==seed
            assert status['best_sha256']==sha(run/'edge_predictor_best.pth')
            relative=f'models/{fold}/{role}/edge_predictor_best.pth';folds[fold][role]=relative
            for name in ('edge_predictor_best.pth','config.json','status.json','history.json'):
                inputs[f'models/{fold}/{role}/{name}']=run/name
        center=a.root/f'runs/exp180_reciprocal_deepcenter_training_20260910/output/{fold}/best.pt'
        assert sha(center)==plan['center']['source'+fold+'_sha256']
        relative=f'models/{fold}/center/best.pt';folds[fold]['center']=relative;inputs[relative]=center
    code_manifest=json.loads((a.code/'code_manifest.json').read_text())
    for name,digest in code_manifest.items():
        assert sha(a.code/name)==digest,name;inputs['code/'+name]=a.code/name
    inputs['training_plan.json']=a.plan
    a.output.mkdir(parents=True,exist_ok=False)
    for name,source in inputs.items():
        target=a.output/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        assert sha(target)==sha(source),name
    manifest={'status':'PASS_FOUR_COMPLETE_CLEAN_REDUCED_REFITS','training_plan_sha256':plan_sha,
        'folds':folds,'files':{name:sha(a.output/name) for name in inputs},
        'scope':'12epoch source-only refit; not OOF of public400epoch weights. Center is clean EXP180 full teacher.',
        'training_input_bytes':2893336649,'unknown_embryo_selector_oof':None}
    (a.output/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':manifest['status'],'bytes':sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file()),'manifest_sha256':sha(a.output/'artifact_manifest.json')}))


if __name__=='__main__':main()
