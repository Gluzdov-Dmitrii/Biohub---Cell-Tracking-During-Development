"""Stage EXP236 epoch10 inner11 no-label graphs after the exact v2 chain releases."""
import hashlib
import json
from pathlib import Path

from continue_exp236_source_v2_to_epoch10 import (
    EPOCHS, audit_block, lease_for, local_block,
    queue_status,
)
from monitor_exp213_job import ssh
from run_exp236_source_graph10_v2 import (
    CODE, DUPLICATE_MAP_SHA, INNER_IDS, POLICY, REMOTE, RUN, SOURCE_BUNDLE_SHA,
    SOURCE_MANIFEST_SHA, TRAIN_RUN, validate,
)


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_CONTROLLER_RECEIPT = ROOT / "reports/exp236_source_v2_to_epoch10_20260927.json"
CONTROLLER_RECEIPT = ROOT / "reports/exp236_source_v2_epoch10_recovery_20260927.json"
TRAIN_CODE = REMOTE + "/code/exp236_horaz_source6bba_block04_v2_20260927"
PLAN_PATH = ROOT / "reports/exp236_source_graph10_v2_plan_20260927.json"
CONFIG_PATH = ROOT / "reports/exp236_source_graph10_v2_config_20260927.json"
PREPARE_PATH = ROOT / "reports/exp236_source_graph10_v2_prepare_20260927.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def verify_parent_chain():
    """Re-audit all four released blocks and match the finite controller receipt."""
    controller = json.loads(CONTROLLER_RECEIPT.read_text())
    assert controller["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    original = json.loads(ORIGINAL_CONTROLLER_RECEIPT.read_text())
    assert original["status"] == "STOPPED_EXP236_SOURCE_V2_CONTINUATION"
    assert controller["original_receipt_sha256"] == sha(ORIGINAL_CONTROLLER_RECEIPT)
    assert controller["target_data_opened"] is False
    assert controller["final_audit"]["completed_epochs"] == 10
    queue = queue_status()
    chain = []
    parent = None
    for block, epoch in enumerate(EPOCHS.values(), 1):
        prepared, config, training_plan, launch = local_block(block, launched=True)
        assert launch is not None
        assert training_plan["block_end_epoch"] == epoch
        assert training_plan["source_duplicate_policy"] == POLICY
        assert training_plan["source_duplicate_map_sha256"] == DUPLICATE_MAP_SHA
        assert training_plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
        assert training_plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
        assert [row["dataset_id"] for row in training_plan["inner_validation"]] == list(INNER_IDS)
        lease = lease_for(queue, block)
        assert lease["state"] == "RELEASED" and lease["alias"] == config["alias"]
        assert lease["run_path"] == config["run"]
        audited = audit_block(block, parent)
        assert controller[f"block{block:02d}_audit"] == audited
        assert audited["completed_epochs"] == epoch and audited["target_data_opened"] is False
        assert audited["manifest_sha256"] == prepared["stage"]["manifest_sha256"]
        assert audited["plan_sha256"] == prepared["stage"]["plan_sha256"]
        chain.append({**audited, "code": config["code"], "run": config["run"]})
        parent = audited
    assert controller["final_audit"] == parent
    assert chain[-1]["run"] == TRAIN_RUN and chain[-1]["code"] == TRAIN_CODE
    return chain, sha(CONTROLLER_RECEIPT)


def main():
    assert not any(path.exists() for path in (PLAN_PATH, CONFIG_PATH, PREPARE_PATH))
    chain, controller_sha = verify_parent_chain()
    preflight = '''import hashlib,json,pathlib
code=pathlib.Path(@@TRAIN_CODE@@);run=pathlib.Path(@@TRAIN_RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==@@PLAN_SHA@@
assert sha(code/'source6bba_manifest.json')==@@SOURCE_MANIFEST_SHA@@
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@DUPLICATE_MAP_SHA@@
assert not pathlib.Path(@@INFER_CODE@@).exists() and not pathlib.Path(@@INFER_RUN@@).exists()
plan=json.loads((code/'plan.json').read_text())
assert plan['experiment']=='EXP236' and plan['block_end_epoch']==10 and plan['planned_epochs']==50
assert plan['fold']==0 and plan['source_embryo']=='6bba' and plan['target_embryo']=='44b6'
assert plan['source_bundle_sha256']==@@SOURCE_BUNDLE_SHA@@
assert plan['source_duplicate_policy']==@@POLICY@@
assert plan['source_duplicate_map_sha256']==@@DUPLICATE_MAP_SHA@@
assert plan['excluded_pairs_by_split']=={'train':824,'inner_validation':103}
assert plan['removed_sampled_windows_by_split']=={'train':809,'inner_validation':101}
source=json.loads((code/'source6bba_manifest.json').read_text())
assert source['train']==plan['train'] and source['inner_validation']==plan['inner_validation']
assert len(source['train'])==115
assert [row['dataset_id'] for row in source['inner_validation']]==@@INNER_IDS@@
result_path=run/'output/result.json';assert sha(result_path)==@@RESULT_SHA@@
result=json.loads(result_path.read_text())
assert result['status']=='PASS_EXP236_SOURCE_BLOCK_10_OF_50'
assert result['completed_epochs']==10 and result['planned_epochs']==50
assert result['target_data_opened'] is False and result['denied_accesses']==[]
assert result['checkpoint_reload']=='PASS_weights_only'
assert result['source_duplicate_policy']==@@POLICY@@
assert result['source_duplicate_map_sha256']==@@DUPLICATE_MAP_SHA@@
assert result['excluded_pairs_by_split']==plan['excluded_pairs_by_split']
assert result['removed_sampled_windows_by_split']==plan['removed_sampled_windows_by_split']
assert result['opened_datasets']==sorted(row['dataset_id'] for row in plan['train']+plan['inner_validation'])
assert result['checkpoint_sha256']==@@CHECKPOINT_SHA@@
history_path=run/'output/fold0/history.json';assert sha(history_path)==@@HISTORY_SHA@@
history=json.loads(history_path.read_text())
assert [row['epoch'] for row in history]==list(range(1,11)) and result['history']==history
checkpoint=run/'output/fold0/last.pt';assert sha(checkpoint)==@@CHECKPOINT_SHA@@
ex=json.loads((run/'exit.json').read_text());assert sha(run/'exit.json')==@@EXIT_SHA@@
sup=json.loads((run/'supervision/complete.json').read_text())
ctl=json.loads((run/'supervision/control.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and sup['exit']==ex
assert ctl['action']=='release' and ctl['queue']['state']=='RELEASED'
assert pathlib.Path(ctl['queue']['run_path']).resolve()==run.resolve()
movies=[]
for row in source['inner_validation']:
 name=row['dataset_id'];assert name.startswith('6bba_')
 zarr=pathlib.Path(row['zarr_path']);assert set(p.name for p in zarr.iterdir())=={'0','zarr.json'}
 shape=json.loads((zarr/'0/zarr.json').read_text())['shape']
 assert len(shape)==4 and all(isinstance(v,int) and v>0 for v in shape)
 movies.append({'dataset':name,'zarr':str(zarr),'shape':shape})
print(json.dumps({'status':'PASS_EXP236_SOURCE10_V2_PARENT_PREFLIGHT',
 'checkpoint_sha256':sha(checkpoint),'training_result_sha256':sha(result_path),
 'training_history_sha256':sha(history_path),'movies':movies}))
'''.replace("@@TRAIN_CODE@@", repr(TRAIN_CODE)).replace("@@TRAIN_RUN@@", repr(TRAIN_RUN)).replace(
        "@@MANIFEST_SHA@@", repr(chain[-1]["manifest_sha256"])).replace(
        "@@PLAN_SHA@@", repr(chain[-1]["plan_sha256"])).replace(
        "@@SOURCE_MANIFEST_SHA@@", repr(SOURCE_MANIFEST_SHA)).replace(
        "@@DUPLICATE_MAP_SHA@@", repr(DUPLICATE_MAP_SHA)).replace(
        "@@SOURCE_BUNDLE_SHA@@", repr(SOURCE_BUNDLE_SHA)).replace(
        "@@POLICY@@", repr(POLICY)).replace("@@INNER_IDS@@", repr(list(INNER_IDS))).replace(
        "@@INFER_CODE@@", repr(CODE)).replace("@@INFER_RUN@@", repr(RUN)).replace(
        "@@RESULT_SHA@@", repr(chain[-1]["result_sha256"])).replace(
        "@@HISTORY_SHA@@", repr(chain[-1]["history_sha256"])).replace(
        "@@CHECKPOINT_SHA@@", repr(chain[-1]["checkpoint_sha256"])).replace(
        "@@EXIT_SHA@@", repr(chain[-1]["exit_sha256"]))
    remote = ssh("nsu-a100", "python3 -", preflight)
    assert remote["status"] == "PASS_EXP236_SOURCE10_V2_PARENT_PREFLIGHT"
    assert [row["dataset"] for row in remote["movies"]] == list(INNER_IDS)
    assert remote["checkpoint_sha256"] == chain[-1]["checkpoint_sha256"]
    assert remote["training_result_sha256"] == chain[-1]["result_sha256"]
    assert remote["training_history_sha256"] == chain[-1]["history_sha256"]
    plan = {"experiment": "EXP236_SOURCE_GRAPH10", "source_embryo": "6bba",
            "target_embryo": "44b6", "fold": 0, "checkpoint_epoch": 10,
            "source_manifest_sha256": SOURCE_MANIFEST_SHA,
            "source_bundle_sha256": SOURCE_BUNDLE_SHA,
            "source_duplicate_policy": POLICY,
            "source_duplicate_map_sha256": DUPLICATE_MAP_SHA,
            "excluded_pairs_by_split": {"train": 824, "inner_validation": 103},
            "removed_sampled_windows_by_split": {"train": 809, "inner_validation": 101},
            "training_chain": chain,
            "training_code_manifest_sha256": chain[-1]["manifest_sha256"],
            "training_plan_sha256": chain[-1]["plan_sha256"],
            "checkpoint": TRAIN_RUN + "/output/fold0/last.pt",
            "checkpoint_sha256": chain[-1]["checkpoint_sha256"],
            "training_run": TRAIN_RUN,
            "training_result_sha256": chain[-1]["result_sha256"],
            "training_history_sha256": chain[-1]["history_sha256"],
            "data_root": REMOTE + "/data/exp213_source_view_20260912",
            "code": CODE, "output": RUN + "/output", "movies": remote["movies"]}
    validate(plan)
    infer = (ROOT / "scripts/run_exp236_source_graph10_v2.py").read_text()
    helper = (ROOT / "scripts/run_exp223_inference.py").read_text()
    plan_text = json.dumps(plan, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(@@TRAIN_CODE@@);target=pathlib.Path(@@INFER_CODE@@)
assert not target.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'code_manifest.json')==@@TRAIN_MANIFEST_SHA@@
for name,digest in json.loads((source/'code_manifest.json').read_text()).items():
 path=(source/name).resolve();assert path.is_relative_to(source.resolve()) and sha(path)==digest,name
assert sha(source/'plan.json')==@@TRAIN_PLAN_SHA@@
assert sha(source/'horaz/src/src/exp236_source_duplicate_pairs.json')==@@DUPLICATE_MAP_SHA@@
shutil.copytree(source,target)
wrapper=target/'exp227_job.py';body=wrapper.read_text()
old="assert config['script'] == 'run_exp236_source_resume_v2.py'"
assert body.count(old)==1
wrapper.write_text(body.replace(old,"assert config['script'] == 'run_exp236_source_graph10_v2.py'"))
(target/'run_exp236_source_graph10_v2.py').write_text(@@INFERENCE@@)
(target/'run_exp223_inference.py').write_text(@@HELPER@@)
(target/'plan.json').write_text(@@PLAN@@)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
manifest={path.relative_to(target).as_posix():sha(path)
          for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP236_SOURCE_GRAPH10_V2','code':str(target),
 'manifest_sha256':sha(target/'code_manifest.json'),
 'plan_sha256':sha(target/'plan.json'),
 'runner_sha256':sha(target/'run_exp236_source_graph10_v2.py'),
 'duplicate_map_sha256':sha(target/'horaz/src/src/exp236_source_duplicate_pairs.json')}))
'''.replace("@@TRAIN_CODE@@", repr(TRAIN_CODE)).replace("@@INFER_CODE@@", repr(CODE)).replace(
        "@@TRAIN_MANIFEST_SHA@@", repr(chain[-1]["manifest_sha256"])).replace(
        "@@TRAIN_PLAN_SHA@@", repr(chain[-1]["plan_sha256"])).replace(
        "@@DUPLICATE_MAP_SHA@@", repr(DUPLICATE_MAP_SHA)).replace(
        "@@INFERENCE@@", repr(infer)).replace("@@HELPER@@", repr(helper)).replace(
        "@@PLAN@@", repr(plan_text))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP236_SOURCE_GRAPH10_V2"
    assert staged["code"] == CODE
    assert staged["plan_sha256"] == sha_bytes(plan_text.encode())
    assert staged["runner_sha256"] == sha_bytes(infer.encode())
    assert staged["duplicate_map_sha256"] == DUPLICATE_MAP_SHA
    config = {"experiment": "EXP236",
              "lease_id": "exp236-source-graph10-v2-20260927",
              "token": "exp236_source_graph10_v2_20260927",
              "code": CODE, "run": RUN, "max_seconds": 7200,
              "cpu_affinity": "0-7", "script": "run_exp236_source_graph10_v2.py",
              "arguments": [CODE + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    receipt = {"status": "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS",
               "preflight": remote, "stage": staged, "movies": 11,
               "controller_receipt_sha256": controller_sha,
               "training_chain": chain,
               "source_labels_read": False, "target_labels_read": False,
               "target_data_opened": False}
    PREPARE_PATH.write_text(json.dumps(receipt, indent=2) + "\n")
    PLAN_PATH.write_bytes(plan_text.encode())
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "checkpoint_sha256": remote["checkpoint_sha256"],
                      "manifest_sha256": staged["manifest_sha256"]}))


if __name__ == "__main__":
    main()
