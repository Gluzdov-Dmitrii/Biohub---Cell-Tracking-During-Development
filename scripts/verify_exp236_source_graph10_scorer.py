"""Read back the completed official EXP236 source6bba score once."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp236_source_graph10_scorer_prepare_20260927.json"
LAUNCH = ROOT / "reports/exp236_source_graph10_scorer_launch_20260927.json"
RECEIPT = ROOT / "reports/exp236_source_graph10_score_20260927.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not RECEIPT.exists(), "Existing score receipt must be reconciled"
    prepared = json.loads(PREPARE.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE10_OFFICIAL_SCORER_NO_LABELS"
    assert prepared["target_labels_read"] is False and prepared["source_labels_read"] is False
    assert prepared["target_data_opened"] is False
    launched = json.loads(LAUNCH.read_text())
    assert launched["status"] == "EXP236_SOURCE10_OFFICIAL_SCORER_LAUNCHED"
    config = prepared["config"]
    assert config["experiment"] == "EXP236_SOURCE_GRAPH10_OFFICIAL"
    assert launched["score_config_sha256"] == prepared["stage"]["score_config_sha256"]
    code = prepared["stage"]["code"]
    run = launched["run"]
    assert config["output"] == run + "/output"
    source = '''import hashlib,json,math,pathlib
code=pathlib.Path(CODE);run=pathlib.Path(RUN);config=json.loads((code/'score_config.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=EXPECTED_MOVIES
assert sha(code/'code_manifest.json')==MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'score_config.json')==CONFIG_SHA
assert config['experiment']=='EXP236_SOURCE_GRAPH10_OFFICIAL'
assert pathlib.Path(config['output']).resolve()==(run/'output').resolve()
assert [row['dataset'] for row in config['inference_graph_hashes']]==names
launch=json.loads((run/'launch.json').read_text());assert launch['run']==str(run)
assert launch['score_config_sha256']==CONFIG_SHA
ex=json.loads((run/'exit.json').read_text())
assert ex['returncode']==0 and ex['timeout'] is False
child=json.loads((run/'child.json').read_text())
assert child['pid']==ex['pid'] and child['start']==ex['start']
assert child['command'][1]==str(code/'score_exp236_source_graph10.py')
assert child['command'][2:]==[str(code/'score_config.json'),'--config-sha256',CONFIG_SHA]
stat=pathlib.Path('/proc')/str(child['pid'])/'stat'
if stat.exists():
 raw=stat.read_text();fields=raw[raw.rfind(')')+2:].split()
 assert fields[0]=='Z' or fields[19]!=child['start']
gate_path=run/'output/no_metric_gate.json';result_path=run/'output/result.json'
assert {p.name for p in (run/'output').iterdir()}=={'no_metric_gate.json','result.json'}
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP236_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS'
assert gate['target_labels_read'] is False and gate['source_labels_read'] is False
assert gate['hashes']==config['inference_graph_hashes']
assert gate['plan_sha256']==config['plan_sha256']
assert gate['checkpoint_sha256']==config['checkpoint_sha256']
assert gate['inference_manifest_sha256']==config['inference_manifest_sha256']
assert gate['inference_status_sha256']==config['inference_status_sha256']
assert gate['inference_exit_sha256']==config['inference_exit_sha256']
assert config['source_manifest_sha256']==SOURCE_MANIFEST_SHA
assert config['source_duplicate_map_sha256']==SOURCE_DUPLICATE_MAP_SHA
assert result['status']=='PASS_EXP236_SOURCE_GRAPH10_OFFICIAL'
assert result['source_labels_read'] is True and result['target_labels_read'] is False
assert result['target_data_opened'] is False
assert result['no_metric_gate_sha256']==sha(gate_path)
assert result['checkpoint_sha256']==config['checkpoint_sha256']
assert [row['dataset'] for row in gate['hashes']]==names
assert [row['dataset'] for row in result['rows']]==names
assert result['evidence_class']=='source6bba inner validation used during training monitoring; not target OOF'
assert math.isfinite(result['summary']['score'])
print(json.dumps({'status':'VERIFIED_EXP236_SOURCE10_OFFICIAL',
 'source_score':result['summary']['score'],
 'result_sha256':sha(result_path),'gate_sha256':sha(gate_path),
 'checkpoint_sha256':config['checkpoint_sha256'],'rows':11,
 'evidence_class':result['evidence_class']}))
'''.replace("SOURCE_MANIFEST_SHA", repr(config["source_manifest_sha256"])).replace(
        "SOURCE_DUPLICATE_MAP_SHA", repr(config["source_duplicate_map_sha256"])).replace(
        "MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "CONFIG_SHA", repr(prepared["stage"]["score_config_sha256"])).replace(
        "EXPECTED_MOVIES", repr([
            "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1",
            "6bba_786893ac", "6bba_825bd1c6", "6bba_a5e926bb",
            "6bba_b329af44", "6bba_b693381b", "6bba_bb9f20c3",
            "6bba_f20478e9", "6bba_f4ae811c",
        ])).replace(
        "CODE", repr(code)).replace("RUN", repr(run))
    verified = ssh("nsu-quadro", "python3 -", source)
    assert verified["status"] == "VERIFIED_EXP236_SOURCE10_OFFICIAL"
    receipt = {**verified, "prepare_receipt_sha256": sha(PREPARE),
               "launch_receipt_sha256": sha(LAUNCH),
               "source_labels_read": True, "target_labels_read": False}
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
