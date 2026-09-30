"""Build a portable reduced-frame cache from verified XY4 cache, without hardlinks."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from build_exp214_training_cache import selected_frames, tree_bytes


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--full-cache',type=Path,required=True)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    import numpy as np
    import zarr
    from numcodecs import Blosc
    base=json.loads((args.full_cache/'manifest.json').read_text())
    plan=json.loads(args.plan.read_text()); reduction=json.loads(args.selection.read_text())
    assert base['status']=='PASS_ALL_RETAINED_PIXELS_EXACT' and base['movies']==199
    assert reduction['plan_sha256']==hashlib.sha256(args.plan.read_bytes()).hexdigest()
    assert base['contract']['plan_sha256']==reduction['plan_sha256']
    root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/data')
    assert args.output.resolve().is_relative_to(root) and args.output.resolve()!=args.full_cache.resolve()
    args.output.mkdir(exist_ok=False)
    contract={**base['contract'],'mode':'stride4_windows',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'parent_cache_manifest_sha256':hashlib.sha256((args.full_cache/'manifest.json').read_bytes()).hexdigest()}
    (args.output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    rows=[]; started=time.monotonic()
    for original in base['records']:
        name=original['dataset']; source=zarr.open_group(str(args.full_cache/(name+'.zarr')),mode='r')
        times=selected_frames(plan,reduction,name,source['0'].shape[0],True)
        dest=args.output/(name+'.zarr'); group=zarr.open_group(str(dest),mode='w',zarr_format=2)
        array=group.create_array('0',shape=source['0'].shape,chunks=source['0'].chunks,dtype='uint16',
            compressor=Blosc(cname='zstd',clevel=5,shuffle=Blosc.BITSHUFFLE),fill_value=0)
        group.attrs.update({**dict(source.attrs),'available_frames':times})
        digest=hashlib.sha256()
        for t in times:
            raw=np.asarray(source['0'][t]); array[t]=raw
            assert np.array_equal(raw,np.asarray(array[t]))
            digest.update(t.to_bytes(8,'little')); digest.update(raw.tobytes())
        row={**original,'contract':contract,'cache_bytes':tree_bytes(dest),'retained_frames':len(times),
            'decoded_retained_bytes':len(times)*int(np.prod(array.shape[1:]))*2,'decoded_sha256':digest.hexdigest()}
        (args.output/(name+'.receipt.json')).write_text(json.dumps(row,indent=2)+'\n'); rows.append(row)
        print(json.dumps({'dataset':name,'done':len(rows),'cache_bytes':row['cache_bytes']}),flush=True)
    result={**base,'contract':contract,'records':rows,'cache_image_bytes':sum(r['cache_bytes'] for r in rows),
        'elapsed_seconds':time.monotonic()-started}
    result['cache_GB']=result['cache_image_bytes']/1e9
    (args.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)


if __name__=='__main__': main()
