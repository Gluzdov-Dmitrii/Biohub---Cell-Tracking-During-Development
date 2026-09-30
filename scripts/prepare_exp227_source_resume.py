"""Stage immutable EXP227 source44 epochs 11–20 after exact block02 release."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh
from run_exp227_source_resume import (INITIAL_OUTPUT_ROOT, PARENT_CHECKPOINT_SHA,
                                      PARENT_RESULT_SHA, PARENT_RUN, REMOTE, RUN,
                                      SOURCE_MANIFEST_SHA, validate)


ROOT = Path(__file__).resolve().parents[1]
PARENT_CODE = REMOTE + "/code/exp227_horaz_source_block02_20260927"
CODE = REMOTE + "/code/exp227_horaz_source_block03_20260927"
PARENT_MANIFEST_SHA = "c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26"
PARENT_PLAN_SHA = "cfb672acab7bbd3ca2b551b6f688503dbd109457b53ce68bf04ce8267ef03ff1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    parent_plan_path = ROOT / "reports/exp227_source_block02_plan_20260927.json"
    parent_prepare_path = ROOT / "reports/exp227_source_block02_prepare_20260927.json"
    parent_config_path = ROOT / "reports/exp227_source_block02_config_20260927.json"
    plan_path = ROOT / "reports/exp227_source_block03_plan_20260927.json"
    config_path = ROOT / "reports/exp227_source_block03_config_20260927.json"
    receipt_path = ROOT / "reports/exp227_source_block03_prepare_20260927.json"
    assert not any(path.exists() for path in (plan_path, config_path, receipt_path))
    prepared = json.loads(parent_prepare_path.read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_BLOCK02"
    assert prepared["stage"]["code"] == PARENT_CODE
    assert prepared["stage"]["manifest_sha256"] == PARENT_MANIFEST_SHA
    assert prepared["stage"]["plan_sha256"] == PARENT_PLAN_SHA
    # Python text reads normalize the local CRLF receipt; the immutable Linux
    # code bundle stores LF bytes and its manifest hashes those exact bytes.
    assert sha_bytes(parent_plan_path.read_text().encode()) == PARENT_PLAN_SHA
    parent_plan = json.loads(parent_plan_path.read_text())
    assert parent_plan["block_end_epoch"] == 10
    assert parent_plan["parent_checkpoint"] == INITIAL_OUTPUT_ROOT + "/fold1/last.pt"
    assert parent_plan["output"] == PARENT_RUN + "/output"
    assert parent_plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    parent_config = json.loads(parent_config_path.read_text())
    assert parent_config["experiment"] == "EXP227"
    assert parent_config["code"] == PARENT_CODE and parent_config["run"] == PARENT_RUN
    assert parent_config["script"] == "run_exp227_source_block02.py"
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    parents = [row for row in state["requests"] if row["id"] == parent_config["lease_id"]]
    assert len(parents) == 1 and parents[0]["state"] == "RELEASED"
    assert parents[0]["run_path"] == PARENT_RUN

    preflight = '''import hashlib,json,pathlib
code=pathlib.Path(PARENT_CODE);run=pathlib.Path(PARENT_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==PARENT_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==PARENT_PLAN_SHA
assert sha(code/'source44_manifest.json')==SOURCE_MANIFEST_SHA
result_path=run/'output/result.json';assert sha(result_path)==PARENT_RESULT_SHA
result=json.loads(result_path.read_text())
assert result['status']=='PASS_FULL_SOURCE_BLOCK_10_OF_50'
assert result['completed_epochs']==10 and result['planned_epochs']==50
assert result['plan_sha256']==PARENT_PLAN_SHA
assert result['target_data_opened'] is False and not result['denied_accesses']
assert result['checkpoint_reload']=='PASS_weights_only'
exit_record=json.loads((run/'exit.json').read_text())
supervision=json.loads((run/'supervision/complete.json').read_text())
control=json.loads((run/'supervision/control.json').read_text())
assert exit_record['returncode']==0 and exit_record['hard_timeout'] is False
assert supervision['status']=='RELEASED_AFTER_VERIFIED_EXIT' and supervision['exit']==exit_record
assert control['action']=='release' and control['queue']['state']=='RELEASED'
assert pathlib.Path(control['queue']['run_path'])==run
checkpoint=run/'output/fold1/last.pt'
assert sha(checkpoint)==result['checkpoint_sha256']==PARENT_CHECKPOINT_SHA
history_path=run/'output/fold1/history.json';history=json.loads(history_path.read_text())
assert [row['epoch'] for row in history]==list(range(1,11))
assert result['history']==history
manifest=json.loads((code/'source44_manifest.json').read_text())
assert set(result['opened_datasets'])=={r['dataset_id'] for r in manifest['train']+manifest['inner_validation']}
assert not pathlib.Path(NEXT_CODE).exists() and not pathlib.Path(NEXT_RUN).exists()
print(json.dumps({'status':'PASS_EXP227_BLOCK03_PARENT_PREFLIGHT',
 'checkpoint_sha256':sha(checkpoint),'history_sha256':sha(history_path),
 'result_sha256':sha(result_path)}))
'''.replace("PARENT_MANIFEST_SHA", repr(PARENT_MANIFEST_SHA)).replace(
        "PARENT_PLAN_SHA", repr(PARENT_PLAN_SHA)).replace(
        "SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "PARENT_CHECKPOINT_SHA", repr(PARENT_CHECKPOINT_SHA)).replace(
        "PARENT_RESULT_SHA", repr(PARENT_RESULT_SHA)).replace(
        "PARENT_CODE", repr(PARENT_CODE)).replace("PARENT_RUN", repr(PARENT_RUN)).replace(
        "NEXT_CODE", repr(CODE)).replace("NEXT_RUN", repr(RUN))
    parent = ssh("nsu-a100", "python3 -", preflight)
    assert parent["status"] == "PASS_EXP227_BLOCK03_PARENT_PREFLIGHT"
    assert parent["checkpoint_sha256"] == PARENT_CHECKPOINT_SHA
    assert parent["result_sha256"] == PARENT_RESULT_SHA

    plan = {**parent_plan,
            "purpose": "source_only_full_training_block03", "seed": 3407,
            "start_epoch": 11, "block_end_epoch": 20,
            "parent_completed_epochs": 10, "planned_epochs": 50, "resume": True,
            "initial_output_root": INITIAL_OUTPUT_ROOT,
            "parent_checkpoint": PARENT_RUN + "/output/fold1/last.pt",
            "parent_checkpoint_sha256": PARENT_CHECKPOINT_SHA,
            "parent_history_sha256": parent["history_sha256"],
            "parent_result_sha256": PARENT_RESULT_SHA,
            "output": RUN + "/output"}
    validate(plan)
    plan_text = json.dumps(plan, indent=2) + "\n"
    runner = (ROOT / "scripts/run_exp227_source_resume.py").read_text()
    stage = '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(PARENT_CODE);target=pathlib.Path(NEXT_CODE)
assert not target.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'code_manifest.json')==PARENT_MANIFEST_SHA
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 path=(source/name).resolve();assert path.is_relative_to(source.resolve()) and sha(path)==digest,name
shutil.copytree(source,target)
wrapper=target/'exp227_job.py';body=wrapper.read_text()
old="assert config['script'] == 'run_exp227_source_block02.py'"
new="assert config['script'] == 'run_exp227_source_resume.py'"
assert body.count(old)==1
wrapper.write_text(body.replace(old,new))
(target/'run_exp227_source_resume.py').write_text(RUNNER)
(target/'plan.json').write_text(PLAN)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
manifest={path.relative_to(target).as_posix():sha(path)
          for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_SOURCE_BLOCK03','code':str(target),
 'manifest_sha256':sha(target/'code_manifest.json'),
 'plan_sha256':sha(target/'plan.json'),
 'runner_sha256':sha(target/'run_exp227_source_resume.py')}))
'''.replace("PARENT_MANIFEST_SHA", repr(PARENT_MANIFEST_SHA)).replace(
        "PARENT_CODE", repr(PARENT_CODE)).replace("NEXT_CODE", repr(CODE)).replace(
        "RUNNER", repr(runner)).replace("PLAN", repr(plan_text))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP227_SOURCE_BLOCK03"
    assert staged["code"] == CODE
    assert staged["plan_sha256"] == sha_bytes(plan_text.encode())
    assert staged["runner_sha256"] == sha_bytes(runner.encode())
    config = {"experiment": "EXP227",
              "lease_id": "exp227-horaz-source-block03-20260927",
              "token": "exp227_horaz_source_block03_20260927",
              "code": CODE, "run": RUN, "max_seconds": 21600,
              "cpu_affinity": "0-7", "script": "run_exp227_source_resume.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    plan_path.write_bytes(plan_text.encode())
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    receipt = {"status": "PREPARED_EXP227_SOURCE_BLOCK03_NO_TARGET_ACCESS",
               "preflight": parent, "stage": staged,
               "parent_prepare_sha256": sha(parent_prepare_path),
               "train_count": 63, "inner_count": 8, "epochs": [11, 20],
               "target_data_opened": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "manifest_sha256": staged["manifest_sha256"],
                      "plan_sha256": staged["plan_sha256"]}))


if __name__ == "__main__":
    main()
