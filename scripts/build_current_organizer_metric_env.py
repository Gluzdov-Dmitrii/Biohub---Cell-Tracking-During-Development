"""One-shot remote build of an isolated CPU organizer-metric Python 3.11 env."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "reports/exp234_current_organizer_stage_20260927.json"
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_organizer_env_launch_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not RECEIPT.exists(), "Environment launch receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    staged = json.loads(STAGE.read_text())
    assert staged["status"] == "STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS"
    assert staged["stage"]["manifest_sha256"] == prepared["code_manifest_sha256"]
    assert staged["stage"]["config_sha256"] == prepared["score_config_sha256"]
    code = prepared["remote_code_intended"]
    env = str(Path(prepared["interpreter_intended"]).parent.parent).replace("\\", "/")
    build = REMOTE + "/runs/exp234_current_organizer_env_build_v1_20260927"
    assert env == REMOTE + "/envs/current-organizer-py311-e13cf-v1"
    assert code == REMOTE + "/code/exp234_current_organizer_v1_20260927"
    req_sha = prepared["source_hashes"]["requirements_current_organizer_py311.txt"]
    checker_sha = prepared["source_hashes"]["check_current_organizer_metric_runtime.py"]
    source = r'''import hashlib,json,os,pathlib,subprocess,time
code=pathlib.Path(@@CODE@@);env=pathlib.Path(@@ENV@@);build=pathlib.Path(@@BUILD@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert not env.exists() and not build.exists()
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(code/'requirements_current_organizer_py311.txt')==@@REQ_SHA@@
assert sha(code/'check_current_organizer_metric_runtime.py')==@@CHECKER_SHA@@
assert not pathlib.Path(@@SCORE_RUN@@).exists()
build.mkdir(parents=True)
builder=r''' + "\"\"\"" + r'''import hashlib,json,os,pathlib,subprocess,sys,time,traceback
code=pathlib.Path(__CODE__);env=pathlib.Path(__ENV__);build=pathlib.Path(__BUILD__)
def write(name,obj):
 (build/name).write_text(json.dumps(obj,indent=2)+'\n')
def step(name,cmd,timeout):
 write('phase.json',{'phase':name,'started':time.time()})
 with (build/(name+'.log')).open('x') as out:
  done=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                      timeout=timeout,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',
                                               PIP_DISABLE_PIP_VERSION_CHECK='1',
                                               PIP_NO_INPUT='1',CUDA_VISIBLE_DEVICES=''))
 assert done.returncode==0,(name,done.returncode)
try:
 step('venv',['/usr/bin/python3.11','-m','venv',str(env)],120)
 python=env/'bin/python'
 cfg=(env/'pyvenv.cfg').read_text()
 assert 'include-system-site-packages = false' in cfg
 step('install',[str(python),'-m','pip','install','-r',str(code/'requirements_current_organizer_py311.txt')],1800)
 step('pip_check',[str(python),'-m','pip','check'],120)
 step('synthetic',[str(python),str(code/'check_current_organizer_metric_runtime.py'),
                   '--profile','remote_py311','--package-root',str(code)],300)
 synthetic=json.loads((build/'synthetic.log').read_text().strip())
 assert synthetic['status']=='PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT'
 assert synthetic['positive_division']==[1,0,0]
 assert synthetic['remote_weak_component_division']==[0,0,1]
 step('freeze',[str(python),'-m','pip','freeze','--all'],120)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 write('result.json',{'status':'PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV',
   'python':str(python),'pyvenv_cfg_sha256':sha(env/'pyvenv.cfg'),
   'requirements_sha256':sha(code/'requirements_current_organizer_py311.txt'),
   'synthetic_log_sha256':sha(build/'synthetic.log'),
   'pip_check_log_sha256':sha(build/'pip_check.log'),
   'freeze_log_sha256':sha(build/'freeze.log'),'runtime':synthetic,
   'system_site_packages':False,'finished':time.time()})
except BaseException as exc:
 write('failure.json',{'status':'STOPPED_CURRENT_ORGANIZER_ENV_BUILD',
                       'error':repr(exc),'traceback':traceback.format_exc(),
                       'time':time.time()})
 raise
''' + "\"\"\"" + r'''
builder=builder.replace('__CODE__',repr(str(code))).replace('__ENV__',repr(str(env))).replace('__BUILD__',repr(str(build)))
(build/'builder.py').write_text(builder)
with (build/'builder.log').open('x') as out:
 process=subprocess.Popen(['python3','-u',str(build/'builder.py')],stdout=out,
    stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
launch={'status':'LAUNCHED_CURRENT_ORGANIZER_ENV_BUILD','pid':process.pid,
        'code':str(code),'env':str(env),'build':str(build),
        'builder_sha256':sha(build/'builder.py'),'started':time.time(),
        'target_labels_read':False,'kaggle_post':False}
(build/'launch.json').write_text(json.dumps(launch,indent=2)+'\n')
print(json.dumps(launch))
'''
    replacement = {
        "@@CODE@@": repr(code), "@@ENV@@": repr(env), "@@BUILD@@": repr(build),
        "@@MANIFEST_SHA@@": repr(prepared["code_manifest_sha256"]),
        "@@CONFIG_SHA@@": repr(prepared["score_config_sha256"]),
        "@@REQ_SHA@@": repr(req_sha), "@@CHECKER_SHA@@": repr(checker_sha),
        "@@SCORE_RUN@@": repr(prepared["remote_run_intended"]),
    }
    for token, value in replacement.items():
        source = source.replace(token, value)
    launch = ssh("nsu-quadro", "python3 -", source)
    assert launch["status"] == "LAUNCHED_CURRENT_ORGANIZER_ENV_BUILD"
    assert launch["target_labels_read"] is False and launch["kaggle_post"] is False
    receipt = {"status": launch["status"], "stage_sha256": sha(STAGE),
               "prepare_sha256": sha(PREPARE), "launch": launch,
               "target_labels_read": False, "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"], "build": build,
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
