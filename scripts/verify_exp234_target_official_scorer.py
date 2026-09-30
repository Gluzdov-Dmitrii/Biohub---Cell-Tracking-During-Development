"""Read back the completed EXP234 official target175 scorer exactly once."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp234_target_official_scorer_prepare_20260927.json"
LAUNCH = ROOT / "reports/exp234_target_official_scorer_launch_20260927.json"
COORDINATOR = ROOT / "reports/exp234_target_recovery_v2_20260927.json"
ORIGINAL = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
RELEASE = ROOT / "reports/exp234_target_release_manifest_v2_20260927.json"
RECEIPT = ROOT / "reports/exp234_target_official_score_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def remote_probe(prepared, launched):
    """Build a read-only remote check; the scorer has already exited."""
    config = prepared["config"]
    stage = prepared["stage"]
    code = stage["code"]
    run = launched["run"]
    source = '''import hashlib,json,math,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert manifest['score_exp234_target_official.py']==@@SCORER_SHA@@
for name,digest in manifest.items():
 path=(code/name).resolve()
 assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(code/'release_manifest.json')==@@RELEASE_SHA@@
config=json.loads((code/'score_config.json').read_text())
assert config==@@CONFIG@@
assert pathlib.Path(config['output'])==run/'output'
assert json.loads((run/'launch.json').read_text())==@@LAUNCHED@@
child=json.loads((run/'child.json').read_text())
ex=json.loads((run/'exit.json').read_text())
assert ex['returncode']==0 and ex['timeout'] is False
assert child['pid']==ex['pid'] and child['start']==ex['start']
assert child['command']==[@@PYTHON@@,str(code/'score_exp234_target_official.py'),
                          str(code/'score_config.json'),'--config-sha256',@@CONFIG_SHA@@]
assert (run/'cpu_wrapper.py').is_file() and (run/'worker.log').is_file()
# Both the wrapper process group and scorer process group must be gone.
for stat in pathlib.Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=stat.read_text();fields=raw[raw.rfind(')')+2:].split()
  if fields[0]!='Z':
   assert int(fields[2]) not in (child['pid'],@@WRAPPER_PID@@),str(stat)
   cmd=(stat.parent/'cmdline').read_bytes().replace(b'\\x00',b' ')
   assert str(run/'cpu_wrapper.py').encode() not in cmd,str(stat)
   assert str(code/'score_exp234_target_official.py').encode() not in cmd,str(stat)
 except (FileNotFoundError,ProcessLookupError):
  pass
output=run/'output'
assert {p.name for p in output.iterdir()}=={'no_metric_gate.json','result.json'}
gate_path=output/'no_metric_gate.json';result_path=output/'result.json'
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS'
assert gate['candidate_count']==gate['baseline_count']==175
assert gate['cohort_sha256']==config['cohort_sha256']
assert gate['assignment_sha256']==config['assignment_sha256']
assert gate['release_manifest_sha256']==config['release_manifest_sha256']
assert gate['source_selection']==config['source_selection']
# Match score_exp234_target_official.SOURCES and its gate append order.
tokens=['44b6_chunk%02d'%i for i in range(8)]+['6bba_chunk%02d'%i for i in range(4)]
assert [row['token'] for row in gate['prediction_hashes']]==tokens
assert len(gate['baseline_hashes'])==8
assert sha(config['cohort'])==config['cohort_sha256']
cohort=json.loads(pathlib.Path(config['cohort']).read_text())['rows']
names={row['dataset'] for row in cohort}
assert len(cohort)==len(names)==175
assert sum(name.startswith('44b6_') for name in names)==59
assert sum(name.startswith('6bba_') for name in names)==116
assert result['status']=='PASS_EXP234_SOURCE_SELECTED_TARGET175'
assert result['no_metric_gate_sha256']==sha(gate_path)
assert result['baseline_replay']=='PASS_1e-12'
assert sha(config['baseline_metrics'])==config['baseline_metrics_sha256']
baseline=json.loads(pathlib.Path(config['baseline_metrics']).read_text())
assert abs(result['baseline_summary']['score']-baseline['summary']['public']['score'])<=1e-12
assert math.isfinite(result['candidate_summary']['score'])
assert math.isfinite(result['delta_vs_exp214'])
assert abs(result['delta_vs_exp214']-(result['candidate_summary']['score']-
                                    result['baseline_summary']['score']))<=1e-12
assert set(result['candidate_by_embryo'])=={'44b6','6bba'}
assert all(math.isfinite(row['score']) for row in result['candidate_by_embryo'].values())
rows=result['rows'];assert len(rows)==175
assert {row['dataset'] for row in rows}==names
assert len({row['dataset'] for row in rows})==175
print(json.dumps({'status':'VERIFIED_EXP234_TARGET175_OFFICIAL',
 'official_score':result['candidate_summary']['score'],
 'delta_vs_exp214':result['delta_vs_exp214'],
 'baseline_score':result['baseline_summary']['score'],
 'baseline_replay':result['baseline_replay'],
 'result_sha256':sha(result_path),'gate_sha256':sha(gate_path),
 'rows':175,'target_labels_read_after_graph_gate':True}))
'''
    return (source.replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run))
            .replace("@@MANIFEST_SHA@@", repr(stage["manifest_sha256"]))
            .replace("@@SCORER_SHA@@", repr(sha(ROOT / "scripts/score_exp234_target_official.py")))
            .replace("@@CONFIG_SHA@@", repr(stage["score_config_sha256"]))
            .replace("@@RELEASE_SHA@@", repr(stage["release_manifest_sha256"]))
            .replace("@@CONFIG@@", repr(config)).replace("@@LAUNCHED@@", repr(launched))
            .replace("@@PYTHON@@", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"))
            .replace("@@WRAPPER_PID@@", repr(launched["wrapper_pid"])))


def verify(*, write_receipt):
    assert not RECEIPT.exists(), "Existing score receipt must be reconciled"
    prepared = json.loads(PREPARE.read_text())
    launched = json.loads(LAUNCH.read_text())
    assert prepared["status"] == "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS"
    assert prepared["target_labels_read"] is False
    assert launched["status"] == "EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED"
    assert prepared["coordinator_receipt_sha256"] == sha(COORDINATOR)
    coordinator = json.loads(COORDINATOR.read_text())
    assert coordinator["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    assert coordinator["target_labels_read"] is False
    assert prepared["original_coordinator_receipt_sha256"] == sha(ORIGINAL)
    assert coordinator["original_coordinator_sha256"] == sha(ORIGINAL)
    assert coordinator["completed"][:5] == json.loads(ORIGINAL.read_text())["completed"]
    assert len(coordinator["completed"]) == 12
    assert sum(item["movies"] for item in coordinator["completed"]) == 175
    assert prepared["release_manifest_local_sha256"] == sha(RELEASE)
    stage = prepared["stage"]
    config = prepared["config"]
    assert config["experiment"] == "EXP234_OFFICIAL_TARGET175"
    assert stage["code"] == REMOTE + "/code/exp234_target_official_scorer_v1_20260927"
    assert launched["run"] == REMOTE + "/runs/exp234_target_official_score175_20260927"
    assert config["output"] == launched["run"] + "/output"
    assert launched["score_config_sha256"] == stage["score_config_sha256"]
    verified = ssh("nsu-quadro", "python3 -", remote_probe(prepared, launched))
    assert verified["status"] == "VERIFIED_EXP234_TARGET175_OFFICIAL"
    assert verified["baseline_replay"] == "PASS_1e-12" and verified["rows"] == 175
    receipt = {**verified, "prepare_receipt_sha256": sha(PREPARE),
               "launch_receipt_sha256": sha(LAUNCH),
               "coordinator_receipt_sha256": sha(COORDINATOR),
               "target_labels_read_after_graph_gate": True,
               "metric_identity": "HISTORICAL_EXP214_SUPPORT_PACK_REPLAY",
               "historical_exp214_score": verified["official_score"],
               "current_organizer_score": None,
               "evidence_class": ("Exact EXP214-pinned historical evaluator replay; its "
                                  "weak-component division metric is stale relative to "
                                  "the current organizer local-fork metric. Not a current "
                                  "official score or pristine untouched OOF."),
               "kaggle_post": False}
    if write_receipt:
        RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    print(json.dumps(verify(write_receipt=True)))


if __name__ == "__main__":
    main()
