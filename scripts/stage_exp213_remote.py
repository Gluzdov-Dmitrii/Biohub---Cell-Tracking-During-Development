"""Create an isolated symlink view of already-staged Biohub data; no downloads."""
from pathlib import Path
import hashlib
import json

root = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
code = root/'code/exp213_honest_refit_v1_20260912'
plan = json.loads((code/'plan.json').read_text())
view = root/'data/exp213_source_view_20260912'
locations = [root/'data/honest195_missing/train', root/'data/official24/train',
             root/'data/pilot_single_44b6', root/'data/pilot_single_6bba', root/'data/pilot_development_6bba']
selected = {}
missing = []
for name in plan['all_train_movies']:
    for suffix in ('.zarr', '.geff'):
        candidates = [p/(name+suffix) for p in locations if (p/(name+suffix)).is_dir()]
        if not candidates:
            missing.append(name+suffix)
        else:
            target = candidates[0].resolve()
            assert target.is_relative_to(root/'data')
            selected[name+suffix] = target
if missing:
    raise RuntimeError({'missing':missing})
view.mkdir(exist_ok=False)
records = {}
for name, path in selected.items():
    (view/name).symlink_to(path, target_is_directory=True)
    meta = path/'zarr.json'
    records[name] = {'target':str(path),'metadata_sha256':hashlib.sha256(meta.read_bytes()).hexdigest()}
receipt = {'status':'PASS_EXISTING_DATA_LINK_VIEW','images':199,'labels':199,
           'scope':'Read-only view, original data hashes remain in EXP192/official24 receipts; no new bulk copy',
           'plan_sha256':hashlib.sha256((code/'plan.json').read_bytes()).hexdigest(), 'paths':records}
(view/'view_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'images':199,'labels':199,'view':str(view)}))
