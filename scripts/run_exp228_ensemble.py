"""Fixed same-fold Horaz e20/e50 ensemble: no labels, training or weight sweep."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

WEIGHTS = {
    'selected/fold1_selected.pt': '009c105cc3d745c3fa7e90fdf4c81d041627235274a37003631085c3c929ec53',
    'fixed_last/fold1_last.pt': '71cd74068a8a865a7ffb8edeca51f9ccb34e5dcc0815fb0b68c77668874beceb',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(plan):
    assert plan['experiment'] == 'EXP228' and plan['mode'] == 'heldout_same_fold_ensemble'
    assert plan['weights'] == WEIGHTS and plan['mixture'] == [0.5,0.5]
    chunks=plan.get('chunk_count',4)
    assert chunks in (4,8) and plan['chunk'] in range(chunks)
    expected=(116-plan['chunk']+chunks-1)//chunks
    assert len(plan['rows']) == expected
    names = [r['dataset'] for r in plan['rows']]
    assert len(set(names)) == expected
    for row in plan['rows']:
        assert row['dataset'].startswith('6bba_') and row['fold'] == 1, 'Wrong heldout direction'
        assert Path(row['zarr']).name == row['dataset']+'.zarr', 'Dataset/path mismatch'
        assert len(row['shape']) == 4 and all(isinstance(v,int) and v > 0 for v in row['shape'])


def main():
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('--plan-sha256',required=True)
    args=p.parse_args();assert sha(args.plan)==args.plan_sha256
    plan=json.loads(args.plan.read_text());validate_plan(plan)
    code=Path(__file__).resolve().parent
    for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
        assert sha(code/name)==digest,name
    for name,digest in WEIGHTS.items():assert sha(code/name)==digest,name
    cohort=json.loads((code/'heldout175_manifest.json').read_text())['rows']
    assert sha(code/'heldout175_manifest.json')==plan['cohort_sha256']
    by_name={r['dataset']:r for r in cohort};assert len(by_name)==175
    assert all(by_name[r['dataset']]==r for r in plan['rows'])
    ordered=sorted([r for r in cohort if r['fold']==1],key=lambda r:hashlib.sha256(('EXP228-chunks-v1:'+r['dataset']).encode()).hexdigest())
    assert plan['rows']==ordered[plan['chunk']::plan.get('chunk_count',4)], 'Changed frozen partition'
    out=Path(plan['output']);out.mkdir(parents=True,exist_ok=False)
    def no_labels(event, args):
        if event=='open' and args and isinstance(args[0],(str,bytes)) and '.geff' in str(args[0]).lower():
            raise PermissionError('EXP228 prohibits label access')
    sys.addaudithook(no_labels)
    sys.path.insert(0,str(code/'selected/src/src'))
    import torch
    from engine import load_checkpoint,predict_graph_ensemble
    from inference import write_submission
    from settings import DetectionConfig,AssignmentConfig,PostprocessConfig
    from run_exp223_inference import verify_csv,atomic_json
    assert torch.cuda.is_available()
    cfg=SimpleNamespace(**json.loads((code/'selected/resolved_config.json').read_text()))
    loaded=[load_checkpoint(code/name,torch.device('cuda')) for name in WEIGHTS]
    model_configs=[config for model,config in loaded]
    assert model_configs[0]==model_configs[1]
    models=[model for model,config in loaded];records=[];started=time.time()
    for row in plan['rows']:
        t0=time.time()
        graph,stats=predict_graph_ensemble(models,Path(row['zarr']),torch.device('cuda'),model_configs[0],
                     DetectionConfig.from_cfg(cfg),AssignmentConfig.from_cfg(cfg),PostprocessConfig.from_cfg(cfg),max_frames=None)
        path=out/('ensemble__'+row['dataset']+'.csv');temporary=path.with_suffix('.tmp')
        write_submission([(row['dataset'],graph)],temporary)
        counts=verify_csv(temporary,row);temporary.replace(path)
        record={'dataset':row['dataset'],'fold':1,'source_embryo':'44b6','target_embryo':'6bba',
                'csv':str(path),'csv_sha256':sha(path),'shape':row['shape'],'weights':WEIGHTS,
                'mixture':[0.5,0.5],'seconds':time.time()-t0,'plan_sha256':args.plan_sha256,
                'decoder_sha256':sha(code/'selected/resolved_config.json'),'stats':stats,**counts}
        atomic_json(path.with_suffix('.json'),record);records.append(record)
        print(json.dumps({k:record[k] for k in ('dataset','seconds','nodes','edges')}),flush=True)
    atomic_json(out/'complete.json',{'status':'PASS_EXP228_NO_LABEL_CHUNK','chunk':plan['chunk'],
                'n_movies':len(records),'records':records,'elapsed_seconds':time.time()-started,
                'no_target_labels':True,'private_quality_unknown':True})
    print(json.dumps({'status':'PASS_EXP228_NO_LABEL_CHUNK','n_movies':len(records),'seconds':time.time()-started}),flush=True)


if __name__=='__main__':main()
