"""Stage the epoch-10 source scorer after all eight no-label graphs release."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
INFERENCE_CODE = REMOTE + "/code/exp227_source_graph10_v1_20260927"
INFERENCE_RUN = REMOTE + "/runs/exp227_source_graph10_v1_20260927"
CODE = REMOTE + "/code/exp227_source_graph10_scorer_v1_20260927"
RUN = REMOTE + "/runs/exp227_source_graph10_official_v1_20260927"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    prepared_path = ROOT / "reports/exp227_source_graph10_prepare_20260927.json"
    prepared = json.loads(prepared_path.read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_GRAPH10_NO_LABELS"
    assert prepared["target_labels_read"] is False
    config = json.loads((ROOT / "reports/exp227_source_graph10_config_20260927.json").read_text())
    assert config["experiment"] == "EXP227"
    assert config["code"] == INFERENCE_CODE and config["run"] == INFERENCE_RUN
    assert config["arguments"] == [INFERENCE_CODE + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    leases = [row for row in state["requests"] if row["id"] == config["lease_id"]]
    assert len(leases) == 1 and leases[0]["state"] == "RELEASED"
    assert leases[0]["run_path"] == INFERENCE_RUN

    preflight = '''import hashlib,json,pathlib
code=pathlib.Path(INFERENCE_CODE);run=pathlib.Path(INFERENCE_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==INFERENCE_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==PLAN_SHA
plan=json.loads((code/'plan.json').read_text())
assert plan['experiment']=='EXP227_SOURCE_GRAPH10' and plan['checkpoint_epoch']==10
assert plan['source_embryo']=='44b6' and len(plan['movies'])==8
assert sha(pathlib.Path(plan['checkpoint']))==CHECKPOINT_SHA
assert pathlib.Path(plan['output']).parent==run
ex=json.loads((run/'exit.json').read_text())
sup=json.loads((run/'supervision/complete.json').read_text())
ctl=json.loads((run/'supervision/control.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and sup['exit']==ex
assert ctl['action']=='release' and ctl['queue']['state']=='RELEASED'
assert pathlib.Path(ctl['queue']['run_path'])==run
status=json.loads((run/'output/status.json').read_text())
assert status['status']=='PASS_EXP227_SOURCE_GRAPH10_NO_LABELS'
assert status['target_labels_read'] is False and len(status['records'])==8
assert status['checkpoint_sha256']==CHECKPOINT_SHA and status['plan_sha256']==PLAN_SHA
assert status['movies']==[row['dataset'] for row in plan['movies']]
expected={'status.json'}|{'graph__'+name+suffix for name in status['movies'] for suffix in ('.csv','.json')}
assert {p.name for p in (run/'output').iterdir()}==expected
assert not pathlib.Path(SCORE_CODE).exists() and not pathlib.Path(SCORE_RUN).exists()
print(json.dumps({'status':'PASS_EXP227_SOURCE10_SCORER_PREFLIGHT',
 'inference_status_sha256':sha(run/'output/status.json'),
 'inference_exit_sha256':sha(run/'exit.json')}))
'''.replace("INFERENCE_MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PLAN_SHA", repr(prepared["stage"]["plan_sha256"])).replace(
        "CHECKPOINT_SHA", repr(prepared["preflight"]["checkpoint_sha256"])).replace(
        "INFERENCE_CODE", repr(INFERENCE_CODE)).replace("INFERENCE_RUN", repr(INFERENCE_RUN)).replace(
        "SCORE_CODE", repr(CODE)).replace("SCORE_RUN", repr(RUN))
    gate = ssh("nsu-a100", "python3 -", preflight)
    assert gate["status"] == "PASS_EXP227_SOURCE10_SCORER_PREFLIGHT"

    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp227_source_graph10.py", "score_exp214_paired.py", "score_exp223_official.py")}
    files["exp223_config.json"] = (ROOT / "reports/exp223_official_score_config_v2_20260922.json").read_text()
    score_config = {"experiment": "EXP227_SOURCE_GRAPH10_OFFICIAL",
                    "inference_code": INFERENCE_CODE,
                    "inference_manifest_sha256": prepared["stage"]["manifest_sha256"],
                    "plan_sha256": prepared["stage"]["plan_sha256"],
                    "checkpoint_sha256": prepared["preflight"]["checkpoint_sha256"],
                    "inference_run": INFERENCE_RUN,
                    "inference_status_sha256": gate["inference_status_sha256"],
                    "inference_exit_sha256": gate["inference_exit_sha256"],
                    "evaluator_config": CODE + "/exp223_config.json",
                    "evaluator_config_sha256": sha_bytes(files["exp223_config.json"].encode()),
                    "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
                    "data_dir": REMOTE + "/data/exp213_source_view_20260912",
                    "output": RUN + "/output"}
    files["score_config.json"] = json.dumps(score_config, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir(parents=True)
files=FILES
for name,body in files.items():
 path=code/name;path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_SOURCE10_SCORER','code':str(code),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-quadro", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP227_SOURCE10_SCORER"
    assert staged["score_config_sha256"] == sha_bytes(files["score_config.json"].encode())
    receipt = {"status": "PREPARED_EXP227_SOURCE10_OFFICIAL_SCORER_NO_LABELS",
               "preflight": gate, "stage": staged, "config": score_config,
               "inference_prepare_sha256": sha(prepared_path),
               "target_labels_read": False}
    receipt_path = ROOT / "reports/exp227_source_graph10_scorer_prepare_20260927.json"
    assert not receipt_path.exists()
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "score_config_sha256": staged["score_config_sha256"]}))


if __name__ == "__main__":
    main()
