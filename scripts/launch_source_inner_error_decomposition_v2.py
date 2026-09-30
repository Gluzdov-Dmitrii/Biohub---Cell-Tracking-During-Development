"""Review-gated, one-shot CPU launch of the sealed SOURCE-INNER audit.

This script is prepared locally only. An existing intent means reconcile first;
it never launches a second process on an uncertain result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from stage_source_inner_error_decomposition_v2 import (
    BUNDLE, CODE, MANIFEST_SHA, PYTHON, REMOTE, ROOT, RUN,
    STAGE_INTENT, STAGE_RECEIPT, import_preflight, local_bundle,
    remote_readback_source, sha, write_json_exclusive,
)


LAUNCH_INTENT = ROOT / "reports/source_inner_error_decomposition_v2_launch_intent_20260927.json"
LAUNCH_RECEIPT = ROOT / "reports/source_inner_error_decomposition_v2_launch_20260927.json"
AFFINITY = (24, 25, 26, 27)
RAM_BYTES = 16 * 1024**3
WALL_SECONDS = 2700


def _replace(source: str, replacements: dict[str, object]) -> str:
    for token, value in replacements.items():
        assert token in source, token
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "source_inner_remote_launch", "exec")
    return source


def command() -> list[str]:
    return [PYTHON, "-B", CODE + "/audit_source_inner.py",
            "--bundle-sha256", MANIFEST_SHA]


def cpu_wrapper_source() -> str:
    """Bound one child; write exit evidence even on a timeout or nonzero exit."""
    source = r'''import hashlib,json,os,pathlib,resource,signal,subprocess,time,traceback
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
manifest_sha=@@MANIFEST_SHA@@;cmd=@@COMMAND@@
affinity=@@AFFINITY@@;ram_bytes=@@RAM_BYTES@@;wall_seconds=@@WALL_SECONDS@@
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert sha(code/'manifest.json')==manifest_sha
assert not (run/'output').exists()
os.sched_setaffinity(0,set(affinity))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',POLARS_MAX_THREADS='4',
         OPENBLAS_NUM_THREADS='4',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',
         PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',TMPDIR=str(run/'tmp'))
def limits():
 os.sched_setaffinity(0,set(affinity))
 resource.setrlimit(resource.RLIMIT_AS,(ram_bytes,ram_bytes))
 resource.setrlimit(resource.RLIMIT_CPU,(2400,2400))
timed_out=False;returncode=None;pid=None;start=None;error=None
try:
 with (run/'worker.log').open('x') as out:
  child=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
  pid=child.pid
  try:start=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[19]
  except FileNotFoundError:start=None
  (run/'child.json').write_text(json.dumps({'pid':pid,'start':start,
   'command':cmd,'cpu_affinity':affinity,'ram_bytes':ram_bytes,
   'cuda_visible_devices':'','started':time.time()},indent=2)+'\n')
  try:returncode=child.wait(timeout=wall_seconds)
  except subprocess.TimeoutExpired:
   timed_out=True
   os.killpg(pid,signal.SIGTERM)
   try:returncode=child.wait(timeout=30)
   except subprocess.TimeoutExpired:
    os.killpg(pid,signal.SIGKILL);returncode=child.wait()
except BaseException as exc:
 error=repr(exc)
 if pid is not None:
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:returncode=child.wait(timeout=30)
  except subprocess.TimeoutExpired:
   os.killpg(pid,signal.SIGKILL);returncode=child.wait()
 (run/'wrapper_error.log').write_text(traceback.format_exc())
finally:
 (run/'exit.json').write_text(json.dumps({'returncode':returncode,
  'timeout':timed_out,'finished':time.time(),'pid':pid,'start':start,
  'error':error,'source_labels_only':True,'gpu_used':False,'kaggle_post':False},indent=2)+'\n')
'''
    return _replace(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@MANIFEST_SHA@@": MANIFEST_SHA,
                             "@@COMMAND@@": command(), "@@AFFINITY@@": AFFINITY,
                             "@@RAM_BYTES@@": RAM_BYTES,
                             "@@WALL_SECONDS@@": WALL_SECONDS})


def remote_launch_source(manifest: dict) -> str:
    wrapper = cpu_wrapper_source()
    wrapper_sha = hashlib.sha256(wrapper.encode("utf-8")).hexdigest()
    source = r'''import ast,hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
expected=@@EXPECTED@@;wrapper=@@WRAPPER@@;wrapper_sha=@@WRAPPER_SHA@@
manifest_sha=@@MANIFEST_SHA@@;command=@@COMMAND@@
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert code.is_dir() and not run.exists()
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed==expected and sha(code/'manifest.json')==manifest_sha
for name in observed:
 if name.endswith('.py'):ast.parse((code/name).read_bytes().decode('utf-8'),filename=name)
config=json.loads((code/'config.json').read_text())
assert config['status']=='PREREGISTERED_SOURCE_INNER_DECOMPOSITION_LOCAL_ONLY'
assert config['output']==str(run/'output')
assert command[0]==@@PYTHON@@ and command[-1]==manifest_sha
ast.parse(wrapper,filename='cpu_wrapper.py')
assert hashlib.sha256(wrapper.encode('utf-8')).hexdigest()==wrapper_sha
run.mkdir(parents=True,exist_ok=False);(run/'tmp').mkdir()
(run/'cpu_wrapper.py').write_bytes(wrapper.encode('utf-8'))
assert sha(run/'cpu_wrapper.py')==wrapper_sha
with (run/'wrapper.log').open('x') as log:
 process=subprocess.Popen(['python3','-B',str(run/'cpu_wrapper.py')],
  stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch={'status':'LAUNCHED_SOURCE_INNER_AUDIT_CPU','run':str(run),'code':str(code),
 'wrapper_pid':process.pid,'command':command,'source_manifest_sha256':manifest_sha,
 'wrapper_sha256':wrapper_sha,'cpu_affinity':[24,25,26,27],
 'ram_gib':16,'max_seconds':2700,'cuda_visible_devices':'',
 'started':time.time(),'source_labels_only':True,'gpu_used':False,'kaggle_post':False}
(run/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
print(json.dumps(launch))
'''
    return _replace(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@EXPECTED@@": {**manifest["files"], "manifest.json": MANIFEST_SHA},
                             "@@WRAPPER@@": wrapper, "@@WRAPPER_SHA@@": wrapper_sha,
                             "@@MANIFEST_SHA@@": MANIFEST_SHA,
                             "@@COMMAND@@": command(), "@@PYTHON@@": PYTHON})


def launch_readback_source() -> str:
    source = r'''import ast,hashlib,json,os,pathlib
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
launch=json.loads((run/'launch.json').read_text())
assert launch['status']=='LAUNCHED_SOURCE_INNER_AUDIT_CPU'
assert launch['run']==str(run) and launch['code']==str(code)
assert launch['source_manifest_sha256']==@@MANIFEST_SHA@@
assert sha(run/'cpu_wrapper.py')==launch['wrapper_sha256']
ast.parse((run/'cpu_wrapper.py').read_bytes().decode('utf-8'),filename='cpu_wrapper.py')
manifest=json.loads((code/'manifest.json').read_text())
for name,digest in manifest['files'].items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
 if name.endswith('.py'):ast.parse(path.read_bytes().decode('utf-8'),filename=name)
exit_path=run/'exit.json'
exit_record=json.loads(exit_path.read_text()) if exit_path.exists() else None
pid=launch['wrapper_pid']
try:state=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0]
except FileNotFoundError:state=None
assert state not in (None,'Z') or exit_record is not None
print(json.dumps({'status':'PASS_SOURCE_INNER_AUDIT_LAUNCH_READBACK',
 'run':str(run),'launch_sha256':sha(run/'launch.json'),
 'wrapper_sha256':sha(run/'cpu_wrapper.py'),'wrapper_state':state,
 'exit_record':exit_record,'source_manifest_sha256':@@MANIFEST_SHA@@,
 'source_labels_only':True,'gpu_used':False,'kaggle_post':False}))
'''
    return _replace(source, {"@@CODE@@": CODE, "@@RUN@@": RUN,
                             "@@MANIFEST_SHA@@": MANIFEST_SHA})


def local_gate():
    manifest, config = local_bundle()
    assert not LAUNCH_INTENT.exists() and not LAUNCH_RECEIPT.exists(), (
        "Existing launch intent or receipt requires reconciliation")
    staged = json.loads(STAGE_RECEIPT.read_text())
    assert staged["status"] == "STAGED_SOURCE_INNER_AUDIT_NO_LABELS"
    assert staged["manifest_sha256"] == MANIFEST_SHA
    assert staged["intent_sha256"] == sha(STAGE_INTENT)
    assert staged["stage"]["code"] == CODE and staged["readback"]["run_absent"] is True
    assert staged["source_labels_read"] is False and staged["reciprocal_target_labels_read"] is False
    assert staged["run_started"] is False
    assert staged["readback"]["file_hashes"] == {**manifest["files"], "manifest.json": MANIFEST_SHA}
    assert config["output"] == RUN + "/output"
    return manifest, config, staged


def dry_run_plan():
    manifest, config = local_bundle()
    return {"status": "DRY_RUN_SOURCE_INNER_CPU_LAUNCH_NO_REMOTE_CALL",
            "source_manifest_sha256": MANIFEST_SHA, "code": CODE, "run": RUN,
            "command": command(), "cpu_affinity": AFFINITY,
            "ram_bytes": RAM_BYTES, "max_seconds": WALL_SECONDS,
            "remote_launch_source_sha256": hashlib.sha256(
                remote_launch_source(manifest).encode()).hexdigest(),
            "remote_readback_source_sha256": hashlib.sha256(
                launch_readback_source().encode()).hexdigest(),
            "source_only": config["source_only"], "remote_mutation": False}


def launch():
    manifest, config, staged = local_gate()
    # A fresh read-only import check and byte/AST readback precede the intent.
    preflight = import_preflight(config, expect_code=True)
    assert preflight["torch_available"] is False, "Unexpected runtime drift requires review"
    readback = ssh("nsu-quadro", "python3 -B -", remote_readback_source(manifest))
    assert readback["status"] == "PASS_SOURCE_INNER_REMOTE_STAGE_READBACK"
    assert readback["run_absent"] is True
    intent = {"status": "SOURCE_INNER_AUDIT_LAUNCH_INTENT",
              "stage_receipt_sha256": sha(STAGE_RECEIPT),
              "source_manifest_sha256": MANIFEST_SHA,
              "import_preflight": preflight, "stage_readback": readback,
              "command": command(), "cpu_affinity": AFFINITY,
              "ram_bytes": RAM_BYTES, "max_seconds": WALL_SECONDS,
              "code": CODE, "run": RUN, "source_labels_only": True,
              "gpu_used": False, "kaggle_post": False}
    write_json_exclusive(LAUNCH_INTENT, intent)
    launched = ssh("nsu-quadro", "python3 -B -", remote_launch_source(manifest))
    assert launched["status"] == "LAUNCHED_SOURCE_INNER_AUDIT_CPU"
    assert launched["run"] == RUN and launched["code"] == CODE
    assert launched["command"] == command()
    assert launched["source_manifest_sha256"] == MANIFEST_SHA
    assert launched["cpu_affinity"] == list(AFFINITY)
    assert launched["ram_gib"] == 16 and launched["max_seconds"] == WALL_SECONDS
    assert launched["cuda_visible_devices"] == "" and launched["gpu_used"] is False
    readback_launch = ssh("nsu-quadro", "python3 -B -", launch_readback_source())
    assert readback_launch["status"] == "PASS_SOURCE_INNER_AUDIT_LAUNCH_READBACK"
    assert readback_launch["run"] == RUN and readback_launch["gpu_used"] is False
    receipt = {"status": "LAUNCHED_SOURCE_INNER_AUDIT_CPU",
               "intent_sha256": sha(LAUNCH_INTENT),
               "stage_receipt_sha256": sha(STAGE_RECEIPT),
               "source_manifest_sha256": MANIFEST_SHA,
               "import_preflight": preflight, "stage_readback": readback,
               "launch": launched, "launch_readback": readback_launch,
               "score_computed_at_launch": False, "source_labels_only": True,
               "reciprocal_target_labels_read": False,
               "gpu_used": False, "kaggle_post": False}
    write_json_exclusive(LAUNCH_RECEIPT, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = dry_run_plan() if args.dry_run else launch()
    print(json.dumps(result if args.dry_run else {
        "status": result["status"], "run": RUN, "source_manifest_sha256": MANIFEST_SHA}))


if __name__ == "__main__":
    main()
