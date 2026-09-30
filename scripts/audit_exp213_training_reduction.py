"""Source-only window-selection feasibility audit, never calculates OOF metrics.

Each selected unit retains its original consecutive frames. Stride is between
window starts, not within the movie. Division-adjacent windows are always kept.
No pretrained public model influences this selection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def select_windows(starts, division_starts, stride, salt):
    phase=int(hashlib.sha256(salt.encode()).hexdigest()[:8],16)%stride
    return [t for t in starts if t%stride==phase or any(abs(t-d)<=2 for d in division_starts)]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--data-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    sys.path[:0]=[str(args.repo/'src'),str(args.repo/'scripts')]
    import train_unet_transformer as upstream
    import torch
    torch.set_num_threads(2)
    plan=json.loads(args.plan.read_text())
    started=time.monotonic()
    receipt={'scope':'Source training-window metadata only. No OOF metric, no target inference.',
        'plan_sha256':hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'policy':'hash-phased window starts plus all division transitions +/-2 frames; original time interval and spatial resolution retained',
        'folds':{}}
    for fold_key,fold in plan['folds'].items():
        assert not set(fold['train'])&set(fold['validation'])
        summaries={str(s):{'full_windows':0,'selected_windows':0,'full_positive_edges':0,
            'selected_positive_edges':0,'full_division_transitions':0,'selected_division_transitions':0,
            'movies':[]} for s in [2,4,8]}
        for name in fold['train']:
            vm,windows=upstream.load_dataset_windows(args.data_dir/(name+'.zarr'),window_size=2,downsample=(1,4,4))
            info={w.t_start:{'edges':int(w.targets[0].sum()),
                'divisions':int((w.targets[0].sum(dim=1)>1).sum())} for w in windows}
            divisions=[t for t,v in info.items() if v['divisions']]
            for stride in [2,4,8]:
                selected=select_windows(sorted(info),divisions,stride,'EXP213-WINDOW-v1:'+name)
                s=summaries[str(stride)]
                s['full_windows']+=len(info); s['selected_windows']+=len(selected)
                s['full_positive_edges']+=sum(v['edges'] for v in info.values())
                s['selected_positive_edges']+=sum(info[t]['edges'] for t in selected)
                s['full_division_transitions']+=sum(v['divisions'] for v in info.values())
                s['selected_division_transitions']+=sum(info[t]['divisions'] for t in selected)
                s['movies'].append({'dataset':name,'full_windows':len(info),'selected_starts':selected,
                    'division_starts':divisions,'downsampled_image_shape':list(vm.image_shape)})
        for s in summaries.values():
            s['retained_fraction']=s['selected_windows']/s['full_windows']
            s['train_step_reduction_upper_bound']=s['full_windows']/s['selected_windows']
            assert s['full_division_transitions']==s['selected_division_transitions']
        receipt['folds'][fold_key]=summaries
        print(json.dumps({'fold':fold_key,'strides':{k:{a:b for a,b in v.items() if a!='movies'} for k,v in summaries.items()}}),flush=True)
    receipt['elapsed_seconds']=time.monotonic()-started
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__': main()
