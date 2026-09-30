"""EXP219: frozen90/60 public graph, single predeclared source per runtime movie.
Known embryos use reciprocal clean folds; unseen embryos use source6bba,
the larger source training cohort. No OOF claim for unseen routing.
"""
from pathlib import Path
import csv,hashlib,importlib.metadata,json,os,subprocess,sys,time
from concurrent.futures import ThreadPoolExecutor
COMPETITION='biohub-cell-tracking-during-development'
WORK=Path('/kaggle/working');INPUT=Path('/kaggle/input')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def locate(owner,slug):
    found=[p for p in (INPUT/'datasets'/owner/slug,INPUT/slug) if p.is_dir()]
    assert len(found)==1,(owner,slug,found)
    return found[0]
SUPPORT=locate('pilkwang','biohub-tracking-support-pack-50ep-v1')
ARTIFACTS=locate('dmitriigluzdov','biohub-exp219-frontier90-models')
manifest=json.loads((ARTIFACTS/'artifact_manifest.json').read_text())
for name,digest in manifest['files'].items():assert sha(ARTIFACTS/name)==digest,name
numeric=('numpy','scipy','numba','llvmlite','torch')
before={n:importlib.metadata.version(n) for n in numeric}
subprocess.check_call([sys.executable,'-m','pip','install','--quiet','--no-index','--no-deps','--force-reinstall','--find-links',str(SUPPORT/'wheels'),'-r',str(SUPPORT/'requirements-unet-ilp-kaggle-predownload.txt')])
assert before=={n:importlib.metadata.version(n) for n in numeric}
os.environ.update(OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
sys.path[:0]=[str(ARTIFACTS/'code'),str(SUPPORT/'repo/src'),str(SUPPORT/'repo/scripts')]
import numpy as np
import torch
from score_exp214_paired import read_graphs,COLUMNS
from biohub_tracking.io import open_dataset
TEST=next(p for p in (INPUT/'competitions'/COMPETITION/'test',INPUT/COMPETITION/'test') if p.is_dir())
paths=sorted(TEST.glob('*.zarr'));assert paths
assert len(paths)==len({p.stem for p in paths})
def source_for(name):return '44b6' if name.startswith('6bba_') else '6bba'
shapes={p.stem:tuple(open_dataset(p,require_tracks=False,load_image=False).image_shape) for p in paths}
visible=os.environ.get('CUDA_VISIBLE_DEVICES')
devices=visible.split(',') if visible else [str(i) for i in range(torch.cuda.device_count())]
devices=devices[:min(2,torch.cuda.device_count())];assert devices
lanes=[[] for _ in devices];loads=[0]*len(devices)
for path in sorted(paths,key=lambda p:(-int(np.prod(shapes[p.stem])),p.stem)):
    lane=min(range(len(devices)),key=lambda i:(loads[i],i))
    lanes[lane].append(path.stem);loads[lane]+=int(np.prod(shapes[path.stem]))
def run_lane(index):
    started=time.monotonic();records=[];graphs={}
    for source in ('44b6','6bba'):
        movies=sorted(n for n in lanes[index] if source_for(n)==source)
        if not movies:continue
        bundle={'source_embryo':source,'training_plan_sha256':manifest['training_plan_sha256']}
        for role in ('primary','secondary','center'):
            name=manifest['folds'][source][role];bundle[role]={'path':str(ARTIFACTS/name),'sha256':manifest['files'][name]}
        tag=f'lane{index}_{source}'
        bp=WORK/(tag+'_bundle.json');bp.write_text(json.dumps(bundle))
        mp=WORK/(tag+'_movies.json');mp.write_text(json.dumps(movies))
        out=WORK/tag
        subprocess.check_call([sys.executable,str(ARTIFACTS/'code/run_exp214_public_fold.py'),'--notebook',str(ARTIFACTS/'code/compact47_v20.ipynb'),'--repo',str(SUPPORT/'repo'),'--bundle',str(bp),'--data-dir',str(TEST),'--movies',str(mp),'--output',str(out)],env=dict(os.environ,CUDA_VISIBLE_DEVICES=devices[index]))
        got=read_graphs(out/'submission.csv');assert set(got)==set(movies)
        graphs.update(got);records.append(json.loads((out/'inference_receipt.json').read_text()))
        (out/'submission.csv').rename(out/'predictions.csv')
        for link in (out/'runtime_test').iterdir():
            assert link.is_symlink() and link.resolve().is_relative_to(TEST.resolve());link.unlink()
        (out/'runtime_test').rmdir()
    return graphs,records,{'lane':index,'device':devices[index],'movies':lanes[index],'elapsed_seconds':time.monotonic()-started}
all_graphs={};receipts=[];timings=[]
with ThreadPoolExecutor(max_workers=len(devices)) as pool:
    for graphs,records,timing in pool.map(run_lane,range(len(devices))):
        assert not set(all_graphs)&set(graphs)
        all_graphs.update(graphs);receipts.extend(records);timings.append(timing)
assert set(all_graphs)=={p.stem for p in paths}
idx=0;selections=[]
with (WORK/'submission.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(COLUMNS)
    for path in paths:
        graph=all_graphs[path.stem]
        assert graph['nodes'],('No predicted nodes',path.stem)
        for node,(t,z,y,x) in sorted(graph['nodes'].items()):
            assert all(0<=v<s for v,s in zip((t,z,y,x),shapes[path.stem]))
            writer.writerow([idx,path.stem,'node',int(node),int(t),format(z,'.17g'),format(y,'.17g'),format(x,'.17g'),-1,-1]);idx+=1
        for source,target in sorted(graph['edges']):
            writer.writerow([idx,path.stem,'edge',-1,-1,-1,-1,-1,int(source),int(target)]);idx+=1
        selections.append({'dataset':path.stem,'source':source_for(path.stem),'rule':'reciprocal_known_else_larger_source6bba','oof_claim':None})
assert set(read_graphs(WORK/'submission.csv'))==set(all_graphs)
assert list(WORK.rglob('submission.csv'))==[WORK/'submission.csv']
receipt={'status':'PASS_FULL_INFERENCE','graph_family':'public','runtime_datasets':sorted(all_graphs),'submission_sha256':sha(WORK/'submission.csv'),'rows':idx,'selections':selections,'runtime_shapes':shapes,'artifact_manifest_sha256':sha(ARTIFACTS/'artifact_manifest.json'),'source_sha256':sha(__file__),'numerical_stack':before,'fold_receipts':receipts,'unknown_embryo_selector_oof':None,'timings':timings,'routing':'one frozen source per movie; no unknown-prefix double inference'}
(WORK/'exp214_runtime_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='fold_receipts'}),flush=True)
