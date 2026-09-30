"""Future one-shot CPU launch for the staged EXP227 current target116 scorer."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import ssh
from stage_exp227_target6bba_scorer_v4 import (ROOT, REMOTE, CODE, RUN, FINAL,
    ATTEMPT1_LEASE, ATTEMPT1_RESULT_SHA, exact_final_pin, ssh_gate_only)


STAGE = ROOT / "reports/exp227_target6bba_scorer_stage_v4_20260927.json"
INTENT = ROOT / "reports/exp227_target6bba_scorer_launch_intent_v4_20260927.json"
RECEIPT = ROOT / "reports/exp227_target6bba_scorer_launch_v4_20260927.json"
PYTHON = REMOTE + "/envs/current-organizer-py311-e13cf-v1/bin/python"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source(prepared):
    stage = prepared["stage"]
    return """import ast,hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not run.exists(),'Existing scorer run requires reconciliation'
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
for name,digest in manifest.items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
config=json.loads((code/'score_config.json').read_text())
assert config['output']==str(run/'output')
assert config['coordinator_sha256']==@@FINAL_SHA@@
run.mkdir();(run/'tmp').mkdir()
wrapper='''import json,os,pathlib,resource,signal,subprocess,time
run=pathlib.Path(__RUN__);code=pathlib.Path(__CODE__)
def limits():
 os.sched_setaffinity(0,set(range(16,20)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
cmd=[__PYTHON__,str(code/'score_exp227_target6bba_current_v4.py'),str(code/'score_config.json'),'--config-sha256',__CONFIG_SHA__]
with (run/'worker.log').open('x') as out:
 process=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
start=pathlib.Path(f'/proc/{process.pid}/stat').read_text().split(') ')[1].split()[19]
(run/'child.json').write_text(json.dumps({'pid':process.pid,'start':start,'command':cmd}))
timed=False
try:rc=process.wait(timeout=3600)
except subprocess.TimeoutExpired:
 timed=True;os.killpg(process.pid,signal.SIGTERM)
 try:rc=process.wait(timeout=30)
 except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);rc=process.wait()
(run/'exit.json').write_text(json.dumps({'returncode':rc,'timeout':timed,'finished':time.time(),'pid':process.pid,'start':start}))
'''
wrapper=wrapper.replace('__RUN__',repr(str(run))).replace('__CODE__',repr(str(code))).replace('__PYTHON__',repr(@@PYTHON@@)).replace('__CONFIG_SHA__',repr(@@CONFIG_SHA@@))
ast.parse(wrapper,filename='cpu_wrapper.py')
(run/'cpu_wrapper.py').write_text(wrapper)
with (run/'wrapper.log').open('x') as out:
 process=subprocess.Popen(['python3',str(run/'cpu_wrapper.py')],stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
result={'status':'LAUNCHED_EXP227_TARGET116_CURRENT_SCORER_V4','wrapper_pid':process.pid,'run':str(run),'started':time.time(),'cpu':4,'ram_gib':32,'max_seconds':3600,'score_config_sha256':@@CONFIG_SHA@@,'final_receipt_sha256':@@FINAL_SHA@@,'successor_actual_lease_id':@@ATTEMPT1_LEASE@@}
(run/'launch.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
""".replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@MANIFEST_SHA@@", repr(stage["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(stage["score_config_sha256"])).replace(
        "@@PYTHON@@", repr(PYTHON)).replace(
        "@@FINAL_SHA@@", repr(prepared["coordinator_local_sha256"])).replace(
        "@@ATTEMPT1_LEASE@@", repr(ATTEMPT1_LEASE))


def launch(final_sha256):
    assert not INTENT.exists() and not RECEIPT.exists(), "Existing launch intent requires reconciliation"
    prepared = json.loads(STAGE.read_text())
    assert prepared["status"] == "STAGED_EXP227_TARGET116_CURRENT_SCORER_V4_NO_LABELS"
    assert prepared["target_labels_read"] is False and prepared["target_score_computed"] is False
    assert prepared["gate_only"]["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    coordinator = Path(prepared["coordinator_local_path"])
    assert coordinator.resolve(strict=True) == FINAL.resolve(strict=True)
    assert prepared["coordinator_local_sha256"] == final_sha256 == sha(coordinator)
    exact_final_pin(json.loads(coordinator.read_text()), final_sha256, coordinator)
    assert prepared["successor_actual_attempt"] == 1
    assert prepared["successor_actual_lease_id"] == ATTEMPT1_LEASE
    assert prepared["successor_launch_result_sha256"] == ATTEMPT1_RESULT_SHA
    assert prepared["config"]["coordinator_sha256"] == final_sha256
    assert prepared["stage"]["code"] == CODE
    assert prepared["config"]["output"] == RUN + "/output"
    gate = ssh_gate_only(shlex.join([
        PYTHON, CODE + "/score_exp227_target6bba_current_v4.py", CODE + "/score_config.json",
        "--config-sha256", prepared["stage"]["score_config_sha256"], "--gate-only"]))
    assert gate["status"] == "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS"
    assert gate["score"] is None
    intent = {"status": "EXP227_TARGET116_CURRENT_SCORER_V4_LAUNCH_INTENT",
              "stage_receipt_sha256": sha(STAGE),
              "coordinator_local_path": str(coordinator),
              "coordinator_local_sha256": final_sha256,
              "successor_actual_attempt": 1,
              "successor_actual_lease_id": ATTEMPT1_LEASE,
              "successor_launch_result_sha256": ATTEMPT1_RESULT_SHA,
              "gate_only": gate, "target_labels_read": False}
    with INTENT.open("x") as stream:
        stream.write(json.dumps(intent, indent=2) + "\n")
    result = ssh("nsu-quadro", "python3 -", source(prepared))
    assert result["status"] == "LAUNCHED_EXP227_TARGET116_CURRENT_SCORER_V4"
    assert result["run"] == RUN
    assert result["score_config_sha256"] == prepared["stage"]["score_config_sha256"]
    receipt = {**result, "intent_sha256": sha(INTENT), "stage_receipt_sha256": sha(STAGE),
               "target_score_computed": False}
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-sha256", required=True,
                        help="Reviewed SHA256 of the completed v3 all116 final receipt")
    args = parser.parse_args()
    print(json.dumps(launch(args.final_sha256)))
