"""Paired uncertainty and measured time for the fixed three-way data control."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np

def main():
    p=argparse.ArgumentParser()
    for k in ('metrics','full-receipt','reduced12-history','reduced60-history','inference-code','output'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.inference_code))
    from compare_exp214_results import arrays,score
    m=json.loads(a.metrics.read_text());assert m['status']=='PASS_EQUAL_TIME_DATA_REDUCTION_CONTROL'
    order=[k+'_same_single_detector_public_graph' for k in ('full12','reduced12','reduced60')]
    assert set(order)==set(m['rows'])
    names=sorted(r['dataset'] for r in m['rows'][order[0]])
    assert len(names)==len(set(names))==20 and all(n.startswith('6bba_') for n in names)
    data={}
    for arm in order:
        rows=sorted(m['rows'][arm],key=lambda r:r['dataset']);assert [r['dataset'] for r in rows]==names
        data[arm]=arrays(rows)
        assert abs(float(score(data[arm]))-m['summary'][arm]['score'])<1e-12
    rng=np.random.default_rng(314159);indices=rng.integers(0,20,size=(10000,20))
    samples={k:score(v[indices]) for k,v in data.items()};comparisons=[]
    for first,second in itertools.combinations(order,2):
        delta=samples[second]-samples[first]
        comparisons.append({'reference':first,'candidate':second,
            'candidate_minus_reference':float(score(data[second])-score(data[first])),
            'conditional_movie_delta_interval_95':np.quantile(delta,[.025,.975]).tolist(),
            'resample_fraction_positive':float(np.mean(delta>0))})
    histories={'full12':json.loads(a.full_receipt.read_text())['history'],
               'reduced12':json.loads(a.reduced12_history.read_text()),
               'reduced60':json.loads(a.reduced60_history.read_text())}
    times={}
    for arm,h in histories.items():
        assert [r['epoch'] for r in h]==list(range(1,(60 if arm=='reduced60' else 12)+1))
        best=max(h,key=lambda r:r['selection_score'])
        times[arm]={'all_epochs_train_seconds':sum(r['train_seconds'] for r in h),
                    'all_epochs_including_validation_seconds':sum(r['epoch_seconds'] for r in h),
                    'selected_epoch':best['epoch'],'source_selection_proxy':best['selection_score']}
    full=times['full12']['all_epochs_including_validation_seconds']
    result={'status':'PASS_PAIRED_DATA_REDUCTION_COMPARISON','movies':20,
            'scores':{k:float(score(v)) for k,v in data.items()},'comparisons':comparisons,'training_times':times,
            'full12_over_reduced12_time_ratio':full/times['reduced12']['all_epochs_including_validation_seconds'],
            'reduced60_over_full12_time_ratio':times['reduced60']['all_epochs_including_validation_seconds']/full,
            'metrics_sha256':hashlib.sha256(a.metrics.read_bytes()).hexdigest(),
            'limitations':['Only20 movies of one held-out embryo; bootstrap does not measure new-embryo uncertainty.',
                'One initialization, uncontrolled upstream augmentation RNG; not a noise-free causal estimate.',
                'Time sums all epochs including the12 pre-resume epochs, excluding loading/restart overhead.',
                'An interval including zero is not proof of equal quality; no universal no-loss claim.']}
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
