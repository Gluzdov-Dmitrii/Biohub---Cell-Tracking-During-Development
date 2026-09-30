"""Read-only proof of the sealed EXP241 v1 pre-label assertion failure.

Default mode checks local evidence and compiles the remote readback. Only
--execute opens a read-only SSH session and writes an exclusive local receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp241_source_paired_scorer import (
    CODE, MANIFEST_SHA, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    local_bundle, render, sha,
)
from launch_exp241_source_paired_scorer import (
    AFFINITY, CPU_SECONDS, RAM_BYTES, RECEIPT as LAUNCH_RECEIPT,
    WRAPPER_WALL_SECONDS, command,
)


if not __debug__:
    raise RuntimeError("EXP241 failure reconciliation requires assertions")

STAGE_SHA = "036f640ddbc62007e64443dd483c0a22d789af0da94087aadfb9b24eabc7712b"
LAUNCH_SHA = "6961df16cbcbd35dd0bc28dedcea74ad5d297c03288ae71938a75d4f55c48a8f"
LAUNCH_REMOTE_SHA = "3eb2ecdb4625d111278d2417e21f41791b0dbc10c47733d4f69cb780b191251b"
WRAPPER_SHA = "26e95d2c0125a6e8d5f5ed81e4d599f9f79f9a0b4db022d3c5d929412b199ca2"
RUNNER_SHA = "174cefb283b330e71b65ec4cae57702f21ac72086dabec87053f19edfd3d6bf9"
PRIOR_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
PRIOR_GATE_ACTUAL_SHA = "735496f5cf6dca2e24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
PRIOR_GATE_V1_TYPO = "735496f5cf6d2a24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
OUT = ROOT / "reports/exp241_source_paired_scorer_v1_failure_reconciled_20260927.json"


def local_gate() -> tuple[dict, dict, dict]:
    manifest, _ = local_bundle()
    assert manifest["files"]["score_exp241_source_paired.py"] == RUNNER_SHA
    assert sha(STAGE_RECEIPT) == STAGE_SHA
    assert sha(LAUNCH_RECEIPT) == LAUNCH_SHA
    stage = json.loads(STAGE_RECEIPT.read_text())
    launch = json.loads(LAUNCH_RECEIPT.read_text())
    assert stage["manifest_sha256"] == launch["manifest_sha256"] == MANIFEST_SHA
    assert stage["stage"]["file_hashes"] == {**manifest["files"], "manifest.json": MANIFEST_SHA}
    assert launch["stage_receipt_sha256"] == STAGE_SHA
    assert launch["launch_readback"]["launch_sha256"] == LAUNCH_REMOTE_SHA
    assert launch["remote"]["wrapper_sha256"] == WRAPPER_SHA
    assert launch["remote"]["command"] == command()
    source = (Path(CODE).name, (Path(__file__).resolve().parents[1] /
              "work/exp241_source_paired_scorer_v1_20260927/score_exp241_source_paired.py").read_text())
    lines = source[1].splitlines()
    assert source[0] == "exp241_source_paired_scorer_v1_20260927"
    assert lines[33] == f'SOURCE_GATE_SHA = "{PRIOR_GATE_V1_TYPO}"'
    assert lines[421].strip() == 'assert prior["no_label_gate_sha256"] == SOURCE_GATE_SHA'
    assert next(i for i, line in enumerate(lines, 1) if "audit.score_cohort(" in line) > 422
    verified = json.loads((ROOT / "work/exp241_source_paired_scorer_v1_20260927/source_inner_verified.json").read_text())
    assert verified["remote"]["gate_sha256"] == PRIOR_GATE_ACTUAL_SHA
    assert verified["remote"]["result_sha256"] == PRIOR_RESULT_SHA
    return manifest, stage, launch


def remote_source(manifest: dict) -> str:
    source = r'''import ast,hashlib,json,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP241 readback requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
expected=@@EXPECTED@@;command=@@COMMAND@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP241 failure reconciliation denies GEFF')
sys.addaudithook(deny)
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
assert {p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}==expected
runner=code/'score_exp241_source_paired.py'
assert sha(runner)==@@RUNNER_SHA@@
lines=runner.read_text().splitlines();ast.parse(runner.read_text(),filename=str(runner))
assert lines[33]=='SOURCE_GATE_SHA = "'+@@TYPO@@+'"'
assert lines[421].strip()=='assert prior["no_label_gate_sha256"] == SOURCE_GATE_SHA'
assert min(i for i,line in enumerate(lines,1) if 'audit.score_cohort(' in line)>422
assert min(i for i,line in enumerate(lines,1) if 'candidate_movie(' in line and 'def ' not in line)>422
assert sha(run/'launch.json')==@@LAUNCH_REMOTE_SHA@@
assert sha(run/'cpu_wrapper.py')==@@WRAPPER_SHA@@
launch=json.loads((run/'launch.json').read_text())
child=json.loads((run/'child.json').read_text())
exit_record=json.loads((run/'exit.json').read_text())
assert launch['status']=='LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU'
assert launch['run']==str(run) and launch['code']==str(code)
assert launch['manifest_sha256']==@@MANIFEST_SHA@@
assert launch['command']==child['command']==command
assert launch['cpu_affinity']==child['cpu_affinity']==@@AFFINITY@@
assert launch['ram_bytes']==child['ram_bytes']==@@RAM@@
assert launch['cpu_seconds']==child['cpu_seconds']==@@CPU@@
assert launch['max_seconds']==@@WALL@@
assert child['pid']==exit_record['pid'] and child['start']==exit_record['start']
assert exit_record['returncode']==1 and exit_record['timeout'] is False
assert exit_record['error'] is None
assert exit_record['target_data_opened'] is False
assert exit_record['gpu_used'] is False and exit_record['kaggle_post'] is False
pid=child['pid'];proc=pathlib.Path(f'/proc/{pid}/stat')
if proc.exists():
 fields=proc.read_text().split(') ')[1].split()
 assert fields[0]=='Z' or fields[19]!=str(child['start'])
output=run/'output'
assert output.is_dir()
output_files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()}
assert set(output_files)=={'no_label_gate.json'}
gate=json.loads((output/'no_label_gate.json').read_text())
assert gate['status']=='PASS_EXP241_SOURCE19_GRAPH_AND_RUNTIME_BEFORE_GEFF'
assert gate['manifest_sha256']==@@MANIFEST_SHA@@
assert gate['source_inner_result_sha256']==@@PRIOR_RESULT_SHA@@
assert not any(gate[k] for k in ('source_labels_read','target_data_opened','gpu_used','kaggle_post'))
assert sha(run/'worker.log')
log=(run/'worker.log').read_text(errors='replace')
assert 'Traceback (most recent call last):' in log and 'AssertionError' in log
assert 'score_exp241_source_paired.py", line 422, in main' in log
assert 'assert prior["no_label_gate_sha256"] == SOURCE_GATE_SHA' in log
assert 'parent_replay_pass.json' not in log and 'PASS_EXP241_SOURCE19_PAIRED_SCORE_RECORDED' not in log
assert not (run/'wrapper_error.log').exists()
assert (run/'wrapper.log').is_file()
prior_path=pathlib.Path(@@PRIOR_RESULT@@)
assert sha(prior_path)==@@PRIOR_RESULT_SHA@@
prior=json.loads(prior_path.read_text())
assert prior['no_label_gate_sha256']==@@ACTUAL@@ and @@ACTUAL@@!=@@TYPO@@
print(json.dumps({'status':'PASS_EXP241_V1_FAILURE_RECONCILED_BEFORE_GEFF',
 'run':str(run),'manifest_sha256':@@MANIFEST_SHA@@,
 'launch_sha256':sha(run/'launch.json'),'wrapper_sha256':sha(run/'cpu_wrapper.py'),
 'child_sha256':sha(run/'child.json'),'exit_sha256':sha(run/'exit.json'),
 'worker_log_sha256':sha(run/'worker.log'),'wrapper_log_sha256':sha(run/'wrapper.log'),
 'output_files':output_files,'prior_result_sha256':sha(prior_path),
 'prior_gate_actual_sha256':prior['no_label_gate_sha256'],
 'runner_gate_v1_typo':@@TYPO@@,'assertion_line':422,
 'first_score_cohort_line':min(i for i,line in enumerate(lines,1) if 'audit.score_cohort(' in line),
 'exit_returncode':1,'timeout':False,'child_absent':True,
 'source_geff_reached':False,'candidate_metric_reached':False,
 'target_data_opened':False,'gpu_used':False,'kaggle_post':False}))
'''
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                           "@@EXPECTED@@": {**manifest["files"], "manifest.json": MANIFEST_SHA},
                           "@@COMMAND@@": command(), "@@MANIFEST_SHA@@": MANIFEST_SHA,
                           "@@RUNNER_SHA@@": RUNNER_SHA, "@@TYPO@@": PRIOR_GATE_V1_TYPO,
                           "@@LAUNCH_REMOTE_SHA@@": LAUNCH_REMOTE_SHA,
                           "@@WRAPPER_SHA@@": WRAPPER_SHA, "@@AFFINITY@@": AFFINITY,
                           "@@RAM@@": RAM_BYTES, "@@CPU@@": CPU_SECONDS,
                           "@@WALL@@": WRAPPER_WALL_SECONDS,
                           "@@PRIOR_RESULT@@": CODE.rsplit("/code/", 1)[0] +
                           "/runs/source_inner_error_decomposition_v2_20260927/output/result.json",
                           "@@PRIOR_RESULT_SHA@@": PRIOR_RESULT_SHA,
                           "@@ACTUAL@@": PRIOR_GATE_ACTUAL_SHA})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest, _, _ = local_gate()
    remote_source(manifest)
    if not args.execute:
        print(json.dumps({"status": "EXP241_V1_FAILURE_RECONCILIATION_LOCAL_REVIEW_ONLY",
                          "stage_receipt_sha256": STAGE_SHA,
                          "launch_receipt_sha256": LAUNCH_SHA,
                          "v1_runner_sha256": RUNNER_SHA,
                          "remote_read": False, "source_geff_read": False}))
        return
    assert not OUT.exists(), "Reconcile existing failure receipt first"
    checked = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -", remote_source(manifest))
    assert checked["status"] == "PASS_EXP241_V1_FAILURE_RECONCILED_BEFORE_GEFF"
    assert checked["source_geff_reached"] is False and checked["child_absent"]
    receipt = {"status": "PASS_EXP241_V1_FAILURE_RECONCILED_BEFORE_GEFF",
               "manifest_sha256": MANIFEST_SHA,
               "stage_receipt_sha256": STAGE_SHA,
               "launch_receipt_sha256": LAUNCH_SHA,
               "reconciler_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "remote": checked, "source_geff_read_by_reconciler": False,
               "target_data_opened": False, "gpu_used": False, "kaggle_post": False}
    with OUT.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT),
                      "exit_sha256": checked["exit_sha256"],
                      "worker_log_sha256": checked["worker_log_sha256"]}))


if __name__ == "__main__":
    main()
