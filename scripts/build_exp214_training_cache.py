"""Materialize exactly the uint16 pixels consumed by the existing detector.

Full mode preserves all frames; reduced mode preserves a frozen union of
consecutive source-training windows and every source-validation frame.
Never overwrite original data. Verify decoded bytes for EVERY retained frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time


def tree_bytes(path):
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file())


def selected_frames(plan, reduction, name, frame_count, reduced):
    if not reduced: return list(range(frame_count))
    for fold_key, fold in plan['folds'].items():
        if name in fold['validation']: return list(range(frame_count))
        if name in fold['train']:
            row=next(r for r in reduction['folds'][fold_key]['4']['movies'] if r['dataset']==name)
            return sorted({t+offset for t in row['selected_starts'] for offset in [0,1]})
    raise ValueError('Unassigned movie '+name)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--selection',type=Path,required=True)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reduced',action='store_true')
    p.add_argument('--limit',type=int,default=0)
    args=p.parse_args()
    import numpy as np
    import zarr
    from numcodecs import Blosc
    root=Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
    assert args.output.resolve().is_relative_to(root/'data')
    assert args.output.resolve()!=args.data.resolve()
    plan=json.loads(args.plan.read_text()); reduction=json.loads(args.selection.read_text())
    assert hashlib.sha256(args.plan.read_bytes()).hexdigest()==reduction['plan_sha256']
    args.output.mkdir(parents=True,exist_ok=True)
    contract={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'plan_sha256':reduction['plan_sha256'],'selection_sha256':hashlib.sha256(args.selection.read_bytes()).hexdigest(),
        'mode':'stride4_windows' if args.reduced else 'all_frames','spatial_stride':[1,4,4],
        'dtype':'original lossless uint16','scope':'Training cache only; OOF and hidden inference must read original runtime data.'}
    contract_file=args.output/'contract.json'
    if contract_file.exists(): assert json.loads(contract_file.read_text())==contract
    else: contract_file.write_text(json.dumps(contract,indent=2)+'\n')
    rows=[]; start=time.monotonic()
    for name in plan['all_train_movies'][:args.limit or None]:
        destination=args.output/(name+'.zarr')
        receipt_path=args.output/(name+'.receipt.json')
        if receipt_path.exists():
            row=json.loads(receipt_path.read_text()); assert row['contract']==contract
            assert tree_bytes(destination)==row['cache_bytes']; rows.append(row); continue
        if destination.exists(): raise RuntimeError('Incomplete cache requires explicit diagnostic: '+str(destination))
        original=args.data/(name+'.zarr')
        source=zarr.open_group(str(original),mode='r')['0']
        assert len(source.shape)==4 and source.dtype==np.dtype('uint16')
        times=selected_frames(plan,reduction,name,source.shape[0],args.reduced)
        shape=(source.shape[0],source.shape[1],len(range(0,source.shape[2],4)),len(range(0,source.shape[3],4)))
        group=zarr.open_group(str(destination),mode='w',zarr_format=2)
        array=group.create_array('0',shape=shape,chunks=(1,*shape[1:]),dtype=source.dtype,
            compressor=Blosc(cname='zstd',clevel=5,shuffle=Blosc.BITSHUFFLE),fill_value=0)
        group.attrs.update({'original_shape':list(source.shape),'spatial_stride':[1,4,4],'available_frames':times,
            'original_path':str(original.resolve()),'not_a_competition_raw_zarr':True})
        digest=hashlib.sha256()
        for t in times:
            raw=np.asarray(source[t,:,::4,::4]); array[t]=raw
            decoded=np.asarray(array[t])
            assert np.array_equal(raw,decoded),(name,t)
            digest.update(t.to_bytes(8,'little')); digest.update(raw.tobytes())
        row={'dataset':name,'contract':contract,'original_bytes':tree_bytes(original.resolve()),
            'label_bytes':tree_bytes((args.data/(name+'.geff')).resolve()),'original_shape':list(source.shape),
            'cache_bytes':tree_bytes(destination),'decoded_retained_bytes':len(times)*int(np.prod(shape[1:]))*2,
            'retained_frames':len(times),'total_frames':source.shape[0],
            'decoded_sha256':digest.hexdigest(),'all_retained_frames_exact_equal':True}
        receipt_path.write_text(json.dumps(row,indent=2)+'\n'); rows.append(row)
        print(json.dumps({'dataset':name,'original_bytes':row['original_bytes'],'cache_bytes':row['cache_bytes'],
            'retained_frames':len(times),'done':len(rows)}),flush=True)
    report={'status':'PASS_ALL_RETAINED_PIXELS_EXACT','contract':contract,'movies':len(rows),
        'original_image_bytes':sum(r['original_bytes'] for r in rows),'cache_image_bytes':sum(r['cache_bytes'] for r in rows),
        'label_bytes':sum(r['label_bytes'] for r in rows),'elapsed_seconds':time.monotonic()-start,'records':rows}
    report['original_GB']=report['original_image_bytes']/1e9; report['cache_GB']=report['cache_image_bytes']/1e9
    (args.output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)


if __name__=='__main__': main()
