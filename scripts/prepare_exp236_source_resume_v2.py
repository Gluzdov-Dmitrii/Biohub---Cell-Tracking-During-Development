"""Stage one immutable v2 source6bba continuation after verified parent release."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh
from prepare_exp236_source_block01_v2 import (
    CODE_MANIFEST_SHA256 as BLOCK01_CODE_MANIFEST_SHA256,
    PLAN_SHA256 as BLOCK01_PLAN_SHA256,
    verify_source_audits,
)
from run_exp236_source_resume_v2 import SOURCE_DUPLICATE_MAP_SHA, SOURCE_MANIFEST_SHA, validate


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
SCHEDULE = {1: (3, 4, 6), 2: (6, 7, 9), 3: (9, 10, 10)}
WORK = ROOT / "work/exp236_source6bba_v2_20260927"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def staged_parent_plan_sha(path, block):
    """Account for Windows CRLF in locally saved resume plans only."""
    raw = Path(path).read_bytes()
    if block > 1:
        raw = raw.replace(b"\r\n", b"\n")
        assert b"\r" not in raw, "Resume parent plan contains an unexpected CR byte"
    return sha_bytes(raw)


def paths(block):
    stem = f"exp236_horaz_source6bba_block{block:02d}_v2_20260927"
    return REMOTE + "/code/" + stem, REMOTE + "/runs/" + stem


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-block", type=int, choices=tuple(SCHEDULE))
    args = parser.parse_args()
    assert args.parent_block is not None
    parent_block = args.parent_block
    previous, start, end = SCHEDULE[parent_block]
    next_block = parent_block + 1
    parent_code, parent_run = paths(parent_block)
    code, run = paths(next_block)
    plan_path = ROOT / f"reports/exp236_source_block{next_block:02d}_v2_plan_20260927.json"
    config_path = ROOT / f"reports/exp236_source_block{next_block:02d}_v2_config_20260927.json"
    receipt_path = ROOT / f"reports/exp236_source_block{next_block:02d}_v2_prepare_20260927.json"
    assert not any(path.exists() for path in (plan_path, config_path, receipt_path))
    parent_prepared_path = ROOT / f"reports/exp236_source_block{parent_block:02d}_v2_prepare_20260927.json"
    parent_config_path = ROOT / f"reports/exp236_source_block{parent_block:02d}_v2_config_20260927.json"
    parent_plan_path = (WORK / "plan.json" if parent_block == 1 else
                        ROOT / f"reports/exp236_source_block{parent_block:02d}_v2_plan_20260927.json")
    audits = verify_source_audits()
    audit_summary = {key: value for key, value in audits.items() if key != "duplicate_starts"}
    prepared = json.loads(parent_prepared_path.read_text())
    assert prepared["stage"]["code"] == parent_code
    assert prepared["target_data_opened"] is False
    assert prepared["source_duplicate_audits"] == audit_summary
    assert prepared["status"] == ("PREPARED_EXP236_SOURCE6BBA_BLOCK01_V2_NO_TARGET_ACCESS"
                                  if parent_block == 1 else
                                  "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS")
    assert prepared["stage"]["status"] == ("STAGED_EXP236_SOURCE6BBA_BLOCK01_V2"
                                            if parent_block == 1 else
                                            "STAGED_EXP236_SOURCE_RESUME_V2")
    if parent_block == 1:
        assert prepared["stage"]["manifest_sha256"] == BLOCK01_CODE_MANIFEST_SHA256
        assert prepared["stage"]["plan_sha256"] == BLOCK01_PLAN_SHA256
    parent_config = json.loads(parent_config_path.read_text())
    assert parent_config["experiment"] == "EXP236"
    assert parent_config["code"] == parent_code and parent_config["run"] == parent_run
    assert parent_config["lease_id"] == f"exp236-horaz-source6bba-block{parent_block:02d}-v2-20260927"
    assert staged_parent_plan_sha(parent_plan_path, parent_block) == (
        prepared["stage"]["plan_sha256"])
    parent_plan = json.loads(parent_plan_path.read_text())
    assert parent_plan["block_end_epoch"] == previous
    assert parent_plan["source_duplicate_policy"] == "exclude_all_effective_duplicate_windows_v2"
    assert parent_plan["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert parent_plan["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert parent_plan["removed_sampled_windows_by_split"] == {"train": 809,
                                                               "inner_validation": 101}
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    leases = [row for row in state["requests"] if row["id"] == parent_config["lease_id"]]
    assert len(leases) == 1 and leases[0]["state"] == "RELEASED"
    assert leases[0]["run_path"] == parent_run

    preflight = '''import hashlib,json,pathlib
code=pathlib.Path(PARENT_CODE);run=pathlib.Path(PARENT_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==PARENT_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==PARENT_PLAN_SHA
assert sha(code/'source6bba_manifest.json')==SOURCE_MANIFEST_SHA
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==SOURCE_DUPLICATE_MAP_SHA
plan=json.loads((code/'plan.json').read_text())
assert plan['source_duplicate_policy']=='exclude_all_effective_duplicate_windows_v2'
assert plan['source_duplicate_map_sha256']==SOURCE_DUPLICATE_MAP_SHA
result_path=run/'output/result.json';result=json.loads(result_path.read_text())
assert result['status']==EXPECTED_STATUS and result['completed_epochs']==PREVIOUS
assert result['target_data_opened'] is False and result['checkpoint_reload']=='PASS_weights_only'
assert result['source_duplicate_policy']==plan['source_duplicate_policy']
assert result['source_duplicate_map_sha256']==SOURCE_DUPLICATE_MAP_SHA
assert result['excluded_pairs_by_split']==plan['excluded_pairs_by_split']
assert result['removed_sampled_windows_by_split']==plan['removed_sampled_windows_by_split']
assert result['denied_accesses']==[]
assert set(result['opened_datasets'])=={row['dataset_id'] for row in plan['train']+plan['inner_validation']}
exit_record=json.loads((run/'exit.json').read_text())
supervision=json.loads((run/'supervision/complete.json').read_text())
control=json.loads((run/'supervision/control.json').read_text())
assert exit_record['returncode']==0 and exit_record['hard_timeout'] is False
assert supervision['status']=='RELEASED_AFTER_VERIFIED_EXIT' and supervision['exit']==exit_record
assert control['action']=='release' and control['queue']['state']=='RELEASED'
assert pathlib.Path(control['queue']['run_path'])==run
checkpoint=run/'output/fold0/last.pt'
assert checkpoint.is_file() and sha(checkpoint)==result['checkpoint_sha256']
history_path=run/'output/fold0/history.json';history=json.loads(history_path.read_text())
assert [row['epoch'] for row in history]==list(range(1,PREVIOUS+1))
assert not pathlib.Path(NEXT_CODE).exists() and not pathlib.Path(NEXT_RUN).exists()
print(json.dumps({'status':'PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT',
 'checkpoint_sha256':sha(checkpoint),'history_sha256':sha(history_path),
 'result_sha256':sha(result_path),'duplicate_map_sha256':SOURCE_DUPLICATE_MAP_SHA}))
'''.replace("PARENT_MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PARENT_PLAN_SHA", repr(prepared["stage"]["plan_sha256"])).replace(
        "SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "SOURCE_DUPLICATE_MAP_SHA", repr(SOURCE_DUPLICATE_MAP_SHA)).replace(
        "EXPECTED_STATUS", repr(f"PASS_EXP236_SOURCE_BLOCK_{previous}_OF_50")).replace(
        "PREVIOUS", repr(previous)).replace("PARENT_CODE", repr(parent_code)).replace(
        "PARENT_RUN", repr(parent_run)).replace("NEXT_CODE", repr(code)).replace(
        "NEXT_RUN", repr(run))
    parent = ssh("nsu-a100", "python3 -", preflight)
    assert parent["status"] == "PASS_EXP236_RESUME_V2_PARENT_PREFLIGHT"
    assert parent["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA

    plan = {"experiment": "EXP236", "purpose": "source_only_reciprocal_horaz_resume",
            "source_embryo": "6bba", "target_embryo": "44b6", "fold": 0,
            "start_epoch": start, "block_end_epoch": end,
            "parent_completed_epochs": previous, "planned_epochs": 50,
            "resume": True,
            "checkpoint_selection": "deferred_source_graph_10_20_30_40_50",
            "source_bundle_sha256": parent_plan["source_bundle_sha256"],
            "source_manifest_sha256": SOURCE_MANIFEST_SHA,
            "source_duplicate_policy": parent_plan["source_duplicate_policy"],
            "source_duplicate_map_sha256": SOURCE_DUPLICATE_MAP_SHA,
            "excluded_pairs_by_split": parent_plan["excluded_pairs_by_split"],
            "removed_sampled_windows_by_split": parent_plan["removed_sampled_windows_by_split"],
            "train": parent_plan["train"], "inner_validation": parent_plan["inner_validation"],
            "data_root": parent_plan["data_root"],
            "initial_output_root": paths(1)[1] + "/output",
            "parent_code": parent_code,
            "parent_plan_sha256": prepared["stage"]["plan_sha256"],
            "parent_code_manifest_sha256": prepared["stage"]["manifest_sha256"],
            "parent_checkpoint": parent_run + "/output/fold0/last.pt",
            "parent_checkpoint_sha256": parent["checkpoint_sha256"],
            "parent_history_sha256": parent["history_sha256"],
            "parent_result_sha256": parent["result_sha256"],
            "output": run + "/output"}
    validate(plan)
    plan_text = json.dumps(plan, indent=2) + "\n"
    runner = (ROOT / "scripts/run_exp236_source_resume_v2.py").read_text()
    stage = '''import ast,hashlib,json,pathlib,shutil
source=pathlib.Path(PARENT_CODE);target=pathlib.Path(NEXT_CODE)
assert not target.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'code_manifest.json')==PARENT_MANIFEST_SHA
parent_manifest=json.loads((source/'code_manifest.json').read_text())
for name,digest in parent_manifest.items():
 path=(source/name).resolve()
 assert path.is_relative_to(source.resolve()) and sha(path)==digest,name
assert sha(source/'horaz/src/src/exp236_source_duplicate_pairs.json')==SOURCE_DUPLICATE_MAP_SHA
target.mkdir()
for name in parent_manifest:
 path=source/name
 destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(path,destination)
 assert sha(destination)==parent_manifest[name],name
assert sha(target/'horaz/src/src/exp236_source_duplicate_pairs.json')==SOURCE_DUPLICATE_MAP_SHA
wrapper=target/'exp227_job.py';body=wrapper.read_text()
old=OLD_ASSERT;new="assert config['script'] == 'run_exp236_source_resume_v2.py'"
assert body.count(old)==1
wrapper.write_text(body.replace(old,new))
(target/'run_exp236_source_resume_v2.py').write_text(RUNNER)
(target/'plan.json').write_text(PLAN)
for path in target.rglob('*.py'):ast.parse(path.read_text(),filename=str(path))
manifest={path.relative_to(target).as_posix():sha(path)
          for path in sorted(target.rglob('*')) if path.is_file() and path.name!='code_manifest.json'}
(target/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP236_SOURCE_RESUME_V2','code':str(target),
 'manifest_sha256':sha(target/'code_manifest.json'),
 'plan_sha256':sha(target/'plan.json'),
 'runner_sha256':sha(target/'run_exp236_source_resume_v2.py'),
 'duplicate_map_sha256':sha(target/'horaz/src/src/exp236_source_duplicate_pairs.json')}))
'''.replace("PARENT_MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PARENT_CODE", repr(parent_code)).replace("NEXT_CODE", repr(code)).replace(
        "SOURCE_DUPLICATE_MAP_SHA", repr(SOURCE_DUPLICATE_MAP_SHA)).replace(
        "OLD_ASSERT", repr("assert config['script'] == 'run_exp236_source_block01_v2.py'"
                           if parent_block == 1 else
                           "assert config['script'] == 'run_exp236_source_resume_v2.py'")).replace(
        "RUNNER", repr(runner)).replace("PLAN", repr(plan_text))
    staged = ssh("nsu-a100", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP236_SOURCE_RESUME_V2"
    assert staged["plan_sha256"] == sha_bytes(plan_text.encode())
    assert staged["runner_sha256"] == sha_bytes(runner.encode())
    assert staged["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    config = {"experiment": "EXP236",
              "lease_id": f"exp236-horaz-source6bba-block{next_block:02d}-v2-20260927",
              "token": f"exp236_horaz_source6bba_block{next_block:02d}_v2_20260927",
              "code": code, "run": run, "max_seconds": 10800,
              "cpu_affinity": "0-7", "script": "run_exp236_source_resume_v2.py",
              "arguments": [code + "/plan.json", "--plan-sha256", staged["plan_sha256"]]}
    plan_path.write_text(plan_text)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    receipt = {"status": "PREPARED_EXP236_SOURCE_RESUME_V2_NO_TARGET_ACCESS",
               "parent_block": parent_block, "next_block": next_block,
               "preflight": parent, "stage": staged,
               "source_duplicate_audits": audit_summary,
               "source_duplicate_map_sha256": SOURCE_DUPLICATE_MAP_SHA,
               "parent_prepare_sha256": sha(parent_prepared_path),
               "target_data_opened": False}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "next_block": next_block,
                      "manifest_sha256": staged["manifest_sha256"],
                      "plan_sha256": staged["plan_sha256"]}))


if __name__ == "__main__":
    main()
