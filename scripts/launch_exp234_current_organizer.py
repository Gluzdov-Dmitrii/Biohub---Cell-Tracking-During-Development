"""One-shot bounded CPU launch of EXP234 current-organizer target175 rescore."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
STAGE = ROOT / "reports/exp234_current_organizer_stage_20260927.json"
ENV_VERIFY = ROOT / "reports/exp234_current_organizer_env_verify_20260927.json"
SCALE_AUDIT = ROOT / "reports/exp234_current_image_scale_audit_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_organizer_launch_20260927.json"
SCALE_SHA = "7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not RECEIPT.exists(), "Scorer launch receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    staged = json.loads(STAGE.read_text())
    runtime = json.loads(ENV_VERIFY.read_text())
    audit = json.loads(SCALE_AUDIT.read_text())
    assert sha(SCALE_AUDIT) == SCALE_SHA
    assert audit["status"] == "PASS_EXP234_ALL175_IMAGE_SCALE_EQUIVALENCE_NO_LABELS"
    assert audit["count"] == 175 and audit["target_labels_read"] is False
    assert staged["status"] == "STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS"
    assert staged["prepare_sha256"] == sha(PREPARE)
    assert runtime["status"] == "PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV_VERIFIED"
    assert runtime["stage_sha256"] == sha(STAGE)
    assert runtime["verify"]["code_manifest_sha256"] == prepared["code_manifest_sha256"]
    assert runtime["verify"]["score_config_sha256"] == prepared["score_config_sha256"]
    assert runtime["verify"]["python"] == prepared["interpreter_intended"]
    assert runtime["verify"]["runtime"]["positive_division"] == [1, 0, 0]
    assert runtime["verify"]["runtime"]["remote_weak_component_division"] == [0, 0, 1]
    for name, digest in prepared["prerequisite_local_sha256"].items():
        assert sha(ROOT / name) == digest, name
    code = prepared["remote_code_intended"]
    run = prepared["remote_run_intended"]
    python = prepared["interpreter_intended"]
    config_sha = prepared["score_config_sha256"]
    env_result_sha = runtime["verify"]["env_result_sha256"]
    env_build = str(Path(python).parent.parent).replace("\\", "/").replace(
        "/envs/current-organizer-py311-e13cf-v1",
        "/runs/exp234_current_organizer_env_build_v1_20260927")
    source = r'''import hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
old=pathlib.Path(@@OLD_RUN@@);build=pathlib.Path(@@ENV_BUILD@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not run.exists(),'Existing scorer run: reconcile before launch'
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(build/'result.json')==@@ENV_RESULT_SHA@@
env_result=json.loads((build/'result.json').read_text())
assert env_result['status']=='PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV'
assert env_result['runtime']['positive_division']==[1,0,0]
assert env_result['runtime']['remote_weak_component_division']==[0,0,1]
assert sha(old/'output/no_metric_gate.json')==@@OLD_GATE_SHA@@
assert sha(old/'output/result.json')==@@OLD_RESULT_SHA@@
old_exit=json.loads((old/'exit.json').read_text())
assert old_exit['returncode']==0 and old_exit['timeout'] is False
config=json.loads((code/'score_config.json').read_text())
assert config['experiment']=='EXP234_CURRENT_ORGANIZER_TARGET175_V1'
assert config['code']==str(code) and config['run']==str(run)
assert config['output']==str(run/'output') and config['python']==@@PYTHON@@
run.mkdir(parents=True);(run/'tmp').mkdir()
wrapper=r''' + "\"\"\"" + r'''import json,os,pathlib,resource,signal,subprocess,time,traceback
run=pathlib.Path(__RUN__);code=pathlib.Path(__CODE__)
def limits():
 os.sched_setaffinity(0,set(range(16,20)))
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',
         OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
         TMPDIR=str(run/'tmp'))
cmd=[__PYTHON__,str(code/'score_exp234_current_organizer.py'),str(code/'score_config.json'),
     '--config-sha256',__CONFIG_SHA__]
with (run/'worker.log').open('x') as out:
 process=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL,start_new_session=True,
                          env=env,preexec_fn=limits)
start=pathlib.Path(f'/proc/{process.pid}/stat').read_text().split(') ')[1].split()[19]
(run/'child.json').write_text(json.dumps({'pid':process.pid,'start':start,
                                          'command':cmd,'cpu_affinity':[16,17,18,19],
                                          'ram_gib':32,'cuda_visible_devices':''},indent=2)+'\n')
timed=False
try:rc=process.wait(timeout=3600)
except subprocess.TimeoutExpired:
 timed=True;os.killpg(process.pid,signal.SIGTERM)
 try:rc=process.wait(timeout=30)
 except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);rc=process.wait()
(run/'exit.json').write_text(json.dumps({'returncode':rc,'timeout':timed,
  'finished':time.time(),'pid':process.pid,'start':start},indent=2)+'\n')
''' + "\"\"\"" + r'''
wrapper=wrapper.replace('__RUN__',repr(str(run))).replace('__CODE__',repr(str(code))).replace('__PYTHON__',repr(@@PYTHON@@)).replace('__CONFIG_SHA__',repr(@@CONFIG_SHA@@))
(run/'cpu_wrapper.py').write_text(wrapper)
with (run/'wrapper.log').open('x') as out:
 process=subprocess.Popen(['python3','-u',str(run/'cpu_wrapper.py')],stdout=out,
    stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
launch={'status':'LAUNCHED_EXP234_CURRENT_ORGANIZER_TARGET175_CPU',
 'wrapper_pid':process.pid,'run':str(run),'code':str(code),
 'python':@@PYTHON@@,'started':time.time(),'cpu':4,'ram_gib':32,
 'max_seconds':3600,'score_config_sha256':@@CONFIG_SHA@@,
 'code_manifest_sha256':@@MANIFEST_SHA@@,'env_result_sha256':@@ENV_RESULT_SHA@@,
 'historical_gate_sha256':@@OLD_GATE_SHA@@,'historical_result_sha256':@@OLD_RESULT_SHA@@,
 'kaggle_post':False}
(run/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
print(json.dumps(launch))
'''
    replacements = {
        "@@CODE@@": repr(code), "@@RUN@@": repr(run),
        "@@OLD_RUN@@": repr(json.loads((ROOT / "work/exp234_current_organizer_v1/score_config.json").read_text())["historical_run"]),
        "@@ENV_BUILD@@": repr(env_build),
        "@@MANIFEST_SHA@@": repr(prepared["code_manifest_sha256"]),
        "@@CONFIG_SHA@@": repr(config_sha),
        "@@ENV_RESULT_SHA@@": repr(env_result_sha),
        "@@OLD_GATE_SHA@@": repr(prepared["historical_gate_sha256"]),
        "@@OLD_RESULT_SHA@@": repr(prepared["historical_result_sha256"]),
        "@@PYTHON@@": repr(python),
    }
    for token, value in replacements.items():
        source = source.replace(token, value)
    launch = ssh("nsu-quadro", "python3 -", source)
    assert launch["status"] == "LAUNCHED_EXP234_CURRENT_ORGANIZER_TARGET175_CPU"
    assert launch["run"] == run and launch["code"] == code and launch["python"] == python
    assert launch["kaggle_post"] is False
    receipt = {"status": launch["status"], "prepare_sha256": sha(PREPARE),
               "stage_sha256": sha(STAGE), "env_verify_sha256": sha(ENV_VERIFY),
               "scale_audit_sha256": sha(SCALE_AUDIT), "launch": launch,
               "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "run": run,
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
