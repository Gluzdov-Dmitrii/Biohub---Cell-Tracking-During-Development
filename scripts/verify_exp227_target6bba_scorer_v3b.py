"""Read back an exited EXP227 target116 scorer without starting a new run."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from launch_exp227_target6bba_scorer_v3b import ROOT, REMOTE, CODE, RUN, STAGE, RECEIPT as LAUNCH, PYTHON


RECEIPT = ROOT / "reports/exp227_target6bba_current_score_v3b_20260927.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def remote_probe(prepared, launched):
    return '''import hashlib,json,math,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
config=json.loads((code/'score_config.json').read_text())
assert config==@@CONFIG@@
assert config['output']==str(run/'output')
launch=json.loads((run/'launch.json').read_text())
assert launch==@@REMOTE_LAUNCH@@
child=json.loads((run/'child.json').read_text())
ex=json.loads((run/'exit.json').read_text())
assert ex['returncode']==0 and ex['timeout'] is False
assert child['pid']==ex['pid'] and child['start']==ex['start']
assert child['command']==[@@PYTHON@@,str(code/'score_exp227_target6bba_current_v3b.py'),
                          str(code/'score_config.json'),'--config-sha256',@@CONFIG_SHA@@]
assert (run/'cpu_wrapper.py').is_file() and (run/'worker.log').is_file()
for stat in pathlib.Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=stat.read_text();fields=raw[raw.rfind(')')+2:].split()
  if fields[0]!='Z':
   assert int(fields[2]) not in (child['pid'],@@WRAPPER_PID@@),str(stat)
   cmd=(stat.parent/'cmdline').read_bytes().replace(b'\\x00',b' ')
   assert str(run/'cpu_wrapper.py').encode() not in cmd,str(stat)
   assert str(code/'score_exp227_target6bba_current_v3b.py').encode() not in cmd,str(stat)
 except (FileNotFoundError,ProcessLookupError):pass
output=run/'output'
assert {p.name for p in output.iterdir()}=={'no_metric_gate.json','label_tree_hashes.json','result.json'}
gate_path=output/'no_metric_gate.json';result_path=output/'result.json'
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS'
assert gate['candidate_count']==gate['baseline_count']==116
assert gate['target_labels_read'] is False
assert gate['assignment_sha256']==config['assignment_sha256']
assert gate['selection_sha256']==config['selection_sha256']
assert gate['checkpoint_sha256']==config['checkpoint_sha256']
assert gate['coordinator_sha256']==config['coordinator_sha256']
assert gate['evaluator_config_sha256']==config['evaluator_config_sha256']
assert gate['current_metrics_sha256']==config['current_metrics_sha256']
assert gate['current_division_sha256']==config['current_division_sha256']
assert gate['tracksdata_commit']==config['tracksdata_commit']
assert gate['image_scale_audit_sha256']==config['image_scale_audit_sha256']
assert gate['baseline_target_rows_sha256']==config['baseline_target_rows_sha256']
assert gate['successor_prepare_sha256']==config['successor_prepare_sha256']
assert gate['successor_stage_sha256']==config['successor_stage_sha256']
assert gate['final_graph_hashes_sha256']==config['final_graph_hashes_sha256']
assert len(gate['image_metadata'])==116
assert [r['dataset'] for r in gate['graph_hashes']]==config['target_ids']
assert len(gate['live_release'])==8 and all(r['state']=='RELEASED' for r in gate['live_release'])
assert len(gate['baseline_hashes'])==8
assert result['status']=='PASS_EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3B'
assert result['evidence_class']==config['evidence_class']
assert result['target_labels_read_after_graph_gate'] is True
assert result['no_metric_gate_sha256']==sha(gate_path)
assert result['label_tree_hashes_sha256']==sha(output/'label_tree_hashes.json')
labels=json.loads((output/'label_tree_hashes.json').read_text())
assert set(labels)==set(config['target_ids']) and len(labels)==116
assert result['baseline_replay']=='PASS_1e-12'
assert result['metric_source']=='current organizer commit 075fc5f5a52d11077f9dc2b074644618f26939e2'
assert result['current_metrics_sha256']==config['current_metrics_sha256']
assert result['current_division_sha256']==config['current_division_sha256']
assert len(result['candidate_rows'])==len(result['baseline_rows'])==len(result['legacy_exp214_baseline_rows'])==116
assert {r['dataset'] for r in result['candidate_rows']}==set(config['target_ids'])
assert {r['dataset'] for r in result['baseline_rows']}==set(config['target_ids'])
assert {r['dataset'] for r in result['legacy_exp214_baseline_rows']}==set(config['target_ids'])
assert len({r['dataset'] for r in result['candidate_rows']})==116
assert len({r['dataset'] for r in result['baseline_rows']})==116
assert sha(config['baseline_metrics'])==config['baseline_metrics_sha256']
baseline=json.loads(pathlib.Path(config['baseline_metrics']).read_text())
old={r['dataset']:r for r in baseline['rows']['public']}
for row in result['legacy_exp214_baseline_rows']:
 expected=old[row['dataset']];assert set(row)==set(expected)
 for key,value in expected.items():
  if isinstance(value,(float,int)) and not isinstance(value,bool):
   assert math.isclose(float(row[key]),float(value),rel_tol=0,abs_tol=1e-12),row['dataset']
  else:assert row[key]==value,row['dataset']
assert math.isfinite(result['baseline_summary']['score'])
assert math.isfinite(result['candidate_summary']['score'])
assert math.isfinite(result['delta_vs_current_baseline'])
assert math.isclose(result['delta_vs_current_baseline'],result['candidate_summary']['score']-
                    result['baseline_summary']['score'],rel_tol=0,abs_tol=1e-12)
print(json.dumps({'status':'VERIFIED_EXP227_TARGET116_CURRENT_V3B',
 'official_score':result['candidate_summary']['score'],
 'baseline_score':result['baseline_summary']['score'],
 'delta_vs_current_baseline':result['delta_vs_current_baseline'],
 'baseline_replay':'PASS_1e-12','rows':116,
 'gate_sha256':sha(gate_path),'result_sha256':sha(result_path),
 'evidence_class':result['evidence_class']}))
'''.replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@MANIFEST_SHA@@", repr(prepared["stage"]["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(prepared["stage"]["score_config_sha256"])).replace(
        "@@CONFIG@@", repr(prepared["config"])).replace(
        "@@REMOTE_LAUNCH@@", repr({key: value for key, value in launched.items()
                                    if key not in ("intent_sha256", "stage_receipt_sha256", "target_score_computed")})).replace(
        "@@PYTHON@@", repr(PYTHON)).replace("@@WRAPPER_PID@@", repr(launched["wrapper_pid"]))


def verify():
    assert not RECEIPT.exists(), "Existing official score receipt requires reconciliation"
    prepared = json.loads(STAGE.read_text())
    launched = json.loads(LAUNCH.read_text())
    assert prepared["status"] == "STAGED_EXP227_TARGET116_CURRENT_SCORER_V3B_NO_LABELS"
    assert launched["status"] == "LAUNCHED_EXP227_TARGET116_CURRENT_SCORER_V3B"
    coordinator = Path(prepared["coordinator_local_path"])
    assert prepared["coordinator_local_sha256"] == sha(coordinator)
    assert prepared["stage"]["code"] == CODE and launched["run"] == RUN
    assert launched["score_config_sha256"] == prepared["stage"]["score_config_sha256"]
    verified = ssh("nsu-quadro", "python3 -", remote_probe(prepared, launched))
    assert verified["status"] == "VERIFIED_EXP227_TARGET116_CURRENT_V3B"
    assert verified["baseline_replay"] == "PASS_1e-12" and verified["rows"] == 116
    receipt = {**verified, "stage_receipt_sha256": sha(STAGE),
               "launch_receipt_sha256": sha(LAUNCH),
               "coordinator_local_path": str(coordinator),
               "coordinator_local_sha256": sha(coordinator),
               "target_labels_read_after_graph_gate": True,
               "kaggle_post": False}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    print(json.dumps(verify()))
