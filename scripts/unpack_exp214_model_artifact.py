"""Safely unpack our completed model archive and verify every scientific file."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import shutil
import tarfile

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    for key in ('archive','destination','receipt'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();dest=a.destination.resolve()
    assert dest.name=='exp214_reduced_honest_fold_models' and dest.parent.name=='kaggle_datasets'
    assert (dest/'dataset-metadata.json').is_file()
    with tarfile.open(a.archive,'r:*') as archive:
        members=archive.getmembers();assert sum(m.size for m in members)<256*1024**2
        for m in members:
            rel=PurePosixPath(m.name)
            assert not rel.is_absolute() and '..' not in rel.parts and (m.isdir() or m.isfile())
            target=dest.joinpath(*rel.parts);assert target.resolve().is_relative_to(dest)
            if m.isfile():assert not target.exists(),str(target)
        for m in members:
            target=dest.joinpath(*PurePosixPath(m.name).parts)
            if m.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(m) as source,target.open('xb') as output:shutil.copyfileobj(source,output)
    manifest=json.loads((dest/'artifact_manifest.json').read_text())
    assert manifest['status']=='PASS_FOUR_COMPLETE_CLEAN_REDUCED_REFITS'
    assert manifest['training_plan_sha256']=='983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a'
    for name,digest in manifest['files'].items():
        path=dest/name;assert path.resolve().is_relative_to(dest) and sha(path)==digest,name
    record={'status':'PASS_LOCAL_MODEL_PACK_SHA_AUDIT','archive_sha256':sha(a.archive),
            'manifest_sha256':sha(dest/'artifact_manifest.json'),'verified_files':len(manifest['files']),
            'total_local_file_bytes':sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()),
            'folds':manifest['folds'],'training_plan_sha256':manifest['training_plan_sha256']}
    with a.receipt.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
