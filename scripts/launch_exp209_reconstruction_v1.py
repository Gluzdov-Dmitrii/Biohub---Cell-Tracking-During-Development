"""One-shot launch of a reviewed EXP209 CPU reconstruction bundle.

No target labels or Kaggle submission are touched by this launcher.  An
ambiguous SSH outcome leaves the remote one-shot namespace for manual audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from prepare_exp209_reconstruction_v1_local import CODE_NAME, LOCAL_WORK, REMOTE_ROOT
from stage_exp209_reconstruction_v1 import pack_checked_bundle, write_once


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote_launch_program(code_dir: str, run_root: str, manifest_sha: str, contract_sha: str) -> str:
    python_bin = REMOTE_ROOT + "/envs/prepost/py3.11-stdlib-v1/bin/python"
    return f'''import hashlib,json,os,pathlib,subprocess
if not __debug__: raise RuntimeError('optimized Python disables launch guards')
code=pathlib.Path({code_dir!r});run=pathlib.Path({run_root!r});python=pathlib.Path({python_bin!r})
assert code.parent==pathlib.Path({(REMOTE_ROOT+'/code')!r}) and code.name=={CODE_NAME!r}
assert run.parent==pathlib.Path({(REMOTE_ROOT+'/runs')!r}) and run.name=={CODE_NAME!r}
assert code.is_dir() and python.is_file() and os.access(python,os.X_OK)
manifest_bytes=(code/'bundle_manifest.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest()=={manifest_sha!r}
manifest=json.loads(manifest_bytes)
expected={{row['name'] for row in manifest['files']}} | {{'bundle_manifest.json'}}
assert {{p.name for p in code.iterdir() if p.is_file()}}==expected
for row in manifest['files']:
    raw=(code/row['name']).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
assert hashlib.sha256((code/'contract.json').read_bytes()).hexdigest()=={contract_sha!r}
assert not run.exists(), 'one-shot reconstruction run namespace already exists'
run.mkdir(parents=False,exist_ok=False)
intent={{'status':'LAUNCH_INTENT_CPU_ONLY_NO_LABELS','contract_sha256':{contract_sha!r},
        'bundle_manifest_sha256':{manifest_sha!r},'labels_read':False,'gpu_used':False}}
with (run/'launch_intent.json').open('x') as f:
    json.dump(intent,f,indent=2,sort_keys=True);f.write('\\n');f.flush();os.fsync(f.fileno())
env=dict(os.environ);env.update({{'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
                                 'OMP_NUM_THREADS':'8','MKL_NUM_THREADS':'8'}})
with (run/'supervisor.log').open('x') as log:
    proc=subprocess.Popen([str(python),str(code/'supervise_exp209_reconstruction_v1.py'),
                           '--contract',str(code/'contract.json'),'--run-root',str(run)],
                          cwd=code,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    stat=pathlib.Path(f'/proc/{{proc.pid}}/stat').read_text()
    tick=int(stat.rsplit(') ',1)[1].split()[19])
receipt={{'status':'STARTED_EXP209_RECONSTRUCTION_V1_CPU_ONLY','pid':proc.pid,
         'start_tick':tick,'run_root':str(run),'contract_sha256':{contract_sha!r},
         'bundle_manifest_sha256':{manifest_sha!r},'labels_read':False,'gpu_used':False}}
with (run/'supervisor_launch.json').open('x') as f:
    json.dump(receipt,f,indent=2,sort_keys=True);f.write('\\n');f.flush();os.fsync(f.fileno())
print(json.dumps(receipt))
'''


def launch(root: Path, host: str, expected_manifest_sha: str) -> dict:
    if not __debug__:
        raise RuntimeError("optimized Python disables launch guards")
    bundle = root / LOCAL_WORK / "bundle"
    _payload, manifest_sha, _count = pack_checked_bundle(bundle)
    assert len(expected_manifest_sha) == 64 and manifest_sha == expected_manifest_sha, "reviewed bundle SHA mismatch"
    contract_sha = sha(bundle / "contract.json")
    code_dir = REMOTE_ROOT + "/code/" + CODE_NAME
    run_root = REMOTE_ROOT + "/runs/" + CODE_NAME
    stage_receipt = root / "reports/exp209_reconstruction_v1_stage_20260927.json"
    assert stage_receipt.is_file(), "reviewed stage receipt missing"
    stage = json.loads(stage_receipt.read_text(encoding="utf-8"))
    assert stage["status"] == "STAGED_EXP209_RECONSTRUCTION_V1_NO_RUN"
    assert stage["bundle_manifest_sha256"] == manifest_sha and stage["code_dir"] == code_dir
    assert stage["labels_read"] is False and stage["gpu_used"] is False
    receipt_path = root / "reports/exp209_reconstruction_v1_launch_20260927.json"
    assert not receipt_path.exists(), "one-shot launch receipt already exists"
    program = remote_launch_program(code_dir, run_root, manifest_sha, contract_sha)
    result = subprocess.run(["ssh", host, "python3", "-"], input=program, text=True,
                            capture_output=True, timeout=180, check=True)
    response = json.loads(result.stdout.strip())
    assert response["status"] == "STARTED_EXP209_RECONSTRUCTION_V1_CPU_ONLY"
    assert response["run_root"] == run_root and response["contract_sha256"] == contract_sha
    assert response["bundle_manifest_sha256"] == manifest_sha
    assert response["labels_read"] is False and response["gpu_used"] is False
    write_once(receipt_path, {**response, "launch_script_sha256": sha(Path(__file__)),
                              "worker": "CPU8, CUDA hidden, 16 GiB worker address-space limit",
                              "target_label_access_authorized": False})
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="nsu-quadro")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--execute-reviewed-launch", action="store_true", required=True)
    args = parser.parse_args()
    print(json.dumps(launch(args.root.resolve(), args.host, args.expected_manifest_sha256), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
