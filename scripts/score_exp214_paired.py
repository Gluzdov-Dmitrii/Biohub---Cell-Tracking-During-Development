"""Open target labels only after all specified arms pass complete prediction gates."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

COLUMNS=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']


def read_graphs(path):
    graphs={}; ids=set()
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f); assert reader.fieldnames==COLUMNS
        for row in reader:
            idx=int(row['id']); assert idx not in ids; ids.add(idx)
            g=graphs.setdefault(row['dataset'],{'nodes':{},'edges':[]})
            if row['row_type']=='node':
                node=int(row['node_id']); assert node not in g['nodes'] and node>=0
                xyz=tuple(float(row[k]) for k in ('z','y','x'))
                assert all(math.isfinite(v) and v>=0 for v in xyz)
                t=int(row['t']); assert t>=0
                g['nodes'][node]=(t,*xyz)
                assert int(row['source_id'])==int(row['target_id'])==-1
            else:
                assert row['row_type']=='edge'
                assert all(float(row[k])==-1 for k in ('node_id','t','z','y','x'))
                g['edges'].append((int(row['source_id']),int(row['target_id'])))
    for g in graphs.values():
        assert len(g['edges'])==len(set(g['edges']))
        incoming={}; outgoing={}
        for s,t in g['edges']:
            assert s in g['nodes'] and t in g['nodes']
            assert g['nodes'][t][0]==g['nodes'][s][0]+1
            incoming[t]=incoming.get(t,0)+1;outgoing[s]=outgoing.get(s,0)+1
        assert max(incoming.values(),default=0)<=1 and max(outgoing.values(),default=0)<=2
    return graphs


def main():
    p=argparse.ArgumentParser()
    for k in ('repo','data','manifest','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args(); spec=json.loads(a.manifest.read_text()); movies=spec['movies']
    assert len(movies)==len(set(movies)) and len(movies) in (40,175)
    assert len(spec['arms'])>=2
    all_graphs={}; hashes={}
    # This entire loop has no target-label access. A missing fold blocks every score.
    for arm,parts in spec['arms'].items():
        merged={}; hashes[arm]=[]
        for part in parts:
            receipt_path=Path(part['receipt']); receipt=json.loads(receipt_path.read_text())
            assert receipt['target_labels_read'] is False
            assert receipt['bundle']['training_plan_sha256']==spec['training_plan_sha256']
            for role in ('primary','secondary','center'):
                model=receipt['bundle'][role]
                assert hashlib.sha256(Path(model['path']).read_bytes()).hexdigest()==model['sha256'],role
            source=receipt['bundle']['source_embryo']
            expected=set(part['movies']); assert all(not n.startswith(source+'_') for n in expected)
            csv_path=Path(part['csv']); digest=hashlib.sha256(csv_path.read_bytes()).hexdigest()
            assert receipt['submission_sha256']==digest
            graphs=read_graphs(csv_path); assert set(graphs)==set(receipt['movies'])
            assert expected<=set(graphs) and not(set(merged)&expected)
            for name in expected: merged[name]=graphs[name]
            hashes[arm].append({'csv':str(csv_path),'sha256':digest,'receipt_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest()})
        assert set(merged)==set(movies),(arm,len(merged),len(movies))
        all_graphs[arm]=merged
    # Image metadata is permitted before the gate; target labels are not.
    import zarr
    for name in movies:
        shape=zarr.open_group(str(a.data/(name+'.zarr')),mode='r')['0'].shape
        for graphs in all_graphs.values():
            assert all(all(0<=v<s for v,s in zip(point,shape)) for point in graphs[name]['nodes'].values())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'no_metric_gate.json').write_text(json.dumps({'status':'PASS_ALL_ARMS_COMPLETE_BEFORE_LABEL_ACCESS','movies':movies,'hashes':hashes},indent=2)+'\n')
    sys.path[:0]=[str(a.repo/'src'),str(a.repo/'scripts')]
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate,node_recall,per_sample_metrics,summarise
    from predict_unet_transformer import build_graph
    import numpy as np
    rows={arm:[] for arm in all_graphs}
    for name in movies:
        ds=open_dataset(a.data/(name+'.zarr'),require_tracks=True,load_image=False)
        estimate=(GeffMetadata.read(a.data/(name+'.geff')).extra or {}).get('estimated_number_of_nodes')
        assert estimate is not None and float(estimate)>0
        for arm,graphs in all_graphs.items():
            g=graphs[name]; ordered=sorted(g['nodes']); mapping={v:i for i,v in enumerate(ordered)}
            coords=np.asarray([g['nodes'][v] for v in ordered],dtype=np.float64).reshape((-1,4))
            assert all(np.all((coords[:,j]>=0)&(coords[:,j]<ds.image_shape[j])) for j in range(4))
            edges=[(mapping[s],mapping[t],1.,0.) for s,t in g['edges']]
            graph=build_graph(coords,edges); metric=evaluate(graph,ds.tracks,scale=ds.scale)
            recall=node_recall(graph,ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.
            rows[arm].append({'dataset':name,**per_sample_metrics(metric,float(estimate),recall)})
        print(json.dumps({'scored_movie':name}),flush=True)
    result={'status':'PASS_HONEST_PAIRED_CV','scope':spec['scope'],'rows':rows,
        'summary':{arm:summarise(r) for arm,r in rows.items()},
        'by_embryo':{arm:{prefix:summarise([r for r in rr if r['dataset'].startswith(prefix+'_')]) for prefix in ('44b6','6bba')} for arm,rr in rows.items()},'input_hashes':hashes}
    (a.output/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))


if __name__=='__main__':main()
