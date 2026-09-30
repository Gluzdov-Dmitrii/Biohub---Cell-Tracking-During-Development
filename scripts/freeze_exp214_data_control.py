"""Freeze one source-only single-detector control, validating its fixed milestone."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--arm',choices=('full12','reduced12','reduced60'),required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.arm=='full12':
        model=a.root/'models/exp214_full_control_12epoch_20260912/edge_predictor_best.pth'
        expected='2d929a856c317208e30056e38f5f74d7ffc91be36b27e217e596ffc210d4dcc4'
        plan='99258515deb4906af43c0231432adeedfb5819077b1e03460e40b424a121e5fe'
    else:
        is60=a.arm=='reduced60'
        run=a.root/('runs/exp214_equal_time44b6_s2026_20260912/output' if is60 else 'runs/exp214_reduced44b6_s2026_20260912/output')
        status=json.loads((run/'status.json').read_text())
        plan=('9b1fd764a4571669d0ed7c51ea4e8f4a3cdd49d455ae8af957413b45c9e398e3' if is60 else '983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a')
        assert status['status']=='COMPLETE_SOURCE_REFIT' and status['epoch']==status['total_epochs']==(60 if is60 else 12)
        assert status['contract']['plan_sha256']==plan and status['contract']['fold']=='44b6' and status['contract']['seed']==2026
        assert status['target_data_opened'] is False
        model=run/'edge_predictor_best.pth';expected=status['best_sha256']
        if not is60:assert expected=='f8e25074a98b651a64740ce9ab013ac957fb8d61462d9c7df982efb4db8e8605'
    assert sha(model)==expected and (model.parent/'config.json').is_file()
    center=a.root/'runs/exp180_reciprocal_deepcenter_training_20260910/output/44b6/best.pt'
    center_sha='ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f'
    assert sha(center)==center_sha
    detector={'path':str(model),'sha256':expected}
    bundle={'purpose':'EVALUATION_DATA_REDUCTION_CONTROL','source_embryo':'44b6','control':a.arm,
            'training_plan_sha256':plan,'primary':detector,'secondary':detector,
            'center':{'path':str(center),'sha256':center_sha}}
    with a.output.open('x') as f:json.dump(bundle,f,indent=2);f.write('\n')
    print(json.dumps(bundle,indent=2))

if __name__=='__main__':main()
