"""Review-gated, one-shot byte-preserved SOURCE-INNER audit stage.

The --preflight-only mode is read-only on nsu-quadro. The default stage mode
requires a fresh intent receipt and never retries an uncertain remote write.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/source_inner_error_decomposition_20260927"
MANIFEST_SHA = "17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/source_inner_error_decomposition_v1_20260927"
RUN = REMOTE + "/runs/source_inner_error_decomposition_v1_20260927"
PYTHON = REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python"
PREFLIGHT_RECEIPT = ROOT / "reports/source_inner_error_decomposition_import_preflight_20260927.json"
STAGE_INTENT = ROOT / "reports/source_inner_error_decomposition_stage_intent_20260927.json"
STAGE_RECEIPT = ROOT / "reports/source_inner_error_decomposition_stage_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_exclusive(path: Path, payload: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def local_bundle():
    assert sha(BUNDLE / "manifest.json") == MANIFEST_SHA
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    assert manifest["status"] == "SEALED_SOURCE_INNER_ERROR_DECOMPOSITION_LOCAL_ONLY"
    assert len(manifest["files"]) == 7
    assert set(manifest["files"]) == {
        "audit_source_inner.py", "config.json", "check_current_organizer_metric_runtime.py",
        "exp234_current_image_scale_audit_20260927.json",
        "tracking_cellmot_official/__init__.py",
        "tracking_cellmot_official/metrics.py",
        "tracking_cellmot_official/division_metrics.py",
    }
    for relative, digest in manifest["files"].items():
        path = (BUNDLE / relative).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and path.is_file()
        assert sha(path) == digest, relative
    config = json.loads((BUNDLE / "config.json").read_text())
    assert config["status"] == "PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY"
    assert config["source_only"] is True
    assert config["output"] == RUN + "/output"
    assert [(c["experiment"], len(c["ids"])) for c in config["cohorts"]] == [
        ("EXP227", 8), ("EXP236", 11)]
    for cohort in config["cohorts"]:
        assert cohort["scorer_code"].startswith(REMOTE + "/code/")
        assert cohort["scorer_run"].startswith(REMOTE + "/runs/")
        assert cohort["graph_run"].startswith(REMOTE + "/runs/")
        assert len(cohort["graph_hashes"]) == len(cohort["ids"])
    return manifest, config


def _replace(source: str, replacements: dict[str, object]) -> str:
    for token, value in replacements.items():
        assert token in source, token
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "remote_stage_source", "exec")
    return source


def import_preflight_source(config: dict, *, expect_code: bool) -> str:
    """Exact remote imports under current-organizer-py311, with GEFF denied."""
    source = r'''import hashlib,importlib,importlib.util,json,os,pathlib,sys
root=pathlib.Path(@@ROOT@@);code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
cohorts=@@COHORTS@@;manifest_sha=@@MANIFEST_SHA@@;expect_code=@@EXPECT_CODE@@
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert pathlib.Path(sys.executable).resolve()==pathlib.Path(@@PYTHON@@).resolve()
assert sys.prefix!=sys.base_prefix and sys.version_info[:2]==(3,11)
assert code.exists()==expect_code and not run.exists()
if expect_code:
 assert sha(code/'manifest.json')==manifest_sha
 manifest=json.loads((code/'manifest.json').read_text())
 for name,digest in manifest['files'].items():
  path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
def deny_labels(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('Import preflight forbids all GEFF access')
sys.addaudithook(deny_labels)
records=[];repo=None
for cohort in cohorts:
 scorer=pathlib.Path(cohort['scorer_code'])
 assert sha(scorer/'code_manifest.json')==cohort['scorer_manifest_sha256']
 assert sha(scorer/'score_config.json')==cohort['scorer_config_sha256']
 scorer_manifest=json.loads((scorer/'code_manifest.json').read_text())
 for name,digest in scorer_manifest.items():
  path=(scorer/name).resolve();assert path.is_relative_to(scorer.resolve()) and sha(path)==digest,name
 score_config=json.loads((scorer/'score_config.json').read_text())
 assert score_config['data_dir']==str(root/'data/exp213_source_view_20260912')
 assert score_config['inference_run']==cohort['graph_run']
 assert score_config['checkpoint_sha256']==cohort['checkpoint_sha256']
 assert sha(score_config['evaluator_config'])==score_config['evaluator_config_sha256']
 evaluator=json.loads(pathlib.Path(score_config['evaluator_config']).read_text())
 assert evaluator['repo_path']==score_config['repo']
 for path,digest in evaluator['evaluator_files'].items():assert sha(path)==digest,path
 module_name='score_exp227_source_graph10' if cohort['experiment']=='EXP227' else 'score_exp236_source_graph10'
 for name in ('score_exp214_paired','score_exp223_official',module_name):sys.modules.pop(name,None)
 sys.path.insert(0,str(scorer))
 try:
  module=importlib.import_module(module_name)
  assert pathlib.Path(module.__file__).resolve()==scorer/(module_name+'.py')
  for dependency in ('score_exp214_paired','score_exp223_official'):
   assert pathlib.Path(sys.modules[dependency].__file__).resolve()==scorer/(dependency+'.py')
 finally:sys.path.pop(0)
 records.append({'experiment':cohort['experiment'],'module':str(pathlib.Path(module.__file__).resolve()),
                 'module_sha256':sha(module.__file__),'scorer_manifest_sha256':cohort['scorer_manifest_sha256']})
 assert repo is None or repo==score_config['repo']
 repo=score_config['repo']
sys.path.insert(0,str(pathlib.Path(repo)/'src'))
old=importlib.import_module('biohub_tracking.metrics')
assert pathlib.Path(old.__file__).resolve()==pathlib.Path(repo)/'src/biohub_tracking/metrics.py'
assert hasattr(old,'evaluate') and hasattr(old,'node_recall') and hasattr(old,'per_sample_metrics')
print(json.dumps({'status':'PASS_SOURCE_INNER_EXACT_IMPORT_PREFLIGHT_NO_LABELS',
 'python':str(pathlib.Path(sys.executable).resolve()),'source_modules':records,
 'legacy_metric':str(pathlib.Path(old.__file__).resolve()),
 'legacy_metric_sha256':sha(old.__file__),
 'torch_available':importlib.util.find_spec('torch') is not None,
 'code_present':expect_code,'run_absent':True,'labels_read':False}))
'''
    return _replace(source, {"@@ROOT@@": REMOTE, "@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@COHORTS@@": config["cohorts"],
                             "@@MANIFEST_SHA@@": MANIFEST_SHA,
                             "@@EXPECT_CODE@@": expect_code, "@@PYTHON@@": PYTHON})


def import_preflight(config: dict, *, expect_code: bool):
    command = shlex.join(["env", "CUDA_VISIBLE_DEVICES=", "PYTHONDONTWRITEBYTECODE=1",
                           "PYTHONNOUSERSITE=1", PYTHON, "-B", "-"])
    result = ssh("nsu-quadro", command, import_preflight_source(config, expect_code=expect_code))
    assert result["status"] == "PASS_SOURCE_INNER_EXACT_IMPORT_PREFLIGHT_NO_LABELS"
    assert result["code_present"] is expect_code and result["run_absent"] is True
    assert result["labels_read"] is False
    assert [row["experiment"] for row in result["source_modules"]] == ["EXP227", "EXP236"]
    return result


def stage_source(manifest: dict) -> str:
    """All payload files, including nested paths, are transferred as bytes."""
    encoded = {relative: base64.b64encode((BUNDLE / relative).read_bytes()).decode("ascii")
               for relative in [*manifest["files"], "manifest.json"]}
    source = r'''import ast,base64,hashlib,json,os,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
files=@@FILES@@;expected=@@EXPECTED@@;manifest_sha=@@MANIFEST_SHA@@
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not code.exists() and not run.exists()
code.mkdir(parents=True,exist_ok=False)
for name,body in files.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_bytes(base64.b64decode(body,validate=True))
 assert sha(path)==expected[name],name
 if name.endswith('.py'):ast.parse(path.read_bytes().decode('utf-8'),filename=name)
assert sha(code/'manifest.json')==manifest_sha
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
print(json.dumps({'status':'STAGED_SOURCE_INNER_AUDIT_BYTES_NO_LABELS','code':str(code),
 'manifest_sha256':sha(code/'manifest.json'),'file_hashes':observed,
 'run_absent':not run.exists(),'labels_read':False}))
'''
    expected = {**manifest["files"], "manifest.json": MANIFEST_SHA}
    return _replace(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@FILES@@": encoded, "@@EXPECTED@@": expected,
                             "@@MANIFEST_SHA@@": MANIFEST_SHA})


def remote_readback_source(manifest: dict) -> str:
    source = r'''import ast,hashlib,json,os,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@);expected=@@EXPECTED@@
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert code.is_dir() and not run.exists()
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
for name in observed:
 if name.endswith('.py'):ast.parse((code/name).read_bytes().decode('utf-8'),filename=name)
print(json.dumps({'status':'PASS_SOURCE_INNER_REMOTE_STAGE_READBACK','code':str(code),
 'manifest_sha256':sha(code/'manifest.json'),'file_hashes':observed,
 'run_absent':True,'labels_read':False}))
'''
    return _replace(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@EXPECTED@@": {**manifest["files"], "manifest.json": MANIFEST_SHA}})


def preflight_only():
    manifest, config = local_bundle()
    assert not STAGE_INTENT.exists() and not STAGE_RECEIPT.exists()
    result = import_preflight(config, expect_code=False)
    receipt = {"status": result["status"], "source_manifest_sha256": MANIFEST_SHA,
               "bundle_files": len(manifest["files"]), "remote": result,
               "remote_mutation": False, "source_labels_read": False,
               "reciprocal_target_labels_read": False}
    if PREFLIGHT_RECEIPT.exists():
        assert json.loads(PREFLIGHT_RECEIPT.read_text()) == receipt
    else:
        write_json_exclusive(PREFLIGHT_RECEIPT, receipt)
    return receipt


def dry_run_plan():
    manifest, config = local_bundle()
    preflight_source = import_preflight_source(config, expect_code=False)
    transfer_source = stage_source(manifest)
    readback_source = remote_readback_source(manifest)
    return {"status": "DRY_RUN_SOURCE_INNER_STAGE_NO_REMOTE_CALL",
            "source_manifest_sha256": MANIFEST_SHA, "code": CODE, "run": RUN,
            "import_command": [PYTHON, "-B", "-"],
            "stage_command": ["python3", "-B", "-"],
            "preflight_source_sha256": hashlib.sha256(preflight_source.encode()).hexdigest(),
            "stage_source_sha256": hashlib.sha256(transfer_source.encode()).hexdigest(),
            "readback_source_sha256": hashlib.sha256(readback_source.encode()).hexdigest(),
            "source_files": len(manifest["files"]),
            "source_only": config["source_only"], "remote_mutation": False}


def stage():
    manifest, config = local_bundle()
    assert not STAGE_INTENT.exists() and not STAGE_RECEIPT.exists(), (
        "Existing stage intent or receipt requires reconciliation")
    preflight = import_preflight(config, expect_code=False)
    assert preflight["torch_available"] is False, "Unexpected runtime drift requires review"
    intent = {"status": "SOURCE_INNER_AUDIT_STAGE_INTENT",
              "source_manifest_sha256": MANIFEST_SHA,
              "local_file_hashes": manifest["files"], "preflight": preflight,
              "code": CODE, "run": RUN, "source_labels_read": False,
              "reciprocal_target_labels_read": False}
    write_json_exclusive(STAGE_INTENT, intent)
    staged = ssh("nsu-quadro", "python3 -B -", stage_source(manifest))
    assert staged["status"] == "STAGED_SOURCE_INNER_AUDIT_BYTES_NO_LABELS"
    expected = {**manifest["files"], "manifest.json": MANIFEST_SHA}
    assert staged["code"] == CODE and staged["file_hashes"] == expected
    assert staged["run_absent"] is True and staged["labels_read"] is False
    readback = ssh("nsu-quadro", "python3 -B -", remote_readback_source(manifest))
    assert readback["status"] == "PASS_SOURCE_INNER_REMOTE_STAGE_READBACK"
    assert readback["file_hashes"] == expected and readback["run_absent"] is True
    receipt = {"status": "STAGED_SOURCE_INNER_AUDIT_NO_LABELS",
               "intent_sha256": sha(STAGE_INTENT), "manifest_sha256": MANIFEST_SHA,
               "preflight": preflight, "stage": staged, "readback": readback,
               "run_started": False, "source_labels_read": False,
               "reciprocal_target_labels_read": False, "gpu_used": False,
               "kaggle_post": False}
    write_json_exclusive(STAGE_RECEIPT, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--preflight-only", action="store_true")
    choice.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = (dry_run_plan() if args.dry_run else
              preflight_only() if args.preflight_only else stage())
    print(json.dumps(result if args.dry_run else
                     {"status": result["status"], "manifest_sha256": MANIFEST_SHA}))


if __name__ == "__main__":
    main()
