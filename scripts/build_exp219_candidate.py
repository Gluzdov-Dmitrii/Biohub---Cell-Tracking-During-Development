"""Build private frontier artifact and bounded single-route runtime."""
import hashlib,json,tarfile
from pathlib import Path
L=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    archive=L/'outputs/exp219_frontier90_20260916.tar'
    expected=json.loads((L/'reports/exp219_remote_model_pack_20260916.json').read_text())
    assert sha(archive)==expected['archive_sha256']
    dest=L/'kaggle_datasets/exp219_frontier90_models';dest.mkdir(exist_ok=False)
    with tarfile.open(archive) as f:
        assert sum(x.size for x in f.getmembers())<256*1024**2
        f.extractall(dest,filter='data')
    m=json.loads((dest/'artifact_manifest.json').read_text())
    for name,digest in m['files'].items():assert sha(dest/name)==digest
    metadata={'title':'Biohub EXP219 Frontier90 Models','id':'dmitriigluzdov/biohub-exp219-frontier90-models','licenses':[{'name':'other'}],'description':'Private clean embryo-fold detector checkpoints, primary90 and secondary60, clean EXP180 centers. Public-family code derives from Pilkwang Kim support pack and COMPACT47 v20; original terms and attribution retained. OOF175 reference0.742729 is development-adapted two-embryo CV, not unseen-routing score. No frozen test predictions.'}
    (dest/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    kernel=L/'kaggle_notebooks/exp219_frontier90_public';kernel.mkdir(exist_ok=False)
    runtime=(L/'scripts/exp219_runtime.py').read_text()
    (kernel/'exp219_runtime.py').write_text(runtime)
    meta=json.loads((L/'kaggle_notebooks/exp214_reduced_public/kernel-metadata.json').read_text())
    meta.update(id='dmitriigluzdov/biohub-exp219-frontier90-public',title='Biohub EXP219 Frontier90 Public',code_file='exp219_runtime.py')
    meta['dataset_sources'][1]=metadata['id']
    (kernel/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'source_sha256':sha(kernel/'exp219_runtime.py'),'artifact_manifest_sha256':sha(dest/'artifact_manifest.json'),'files_verified':len(m['files'])}))
if __name__=='__main__':main()
