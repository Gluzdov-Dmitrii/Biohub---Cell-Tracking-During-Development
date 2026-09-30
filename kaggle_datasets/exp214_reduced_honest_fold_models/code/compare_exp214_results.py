"""Paired pooled-score comparison, conditional movie uncertainty and frozen baseline."""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np


def arrays(rows):
    return np.asarray([[r['edge_tp']+r['edge_fp']+r['edge_fn'],r['adj_edge_jaccard'],
                        r['division_tp'],r['division_tp']+r['division_fp']+r['division_fn']] for r in rows],dtype=float)


def score(a):
    edge=np.sum(a[...,0]*a[...,1],axis=-1)/np.sum(a[...,0],axis=-1)
    dt=np.sum(a[...,2],axis=-1);dd=np.sum(a[...,3],axis=-1)
    return edge+.1*np.divide(dt,dd,out=np.zeros_like(dt),where=dd>0)


def main():
    p=argparse.ArgumentParser()
    for k in ('metrics','baseline','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();new=json.loads(a.metrics.read_text());assert new['status']=='PASS_HONEST_PAIRED_CV'
    names=sorted(r['dataset'] for r in next(iter(new['rows'].values())))
    rows={k:sorted(v,key=lambda r:r['dataset']) for k,v in new['rows'].items()}
    baseline=json.loads(a.baseline.read_text());rows['EXP209_frozen']=[r for r in sorted(baseline['rows'],key=lambda r:r['dataset']) if r['dataset'] in set(names)]
    assert all([r['dataset'] for r in rr]==names for rr in rows.values())
    data={k:arrays(rr) for k,rr in rows.items()};assert all(np.isfinite(v).all() for v in data.values())
    for k,v in new['summary'].items():assert abs(float(score(data[k]))-v['score'])<1e-12
    groups=[np.asarray([i for i,n in enumerate(names) if n.startswith(f+'_')]) for f in ('44b6','6bba')]
    rng=np.random.default_rng(314159); draws={k:[] for k in data}
    for _ in range(50):
        idx=np.concatenate([rng.choice(g,size=(200,len(g)),replace=True) for g in groups],axis=1)
        for k,v in data.items():draws[k].append(score(v[idx]))
    draws={k:np.concatenate(v) for k,v in draws.items()}; comparisons=[]
    for x,y in itertools.combinations(data,2):
        d=draws[x]-draws[y]
        leave=[float(score(np.delete(data[x],i,axis=0))-score(np.delete(data[y],i,axis=0))) for i in range(len(names))]
        comparisons.append({'a':x,'b':y,'delta':float(score(data[x])-score(data[y])),
            'movie_stratified_delta_interval_95':np.quantile(d,[.025,.975]).tolist(),
            'resample_fraction_positive':float(np.mean(d>0)),'leave_one_movie_delta_min':min(leave),'leave_one_movie_delta_max':max(leave)})
    result={'status':'PASS_PAIRED_COMPARISON','movies':len(names),'scores':{k:float(score(v)) for k,v in data.items()},
        'by_embryo':{k:{f:float(score(v[g])) for f,g in zip(('44b6','6bba'),groups)} for k,v in data.items()},
        'comparisons':comparisons,'bootstrap_draws':10000,
        'limitations':['Movie bootstrap is conditional on only two embryos; not uncertainty across new embryos.',
            'EXP209 is a historically development-adapted reference. Refit is12epochs, not published400epoch weights.',
            'Unknown-embryo Kaggle routing has no matching OOF estimate.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
