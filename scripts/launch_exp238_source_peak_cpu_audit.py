"""One-shot bounded EXP238 source-only CPU audit launch; default is review only."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp238_source_peak_cpu_audit import (
    BUNDLE, CODE, MANIFEST, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    exclusive_json, local_gate, sha,
)

if not __debug__:
    raise RuntimeError("EXP238 launch requires assertions; PYTHONOPTIMIZE must be 0")


INTENT = ROOT / "reports/exp238_source_peak_cpu_audit_launch_intent_20260927.json"
RECEIPT = ROOT / "reports/exp238_source_peak_cpu_audit_launch_20260927.json"
PYTHON = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/current-organizer-py311-e13cf-v1/bin/python"
CPU_AFFINITY = [24, 25, 26, 27]
RAM_BYTES = 16 * 1024**3
CPU_SECONDS = 2400
WALL_SECONDS = 2800


def command(manifest_sha: str) -> list[str]:
    return [PYTHON, "-B", CODE + "/audit_exp238_source_peaks.py",
            "--bundle-sha256", manifest_sha]


def wrapper_source(manifest_sha: str) -> str:
    source = r'''import json,os,pathlib,resource,signal,subprocess,time,traceback
if not __debug__:raise RuntimeError('EXP238 CPU wrapper needs assertions enabled')
run=pathlib.Path(@@RUN@@);command=@@COMMAND@@
affinity=@@AFFINITY@@;ram_bytes=@@RAM@@;cpu_seconds=@@CPU@@;wall_seconds=@@WALL@@
assert not (run/'output').exists()
os.sched_setaffinity(0,set(affinity))
env=dict(os.environ,PYTHONOPTIMIZE='0',CUDA_VISIBLE_DEVICES='',
 POLARS_MAX_THREADS='4',OPENBLAS_NUM_THREADS='4',OMP_NUM_THREADS='4',
 MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
 TMPDIR=str(run/'tmp'))
def child_limits():
 os.sched_setaffinity(0,set(affinity))
 resource.setrlimit(resource.RLIMIT_AS,(ram_bytes,ram_bytes))
 resource.setrlimit(resource.RLIMIT_CPU,(cpu_seconds,cpu_seconds))
timed_out=False;returncode=None;pid=None;start=None;error=None
try:
 with (run/'worker.log').open('x') as out:
  child=subprocess.Popen(command,stdout=out,stderr=subprocess.STDOUT,
   stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=child_limits)
  pid=child.pid
  try:start=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[19]
  except FileNotFoundError:start=None
  (run/'child.json').write_text(json.dumps({'pid':pid,'start':start,'command':command,
   'cpu_affinity':affinity,'ram_bytes':ram_bytes,'pythonoptimize':'0',
   'cuda_visible_devices':'','started':time.time()},indent=2)+'\n')
  try:returncode=child.wait(timeout=wall_seconds)
  except subprocess.TimeoutExpired:
   timed_out=True;os.killpg(pid,signal.SIGTERM)
   try:returncode=child.wait(timeout=30)
   except subprocess.TimeoutExpired:
    os.killpg(pid,signal.SIGKILL);returncode=child.wait()
except BaseException as exc:
 error=repr(exc)
 (run/'wrapper_error.log').write_text(traceback.format_exc())
 if pid is not None:
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:returncode=child.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(pid,signal.SIGKILL);returncode=child.wait()
finally:
 with (run/'exit.json').open('x') as out:
  out.write(json.dumps({'returncode':returncode,'timeout':timed_out,
   'finished':time.time(),'pid':pid,'start':start,'error':error,
   'source_labels_only':True,'gpu_used':False,'kaggle_post':False,
   'pythonoptimize':'0'},indent=2)+'\n')
  out.flush();os.fsync(out.fileno())
'''
    for token, value in {"@@RUN@@": RUN, "@@COMMAND@@": command(manifest_sha),
                         "@@AFFINITY@@": CPU_AFFINITY, "@@RAM@@": RAM_BYTES,
                         "@@CPU@@": CPU_SECONDS, "@@WALL@@": WALL_SECONDS}.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "exp238_cpu_wrapper", "exec")
    return source


def remote_preflight(manifest_sha: str) -> dict:
    source = r'''import hashlib,json,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP238 preflight needs assertions enabled')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert code.is_dir() and not run.exists()
assert sha(code/'manifest.json')==@@MANIFEST@@
manifest=json.loads((code/'manifest.json').read_text())
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed=={**manifest['files'],'manifest.json':@@MANIFEST@@}
config=json.loads((code/'config.json').read_text())
assert config['output']==str(run/'output')
assert all(isinstance(c['status_sha256'],str) and len(c['status_sha256'])==64 for c in config['cohorts'])
assert isinstance(config['cohorts'][0]['guarded_recheck_receipt_sha256'],str)
print(json.dumps({'status':'PASS_EXP238_CPU_LAUNCH_PREFLIGHT_NO_LABELS',
 'manifest_sha256':sha(code/'manifest.json'),'run_absent':True,
 'labels_read':False,'pythonoptimize':os.getenv('PYTHONOPTIMIZE')}))
'''
    for token, value in {"@@CODE@@": CODE, "@@RUN@@": RUN,
                         "@@MANIFEST@@": manifest_sha}.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    result = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -", source)
    assert result["status"] == "PASS_EXP238_CPU_LAUNCH_PREFLIGHT_NO_LABELS"
    assert result["pythonoptimize"] == "0"
    return result


def remote_launch(manifest_sha: str) -> dict:
    wrapper = wrapper_source(manifest_sha)
    wrapper_sha = hashlib.sha256(wrapper.encode()).hexdigest()
    source = r'''import ast,hashlib,json,os,pathlib,subprocess,time
if not __debug__:raise RuntimeError('EXP238 launcher needs assertions enabled')
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
wrapper=@@WRAPPER@@;wrapper_sha=@@WRAPPER_SHA@@;manifest_sha=@@MANIFEST@@
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert code.is_dir() and not run.exists() and sha(code/'manifest.json')==manifest_sha
assert os.environ.get('PYTHONOPTIMIZE')=='0'
ast.parse(wrapper,filename='cpu_wrapper.py')
assert hashlib.sha256(wrapper.encode()).hexdigest()==wrapper_sha
run.mkdir(parents=True,exist_ok=False);(run/'tmp').mkdir()
(run/'cpu_wrapper.py').write_bytes(wrapper.encode())
assert sha(run/'cpu_wrapper.py')==wrapper_sha
with (run/'wrapper.log').open('x') as out:
 process=subprocess.Popen(['python3','-B',str(run/'cpu_wrapper.py')],
  stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
  start_new_session=True,env=dict(os.environ,PYTHONOPTIMIZE='0'))
launch={'status':'LAUNCHED_EXP238_SOURCE_PEAK_CPU_AUDIT','run':str(run),
 'code':str(code),'wrapper_pid':process.pid,'manifest_sha256':manifest_sha,
 'wrapper_sha256':wrapper_sha,'command':@@COMMAND@@,'cpu_affinity':@@AFFINITY@@,
 'ram_bytes':@@RAM@@,'max_seconds':@@WALL@@,'pythonoptimize':'0',
 'cuda_visible_devices':'','source_labels_only':True,'gpu_used':False,
 'kaggle_post':False,'started':time.time()}
with (run/'launch.json').open('x') as out:
 out.write(json.dumps(launch,indent=2)+'\n');out.flush();os.fsync(out.fileno())
print(json.dumps(launch))
'''
    for token, value in {"@@CODE@@": CODE, "@@RUN@@": RUN, "@@WRAPPER@@": wrapper,
                         "@@WRAPPER_SHA@@": wrapper_sha, "@@MANIFEST@@": manifest_sha,
                         "@@COMMAND@@": command(manifest_sha),
                         "@@AFFINITY@@": CPU_AFFINITY, "@@RAM@@": RAM_BYTES,
                         "@@WALL@@": WALL_SECONDS}.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "exp238_cpu_remote_launch", "exec")
    return ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -", source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    manifest_sha = sha(MANIFEST)
    if not args.execute:
        print(json.dumps({"status": "EXP238_CPU_LAUNCH_LOCAL_REVIEW_ONLY",
                          "manifest_sha256": manifest_sha, "stage_receipt_present": STAGE_RECEIPT.exists(),
                          "pythonoptimize": "0", "remote_mutation": False}))
        return
    local_gate()
    assert not INTENT.exists() and not RECEIPT.exists()
    stage = json.loads(STAGE_RECEIPT.read_text())
    assert stage["status"] == "STAGED_EXP238_CPU_AUDIT_NO_LABELS"
    assert stage["manifest_sha256"] == manifest_sha
    assert stage["config_sha256"] == sha(BUNDLE / "config.json")
    assert stage["run_started"] is False and stage["labels_read"] is False
    preflight = remote_preflight(manifest_sha)
    exclusive_json(INTENT, {"status": "INTENT_EXP238_CPU_LAUNCH",
                            "manifest_sha256": manifest_sha,
                            "stage_receipt_sha256": sha(STAGE_RECEIPT),
                            "preflight": preflight, "pythonoptimize": "0",
                            "labels_read": False})
    launched = remote_launch(manifest_sha)
    assert launched["status"] == "LAUNCHED_EXP238_SOURCE_PEAK_CPU_AUDIT"
    assert launched["manifest_sha256"] == manifest_sha
    assert launched["pythonoptimize"] == "0" and launched["gpu_used"] is False
    exclusive_json(RECEIPT, {"status": launched["status"],
                             "manifest_sha256": manifest_sha,
                             "stage_receipt_sha256": sha(STAGE_RECEIPT),
                             "intent_sha256": sha(INTENT), "remote": launched,
                             "source_labels_only": True, "gpu_used": False,
                             "kaggle_post": False})
    print(json.dumps({"status": launched["status"], "run": RUN}))


if __name__ == "__main__":
    main()
