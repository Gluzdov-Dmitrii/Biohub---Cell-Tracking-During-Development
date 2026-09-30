"""Freeze one completed reciprocal evaluation bundle before opening target metrics."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--fold',choices=['44b6','6bba'],required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();plan=json.loads(a.plan.read_text())
    result={'purpose':'EVALUATION','source_embryo':a.fold,'training_plan_sha256':sha(a.plan)}
    for role,seed in (('primary',2026),('secondary',314159)):
        run=a.root/f'runs/exp214_reduced{a.fold}_s{seed}_20260912/output';status=json.loads((run/'status.json').read_text())
        assert status['status']=='COMPLETE_SOURCE_REFIT' and status['epoch']==status['total_epochs']==12
        assert status['contract']['plan_sha256']==sha(a.plan) and status['target_data_opened'] is False
        assert status['contract']['fold']==a.fold and status['contract']['seed']==seed
        assert sha(run/'edge_predictor_best.pth')==status['best_sha256']
        result[role]={'path':str(run/'edge_predictor_best.pth'),'sha256':status['best_sha256'],
            'training_status_sha256':sha(run/'status.json'),'seed':seed,'epochs':12}
    center=a.root/f'runs/exp180_reciprocal_deepcenter_training_20260910/output/{a.fold}/best.pt'
    assert sha(center)==plan['center']['source'+a.fold+'_sha256']
    result['center']={'path':str(center),'sha256':sha(center),'provenance':'EXP180 source-only teacher'}
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
