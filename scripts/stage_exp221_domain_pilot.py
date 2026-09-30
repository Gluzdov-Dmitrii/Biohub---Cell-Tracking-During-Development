"""Stage only audited experiment-owned files; shared environment remains immutable."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from monitor_exp213_job import ssh

ROOT='/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development'


def main():
    local=Path('outputs/research/exp221_domain_pilot_code_20260921')
    receipts=[]
    for arm in ['control','domain']:
        names=['train_exp213_detector.py','exp214_cache_loader.py','prepare_exp213_honest_refit.py','exp221_domain_augmentation.py','exp213_remote_job.py']
        files={n:base64.b64encode((local/n).read_bytes()).decode() for n in names}
        files['plan.json']=base64.b64encode((local/f'plan_{arm}.json').read_bytes()).decode()
        source='''import base64,json,hashlib
from pathlib import Path
root=Path(ROOT)
code=root/'code'/NAME
code.mkdir(exist_ok=True)
manifest={}
for name, encoded in FILES.items():
 value=base64.b64decode(encoded); p=code/name
 if p.exists(): assert p.read_bytes()==value, 'Refuse overwrite changed staged source'
 else: p.write_bytes(value)
 manifest[name]=hashlib.sha256(value).hexdigest()
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
repo=code/'tracking_repo'
if not repo.exists(): repo.symlink_to(root/'code/exp214_honest_refit_v4_20260912/tracking_repo',target_is_directory=True)
assert repo.is_dir()
print(json.dumps({'code':str(code),'manifest':manifest}))
'''.replace('ROOT',repr(ROOT)).replace('NAME',repr(f'exp221_{arm}_v1_20260921')).replace('FILES',repr(files))
        receipts.append(ssh('nsu-quadro','python3 -',source))
    Path('reports/exp221_staging_20260921.json').write_text(json.dumps(receipts,indent=2)+'\n')
    print(json.dumps(receipts,indent=2))


if __name__=='__main__': main()
