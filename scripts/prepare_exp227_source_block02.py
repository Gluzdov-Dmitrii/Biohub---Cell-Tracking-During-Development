"""Stage the immutable epoch-5-to-10 EXP227 continuation after parent release."""
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import QUEUE, ssh
from run_exp227_source_block02 import validate
import shlex


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
PARENT_CODE = REMOTE + "/code/exp227_horaz_source_block01_20260922"
PARENT_RUN = REMOTE + "/runs/exp227_horaz_source_block01_20260922"
CODE = REMOTE + "/code/exp227_horaz_source_block02_20260927"
RUN = REMOTE + "/runs/exp227_horaz_source_block02_20260927"
PARENT_MANIFEST_SHA = "615daf8b86c0bf5986928697967fcb195a7a330cc9e52c7dda9f3793a353581c"
PARENT_HISTORY_SHA = "de37cb2848183304713e1e37e04f14eea056bfb7ca79b936b46e87a15f74291a"
PARENT_CHECKPOINT_SHA = "c7ecfe2e4ff0f5c039cd4952fe43047e44ff60701016a3ebba3fd932aa543d2e"


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    prior = json.loads((ROOT / "work/horaz_development_20260922/exp227/plan.json").read_text())
    assert prior["experiment"] == "EXP227" and prior["source_embryo"] == "44b6"
    assert prior["block_end_epoch"] == 5 and prior["planned_epochs"] == 50
    plan = {**prior, "purpose": "source_only_full_training_block02",
            "start_epoch": 6, "block_end_epoch": 10, "resume": True,
            "parent_checkpoint": PARENT_RUN + "/output/fold1/last.pt",
            "parent_checkpoint_sha256": PARENT_CHECKPOINT_SHA,
            "parent_history_sha256": PARENT_HISTORY_SHA,
            "output": RUN + "/output"}
    validate(plan)
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    parent_leases = [item for item in queue["requests"]
                     if item["id"] == "exp227-horaz-source-block01-20260922"]
    assert len(parent_leases) == 1 and parent_leases[0]["state"] == "RELEASED"
    assert not any(item["state"].startswith("WAITING") and
                   item["project"] != "biohub-cell-tracking-during-development"
                   for item in queue["requests"])

    preflight = '''import hashlib,json,pathlib
root=pathlib.Path(ROOT);code=pathlib.Path(PARENT_CODE);run=pathlib.Path(PARENT_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==PARENT_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 assert sha(code/name)==digest,name
assert not pathlib.Path(TARGET_CODE).exists() and not pathlib.Path(TARGET_RUN).exists()
ex=json.loads((run/'exit.json').read_text());sup=json.loads((run/'supervision/complete.json').read_text())
result=json.loads((run/'output/result.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT'
assert result['status']=='PASS_FULL_SOURCE_BLOCK_5_OF_50' and result['target_data_opened'] is False
assert result['checkpoint_sha256']==sha(run/'output/fold1/last.pt')==PARENT_CHECKPOINT_SHA
assert sha(run/'output/fold1/history.json')==PARENT_HISTORY_SHA
print(json.dumps({'status':'PASS_EXP227_BLOCK02_PARENT_PREFLIGHT','checkpoint_sha256':PARENT_CHECKPOINT_SHA}))
'''.replace("ROOT", repr(REMOTE)).replace("PARENT_CODE", repr(PARENT_CODE)).replace(
        "PARENT_RUN", repr(PARENT_RUN)).replace("PARENT_MANIFEST_SHA", repr(PARENT_MANIFEST_SHA)).replace(
        "TARGET_CODE", repr(CODE)).replace("TARGET_RUN", repr(RUN)).replace(
        "PARENT_CHECKPOINT_SHA", repr(PARENT_CHECKPOINT_SHA)).replace(
        "PARENT_HISTORY_SHA", repr(PARENT_HISTORY_SHA))
    pre = ssh("nsu-a100", "python3 -", preflight)
    assert pre["status"] == "PASS_EXP227_BLOCK02_PARENT_PREFLIGHT"

    new_runner = (ROOT / "scripts/run_exp227_source_block02.py").read_text()
    plan_text = json.dumps(plan, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(PARENT_CODE);target=pathlib.Path(TARGET_CODE)
assert not target.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'code_manifest.json')==PARENT_MANIFEST_SHA
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 assert sha(source/name)==digest,name
shutil.copytree(source,target)
wrapper=target/'exp227_job.py';body=wrapper.read_text()
old="assert config['script'] == 'run_exp227_source_block.py'"
assert body.count(old)==1
wrapper.write_text(body.replace(old,"assert config['script'] == 'run_exp227_source_block02.py'"))
(target/'run_exp227_source_block02.py').write_text(RUNNER)
(target/'plan.json').write_text(PLAN)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
manifest={str(path.relative_to(target)).replace('\\\\','/'):sha(path)
          for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_BLOCK02','code':str(target),
                  'manifest_sha256':sha(target/'code_manifest.json'),
                  'plan_sha256':manifest['plan.json'],
                  'runner_sha256':manifest['run_exp227_source_block02.py']}))
'''.replace("PARENT_CODE", repr(PARENT_CODE)).replace("TARGET_CODE", repr(CODE)).replace(
        "PARENT_MANIFEST_SHA", repr(PARENT_MANIFEST_SHA)).replace(
        "RUNNER", repr(new_runner)).replace("PLAN", repr(plan_text))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP227_BLOCK02"
    assert staged["plan_sha256"] == sha_bytes(plan_text.encode())
    assert staged["runner_sha256"] == sha_bytes(new_runner.encode())
    config = {"experiment": "EXP227",
              "lease_id": "exp227-horaz-source-block02-20260927",
              "token": "exp227_horaz_source_block02_20260927",
              "code": CODE, "run": RUN, "max_seconds": 10800,
              "cpu_affinity": "0-7", "script": "run_exp227_source_block02.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    receipt = {"status": "PREPARED_EXP227_SOURCE_BLOCK02",
               "parent": pre, "stage": staged,
               "train_count": 63, "inner_count": 8,
               "epochs": [6, 10], "target_labels_opened": False}
    (ROOT / "reports/exp227_source_block02_prepare_20260927.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    (ROOT / "reports/exp227_source_block02_plan_20260927.json").write_text(plan_text)
    (ROOT / "reports/exp227_source_block02_config_20260927.json").write_text(
        json.dumps(config, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "plan_sha256": staged["plan_sha256"]}))


if __name__ == "__main__":
    main()
