"""One-shot bounded CPU EXP241 scorer launcher. Default performs local review only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp241_source_paired_scorer_v2 import (
    BUNDLE, CODE, CONFIG_SHA, GRAPH_RUN, INTENT as STAGE_INTENT,
    MANIFEST_SHA, PYTHON, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    V1_FAILURE_SHA, exclusive_json, failure_gate, local_bundle,
    remote_preflight_source, render, sha,
)


if not __debug__:
    raise RuntimeError("EXP241 launcher requires assertions")

INTENT = ROOT / "reports/exp241_source_paired_scorer_v2_launch_intent_20260927.json"
RECEIPT = ROOT / "reports/exp241_source_paired_scorer_v2_launch_20260927.json"
AFFINITY = [24, 25, 26, 27]
RAM_BYTES = 16 * 1024**3
CPU_SECONDS = 6000
WRAPPER_WALL_SECONDS = 7500


def command() -> list[str]:
    return [PYTHON, "-B", CODE + "/score_exp241_source_paired.py",
            "--manifest-sha256", MANIFEST_SHA]


def pinned_python_preflight_source() -> str:
    source = r'''import hashlib,json,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP241 Python preflight requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP241 launch preflight denies all GEFF')
sys.addaudithook(deny)
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert pathlib.Path(sys.executable).resolve()==pathlib.Path(@@PYTHON@@).resolve()
assert sys.prefix!=sys.base_prefix and sys.version_info[:2]==(3,11)
assert code.is_dir() and not run.exists()
sys.path.insert(0,str(code))
from check_current_organizer_metric_runtime import validate_runtime
runtime=validate_runtime('remote_py311')
print(json.dumps({'status':'PASS_EXP241_PINNED_PYTHON_NO_LABELS',
 'runtime':runtime,'code':str(code),'run_absent':True,
 'source_labels_read':False,'target_data_opened':False}))
'''
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN, "@@PYTHON@@": PYTHON})


def cpu_wrapper_source() -> str:
    source = r'''import json,os,pathlib,resource,signal,subprocess,time,traceback
if not __debug__:raise RuntimeError('EXP241 CPU wrapper requires assertions')
run=pathlib.Path(@@RUN@@);cmd=@@COMMAND@@
affinity=@@AFFINITY@@;ram=@@RAM@@;cpu_seconds=@@CPU@@;wall_seconds=@@WALL@@
assert os.uname().nodename=='prepost'
env=dict(os.environ,PYTHONOPTIMIZE='0',CUDA_VISIBLE_DEVICES='',
 POLARS_MAX_THREADS='4',OPENBLAS_NUM_THREADS='4',OMP_NUM_THREADS='4',
 MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
 TMPDIR=str(run/'tmp'))
def limits():
 os.sched_setaffinity(0,set(affinity))
 resource.setrlimit(resource.RLIMIT_AS,(ram,ram))
 resource.setrlimit(resource.RLIMIT_CPU,(cpu_seconds,cpu_seconds))
def durable(path,value):
 with path.open('x') as stream:
  stream.write(json.dumps(value,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
timed_out=False;returncode=None;pid=None;start=None;error=None;started=time.time();child=None
try:
 assert not (run/'output').exists()
 with (run/'worker.log').open('x') as output:
  child=subprocess.Popen(cmd,stdout=output,stderr=subprocess.STDOUT,
   stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
  pid=child.pid
  try:start=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[19]
  except FileNotFoundError:start=None
  durable(run/'child.json',{'pid':pid,'start':start,'command':cmd,
   'cpu_affinity':affinity,'ram_bytes':ram,'cpu_seconds':cpu_seconds,
   'cuda_visible_devices':'','pythonoptimize':'0','started':started})
  try:returncode=child.wait(timeout=wall_seconds)
  except subprocess.TimeoutExpired:
   timed_out=True
   os.killpg(pid,signal.SIGTERM)
   try:returncode=child.wait(timeout=30)
   except subprocess.TimeoutExpired:
    os.killpg(pid,signal.SIGKILL);returncode=child.wait()
except BaseException as exc:
 error=repr(exc)
 (run/'wrapper_error.log').write_text(traceback.format_exc())
 if pid is not None and child is not None and child.poll() is None:
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:returncode=child.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(pid,signal.SIGKILL);returncode=child.wait()
finally:
 durable(run/'exit.json',{'returncode':returncode,'timeout':timed_out,
  'pid':pid,'start':start,'error':error,'started':started,'finished':time.time(),
  'source_labels_only':True,'target_data_opened':False,
  'gpu_used':False,'kaggle_post':False})
'''
    return render(source, {"@@RUN@@": RUN, "@@COMMAND@@": command(),
                           "@@AFFINITY@@": AFFINITY, "@@RAM@@": RAM_BYTES,
                           "@@CPU@@": CPU_SECONDS, "@@WALL@@": WRAPPER_WALL_SECONDS})


def remote_launch_source(manifest: dict) -> str:
    wrapper = cpu_wrapper_source()
    wrapper_sha = hashlib.sha256(wrapper.encode()).hexdigest()
    source = r'''import ast,hashlib,json,os,pathlib,subprocess,time
if not __debug__:raise RuntimeError('EXP241 remote launcher requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@);graph=pathlib.Path(@@GRAPH_RUN@@)
expected=@@EXPECTED@@;wrapper=@@WRAPPER@@;wrapper_sha=@@WRAPPER_SHA@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert code.is_dir() and not run.exists()
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected
assert sha(graph/'output/result.json')==@@GRAPH_RESULT_SHA@@
assert sha(graph/'output/no_label_gate.json')==@@GRAPH_GATE_SHA@@
ast.parse(wrapper,filename='cpu_wrapper.py')
assert hashlib.sha256(wrapper.encode()).hexdigest()==wrapper_sha
run.mkdir(parents=True,exist_ok=False);(run/'tmp').mkdir()
(run/'cpu_wrapper.py').write_bytes(wrapper.encode())
assert sha(run/'cpu_wrapper.py')==wrapper_sha
with (run/'wrapper.log').open('x') as output:
 process=subprocess.Popen(['python3','-B',str(run/'cpu_wrapper.py')],
  stdout=output,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
  start_new_session=True,env=dict(os.environ,PYTHONOPTIMIZE='0',CUDA_VISIBLE_DEVICES=''))
launch={'status':'LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU','run':str(run),
 'code':str(code),'wrapper_pid':process.pid,'manifest_sha256':@@MANIFEST_SHA@@,
 'wrapper_sha256':wrapper_sha,'command':@@COMMAND@@,'cpu_affinity':@@AFFINITY@@,
 'ram_bytes':@@RAM@@,'cpu_seconds':@@CPU@@,'max_seconds':@@WALL@@,
 'pythonoptimize':'0','cuda_visible_devices':'','source_labels_only':True,
 'target_data_opened':False,'gpu_used':False,'kaggle_post':False,'started':time.time()}
with (run/'launch.json').open('x') as stream:
 stream.write(json.dumps(launch,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
print(json.dumps(launch))
'''
    config = json.loads((BUNDLE / "config.json").read_text())
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                           "@@GRAPH_RUN@@": GRAPH_RUN,
                           "@@EXPECTED@@": {**manifest["files"], "manifest.json": MANIFEST_SHA},
                           "@@WRAPPER@@": wrapper, "@@WRAPPER_SHA@@": wrapper_sha,
                           "@@MANIFEST_SHA@@": MANIFEST_SHA,
                           "@@GRAPH_RESULT_SHA@@": config["graph_result_sha256"],
                           "@@GRAPH_GATE_SHA@@": config["graph_no_label_gate_sha256"],
                           "@@COMMAND@@": command(), "@@AFFINITY@@": AFFINITY,
                           "@@RAM@@": RAM_BYTES, "@@CPU@@": CPU_SECONDS,
                           "@@WALL@@": WRAPPER_WALL_SECONDS})


def remote_readback_source() -> str:
    source = r'''import hashlib,json,os,pathlib
if not __debug__:raise RuntimeError('EXP241 launch readback requires assertions')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'manifest.json').read_text())
assert {p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}=={
 **manifest['files'],'manifest.json':@@MANIFEST_SHA@@}
launch=json.loads((run/'launch.json').read_text())
assert launch['status']=='LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU'
assert launch['run']==str(run) and launch['code']==str(code)
assert launch['manifest_sha256']==@@MANIFEST_SHA@@
assert sha(run/'cpu_wrapper.py')==launch['wrapper_sha256']
exit_path=run/'exit.json'
exit_record=json.loads(exit_path.read_text()) if exit_path.exists() else None
pid=launch['wrapper_pid']
try:state=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0]
except FileNotFoundError:state=None
assert state not in (None,'Z') or exit_record is not None
print(json.dumps({'status':'PASS_EXP241_SCORER_LAUNCH_READBACK',
 'run':str(run),'launch_sha256':sha(run/'launch.json'),
 'wrapper_sha256':sha(run/'cpu_wrapper.py'),'wrapper_state':state,
 'exit_record':exit_record,'manifest_sha256':@@MANIFEST_SHA@@,
 'source_labels_only':True,'gpu_used':False,'kaggle_post':False}))
'''
    return render(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                           "@@MANIFEST_SHA@@": MANIFEST_SHA})


def local_stage_gate() -> tuple[dict, dict, dict]:
    failure_gate()
    manifest, config = local_bundle()
    stage = json.loads(STAGE_RECEIPT.read_text())
    assert stage["status"] == "STAGED_EXP241_SOURCE_PAIRED_SCORER_NO_LABELS"
    assert stage["manifest_sha256"] == MANIFEST_SHA
    assert stage["config_sha256"] == CONFIG_SHA
    assert stage["v1_failure_receipt_sha256"] == V1_FAILURE_SHA
    assert stage["intent_sha256"] == sha(STAGE_INTENT)
    assert stage["stage"]["file_hashes"] == {**manifest["files"], "manifest.json": MANIFEST_SHA}
    assert stage["readback"]["code_present"] is True and stage["readback"]["run_absent"] is True
    assert stage["run_started"] is False and stage["source_labels_read"] is False
    assert config["output"] == RUN + "/output"
    return manifest, config, stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest, config = local_bundle()
    if not args.execute:
        pinned_python_preflight_source()
        cpu_wrapper_source()
        remote_launch_source(manifest)
        remote_readback_source()
        print(json.dumps({"status": "EXP241_SCORER_LAUNCH_LOCAL_REVIEW_ONLY",
                          "manifest_sha256": MANIFEST_SHA,
                          "stage_receipt_present": STAGE_RECEIPT.exists(),
                          "command": command(), "remote_mutation": False}))
        return
    manifest, config, stage = local_stage_gate()
    assert not INTENT.exists() and not RECEIPT.exists(), "Reconcile launch intent first"
    readback = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                   remote_preflight_source(True))
    assert readback["status"] == "PASS_EXP241_STAGE_PREFLIGHT_NO_LABELS"
    runtime = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 CUDA_VISIBLE_DEVICES= " +
                  PYTHON + " -B -", pinned_python_preflight_source())
    assert runtime["status"] == "PASS_EXP241_PINNED_PYTHON_NO_LABELS"
    exclusive_json(INTENT, {"status": "INTENT_EXP241_SCORER_CPU_LAUNCH",
                            "manifest_sha256": MANIFEST_SHA,
                            "stage_receipt_sha256": sha(STAGE_RECEIPT),
                            "stage_readback": readback, "runtime": runtime,
                            "command": command(), "source_labels_read": False,
                            "gpu_used": False, "kaggle_post": False})
    launched = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                   remote_launch_source(manifest))
    assert launched["status"] == "LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU"
    assert launched["manifest_sha256"] == MANIFEST_SHA
    assert launched["command"] == command() and launched["gpu_used"] is False
    launch_readback = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                          remote_readback_source())
    assert launch_readback["status"] == "PASS_EXP241_SCORER_LAUNCH_READBACK"
    exclusive_json(RECEIPT, {"status": launched["status"],
                             "manifest_sha256": MANIFEST_SHA,
                             "stage_receipt_sha256": sha(STAGE_RECEIPT),
                             "intent_sha256": sha(INTENT),
                             "stage_readback": readback, "runtime": runtime,
                             "remote": launched, "launch_readback": launch_readback,
                             "score_computed_at_launch": False,
                             "source_labels_only": True,
                             "target_data_opened": False, "gpu_used": False,
                             "kaggle_post": False})
    print(json.dumps({"status": launched["status"], "run": RUN}))


if __name__ == "__main__":
    main()
