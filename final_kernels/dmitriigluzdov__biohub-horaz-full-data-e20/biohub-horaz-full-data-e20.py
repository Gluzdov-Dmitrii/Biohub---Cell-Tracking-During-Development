"""Horaz full-data, one-checkpoint runtime inference candidate template.

This template is intentionally unconfigured. materialize.py inserts an exact
E10 or E20 checkpoint identity only after a full-data training receipt exists.
"""
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time
from types import SimpleNamespace

COMPETITION = 'biohub-cell-tracking-during-development'
ZIP_SHA = '2e36047d0c800b4c93f82f3833571daea8c721ec4e8d685cd2aa9051b9dc22e2'
SOURCE_MANIFEST_SHA = '905da64804359b4213cb4596db74c321a77290d22d297068939f574863d633d1'
SOURCE_FILE_NAMES = (
    'src/assignment.py', 'src/base_config.py', 'src/config_loader.py',
    'src/configs/cfg_embryo_cv.py', 'src/const.py', 'src/cv.py',
    'src/datasets.py', 'src/detection.py', 'src/engine.py',
    'src/inference.py', 'src/losses.py', 'src/metric.py',
    'src/models/node_transformer.py', 'src/models/temporal_unet.py',
    'src/models/tracker.py', 'src/official_competition_metric.py',
    'src/postprocess.py', 'src/settings.py', 'src/train.py',
    'src/training_report.py', 'src/utils.py',
)
CANDIDATE_CONFIG = {'epoch': 20, 'checkpoint_name': 'full_epoch20.pt', 'checkpoint_sha256': '021b8c533c50a8a5c67ee0e7ede1b8834296c95d56adcdffc0967f0c5cc59090', 'asset_slug': 'biohub-horaz-full-data-e20-20260928', 'asset_manifest_sha256': 'f46050b0ab7f0f26cf15ad2a8039cd5ca537616894941df4d16b486c10e20fc2', 'training_receipt_sha256': '107442043cee38c232a823a8dbb6cc49c2d51d104434c8aa56f7558958dea4c6'}
COLUMNS = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']

def require_candidate_config():
    c = CANDIDATE_CONFIG
    if not isinstance(c, dict) or c.get('epoch') not in (10, 20):
        raise RuntimeError('Full-data candidate is unmaterialized')
    if c.get('checkpoint_name') != f"full_epoch{c['epoch']}.pt":
        raise RuntimeError('Checkpoint name/epoch mismatch')
    if c.get('asset_slug') != f"biohub-horaz-full-data-e{c['epoch']}-20260928":
        raise RuntimeError('Asset slug/epoch mismatch')
    for field in ('checkpoint_sha256', 'asset_manifest_sha256', 'training_receipt_sha256'):
        value = c.get(field)
        if not isinstance(value, str) or len(value) != 64 or any(x not in '0123456789abcdef' for x in value):
            raise RuntimeError(f'Missing or invalid {field}')
    return c

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def locate(owner, slug):
    paths = [Path('/kaggle/input/datasets') / owner / slug, Path('/kaggle/input') / slug]
    found = [p for p in paths if p.is_dir()]
    if len(found) != 1:
        raise RuntimeError(f'Ambiguous or missing input {owner}/{slug}: {found}')
    return found[0]

def discover_test(root):
    paths = sorted((Path(root) / 'test').glob('*.zarr'))
    if not paths or len({p.stem for p in paths}) != len(paths):
        raise RuntimeError('No unique runtime test Zarr inputs')
    return paths

def audit_csv(path, shapes):
    nodes = {d:{} for d in shapes}
    edges = {d:[] for d in shapes}
    row_count = 0
    with Path(path).open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            raise ValueError('CSV column mismatch')
        for i,r in enumerate(reader):
            d = r['dataset']
            if d not in shapes:
                raise ValueError('Unexpected dataset')
            v = {k:int(r[k]) for k in COLUMNS if k not in ('dataset','row_type')}
            if v['id'] != i:
                raise ValueError('Noncontiguous row IDs')
            if r['row_type'] == 'node':
                n=v['node_id'];point=tuple(v[k] for k in ('t','z','y','x'))
                if n < 0 or n in nodes[d] or not all(0<=x<s for x,s in zip(point,shapes[d])):
                    raise ValueError('Node identity or bounds failure')
                if (v['source_id'],v['target_id']) != (-1,-1):
                    raise ValueError('Invalid node sentinels')
                nodes[d][n]=point
            elif r['row_type'] == 'edge':
                if any(v[k] != -1 for k in ('node_id','t','z','y','x')):
                    raise ValueError('Invalid edge sentinels')
                edges[d].append((v['source_id'],v['target_id']))
            else:
                raise ValueError('Unknown row type')
            row_count += 1
    stats={}
    for d in shapes:
        if not nodes[d] or len(edges[d]) != len(set(edges[d])):
            raise ValueError('Empty dataset or duplicate edges')
        inc={};out={}
        for s,t in edges[d]:
            if s not in nodes[d] or t not in nodes[d] or nodes[d][t][0] != nodes[d][s][0]+1:
                raise ValueError('Invalid edge endpoint or time')
            inc[t]=inc.get(t,0)+1;out[s]=out.get(s,0)+1
        if max(inc.values(),default=0)>1 or max(out.values(),default=0)>2:
            raise ValueError('Invalid graph degrees')
        stats[d]={'nodes':len(nodes[d]),'edges':len(edges[d]),'shape':list(shapes[d])}
    return {'rows':row_count,'datasets':stats,'sha256':sha(path)}

def predict_all(paths, loaded, cfg, device, read_metadata, predict_one):
    """Infer every discovered Zarr with the same full-data checkpoint."""
    predictions=[];shapes={};records=[]
    for path in paths:
        t0=time.time()
        shapes[path.stem]=read_metadata(path)[0]
        graph,stats=predict_one(*loaded,path,device,cfg,None)
        if not graph.nodes:
            raise RuntimeError('No output nodes for '+path.stem)
        predictions.append((path.stem,graph))
        record={'dataset':path.stem,'checkpoint':require_candidate_config()['checkpoint_name'],'shape':shapes[path.stem],'seconds':time.time()-t0,'stats':stats}
        records.append(record);print(json.dumps(record),flush=True)
    return predictions,shapes,records

def main():
    if not __debug__:
        raise RuntimeError('Assertions must be enabled')
    started=time.time()
    candidate=require_candidate_config()
    assets=locate('dmitriigluzdov',candidate['asset_slug'])
    support=locate('pilkwang','biohub-tracking-support-pack-50ep-v1')
    assert sha(assets/'asset_manifest.json') == candidate['asset_manifest_sha256']
    if (assets/'horaz_source.zip').is_file():
        assert sha(assets/'horaz_source.zip') == ZIP_SHA
    assert sha(assets/'training_receipt.json') == candidate['training_receipt_sha256']
    manifest=json.loads((assets/'asset_manifest.json').read_text())
    assert manifest['epoch'] == candidate['epoch']
    assert manifest['checkpoint_sha256'] == candidate['checkpoint_sha256']
    assert manifest['training_receipt_sha256'] == candidate['training_receipt_sha256']
    assert set(manifest['files']) == set(SOURCE_FILE_NAMES) | {candidate['checkpoint_name']}
    assert manifest['files'][candidate['checkpoint_name']] == candidate['checkpoint_sha256']
    assert manifest['parent_asset_manifest_sha256'] == SOURCE_MANIFEST_SHA
    assert manifest['source_zip_sha256'] == ZIP_SHA
    code=Path('/kaggle/working/horaz_code')
    # Kaggle unpacks uploaded ZIPs into a directory named after the archive.
    shutil.copytree(assets/'horaz_source',code)
    for name,digest in manifest['files'].items():
        assert sha(code/name if name.startswith('src/') else assets/name)==digest,name
    numeric=('numpy','scipy','torch')
    before={n:importlib.metadata.version(n) for n in numeric}
    subprocess.check_call([sys.executable,'-m','pip','install','--quiet','--no-index','--no-deps','--force-reinstall','--find-links',str(support/'wheels'),'-r',str(support/'requirements-unet-ilp-kaggle-predownload.txt')])
    assert before=={n:importlib.metadata.version(n) for n in numeric}
    os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0,str(code/'src'))
    import torch
    from engine import load_checkpoint
    from inference import predict_one, write_submission
    from datasets import read_zarr_metadata
    assert torch.cuda.is_available()
    torch.set_num_threads(4)
    device=torch.device('cuda')
    roots=[p for p in [Path('/kaggle/input/competitions')/COMPETITION,Path('/kaggle/input')/COMPETITION] if (p/'test').is_dir()]
    assert len(roots)==1,roots
    root=roots[0];paths=discover_test(root);allowed={p.resolve() for p in paths}
    def no_labels(event,args):
        if event not in ('open','os.listdir','os.scandir') or not args or not isinstance(args[0],(str,bytes,os.PathLike)):
            return
        p=Path(os.fsdecode(args[0])).resolve()
        if any(s.lower().endswith('.geff') for s in p.parts) or p.is_relative_to(root/'train'):
            raise PermissionError('Runtime inference forbids labels/train inputs')
        if p.name=='submission.csv' and p.is_relative_to(Path('/kaggle/input')):
            raise PermissionError('Runtime inference forbids frozen output replay')
        for parent in (p,*p.parents):
            if parent.suffix=='.zarr' and parent not in allowed:
                raise PermissionError('Image outside runtime test set')
    sys.addaudithook(no_labels)
    checkpoint_path=assets/candidate['checkpoint_name']
    assert sha(checkpoint_path) == candidate['checkpoint_sha256']
    checkpoint=torch.load(checkpoint_path,map_location='cpu',weights_only=True)
    assert checkpoint['epoch'] == candidate['epoch']
    assert len(checkpoint['history']) == candidate['epoch']
    assert checkpoint['history'][-1]['epoch'] == candidate['epoch']
    raw_config=checkpoint['resolved_config']
    assert raw_config['seed'] == 3407
    cfg=SimpleNamespace(**raw_config);del checkpoint
    loaded=load_checkpoint(checkpoint_path,device)
    predictions,shapes,records=predict_all(paths,loaded,cfg,device,read_zarr_metadata,predict_one)
    output=Path('/kaggle/working/submission.csv')
    assert not output.exists()
    write_submission(predictions,output)
    audit=audit_csv(output,shapes)
    assert len([p for p in Path('/kaggle/working').iterdir() if p.name=='submission.csv' and p.is_file()])==1
    report={'status':'PASS_FULL_INFERENCE','kernel':f"biohub-horaz-full-data-e{candidate['epoch']}-20260928",'epoch':candidate['epoch'],'checkpoint_sha256':candidate['checkpoint_sha256'],'training_receipt_sha256':candidate['training_receipt_sha256'],'asset_manifest_sha256':candidate['asset_manifest_sha256'],'source_zip_sha256':ZIP_SHA,'runtime_test_root':str(root),'runtime_test_ids':[p.stem for p in paths],'audit':audit,'records':records,'elapsed_seconds':time.time()-started,'versions':{n:importlib.metadata.version(n) for n in ('numpy','scipy','torch','tracksdata','zarr','polars')},'policy':'single full-data checkpoint for every runtime test Zarr; no epoch selection by LB'}
    Path('/kaggle/working/horaz_runtime_report.json').write_text(json.dumps(report,indent=2,default=str))
    print('PASS_FULL_INFERENCE '+json.dumps(audit),flush=True)

if __name__=='__main__':
    main()
