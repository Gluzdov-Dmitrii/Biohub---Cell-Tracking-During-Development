"""EXP214 reduced-data reciprocal refit: dynamic hidden-test production.

GRAPH_FAMILY is frozen separately for the two preregistered diagnostics.
No OOF value is assigned to routing of previously unseen embryo prefixes.
"""
from pathlib import Path
import csv
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

GRAPH_FAMILY = 'local'
COMPETITION='biohub-cell-tracking-during-development'
WORK=Path('/kaggle/working')
INPUT=Path('/kaggle/input')


def locate(owner,slug):
    candidates=[INPUT/'datasets'/owner/slug,INPUT/slug]
    present=[p for p in candidates if p.is_dir()]
    assert len(present)==1,(owner,slug,present)
    return present[0]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


SUPPORT=locate('pilkwang','biohub-tracking-support-pack-50ep-v1')
ARTIFACTS=locate('dmitriigluzdov','biohub-exp214-reduced-honest-fold-models')
manifest=json.loads((ARTIFACTS/'artifact_manifest.json').read_text())
for name,expected in manifest['files'].items():assert sha(ARTIFACTS/name)==expected,name
numeric=('numpy','scipy','numba','llvmlite','torch')
before={n:importlib.metadata.version(n) for n in numeric}
subprocess.check_call([sys.executable,'-m','pip','install','--quiet','--no-index','--no-deps',
    '--force-reinstall','--find-links',str(SUPPORT/'wheels'),'-r',str(SUPPORT/'requirements-unet-ilp-kaggle-predownload.txt')])
assert before=={n:importlib.metadata.version(n) for n in numeric}
import numpy as np
from scipy.spatial import cKDTree
sys.path[:0]=[str(ARTIFACTS/'code'),str(SUPPORT/'repo/src'),str(SUPPORT/'repo/scripts')]
from score_exp214_paired import read_graphs,COLUMNS
from biohub_tracking.io import open_dataset
test_options=[INPUT/'competitions'/COMPETITION/'test',INPUT/COMPETITION/'test']
TEST=next(p for p in test_options if p.is_dir())
paths=sorted(TEST.glob('*.zarr'));assert paths
assert len(paths)==len({p.stem for p in paths})
os.environ['OMP_NUM_THREADS']='4';os.environ['MKL_NUM_THREADS']='4';os.environ['PYTHONDONTWRITEBYTECODE']='1'
fold_outputs={};public_graphs={};final_graphs={}; receipts=[]
import torch
visible=os.environ.get('CUDA_VISIBLE_DEVICES')
devices=visible.split(',') if visible else [str(i) for i in range(torch.cuda.device_count())]
assert devices and torch.cuda.device_count()>=1
devices=devices[:min(2,torch.cuda.device_count())]
fold_times={}


def run_source(source,device):
    started=time.monotonic()
    child_env=dict(os.environ,CUDA_VISIBLE_DEVICES=device)
    movies=[p.stem for p in paths if p.stem.split('_',1)[0]!=source]
    if not movies:return
    bundle={'source_embryo':source,'training_plan_sha256':manifest['training_plan_sha256']}
    for role in ('primary','secondary','center'):
        relative=manifest['folds'][source][role]
        bundle[role]={'path':str(ARTIFACTS/relative),'sha256':manifest['files'][relative]}
    bp=WORK/(source+'_bundle.json');bp.write_text(json.dumps(bundle))
    mp=WORK/(source+'_movies.json');mp.write_text(json.dumps(movies))
    output=WORK/('public_'+source)
    subprocess.check_call([sys.executable,str(ARTIFACTS/'code/run_exp214_public_fold.py'),
        '--notebook',str(ARTIFACTS/'code/compact47_v20.ipynb'),'--repo',str(SUPPORT/'repo'),
        '--bundle',str(bp),'--data-dir',str(TEST),'--movies',str(mp),'--output',str(output)],env=child_env)
    public_graphs[source]=read_graphs(output/'submission.csv')
    if GRAPH_FAMILY=='local':
        local=WORK/('local_'+source)
        subprocess.check_call([sys.executable,str(ARTIFACTS/'code/run_exp214_local_graph.py'),
            '--repo',str(SUPPORT/'repo'),'--data',str(TEST),'--bundle',str(bp),
            '--movies',str(mp),'--candidates',str(output/'candidates'),'--output',str(local)],env=child_env)
        final_graphs[source]=read_graphs(local/'submission.csv')
        (local/'submission.csv').rename(local/'predictions.csv')
    else:
        assert GRAPH_FAMILY=='public';final_graphs[source]=public_graphs[source]
    receipts.append(json.loads((output/'inference_receipt.json').read_text()))
    (output/'submission.csv').rename(output/'predictions.csv')
    # These are owned temporary links, not copies or deletions of test images.
    runtime_view=output/'runtime_test'
    for link in runtime_view.iterdir():
        assert link.is_symlink() and link.resolve().is_relative_to(TEST.resolve())
        link.unlink()
    runtime_view.rmdir()
    fold_times[source]={'device':device,'elapsed_seconds':time.monotonic()-started}


with ThreadPoolExecutor(max_workers=len(devices)) as pool:
    jobs=[pool.submit(run_source,source,devices[i%len(devices)]) for i,source in enumerate(('44b6','6bba'))]
    for job in jobs:job.result()
(WORK/'exp214_fold_runtime.json').write_text(json.dumps(fold_times,indent=2)+'\n')


def choose(name,scale):
    prefix=name.split('_',1)[0]
    if prefix in ('44b6','6bba'):return ('6bba' if prefix=='44b6' else '44b6'),{'rule':'reciprocal_known_embryo'}
    graphs=[public_graphs[f][name] for f in ('44b6','6bba')]
    coords=[np.asarray(list(g['nodes'].values()),dtype=float).reshape((-1,4)) for g in graphs]
    matched=0
    for t in sorted(set(coords[0][:,0])&set(coords[1][:,0])):
        a=coords[0][coords[0][:,0]==t,1:]*scale;b=coords[1][coords[1][:,0]==t,1:]*scale
        d,ab=cKDTree(b).query(a);_,ba=cKDTree(a).query(b)
        matched+=sum(float(distance)<2. and int(ba[int(j)])==i for i,(distance,j) in enumerate(zip(d,ab)))
    keys=[(matched/max(len(c),1),len(g['edges'])/max(len(c),1),-len(c)) for c,g in zip(coords,graphs)]
    source='44b6' if keys[0]>=keys[1] else '6bba'
    return source,{'rule':'frozen_public_graph_agreement_then_continuity','keys':keys,'mutual_matches_2um':matched,'oof_claim':None}


selections=[];idx=0
with (WORK/'submission.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(COLUMNS)
    for path in paths:
        ds=open_dataset(path,require_tracks=False,load_image=False)
        source,decision=choose(path.stem,np.asarray(ds.scale));graph=final_graphs[source][path.stem]
        for node,(t,z,y,x) in sorted(graph['nodes'].items()):
            assert all(0<=v<s for v,s in zip((t,z,y,x),ds.image_shape))
            writer.writerow([idx,path.stem,'node',node,t,format(z,'.17g'),format(y,'.17g'),format(x,'.17g'),-1,-1]);idx+=1
        for s,t in sorted(graph['edges']):
            writer.writerow([idx,path.stem,'edge',-1,-1,-1,-1,-1,s,t]);idx+=1
        selections.append({'dataset':path.stem,'source':source,**decision})
assert set(read_graphs(WORK/'submission.csv'))=={p.stem for p in paths}
receipt={'status':'PASS_FULL_INFERENCE','graph_family':GRAPH_FAMILY,'runtime_datasets':[p.stem for p in paths],
    'submission_sha256':sha(WORK/'submission.csv'),'rows':idx,'selections':selections,
    'artifact_manifest_sha256':sha(ARTIFACTS/'artifact_manifest.json'),'source_sha256':sha(__file__),
    'numerical_stack':before,'fold_receipts':receipts,'unknown_embryo_selector_oof':None}
(WORK/'exp214_runtime_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='fold_receipts'}),flush=True)
