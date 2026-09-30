"""Check actual normalized detector tensors against original I/O, without metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser()
    for name in ('repo','data','cache','plan','selection','output'):
        p.add_argument('--'+name, type=Path, required=True)
    a=p.parse_args()
    sys.path[:0]=[str(a.repo/'src'),str(a.repo/'scripts')]
    import torch
    import train_unet_transformer as up
    from exp214_cache_loader import cached_dataset_class
    torch.set_num_threads(2)
    cls=cached_dataset_class(up,a.cache)
    plan=json.loads(a.plan.read_text()); selection=json.loads(a.selection.read_text())
    rows=[]
    for fold in ('44b6','6bba'):
        for name in plan['folds'][fold]['train'][:2]:
            vm,windows=up.load_dataset_windows(a.data/(name+'.zarr'),window_size=2,downsample=(1,4,4))
            entry=next(r for r in selection['folds'][fold]['4']['movies'] if r['dataset']==name)
            starts=entry['selected_starts']; chosen=[w for w in windows if w.t_start in (starts[0],starts[len(starts)//2],starts[-1])]
            normal=up.FrameWindowDataset([(vm,chosen)],augmentations=[])
            cached=cls([(vm,chosen)],augmentations=[])
            for i,w in enumerate(chosen):
                x,y=normal[i],cached[i]
                assert x.keys()==y.keys()
                for key in x:
                    if isinstance(x[key],torch.Tensor): assert torch.equal(x[key],y[key]),(name,w.t_start,key)
                    else: assert x[key]==y[key],(name,w.t_start,key)
                rows.append({'movie':name,'start':w.t_start,'image_tensor_sha256':hashlib.sha256(x['imgs'].numpy().tobytes()).hexdigest()})
    result={'status':'PASS_EXACT_NORMALIZED_DATASET_TENSORS','target_metrics_read':False,
            'scope':'12 source windows, no augmentations; all retained raw frames separately verified byte-exact',
            'cache_manifest_sha256':hashlib.sha256((a.cache/'manifest.json').read_bytes()).hexdigest(),'rows':rows}
    a.output.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))


if __name__=='__main__': main()
