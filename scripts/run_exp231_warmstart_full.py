"""Two full source-only fine-tuning epochs from pinned Horaz fold1 selected20.

Fixed two-epoch source training candidate. Source inner movies were seen by the published weights;
their validation losses cannot select a generalizing checkpoint.
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace

from exp226_protocol import SourceAccessGuard, sha256
from run_exp226_source_pilot import write_training_report

PARENT_SHA='009c105cc3d745c3fa7e90fdf4c81d041627235274a37003631085c3c929ec53'


def validate(plan, manifest):
    assert plan['experiment']=='EXP231' and plan['purpose']=='warmstart_source_only_full2'
    assert plan['source_embryo']=='44b6' and plan['target_embryo']=='6bba' and plan['fold']==1
    assert plan['parent_sha256']==PARENT_SHA and plan['parent_epoch']==20
    assert plan['learning_rate']==0.00002 and plan['epochs']==2 and plan['iterations_per_epoch'] is None
    assert plan['seed']==3407 and plan['resume'] is False
    assert plan['checkpoint_selection']=='fixed_epoch2_no_outer_selection'
    assert plan['num_workers']==0 and plan['torch_compile'] is False
    train,inner=plan['train'],plan['inner_validation']
    assert len(train)==63 and len(inner)==8
    names=[r['dataset_id'] for r in train+inner]
    assert len(set(names))==71 and all(n.startswith('44b6_') for n in names)
    source={r['dataset_id']:r for r in manifest['train']+manifest['inner_validation']}
    assert len(source)==71
    assert train==manifest['train'] and inner==manifest['inner_validation']
    for row in train+inner:
        assert source[row['dataset_id']]==row
        assert Path(row['zarr_path']).name==row['dataset_id']+'.zarr'
        assert Path(row['geff_path']).name==row['dataset_id']+'.geff'


class WarmstartGuard(SourceAccessGuard):
    def __init__(self,records,output,data_root,parent):
        super().__init__(records,output,data_root)
        self.parent=Path(parent).resolve()

    def check(self,path):
        if isinstance(path,(str,bytes,os.PathLike)) and Path(os.fsdecode(path)).resolve()==self.parent:
            return
        return super().check(path)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('plan',type=Path);ap.add_argument('--plan-sha256',required=True)
    args=ap.parse_args();assert sha256(args.plan)==args.plan_sha256
    plan=json.loads(args.plan.read_text());code=Path(__file__).resolve().parent
    for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
        assert sha256(code/name)==digest,name
    assert sha256(code/'source44_manifest.json')==plan['source_manifest_sha256']
    validate(plan,json.loads((code/'source44_manifest.json').read_text()))
    parent=code/'horaz/fold1_selected.pt';assert sha256(parent)==PARENT_SHA
    out=Path(plan['output']);out.mkdir(exist_ok=False,parents=True)
    sys.path.insert(0,str(code/'horaz/src/src'))
    guard=WarmstartGuard(plan['train']+plan['inner_validation'],out,plan['data_root'],parent)
    sys.addaudithook(guard)
    started=time.time();result={'status':'RUNNING_EXP231_WARMSTART_FULL2',
         'plan_sha256':args.plan_sha256,'parent_sha256':PARENT_SHA,
         'inner_validation_status':'SEEN_BY_PARENT_NOT_HONEST_HOLDOUT'}
    (out/'contract.json').write_text(json.dumps(plan,indent=2))
    try:
        import torch
        reporting=ModuleType('training_report');reporting.write_training_report=write_training_report
        sys.modules['training_report']=reporting
        import train
        from engine import load_checkpoint
        assert torch.cuda.is_available();torch.set_num_threads(8)
        saved=torch.load(parent,map_location='cpu',weights_only=True)
        assert {'model','model_config'}.issubset(saved) and 'optimizer' not in saved
        parent_config=train.ModelConfig.from_dict(saved['model_config'])
        assert all(torch.isfinite(v).all().item() for v in saved['model'].values())
        resolved=json.loads((code/'horaz/resolved_config.json').read_text())
        resolved.update(seed=3407,deterministic=False,epochs=2,learning_rate=0.00002,
                        num_workers=0,torch_compile=False,max_iterations_per_epoch=None,
                        batch_size=4,max_frames=None,output_root=str(out))
        cfg=SimpleNamespace(**resolved)
        assert train.ModelConfig.from_cfg(cfg)==parent_config
        original_build=train.build_model;build_calls=[]
        def warm_build(model_config):
            assert model_config==parent_config
            model=original_build(model_config)
            model.load_state_dict(saved['model'],strict=True)
            build_calls.append(True)
            return model
        train.build_model=warm_build
        train.PERIODIC_EPOCHS=(1,2)
        checkpoint=train.train_fold(cfg,1,plan['train'],plan['inner_validation'],out,resolved,resume=False)
        assert len(build_calls)==1
        history=json.loads((out/'fold1/history.json').read_text())
        assert [row['epoch'] for row in history]==[1,2]
        assert all(row['training_iterations']>8 for row in history)
        assert all(math.isfinite(v) for row in history for v in row.values() if isinstance(v,(int,float)))
        model,model_config=load_checkpoint(checkpoint,torch.device('cpu'))
        assert model_config==parent_config
        changed=sum(not torch.equal(v.cpu(),saved['model'][name]) for name,v in model.state_dict().items())
        assert changed>0 and all(torch.isfinite(v).all().item() for v in model.parameters())
        assert guard.opened_ids==guard.allowed_ids and not guard.denied
        result.update(status='PASS_EXP231_WARMSTART_FULL2',elapsed_seconds=time.time()-started,
                      checkpoint_sha256=sha256(checkpoint),checkpoint_reload='PASS_weights_only',
                      fresh_optimizer=True,changed_tensors=changed,history=history,
                      no_generalization_claim=True)
    except BaseException as exc:
        result.update(status='FAILED_EXP231_WARMSTART_FULL2',error=repr(exc),
                      elapsed_seconds=time.time()-started)
        raise
    finally:
        result.update(opened_datasets=sorted(guard.opened_ids),denied_accesses=guard.denied,
                      target_data_opened=False if not guard.denied else 'attempt_blocked')
        (out/'result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)


if __name__=='__main__':main()
