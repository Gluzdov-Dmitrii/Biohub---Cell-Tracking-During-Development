"""Launch bounded CPU-only EXP234 official175 after all target chunks release."""
import json
from pathlib import Path, PurePosixPath

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def main():
    prepared = json.loads((ROOT / "reports/exp234_target_official_scorer_prepare_20260927.json").read_text())
    assert prepared["status"] == "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS"
    assert prepared["target_labels_read"] is False
    coordinator = ROOT / "reports/exp234_target_recovery_v2_20260927.json"
    original = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
    import hashlib
    assert hashlib.sha256(coordinator.read_bytes()).hexdigest() == prepared["coordinator_receipt_sha256"]
    assert hashlib.sha256(original.read_bytes()).hexdigest() == prepared["original_coordinator_receipt_sha256"]
    assert json.loads(coordinator.read_text())["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    stage = prepared["stage"]
    config = prepared["config"]
    code = stage["code"]
    run = str(PurePosixPath(config["output"]).parent)
    assert config["experiment"] == "EXP234_OFFICIAL_TARGET175"
    assert code == REMOTE + "/code/exp234_target_official_scorer_v1_20260927"
    assert run == REMOTE + "/runs/exp234_target_official_score175_20260927"
    source = """import hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not run.exists(),'Existing scorer run: reconcile before launch'
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(code/'release_manifest.json')==@@RELEASE_SHA@@
config=json.loads((code/'score_config.json').read_text())
assert pathlib.Path(config['output']).parent==run
run.mkdir();(run/'tmp').mkdir()
wrapper='''import json,os,pathlib,resource,signal,subprocess,time
run=pathlib.Path(__RUN__);code=pathlib.Path(__CODE__)
def limits():
 os.sched_setaffinity(0,set(range(16,20)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
cmd=[__PYTHON__,str(code/'score_exp234_target_official.py'),str(code/'score_config.json'),'--config-sha256',__CONFIG_SHA__]
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
(run/'cpu_wrapper.py').write_text(wrapper)
with (run/'wrapper.log').open('x') as out:
 process=subprocess.Popen(['python3',str(run/'cpu_wrapper.py')],stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
result={'status':'EXP234_OFFICIAL_TARGET175_SCORER_LAUNCHED','wrapper_pid':process.pid,'run':str(run),'started':time.time(),'cpu':4,'ram_gib':32,'max_seconds':3600,'score_config_sha256':@@CONFIG_SHA@@}
(run/'launch.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
""".replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run)).replace(
        "@@MANIFEST_SHA@@", repr(stage["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(stage["score_config_sha256"])).replace(
        "@@RELEASE_SHA@@", repr(stage["release_manifest_sha256"])).replace(
        "@@PYTHON@@", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"))
    result = ssh("nsu-quadro", "python3 -", source)
    path = ROOT / "reports/exp234_target_official_scorer_launch_20260927.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
