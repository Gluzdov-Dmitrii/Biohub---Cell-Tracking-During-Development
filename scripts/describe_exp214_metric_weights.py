"""Describe pooled metric weights; these are not independent biological samples."""
import argparse,json,math
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    for name in ('metrics','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();m=json.loads(a.metrics.read_text());assert m['status']=='PASS_HONEST_PAIRED_CV'
    rows=dict(m['rows']);names={r['dataset'] for r in next(iter(rows.values()))}
    rows['EXP209_frozen']=[r for r in json.loads(a.baseline.read_text())['rows'] if r['dataset'] in names]
    result={'scope':'Descriptive edge-union weights only; effective weight count is not biological sample size or an uncertainty estimate. Movie dependence remains unmeasured.','arms':{}}
    for arm,rr in rows.items():
        assert {r['dataset'] for r in rr}==names
        ww=[(r['dataset'],float(r['edge_tp']+r['edge_fp']+r['edge_fn'])) for r in rr]
        assert all(math.isfinite(w) and w>=0 for n,w in ww)
        total=sum(w for n,w in ww);assert total>0
        order=sorted(ww,key=lambda t:t[1],reverse=True)
        result['arms'][arm]={'movies':len(rr),'edge_union_sum':total,'weight_concentration_effective_count':total**2/sum(w*w for n,w in ww),'largest_movie_weight_fraction':order[0][1]/total,'top5_movies_weight_fraction':sum(w for n,w in order[:5])/total,'weight_fraction_by_embryo':{e:sum(w for n,w in ww if n.startswith(e+'_'))/total for e in ('44b6','6bba')},'movie_count_by_embryo':{e:sum(n.startswith(e+'_') for n,w in ww) for e in ('44b6','6bba')}}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
