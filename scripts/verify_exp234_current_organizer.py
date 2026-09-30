"""Independent one-shot readback of EXP234 current organizer rescore.

Run only after the separate CPU scorer has exited. On any anomaly this emits no
PASS receipt and leaves every historical and current remote artifact intact.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
STAGE = ROOT / "reports/exp234_current_organizer_stage_20260927.json"
ENV_VERIFY = ROOT / "reports/exp234_current_organizer_env_verify_20260927.json"
SCALE_AUDIT = ROOT / "reports/exp234_current_image_scale_audit_20260927.json"
LAUNCH = ROOT / "reports/exp234_current_organizer_launch_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_organizer_score_verified_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote(source: str, python: str) -> dict:
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-quadro", python + " -"],
        input=source, text=True, capture_output=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f"Remote verifier failed {result.returncode}: {result.stderr[-3000:]}")
    return json.loads(result.stdout)


def main() -> None:
    assert not RECEIPT.exists(), "Current metric score receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    staged = json.loads(STAGE.read_text())
    env = json.loads(ENV_VERIFY.read_text())
    audit = json.loads(SCALE_AUDIT.read_text())
    launched = json.loads(LAUNCH.read_text())
    assert prepared["status"] == "PREPARED_EXP234_CURRENT_ORGANIZER_TARGET175_NO_LABELS_LOCAL_ONLY"
    assert staged["prepare_sha256"] == sha(PREPARE)
    assert env["stage_sha256"] == sha(STAGE)
    assert launched["env_verify_sha256"] == sha(ENV_VERIFY)
    assert launched["scale_audit_sha256"] == sha(SCALE_AUDIT)
    assert audit["status"] == "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS"
    assert audit["count"] == 175 and audit["target_labels_read"] is False
    for name, digest in prepared["prerequisite_local_sha256"].items():
        assert sha(ROOT / name) == digest, name
    assert json.loads((ROOT / "reports/exp234_target_score_handoff_20260927.json").read_text())["status"].startswith("STOPPED")
    assert sha(ROOT / "work/exp234_current_organizer_v1/code_manifest.json") == prepared["code_manifest_sha256"]
    assert sha(ROOT / "work/exp234_current_organizer_v1/score_config.json") == prepared["score_config_sha256"]
    assert staged["stage"]["source_hashes"] == prepared["source_hashes"]
    code = prepared["remote_code_intended"]
    run = prepared["remote_run_intended"]
    python = prepared["interpreter_intended"]
    launch = launched["launch"]
    assert launch["run"] == run and launch["code"] == code and launch["python"] == python
    assert launch["kaggle_post"] is False

    source = r'''import hashlib,json,math,os,pathlib,sys
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
old_code=pathlib.Path(@@OLD_CODE@@);old_run=pathlib.Path(@@OLD_RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert pathlib.Path(sys.executable)==pathlib.Path(@@PYTHON@@)
assert sys.prefix!=sys.base_prefix
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(old_code/'score_config.json')==@@OLD_CONFIG_SHA@@
assert sha(old_run/'output/no_metric_gate.json')==@@OLD_GATE_SHA@@
assert sha(old_run/'output/result.json')==@@OLD_RESULT_SHA@@
assert json.loads((old_run/'exit.json').read_text())['returncode']==0
launch=json.loads((run/'launch.json').read_text())
child=json.loads((run/'child.json').read_text())
exited=json.loads((run/'exit.json').read_text())
assert launch==@@LAUNCH@@
assert launch['status']=='LAUNCHED_EXP234_CURRENT_ORGANIZER_TARGET175_CPU'
assert launch['cpu']==4 and launch['ram_gib']==32 and launch['max_seconds']==3600
assert child['pid']==exited['pid'] and child['start']==exited['start']
assert child['command']==[@@PYTHON@@,str(code/'score_exp234_current_organizer.py'),
                          str(code/'score_config.json'),'--config-sha256',@@CONFIG_SHA@@]
assert child['cpu_affinity']==[16,17,18,19] and child['ram_gib']==32
assert child['cuda_visible_devices']==''
assert exited['returncode']==0 and exited['timeout'] is False
identity=False;group=False
for path in pathlib.Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=path.read_text();fields=raw[raw.rfind(')')+2:].split()
  if fields[0]=='Z':continue
  if int(path.parent.name)==child['pid'] and fields[19]==child['start']:identity=True
  if int(fields[2])==child['pid']:group=True
 except (FileNotFoundError,ProcessLookupError,PermissionError,IndexError):pass
assert not identity and not group
out=run/'output'
assert sorted(p.name for p in out.iterdir())==['label_tree_hashes.json','no_metric_gate.json','result.json']
gate=json.loads((out/'no_metric_gate.json').read_text())
labels=json.loads((out/'label_tree_hashes.json').read_text())
result=json.loads((out/'result.json').read_text())
old_gate=json.loads((old_run/'output/no_metric_gate.json').read_text())
assert gate['status']=='PASS_EXP234_CURRENT_ORGANIZER_ALL175_BEFORE_LABEL_ACCESS'
assert gate['target_labels_read'] is False
assert gate['historical_gate_sha256']==@@OLD_GATE_SHA@@
assert gate['historical_result_sha256']==@@OLD_RESULT_SHA@@
assert gate['historical_config_sha256']==@@OLD_CONFIG_SHA@@
assert gate['candidate_hashes']==old_gate['prediction_hashes']
assert gate['baseline_hashes']==old_gate['baseline_hashes']
assert len(gate['candidate_hashes'])==12 and len(gate['baseline_hashes'])==8
assert gate['candidate_count']==gate['baseline_count']==175
assert gate['cohort_sha256']==old_gate['cohort_sha256']
assert gate['organizer_commit']==@@ORGANIZER_COMMIT@@
assert gate['metric_sha256']==@@METRIC_SHA@@
assert gate['runtime']==@@RUNTIME@@
assert gate['synthetic_contract']=={'status':'PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT',
 'positive_division':[1,0,0],'remote_weak_component_division':[0,0,1]}
assert gate['image_metadata']==@@IMAGE_ROWS@@
names={row['dataset'] for row in gate['image_metadata']}
assert len(names)==175
assert set(labels)==names
def tree(path):
 files=sorted((p for p in path.rglob('*') if p.is_file()),key=lambda p:p.relative_to(path).as_posix())
 assert files and (path/'zarr.json').is_file()
 digest=hashlib.sha256();total=0
 for file in files:
  rel=file.relative_to(path).as_posix().encode()
  blob=file.read_bytes();digest.update(len(rel).to_bytes(4,'big'))
  digest.update(rel);digest.update(len(blob).to_bytes(8,'big'))
  digest.update(hashlib.sha256(blob).digest());total+=len(blob)
 return {'sha256':digest.hexdigest(),'files':len(files),'bytes':total}
cohort_doc=json.loads(pathlib.Path(json.loads((old_code/'score_config.json').read_text())['cohort']).read_text())
cohort={row['dataset']:row for row in cohort_doc['rows']}
assert set(cohort)==names
for name in sorted(names):
 assert labels[name]==tree(pathlib.Path(cohort[name]['zarr']).with_suffix('.geff')),name
assert result['status']=='PASS_EXP234_TARGET175_CURRENT_ORGANIZER_METRIC_PAIRED'
assert result['organizer_commit']==@@ORGANIZER_COMMIT@@
assert result['metric_sha256']==@@METRIC_SHA@@
assert result['no_metric_gate_sha256']==sha(out/'no_metric_gate.json')
assert result['label_tree_hashes_sha256']==sha(out/'label_tree_hashes.json')
assert result['kaggle_post'] is False
assert 'historically exposed embryo domains' in result['evidence_class']
old_rows=result['baseline_rows'];new_rows=result['candidate_rows']
assert len(old_rows)==len(new_rows)==175
assert {r['dataset'] for r in old_rows}=={r['dataset'] for r in new_rows}==names
sys.path.insert(0,str(code))
from tracking_cellmot_official import metrics as metric
from check_current_organizer_metric_runtime import validate_runtime,load_metric,synthetic_contract
assert validate_runtime('remote_py311')==gate['runtime']
assert synthetic_contract(load_metric(code))==gate['synthetic_contract']
assert metric.summarise(old_rows)==result['baseline_summary']
assert metric.summarise(new_rows)==result['candidate_summary']
assert result['baseline_summary']['n']==result['candidate_summary']['n']==175
for arm,rows in [('exp214',old_rows),('exp234',new_rows)]:
 for prefix in ('44b6','6bba'):
  subset=[row for row in rows if row['dataset'].startswith(prefix+'_')]
  assert len(subset)==(59 if prefix=='44b6' else 116)
  assert metric.summarise(subset)==result['by_embryo'][arm][prefix]
baseline=result['baseline_summary']['score'];candidate=result['candidate_summary']['score']
assert math.isfinite(baseline) and math.isfinite(candidate)
assert result['delta_vs_exp214']==candidate-baseline
log=(run/'worker.log').read_text().splitlines()
events=[json.loads(line) for line in log if line.startswith('{')]
scored=[e['scored_movie'] for e in events if 'scored_movie' in e]
assert len(scored)==175 and set(scored)==names
assert events[-1]=={'status':result['status'],'score':candidate,
                    'baseline':baseline,'delta':result['delta_vs_exp214']}
assert not (run/'wrapper.log').read_text().strip()
print(json.dumps({'status':'VERIFIED_EXP234_TARGET175_CURRENT_ORGANIZER_METRIC_PAIRED',
 'score':candidate,'baseline':baseline,'delta':result['delta_vs_exp214'],
 'by_embryo':result['by_embryo'],'cohort_count':175,
 'code_manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json'),
 'historical_gate_sha256':sha(old_run/'output/no_metric_gate.json'),
 'historical_result_sha256':sha(old_run/'output/result.json'),
 'no_metric_gate_sha256':sha(out/'no_metric_gate.json'),
 'label_tree_hashes_sha256':sha(out/'label_tree_hashes.json'),
 'result_sha256':sha(out/'result.json'),'launch_sha256':sha(run/'launch.json'),
 'child_sha256':sha(run/'child.json'),'exit_sha256':sha(run/'exit.json'),
 'worker_log_sha256':sha(run/'worker.log'),
 'target_labels_read_after_gate':True,'kaggle_post':False}))
'''
    replacements = {
        "@@CODE@@": repr(code), "@@RUN@@": repr(run),
        "@@OLD_CODE@@": repr(json.loads((ROOT / "work/exp234_current_organizer_v1/score_config.json").read_text())["historical_code"]),
        "@@OLD_RUN@@": repr(json.loads((ROOT / "work/exp234_current_organizer_v1/score_config.json").read_text())["historical_run"]),
        "@@PYTHON@@": repr(python),
        "@@MANIFEST_SHA@@": repr(prepared["code_manifest_sha256"]),
        "@@CONFIG_SHA@@": repr(prepared["score_config_sha256"]),
        "@@OLD_CONFIG_SHA@@": repr(json.loads((ROOT / "work/exp234_current_organizer_v1/score_config.json").read_text())["historical_config_sha256"]),
        "@@OLD_GATE_SHA@@": repr(prepared["historical_gate_sha256"]),
        "@@OLD_RESULT_SHA@@": repr(prepared["historical_result_sha256"]),
        "@@ORGANIZER_COMMIT@@": repr(prepared["organizer_commit"]),
        "@@METRIC_SHA@@": repr(prepared["metric_sha256"]),
        "@@RUNTIME@@": repr({k: v for k, v in env["verify"]["runtime"].items()
                            if k not in ("status", "positive_division",
                                         "remote_weak_component_division", "organizer_commit",
                                         "metric_sha256")}),
        "@@IMAGE_ROWS@@": repr(audit["rows"]),
        "@@LAUNCH@@": repr(launch),
    }
    for token, value in replacements.items():
        source = source.replace(token, value)
    verified = remote(source, python)
    assert verified["status"] == "VERIFIED_EXP234_TARGET175_CURRENT_ORGANIZER_METRIC_PAIRED"
    assert verified["historical_gate_sha256"] == prepared["historical_gate_sha256"]
    assert verified["historical_result_sha256"] == prepared["historical_result_sha256"]
    assert verified["cohort_count"] == 175 and verified["kaggle_post"] is False
    receipt = {"status": verified["status"],
               "evidence_class": "Current organizer metric on sealed, historically exposed 175 graphs; paired EXP214 and EXP234; no Kaggle submission.",
               "prepare_sha256": sha(PREPARE), "stage_sha256": sha(STAGE),
               "env_verify_sha256": sha(ENV_VERIFY), "scale_audit_sha256": sha(SCALE_AUDIT),
               "launch_receipt_sha256": sha(LAUNCH), "verification": verified,
               "original_stopped_handoff_sha256": sha(ROOT / "reports/exp234_target_score_handoff_20260927.json"),
               "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "score": verified["score"],
                      "baseline": verified["baseline"], "delta": verified["delta"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
