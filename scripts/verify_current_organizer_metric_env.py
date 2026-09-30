"""Independently verify the shared isolated metric environment and contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "reports/exp234_current_organizer_prepare_20260927.json"
STAGE = ROOT / "reports/exp234_current_organizer_stage_20260927.json"
LAUNCH = ROOT / "reports/exp234_current_organizer_env_launch_20260927.json"
RECEIPT = ROOT / "reports/exp234_current_organizer_env_verify_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert not RECEIPT.exists(), "Environment verify receipt already exists"
    prepared = json.loads(PREPARE.read_text())
    staged = json.loads(STAGE.read_text())
    launched = json.loads(LAUNCH.read_text())
    assert staged["status"] == "STAGED_EXP234_CURRENT_ORGANIZER_SOURCE_NO_LABELS"
    assert launched["status"] == "LAUNCHED_CURRENT_ORGANIZER_ENV_BUILD"
    assert launched["stage_sha256"] == sha(STAGE)
    code = prepared["remote_code_intended"]
    python = prepared["interpreter_intended"]
    build = launched["launch"]["build"]
    assert launched["launch"]["code"] == code
    assert launched["launch"]["env"] == str(Path(python).parent.parent).replace("\\", "/")
    source = r'''import hashlib,json,os,pathlib,subprocess,sys
code=pathlib.Path(@@CODE@@);python=pathlib.Path(@@PYTHON@@);build=pathlib.Path(@@BUILD@@)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert sha(code/'code_manifest.json')==@@MANIFEST_SHA@@
assert sha(code/'score_config.json')==@@CONFIG_SHA@@
assert sha(code/'requirements_current_organizer_py311.txt')==@@REQ_SHA@@
assert sha(build/'builder.py')==@@BUILDER_SHA@@
launch=json.loads((build/'launch.json').read_text())
assert launch['builder_sha256']==@@BUILDER_SHA@@
result=json.loads((build/'result.json').read_text())
assert result['status']=='PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV'
assert result['python']==str(python) and result['system_site_packages'] is False
assert result['requirements_sha256']==@@REQ_SHA@@
assert sha(python.parent.parent/'pyvenv.cfg')==result['pyvenv_cfg_sha256']
for name,key in [('synthetic.log','synthetic_log_sha256'),('pip_check.log','pip_check_log_sha256'),('freeze.log','freeze_log_sha256')]:
 assert sha(build/name)==result[key]
assert (build/'pip_check.log').read_text().strip()=='No broken requirements found.'
synthetic=json.loads((build/'synthetic.log').read_text().strip())
assert synthetic==result['runtime']
assert synthetic['positive_division']==[1,0,0]
assert synthetic['remote_weak_component_division']==[0,0,1]
replay=subprocess.run([str(python),str(code/'check_current_organizer_metric_runtime.py'),
                       '--profile','remote_py311','--package-root',str(code)],
                       capture_output=True,text=True,timeout=300,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
assert replay.returncode==0,replay.stderr[-1200:]
assert json.loads(replay.stdout.strip())==synthetic
isolation=subprocess.run([str(python),'-c',
 'import json,site,sys,importlib.util;print(json.dumps({"prefix":sys.prefix,"base_prefix":sys.base_prefix,"path":sys.path,"sites":site.getsitepackages(),"torch":importlib.util.find_spec("torch") is not None}))'],
 capture_output=True,text=True,timeout=30)
assert isolation.returncode==0,isolation.stderr[-1200:]
site_info=json.loads(isolation.stdout)
assert site_info['prefix']==str(python.parent.parent)
assert site_info['prefix']!=site_info['base_prefix']
assert all('/envs/prepost/' not in p for p in site_info['path']+site_info['sites'])
assert all((not p.endswith('/site-packages') or p.startswith(site_info['prefix']))
           for p in site_info['path']+site_info['sites'])
repo=pathlib.Path(@@REPO@@)
adapter_script=''' + "\"\"\"" + r'''import json,sys
sys.path[:0]=[__SRC__,__SCRIPTS__]
out={}
for name in ('biohub_tracking.io','predict_unet_transformer'):
 try:
  __import__(name)
  out[name]={'imported':True}
 except Exception as exc:
  out[name]={'imported':False,'error_type':type(exc).__name__,'message':str(exc)}
print(json.dumps(out))
''' + "\"\"\"" + r'''
adapter_script=adapter_script.replace('__SRC__',repr(str(repo/'src'))).replace('__SCRIPTS__',repr(str(repo/'scripts')))
adapter=subprocess.run([str(python),'-c',adapter_script],capture_output=True,text=True,timeout=60)
assert adapter.returncode==0,adapter.stderr[-1200:]
adapter_imports=json.loads(adapter.stdout.strip())
print(json.dumps({'status':'PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV_VERIFIED',
 'env_result_sha256':sha(build/'result.json'),'env_launch_sha256':sha(build/'launch.json'),
 'builder_sha256':sha(build/'builder.py'),'code_manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json'),'python':str(python),
 'pyvenv_cfg_sha256':result['pyvenv_cfg_sha256'],'runtime':synthetic,
 'isolation':site_info,'adapter_imports':adapter_imports,
 'target_labels_read':False,'kaggle_post':False}))
'''
    replacements = {
        "@@CODE@@": repr(code), "@@PYTHON@@": repr(python),
        "@@BUILD@@": repr(build),
        "@@MANIFEST_SHA@@": repr(prepared["code_manifest_sha256"]),
        "@@CONFIG_SHA@@": repr(prepared["score_config_sha256"]),
        "@@REQ_SHA@@": repr(prepared["source_hashes"]["requirements_current_organizer_py311.txt"]),
        "@@BUILDER_SHA@@": repr(launched["launch"]["builder_sha256"]),
        "@@REPO@@": repr("/home/scientists/gluz_d_s/kaggle/projects/"
                         "biohub-cell-tracking-during-development/"
                         "code/exp214_honest_refit_v4_20260912/tracking_repo"),
    }
    for token, value in replacements.items():
        source = source.replace(token, value)
    verified = ssh("nsu-quadro", "python3 -", source)
    assert verified["status"] == "PASS_CURRENT_ORGANIZER_ISOLATED_PY311_ENV_VERIFIED"
    assert verified["target_labels_read"] is False and verified["kaggle_post"] is False
    receipt = {"status": verified["status"], "prepare_sha256": sha(PREPARE),
               "stage_sha256": sha(STAGE), "env_launch_sha256": sha(LAUNCH),
               "verify": verified, "target_labels_read": False, "kaggle_post": False}
    RECEIPT.write_bytes((json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({"status": receipt["status"],
                      "env_result_sha256": verified["env_result_sha256"],
                      "adapter_imports": verified["adapter_imports"],
                      "receipt_sha256": sha(RECEIPT)}))


if __name__ == "__main__":
    main()
