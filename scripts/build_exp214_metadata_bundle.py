"""Copy only original image metadata and labels; no original image chunks."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser()
    for k in ('data','plan','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args(); plan=json.loads(a.plan.read_text())
    a.output.mkdir(exist_ok=False); records=[]
    for name in plan['all_train_movies']:
        src=a.data/(name+'.zarr'); dst=a.output/(name+'.zarr'); (dst/'0').mkdir(parents=True)
        for relative in ('zarr.json','0/zarr.json'):shutil.copy2(src/relative,dst/relative)
        shutil.copytree(a.data/(name+'.geff'),a.output/(name+'.geff'))
    for f in sorted(a.output.rglob('*')):
        if f.is_file():records.append({'path':f.relative_to(a.output).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    result={'status':'METADATA_AND_LABELS_ONLY_REQUIRES_EXACT_CACHE_LOADER','movies':199,
            'bytes':sum(r['bytes'] for r in records),'files':records,
            'warning':'Image metadata placeholders contain no image chunks. Ordinary image reading is invalid; use only with exp214_cache_loader.'}
    (a.output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))


if __name__=='__main__':main()
