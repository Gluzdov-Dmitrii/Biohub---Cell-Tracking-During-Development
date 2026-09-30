"""Stage one epoch-10 source graph pilot after EXP227 block02 verifies release."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh
from run_exp227_source_graph10 import validate


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
TRAIN_CODE = REMOTE + "/code/exp227_horaz_source_block02_20260927"
TRAIN_RUN = REMOTE + "/runs/exp227_horaz_source_block02_20260927"
CODE = REMOTE + "/code/exp227_source_graph10_v1_20260927"
RUN = REMOTE + "/runs/exp227_source_graph10_v1_20260927"
TRAIN_MANIFEST_SHA = "c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    prepared = json.loads((ROOT / "reports/exp227_source_block02_prepare_20260927.json").read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_BLOCK02"
    assert prepared["stage"]["manifest_sha256"] == TRAIN_MANIFEST_SHA
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    leases = [item for item in state["requests"]
              if item["id"] == "exp227-horaz-source-block02-20260927"]
    assert len(leases) == 1 and leases[0]["state"] == "RELEASED"
    assert not any(item["state"].startswith("WAITING") and
                   item["project"] != "biohub-cell-tracking-during-development"
                   for item in state["requests"])
    preflight = '''import hashlib,json,pathlib
root=pathlib.Path(ROOT);code=pathlib.Path(TRAIN_CODE);run=pathlib.Path(TRAIN_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==TRAIN_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 assert sha(code/name)==digest,name
assert not pathlib.Path(INFER_CODE).exists() and not pathlib.Path(INFER_RUN).exists()
ex=json.loads((run/'exit.json').read_text());sup=json.loads((run/'supervision/complete.json').read_text())
result_path=run/'output/result.json';result=json.loads(result_path.read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT'
assert result['status']=='PASS_FULL_SOURCE_BLOCK_10_OF_50' and result['target_data_opened'] is False
assert result['completed_epochs']==10
checkpoint=run/'output/fold1/epoch_010.pt'
assert checkpoint.is_file()
manifest_path=code/'source44_manifest.json';assert sha(manifest_path)==SOURCE_MANIFEST_SHA
manifest=json.loads(manifest_path.read_text());train={row['dataset_id'] for row in manifest['train']}
assert len(train)==63 and len(manifest['inner_validation'])==8
movies=[]
for row in manifest['inner_validation']:
 name=row['dataset_id'];assert name.startswith('44b6_') and name not in train
 zarr=pathlib.Path(row['zarr_path']);assert set(p.name for p in zarr.iterdir())=={'0','zarr.json'}
 shape=json.loads((zarr/'0/zarr.json').read_text())['shape']
 assert len(shape)==4 and all(isinstance(v,int) and v>0 for v in shape)
 movies.append({'dataset':name,'zarr':str(zarr),'shape':shape})
print(json.dumps({'status':'PASS_EXP227_SOURCE10_PARENT_PREFLIGHT',
 'checkpoint_sha256':sha(checkpoint),'training_result_sha256':sha(result_path),'movies':movies}))
'''.replace("TRAIN_MANIFEST_SHA", repr(TRAIN_MANIFEST_SHA)).replace(
        "SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "TRAIN_CODE", repr(TRAIN_CODE)).replace("TRAIN_RUN", repr(TRAIN_RUN)).replace(
        "INFER_CODE", repr(CODE)).replace("INFER_RUN", repr(RUN)).replace(
        "ROOT", repr(REMOTE))
    remote = ssh("nsu-a100", "python3 -", preflight)
    assert remote["status"] == "PASS_EXP227_SOURCE10_PARENT_PREFLIGHT"
    plan = {"experiment": "EXP227_SOURCE_GRAPH10", "source_embryo": "44b6",
            "target_embryo": "6bba", "fold": 1, "checkpoint_epoch": 10,
            "source_manifest_sha256": SOURCE_MANIFEST_SHA,
            "checkpoint": TRAIN_RUN + "/output/fold1/epoch_010.pt",
            "checkpoint_sha256": remote["checkpoint_sha256"],
            "training_run": TRAIN_RUN,
            "training_result_sha256": remote["training_result_sha256"],
            "data_root": REMOTE + "/data/exp213_source_view_20260912",
            "code": CODE, "output": RUN + "/output", "movies": remote["movies"]}
    validate(plan)
    infer = (ROOT / "scripts/run_exp227_source_graph10.py").read_text()
    helper = (ROOT / "scripts/run_exp223_inference.py").read_text()
    plan_text = json.dumps(plan, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(TRAIN_CODE);target=pathlib.Path(INFER_CODE)
assert not target.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'code_manifest.json')==TRAIN_MANIFEST_SHA
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 assert sha(source/name)==digest,name
shutil.copytree(source,target)
wrapper=target/'exp227_job.py';body=wrapper.read_text()
old="assert config['script'] == 'run_exp227_source_block02.py'"
assert body.count(old)==1
wrapper.write_text(body.replace(old,"assert config['script'] == 'run_exp227_source_graph10.py'"))
(target/'run_exp227_source_graph10.py').write_text(INFERENCE)
(target/'run_exp223_inference.py').write_text(HELPER)
(target/'plan.json').write_text(PLAN)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
manifest={str(path.relative_to(target)).replace('\\\\','/'):sha(path)
          for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_SOURCE_GRAPH10','code':str(target),
                  'manifest_sha256':sha(target/'code_manifest.json'),
                  'plan_sha256':manifest['plan.json'],
                  'runner_sha256':manifest['run_exp227_source_graph10.py']}))
'''.replace("TRAIN_MANIFEST_SHA", repr(TRAIN_MANIFEST_SHA)).replace(
        "TRAIN_CODE", repr(TRAIN_CODE)).replace("INFER_CODE", repr(CODE)).replace(
        "INFERENCE", repr(infer)).replace("HELPER", repr(helper)).replace(
        "PLAN", repr(plan_text))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP227_SOURCE_GRAPH10"
    assert staged["plan_sha256"] == sha_bytes(plan_text.encode())
    assert staged["runner_sha256"] == sha_bytes(infer.encode())
    config = {"experiment": "EXP227",
              "lease_id": "exp227-source-graph10-v1-20260927",
              "token": "exp227_source_graph10_v1_20260927",
              "code": CODE, "run": RUN, "max_seconds": 3600,
              "cpu_affinity": "0-7", "script": "run_exp227_source_graph10.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    receipt = {"status": "PREPARED_EXP227_SOURCE_GRAPH10_NO_LABELS",
               "preflight": remote, "stage": staged, "movies": 8,
               "target_labels_read": False}
    (ROOT / "reports/exp227_source_graph10_prepare_20260927.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    (ROOT / "reports/exp227_source_graph10_plan_20260927.json").write_text(plan_text)
    (ROOT / "reports/exp227_source_graph10_config_20260927.json").write_text(
        json.dumps(config, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "checkpoint_sha256": remote["checkpoint_sha256"],
                      "manifest_sha256": staged["manifest_sha256"]}))


if __name__ == "__main__":
    main()
