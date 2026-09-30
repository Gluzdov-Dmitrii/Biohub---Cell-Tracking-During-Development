"""Read-only source19 Zarr metadata audit for the v2 SOURCE-INNER bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "reports/source_inner19_image_scale_audit_v2_20260927.json"
CONFIG = ROOT / "work/source_inner_error_decomposition_20260927/config.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PYTHON = REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_sources() -> list[dict]:
    config = json.loads(CONFIG.read_text())
    assert config["status"] == "PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY"
    plans = {
        "EXP227": ROOT / "reports/exp227_source_graph10_plan_20260927.json",
        "EXP236": ROOT / "reports/exp236_source_graph10_v2_plan_20260927.json",
    }
    out = []
    for cohort in config["cohorts"]:
        plan_path = plans[cohort["experiment"]]
        plan = json.loads(plan_path.read_text())
        scorer_prepare = json.loads((ROOT / ("reports/" + cohort["experiment"].lower() +
                                                  "_source_graph10_scorer_prepare_20260927.json")).read_text())
        assert [m["dataset"] for m in plan["movies"]] == cohort["ids"]
        assert len(plan["movies"]) == (8 if cohort["experiment"] == "EXP227" else 11)
        assert all(m["zarr"] == REMOTE + "/data/exp213_source_view_20260912/" +
                   m["dataset"] + ".zarr" for m in plan["movies"])
        out.append({"experiment": cohort["experiment"], "ids": cohort["ids"],
                    "scorer_code": cohort["scorer_code"],
                    "scorer_manifest_sha256": cohort["scorer_manifest_sha256"],
                    "scorer_config_sha256": cohort["scorer_config_sha256"],
                    "local_plan_sha256": sha(plan_path),
                    "plan_sha256": scorer_prepare["config"]["plan_sha256"],
                    "movies": plan["movies"]})
    assert len({i for row in out for i in row["ids"]}) == 19
    return out


def remote_source(expected: list[dict]) -> str:
    source = r'''import hashlib,json,os,pathlib,sys
root=pathlib.Path(ROOT);expected=EXPECTED
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert pathlib.Path(sys.executable).resolve()==(root/'envs/prepost/py3.11-stdlib-v1/bin/python').resolve()
assert sys.prefix!=sys.base_prefix and sys.version_info[:2]==(3,11)
def deny_labels(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('Image-only source audit forbids all GEFF access')
sys.addaudithook(deny_labels)
import tracksdata as td
td.graph.IndexedRXGraph.from_geff=lambda *args,**kwargs: (_ for _ in ()).throw(
 AssertionError('Image-only source audit forbids from_geff'))
rows=[];configs=[];repo=None;io_sha=None
for cohort in expected:
 scorer=pathlib.Path(cohort['scorer_code'])
 assert sha(scorer/'code_manifest.json')==cohort['scorer_manifest_sha256']
 assert sha(scorer/'score_config.json')==cohort['scorer_config_sha256']
 scorer_config=json.loads((scorer/'score_config.json').read_text())
 assert scorer_config['data_dir']==str(root/'data/exp213_source_view_20260912')
 assert sha(scorer_config['evaluator_config'])==scorer_config['evaluator_config_sha256']
 evaluator=json.loads(pathlib.Path(scorer_config['evaluator_config']).read_text())
 assert evaluator['repo_path']==scorer_config['repo']
 for path,digest in evaluator['evaluator_files'].items():assert sha(path)==digest,path
 assert repo is None or repo==scorer_config['repo']
 repo=scorer_config['repo']
 plan_path=pathlib.Path(scorer_config['inference_code'])/'plan.json'
 assert sha(plan_path)==scorer_config['plan_sha256']==cohort['plan_sha256']
 plan=json.loads(plan_path.read_text())
 assert plan['movies']==cohort['movies']
 assert [m['dataset'] for m in plan['movies']]==cohort['ids']
 configs.append({'experiment':cohort['experiment'],
  'scorer_config_sha256':sha(scorer/'score_config.json'),
  'evaluator_config_sha256':sha(scorer_config['evaluator_config']),
  'source_plan_sha256':sha(plan_path)})
 for movie in plan['movies']:
  name=movie['dataset'];zarr=pathlib.Path(movie['zarr'])
  assert zarr==root/'data/exp213_source_view_20260912'/(name+'.zarr')
  root_meta=json.loads((zarr/'zarr.json').read_text())
  array_meta=json.loads((zarr/'0/zarr.json').read_text())
  assert list(array_meta['shape'])==movie['shape']
  attrs=root_meta.get('attributes',{})
  if 'multiscales' in attrs:
   transform=attrs['multiscales'][0]['datasets'][0]['coordinateTransformations'][0]
   assert transform['type']=='scale'
   direct=tuple(float(v) for v in transform['scale'][-3:])
  else:direct=(1.625,0.40625,0.40625)
  rows.append({'dataset':name,'experiment':cohort['experiment'],
   'zarr':str(zarr),'shape':movie['shape'],'scale':direct,
   'zarr_root_sha256':sha(zarr/'zarr.json'),
   'zarr_array_sha256':sha(zarr/'0/zarr.json')})
sys.path.insert(0,str(pathlib.Path(repo)/'src'))
from biohub_tracking.io import open_dataset
io_path=pathlib.Path(repo)/'src/biohub_tracking/io.py'
io_sha=sha(io_path)
assert evaluator['evaluator_files'].get(str(io_path))==io_sha
for row in rows:
 historical=open_dataset(pathlib.Path(row['zarr']),require_tracks=False,load_image=False)
 assert tuple(historical.scale)==tuple(row['scale']),row['dataset']
 assert list(historical.image_shape)==row['shape'],row['dataset']
assert len(rows)==19 and len({row['dataset'] for row in rows})==19
assert [row['dataset'] for row in rows]==[name for c in expected for name in c['ids']]
print(json.dumps({'status':'PASS_SOURCE_INNER_EXACT19_IMAGE_SCALE_NO_LABELS',
 'count':19,'unique_scales':sorted({tuple(row['scale']) for row in rows}),
 'source_configs':configs,'historical_loader_sha256':io_sha,
 'rows':rows,'source_labels_read':False,'reciprocal_target_labels_read':False,
 'gpu_used':False,'kaggle_post':False}))
'''
    return source.replace("ROOT", repr(REMOTE)).replace("EXPECTED", repr(expected))


def main() -> None:
    assert not RECEIPT.exists(), "Immutable source19 receipt already exists"
    expected = expected_sources()
    source = remote_source(expected)
    compile(source, "source19_image_only_remote.py", "exec")
    result = ssh("nsu-quadro", "env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "
                 "PYTHONNOUSERSITE=1 " + PYTHON + " -B -", source)
    assert result["status"] == "PASS_SOURCE_INNER_EXACT19_IMAGE_SCALE_NO_LABELS"
    assert [r["dataset"] for r in result["rows"]] == [i for c in expected for i in c["ids"]]
    assert result["count"] == 19 and result["source_labels_read"] is False
    assert result["reciprocal_target_labels_read"] is False
    RECEIPT.write_bytes((json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({"status": result["status"], "count": result["count"],
                      "unique_scales": result["unique_scales"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
