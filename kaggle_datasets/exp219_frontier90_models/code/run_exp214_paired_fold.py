"""Sequential public/local graph predictions on one frozen movie shard; never metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    for k in ('notebook','repo','bundle','data-dir','movies','output'):
        p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--reuse-manifest',type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);code=Path(__file__).parent
    if a.reuse_manifest:
        reuse=json.loads(a.reuse_manifest.read_text());public=Path(reuse['public'])
        for name,digest in reuse['files'].items():
            assert hashlib.sha256((public/name).read_bytes()).hexdigest()==digest,name
        receipt=json.loads((public/'inference_receipt.json').read_text())
        assert receipt['target_labels_read'] is False
        assert receipt['bundle']==json.loads(a.bundle.read_text())
        assert receipt['movies']==json.loads(a.movies.read_text())
        (a.output/'public').symlink_to(public,target_is_directory=True)
    else:
        subprocess.check_call([sys.executable,str(code/'run_exp214_public_fold.py'),
            '--notebook',str(a.notebook),'--repo',str(a.repo),'--bundle',str(a.bundle),
            '--data-dir',str(a.data_dir),'--movies',str(a.movies),'--output',str(a.output/'public')])
    subprocess.check_call([sys.executable,str(code/'run_exp214_local_graph.py'),
        '--repo',str(a.repo),'--data',str(a.data_dir),'--bundle',str(a.bundle),
        '--movies',str(a.movies),'--candidates',str(a.output/'public/candidates'),'--output',str(a.output/'local')])
    result={'status':'PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS','target_labels_read':False,'arms':{}}
    for arm in ('public','local'):
        receipt=json.loads((a.output/arm/'inference_receipt.json').read_text())
        assert receipt['target_labels_read'] is False
        result['arms'][arm]={'movies':receipt['movies'],'receipt_sha256':hashlib.sha256((a.output/arm/'inference_receipt.json').read_bytes()).hexdigest()}
    assert result['arms']['public']['movies']==result['arms']['local']['movies']
    (a.output/'status.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
