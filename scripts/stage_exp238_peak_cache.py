"""Guarded EXP238 code stage. Default is local review; --execute writes a new remote tree.

Do not invoke --execute before root review. This script never opens GEFF or target images.
"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh
from run_exp238_peak_cache import validate_plan


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp238_source_peak_cache_local_20260927"
REPORTS = ROOT / "reports"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def local_preflight(cohort: str) -> tuple[dict, dict]:
    manifest_path = BUNDLE / "local_bundle_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == digest, name
    plan_path = BUNDLE / cohort / "exp238_plan.json"
    plan = json.loads(plan_path.read_text())
    validate_plan(plan)
    assert plan["cohort"] == cohort
    assert plan["prereg_sha256"] == sha(REPORTS / "EXP238_SOURCE_PEAK_CACHE_PREREG_20260927.md")
    assert plan["runner_sha256"] == sha(ROOT / "scripts/run_exp238_peak_cache.py")
    assert plan["patched_engine_sha256"] == sha(BUNDLE / "patched/engine.py")
    assert plan["patched_detection_sha256"] == sha(BUNDLE / "patched/detection.py")
    assert plan["parent_plan_sha256"] == sha(BUNDLE / cohort / "exp238_parent_plan.json")
    return plan, {"manifest_sha256": sha(manifest_path), "plan_sha256": sha(plan_path)}


def remote_preflight(plan: dict) -> dict:
    source = '''import hashlib,json,pathlib
p=json.loads(PLAN)
code=pathlib.Path(p['parent_code']);run=pathlib.Path(p['parent_run'])
new_code=pathlib.Path(p['code']);new_run=pathlib.Path(p['run'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not new_code.exists() and not new_run.exists()
assert sha(code/'code_manifest.json')==p['parent_manifest_sha256']
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==p['parent_plan_sha256']
assert sha(run/'output/status.json')==p['parent_status_sha256']
parent=json.loads((code/'plan.json').read_text())
assert parent['checkpoint']==p['checkpoint'] and sha(pathlib.Path(p['checkpoint']))==p['checkpoint_sha256']
assert [row['dataset'] for row in parent['movies']]==[row['dataset'] for row in p['movies']]
for row in p['movies']:
 name=row['dataset'];zarr=pathlib.Path(row['zarr'])
 assert zarr.is_dir() and zarr.name==name+'.zarr'
 csv=run/'output'/('graph__'+name+'.csv')
 assert sha(csv)==row['graph_csv_sha256'] and sha(csv.with_suffix('.json'))==row['graph_receipt_sha256']
print(json.dumps({'status':'PASS_EXP238_REMOTE_STAGE_PREFLIGHT_NO_LABELS','movies':len(p['movies']),
 'parent_manifest_sha256':p['parent_manifest_sha256'],'parent_status_sha256':p['parent_status_sha256'],
 'new_paths_absent':True,'labels_read':False}))
'''.replace("PLAN", repr(json.dumps(plan, sort_keys=True)))
    return ssh("nsu-a100", "python3 -", source)


def stage_remote(plan: dict, cohort: str) -> dict:
    payloads = {
        "horaz/src/src/engine.py": (BUNDLE / "patched/engine.py").read_bytes(),
        "horaz/src/src/detection.py": (BUNDLE / "patched/detection.py").read_bytes(),
        "run_exp238_peak_cache.py": (ROOT / "scripts/run_exp238_peak_cache.py").read_bytes(),
        "exp238_plan.json": (BUNDLE / cohort / "exp238_plan.json").read_bytes(),
        "exp238_parent_plan.json": (BUNDLE / cohort / "exp238_parent_plan.json").read_bytes(),
    }
    encoded = {name: base64.b64encode(body).decode("ascii") for name, body in payloads.items()}
    source = '''import ast,base64,hashlib,json,pathlib,shutil
p=json.loads(PLAN);payloads=json.loads(PAYLOADS)
parent=pathlib.Path(p['parent_code']);code=pathlib.Path(p['code']);run=pathlib.Path(p['run'])
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert not code.exists() and not run.exists()
assert sha(parent/'code_manifest.json')==p['parent_manifest_sha256']
parent_manifest=json.loads((parent/'code_manifest.json').read_text())
for name,digest in parent_manifest.items():
 path=(parent/name).resolve();assert path.is_relative_to(parent.resolve()) and sha(path)==digest,name
assert sha(parent/'plan.json')==p['parent_plan_sha256']
assert sha(pathlib.Path(p['checkpoint']))==p['checkpoint_sha256']
shutil.copytree(parent,code)
wrapper=code/'exp227_job.py';body=wrapper.read_text()
old_assert=("assert config['script'] == 'run_exp227_source_graph10.py'" if p['cohort']=='source44'
            else "assert config['script'] == 'run_exp236_source_graph10_v2.py'")
assert body.count(old_assert)==1
wrapper.write_text(body.replace(old_assert,"assert config['script'] == 'run_exp238_peak_cache.py'"))
for name,body in payloads.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(body,validate=True))
 if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
manifest=dict(parent_manifest)
manifest['exp227_job.py']=sha(wrapper)
for name in payloads:manifest[name]=sha(code/name)
manifest_path=code/'code_manifest.json'
manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\\n')
assert sha(code/'horaz/src/src/engine.py')==p['patched_engine_sha256']
assert sha(code/'horaz/src/src/detection.py')==p['patched_detection_sha256']
assert sha(code/'run_exp238_peak_cache.py')==p['runner_sha256']
assert sha(code/'exp238_parent_plan.json')==p['parent_plan_sha256']
assert json.loads((code/'exp238_plan.json').read_text())==p
assert not run.exists()
print(json.dumps({'status':'STAGED_EXP238_SOURCE_PEAK_CACHE_NO_LABELS','code':str(code),
 'manifest_sha256':sha(manifest_path),'plan_sha256':sha(code/'exp238_plan.json'),
 'runner_sha256':p['runner_sha256'],'movies':len(p['movies']),'labels_read':False}))
'''.replace("PLAN", repr(json.dumps(plan, sort_keys=True))).replace(
        "PAYLOADS", repr(json.dumps(encoded, sort_keys=True)))
    return ssh("nsu-a100", "python3 -", source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("source44", "source6"), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan, local = local_preflight(args.cohort)
    if not args.execute:
        print(json.dumps({"status": "EXP238_LOCAL_STAGE_REVIEW_ONLY", "cohort": args.cohort,
                          "plan_sha256": local["plan_sha256"],
                          "local_bundle_manifest_sha256": local["manifest_sha256"],
                          "remote_stage": False}, sort_keys=True))
        return
    prefix = REPORTS / ("exp238_" + args.cohort + "_peak_cache_stage_20260927")
    assert not prefix.with_name(prefix.name + "_intent.json").exists()
    assert not prefix.with_suffix(".json").exists()
    preflight = remote_preflight(plan)
    assert preflight["status"] == "PASS_EXP238_REMOTE_STAGE_PREFLIGHT_NO_LABELS"
    assert preflight["movies"] == len(plan["movies"])
    intent = {"status": "INTENT_EXP238_REMOTE_STAGE", "cohort": args.cohort,
              "plan_sha256": local["plan_sha256"],
              "local_bundle_manifest_sha256": local["manifest_sha256"],
              "preflight": preflight}
    atomic_json(prefix.with_name(prefix.name + "_intent.json"), intent)
    result = stage_remote(plan, args.cohort)
    assert result["status"] == "STAGED_EXP238_SOURCE_PEAK_CACHE_NO_LABELS"
    assert result["plan_sha256"] == local["plan_sha256"]
    receipt = {"status": "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS", "cohort": args.cohort,
               "local": local, "preflight": preflight, "stage": result,
               "run_started": False, "labels_read": False}
    atomic_json(prefix.with_suffix(".json"), receipt)
    print(json.dumps({"status": receipt["status"], "cohort": args.cohort,
                      "manifest_sha256": result["manifest_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
