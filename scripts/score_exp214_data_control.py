"""Score the preregistered full12/reduced12/reduced60 twenty-movie control."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PLAN_SHA='9b1fd764a4571669d0ed7c51ea4e8f4a3cdd49d455ae8af957413b45c9e398e3'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for k in ('plan','manifest','repo','inference-code','data','output'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();assert sha(a.plan)==PLAN_SHA
    plan=json.loads(a.plan.read_text());spec=json.loads(a.manifest.read_text());movies=plan['equal_time_control']['target_movies']
    assert len(movies)==20 and all(n.startswith('6bba_') for n in movies)
    assert set(spec['arms'])==set(plan['equal_time_control']['arms'])
    sys.path[:0]=[str(a.inference_code),str(a.repo/'src'),str(a.repo/'scripts')]
    from score_exp214_paired import read_graphs
    import zarr
    graphs={};hashes={}
    for arm,part in spec['arms'].items():
        receipt=json.loads(Path(part['receipt']).read_text());assert receipt['target_labels_read'] is False
        bundle=receipt['bundle'];assert bundle['source_embryo']=='44b6'
        assert bundle['primary']['sha256']==bundle['secondary']['sha256'],'Single-detector control required'
        for role in ('primary','secondary','center'):assert sha(bundle[role]['path'])==bundle[role]['sha256']
        assert bundle['center']['sha256']==plan['center']['source44b6_sha256']
        assert sha(part['csv'])==receipt['submission_sha256']
        g=read_graphs(part['csv']);assert set(g)==set(movies)==set(receipt['movies'])
        graphs[arm]=g;hashes[arm]={'csv_sha256':sha(part['csv']),'model_sha256':bundle['primary']['sha256'],'receipt_sha256':sha(part['receipt'])}
    assert hashes['full12_same_single_detector_public_graph']['model_sha256']=='2d929a856c317208e30056e38f5f74d7ffc91be36b27e217e596ffc210d4dcc4'
    assert hashes['reduced12_same_single_detector_public_graph']['model_sha256']=='f8e25074a98b651a64740ce9ab013ac957fb8d61462d9c7df982efb4db8e8605'
    sixty=json.loads(Path(spec['reduced60_training_status']).read_text())
    assert sixty['status']=='COMPLETE_SOURCE_REFIT' and sixty['epoch']==sixty['total_epochs']==60
    assert sixty['contract']['plan_sha256']==PLAN_SHA and sixty['target_data_opened'] is False
    assert sixty['best_sha256']==hashes['reduced60_same_single_detector_public_graph']['model_sha256']
    for name in movies:
        shape=zarr.open_group(str(a.data/(name+'.zarr')),mode='r')['0'].shape
        for g in graphs.values():assert all(all(0<=v<s for v,s in zip(row,shape)) for row in g[name]['nodes'].values())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'no_metric_gate.json').write_text(json.dumps({'status':'PASS_ALL_THREE_CONTROLS_BEFORE_TARGET_LABELS','hashes':hashes,'movies':movies},indent=2)+'\n')
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate,node_recall,per_sample_metrics,summarise
    from predict_unet_transformer import build_graph
    import numpy as np
    rows={k:[] for k in graphs}
    for name in movies:
        ds=open_dataset(a.data/(name+'.zarr'),require_tracks=True,load_image=False)
        estimate=(GeffMetadata.read(a.data/(name+'.geff')).extra or {})['estimated_number_of_nodes']
        for arm,gg in graphs.items():
            g=gg[name];ids=sorted(g['nodes']);mapping={v:i for i,v in enumerate(ids)}
            coords=np.asarray([g['nodes'][v] for v in ids],dtype=float).reshape((-1,4))
            graph=build_graph(coords,[(mapping[s],mapping[t],1.,0.) for s,t in g['edges']])
            metric=evaluate(graph,ds.tracks,scale=ds.scale)
            recall=node_recall(graph,ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.
            rows[arm].append({'dataset':name,**per_sample_metrics(metric,float(estimate),recall)})
        print(json.dumps({'scored_movie':name}),flush=True)
    result={'status':'PASS_EQUAL_TIME_DATA_REDUCTION_CONTROL','summary':{k:summarise(v) for k,v in rows.items()},'rows':rows,'hashes':hashes,
        'limitations':'One held-out embryo,20 movies, one model initialization; unseeded upstream augmentation stream. Not exact400epoch public-model OOF.'}
    (a.output/'metrics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))


if __name__=='__main__':main()
