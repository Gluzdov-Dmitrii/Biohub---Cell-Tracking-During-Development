"""Paired fixed-cohort comparison of primary90/secondary60 and frozen60/60."""
import argparse,itertools,json
from pathlib import Path
import numpy as np
from compare_exp214_results import arrays,score

def main():
    p=argparse.ArgumentParser()
    for k in ('metrics','baseline','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();new=json.loads(a.metrics.read_text());old=json.loads(a.baseline.read_text())
    assert new['status']==old['status']=='PASS_HONEST_PAIRED_CV'
    rows={prefix+'_'+k:sorted(v,key=lambda x:x['dataset']) for prefix,d in [('90_60',new),('60_60',old)] for k,v in d['rows'].items()}
    names=[x['dataset'] for x in next(iter(rows.values()))]
    assert len(names)==175 and all([x['dataset'] for x in v]==names for v in rows.values())
    data={k:arrays(v) for k,v in rows.items()}
    for prefix,d in [('90_60',new),('60_60',old)]:
        for k,v in d['summary'].items():assert abs(float(score(data[prefix+'_'+k]))-v['score'])<1e-12
    groups=[np.array([i for i,n in enumerate(names) if n.startswith(f+'_')]) for f in ('44b6','6bba')]
    rng=np.random.default_rng(314159);draws={k:[] for k in data}
    for _ in range(50):
        idx=np.concatenate([rng.choice(g,size=(200,len(g)),replace=True) for g in groups],axis=1)
        for k,v in data.items():draws[k].append(score(v[idx]))
    draws={k:np.concatenate(v) for k,v in draws.items()}
    comparisons=[]
    for x,y in [('90_60_public','60_60_public'),('90_60_local','60_60_local'),('90_60_public','90_60_local')]:
        delta=draws[x]-draws[y]
        comparisons.append({'a':x,'b':y,'delta':float(score(data[x])-score(data[y])),'conditional_movie_95_interval':np.quantile(delta,[.025,.975]).tolist()})
    result={'status':'PASS_CONTROLLED_60_90_PAIRED175','scores':{k:float(score(v)) for k,v in data.items()},'by_embryo':{k:{f:float(score(v[g])) for f,g in zip(('44b6','6bba'),groups)} for k,v in data.items()},'comparisons':comparisons,'limitations':['Only primary seed2026 continued90; secondary314159 stays60.','Two biological embryos; movie bootstrap conditional, not new-embryo uncertainty.','Development-adapted CV; no pristine test or unknown-selector score claim.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
