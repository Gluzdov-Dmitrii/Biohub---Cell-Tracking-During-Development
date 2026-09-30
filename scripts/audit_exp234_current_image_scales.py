"""Read-only comparison of EXP234 image metadata with the historical loader."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/exp234_current_image_scale_audit_20260927.json"
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"


def main() -> None:
    assert not RECEIPT.exists(), "Scale audit receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    assert prepared["status"] == "PREPARED_EXP234_CURRENT_ORGANIZER_TARGET175_NO_LABELS_LOCAL_ONLY"
    source = r'''import hashlib,json,pathlib,sys
root=pathlib.Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
old=root/'code/exp234_target_official_scorer_v1_20260927'
config_path=old/'score_config.json'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(config_path)=='45c9a8931e8e8ff243c0e8f09840ee0530a5855fa42b1d26eb91430ab31055a3'
config=json.loads(config_path.read_text())
cohort_path=pathlib.Path(config['cohort'])
assert sha(cohort_path)==config['cohort_sha256']=='001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4'
cohort_doc=json.loads(cohort_path.read_text())
cohort={row['dataset']:row for row in cohort_doc['rows']}
assert len(cohort)==len(cohort_doc['rows'])==175
repo=root/'code/exp214_honest_refit_v4_20260912/tracking_repo/src'
io_path=repo/'biohub_tracking/io.py'
sys.path.insert(0,str(repo))
import tracksdata as td
def forbidden(*args,**kwargs): raise AssertionError('GEFF label access attempted')
td.graph.IndexedRXGraph.from_geff=forbidden
from biohub_tracking.io import open_dataset
rows=[]
for name in sorted(cohort):
 movie=cohort[name]; zarr=pathlib.Path(movie['zarr'])
 root_meta=json.loads((zarr/'zarr.json').read_text())
 array_meta=json.loads((zarr/'0/zarr.json').read_text())
 assert list(array_meta['shape'])==movie['shape']
 attrs=root_meta.get('attributes',{})
 if 'multiscales' in attrs:
  transform=attrs['multiscales'][0]['datasets'][0]['coordinateTransformations'][0]
  assert transform['type']=='scale'
  direct=tuple(float(v) for v in transform['scale'][-3:])
 else: direct=(1.625,0.40625,0.40625)
 historical=open_dataset(zarr,require_tracks=False,load_image=False)
 assert tuple(historical.scale)==direct,(name,historical.scale,direct)
 assert list(historical.image_shape)==movie['shape']
 rows.append({'dataset':name,'scale':direct,'zarr_root_sha256':sha(zarr/'zarr.json'),
              'zarr_array_sha256':sha(zarr/'0/zarr.json')})
assert len(rows)==175
print(json.dumps({'status':'PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS',
 'historical_loader_sha256':sha(io_path),'cohort_sha256':sha(cohort_path),
 'historical_config_sha256':sha(config_path),'count':len(rows),
 'unique_scales':sorted({tuple(row['scale']) for row in rows}),
 'rows':rows,'target_labels_read':False}))
'''
    result = ssh("nsu-quadro", prepared["interpreter_intended"].replace(
        "current-organizer-py311-e13cf-v1", "prepost/py3.11-stdlib-v1") + " -", source)
    assert result["status"] == "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS"
    assert result["count"] == len(result["rows"]) == 175
    assert result["target_labels_read"] is False
    RECEIPT.write_bytes((json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"status": result["status"], "count": result["count"],
                      "unique_scales": result["unique_scales"],
                      "receipt_sha256": hashlib.sha256(RECEIPT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
