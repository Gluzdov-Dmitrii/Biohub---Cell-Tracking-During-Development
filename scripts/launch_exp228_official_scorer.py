"""Launch bounded CPU-only EXP228 diagnostic after eight audited shards."""
import json
from pathlib import Path, PurePosixPath

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]


def main():
    prepared = json.loads((ROOT / "reports/exp228_official_scorer_prepare_20260926.json").read_text())
    assert prepared["status"] == "PREPARED_EXP228_DIAGNOSTIC_SCORER"
    counts = []
    for chunk in range(8):
        path = ROOT / f"reports/exp228_quadro_chunk{chunk:02d}_config_20260923_full_audit.json"
        audit = json.loads(path.read_text())
        assert audit["status"] == "PASS_EXP228_CHUNK_FULL_AUDIT" and audit["chunk"] == chunk
        assert audit["lease"] == "RELEASED" and audit["exit"] == 0
        counts.append(audit["n_movies"])
    assert sum(counts) == 116 and counts == [15] * 4 + [14] * 4

    remote = prepared["remote"]
    config = prepared["config"]
    code = remote["code"]
    run = str(PurePosixPath(config["output"]).parent)
    assert config["experiment"] == "EXP228_OFFICIAL_SCORE175"
    assert code.endswith("/code/exp228_official_scorer_v1_20260926")
    assert run.endswith("/runs/exp228_official_score175_20260926")
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
run.mkdir();(run/'tmp').mkdir()
wrapper='''import json,os,pathlib,resource,signal,subprocess,time
run=pathlib.Path(__RUN__);code=pathlib.Path(__CODE__)
def limits():
 os.sched_setaffinity(0,set(range(4)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',POLARS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(run/'tmp'))
cmd=[__PYTHON__,str(code/'score_exp228_ensemble_official.py'),str(code/'score_config.json'),'--config-sha256',__CONFIG_SHA__]
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
result={'status':'EXP228_OFFICIAL_DIAGNOSTIC_LAUNCHED','wrapper_pid':process.pid,'run':str(run),'started':time.time(),'cpu':4,'ram_gib':32,'max_seconds':3600,'score_config_sha256':@@CONFIG_SHA@@}
(run/'launch.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
""".replace("@@CODE@@", repr(code)).replace("@@RUN@@", repr(run)).replace(
        "@@MANIFEST_SHA@@", repr(remote["manifest_sha256"])).replace(
        "@@CONFIG_SHA@@", repr(remote["score_config_sha256"])).replace(
        "@@PYTHON@@", repr(str(PurePosixPath(run).parents[1] / "envs/prepost/py3.11-stdlib-v1/bin/python")))
    result = ssh("nsu-quadro", "python3 -", source)
    (ROOT / "reports/exp228_official_scorer_launch_20260926.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
