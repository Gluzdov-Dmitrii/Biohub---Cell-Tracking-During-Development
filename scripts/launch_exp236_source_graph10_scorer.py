"""Launch a bounded CPU scorer for the sealed eleven-movie EXP236 source pilot."""
import hashlib
import json
from pathlib import Path, PurePosixPath

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp236_source_graph10_scorer_v1_20260927"
RUN = REMOTE + "/runs/exp236_source_graph10_official_v1_20260927"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    prepared_path = ROOT / "reports/exp236_source_graph10_scorer_prepare_20260927.json"
    prepared = json.loads(prepared_path.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE10_OFFICIAL_SCORER_NO_LABELS"
    assert prepared["target_labels_read"] is False and prepared["source_labels_read"] is False
    assert prepared["target_data_opened"] is False
    inference_prepare = ROOT / "reports/exp236_source_graph10_v2_prepare_20260927.json"
    assert sha(inference_prepare) == prepared["inference_prepare_sha256"]
    stage = prepared["stage"]
    config = prepared["config"]
    assert stage["code"] == CODE
    assert config["experiment"] == "EXP236_SOURCE_GRAPH10_OFFICIAL"
    assert str(PurePosixPath(config["output"]).parent) == RUN
    assert not (ROOT / "reports/exp236_source_graph10_scorer_launch_20260927.json").exists()

    source = """import hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not run.exists(),'Existing scorer run: reconcile before launch'
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
config=json.loads((code/'score_config.json').read_text())
assert pathlib.Path(config['output']).parent==run
assert sha(pathlib.Path(config['inference_run'])/'output/status.json')==config['inference_status_sha256']
assert sha(pathlib.Path(config['inference_run'])/'exit.json')==config['inference_exit_sha256']
run.mkdir();(run/'tmp').mkdir()
wrapper='''import json,os,pathlib,resource,signal,subprocess,time
run=pathlib.Path(__RUN__);code=pathlib.Path(__CODE__)
def limits():
 os.sched_setaffinity(0,set(range(16,20)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
cmd=[__PYTHON__,str(code/'score_exp236_source_graph10.py'),str(code/'score_config.json'),'--config-sha256',__CONFIG_SHA__]
with (run/'worker.log').open('x') as out:
 process=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,env=env,preexec_fn=limits)
start=pathlib.Path(f'/proc/{process.pid}/stat').read_text().split(') ')[1].split()[19]
(run/'child.json').write_text(json.dumps({'pid':process.pid,'start':start,'command':cmd}))
timed=False
try:rc=process.wait(timeout=1800)
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
result={'status':'EXP236_SOURCE10_OFFICIAL_SCORER_LAUNCHED','wrapper_pid':process.pid,'run':str(run),'started':time.time(),'cpu':4,'ram_gib':32,'max_seconds':1800,'score_config_sha256':@@CONFIG_SHA@@}
(run/'launch.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
""".replace("@@CODE@@", repr(CODE)).replace("@@RUN@@", repr(RUN)).replace(
        "@@MANIFEST_SHA@@", repr(stage["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(stage["score_config_sha256"])).replace(
        "@@PYTHON@@", repr(REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"))
    result = ssh("nsu-quadro", "python3 -", source)
    assert result["status"] == "EXP236_SOURCE10_OFFICIAL_SCORER_LAUNCHED"
    path = ROOT / "reports/exp236_source_graph10_scorer_launch_20260927.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
