"""Frozen EXP209 graph policies on the same pre-ILP public-family detections."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser()
    for key in ('repo','data','candidates','movies','bundle','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args(); sys.path[:0]=[str(a.repo/'src'),str(a.repo/'scripts')]
    import numpy as np
    import zarr
    from biohub_tracking.io import open_dataset
    from evaluate_cached_intensity_centroid_refinement import refine_movie
    from evaluate_cached_short_track_family import filter_family
    from evaluate_coordinate_consensus import registered_links
    from evaluate_synthetic_gap_deepcenter import close_synthetic_gaps,load_bundle
    bundle=json.loads(a.bundle.read_text()); fold=bundle['source_embryo']
    movies=json.loads(a.movies.read_text()); assert all(not n.startswith(fold+'_') for n in movies)
    center=load_bundle(Path(bundle['center']['path']),bundle['center']['sha256']) if fold=='6bba' else None
    a.output.mkdir(parents=True,exist_ok=False)
    columns=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
    row_id=0; receipts=[]
    with (a.output/'submission.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns); writer.writeheader()
        for name in movies:
            path=a.data/(name+'.zarr'); cache=a.candidates/(name+'.npz')
            with np.load(cache,allow_pickle=False) as payload: raw=np.asarray(payload['coords'],dtype=np.float64)
            ds=open_dataset(path,require_tracks=False,load_image=False)
            scale=np.asarray(ds.scale,dtype=np.float64)
            if fold=='44b6':
                coords,_=refine_movie(zarr.open(str(path),mode='r')['0'],raw,scale,(3,5,5))
                edges=registered_links(coords,scale); minimum=8
            else:
                coords,edges,_=close_synthetic_gaps(raw,registered_links(raw,scale),scale,path,center,
                    gap_close_um=4.5,deepcenter_threshold=.20,deepcenter_confirm_min_span_um=8.5,synthetic_max_fraction=.05)
                minimum=6
            coords,edges,stats=filter_family(coords,edges,{},minimum)
            assert np.isfinite(coords).all()
            for idx,(t,z,y,x) in enumerate(coords):
                assert 0<=t<ds.image_shape[0] and all(0<=v<s for v,s in zip((z,y,x),ds.image_shape[1:]))
                writer.writerow(dict(zip(columns,[row_id,name,'node',idx,int(t),format(z,'.17g'),format(y,'.17g'),format(x,'.17g'),-1,-1])));row_id+=1
            pairs=[(int(e[0]),int(e[1])) for e in edges]
            assert len(pairs)==len(set(pairs))
            assert len({s for s,t in pairs})==len(pairs) and len({t for s,t in pairs})==len(pairs)
            for s,t in sorted(pairs):
                assert 0<=s<len(coords) and 0<=t<len(coords) and coords[t,0]==coords[s,0]+1
                writer.writerow(dict(zip(columns,[row_id,name,'edge',-1,-1,-1,-1,-1,s,t])));row_id+=1
            receipts.append({'movie':name,'candidate_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'nodes':len(coords),'edges':len(edges),'filter':stats})
            print(json.dumps({'movie':name,'inference_complete':True}),flush=True)
    receipt={'status':'PASS_MATCHED_DETECTOR_LOCAL_GRAPH','movies':movies,'bundle':bundle,'rows':receipts,
        'target_labels_read':False,'submission_sha256':hashlib.sha256((a.output/'submission.csv').read_bytes()).hexdigest()}
    (a.output/'inference_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__': main()
