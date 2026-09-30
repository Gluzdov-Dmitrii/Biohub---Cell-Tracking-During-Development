"""Guarded one-shot CPU launch for the staged EXP209 reconstructed scorer.

This helper remains local-only and uninvoked until root reviews the exact
stage receipt. Any ambiguous SSH outcome leaves intent/control for audit.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import stage_exp209_reconstructed_scorer_v1 as stage_guard


REMOTE = stage_guard.REMOTE
NAME = stage_guard.NAME
CODE_DIR = stage_guard.CODE_DIR
RUN_ROOT = stage_guard.RUN_ROOT
MANIFEST_SHA = stage_guard.MANIFEST_SHA
CONFIG_SHA = stage_guard.CONFIG_SHA
SCORER_SHA = stage_guard.SCORER_SHA
CONTROL = f"{REMOTE}/runs/.{NAME}.control"
PYTHON = f"{REMOTE}/envs/current-organizer-py311-e13cf-v1/bin/python"
RECON_GATE = (f"{REMOTE}/runs/exp209_current_metric_reconstruction_v1_20260927/"
              "no_metric_gate.json")
RECON_GATE_SHA = "8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1"
LOCAL_INTENT = "reports/exp209_reconstructed_scorer_v1_launch_intent_20260927.json"
LOCAL_RECEIPT = "reports/exp209_reconstructed_scorer_v1_launch_20260927.json"
SUPERVISOR_SOURCE = "scripts/supervise_exp209_reconstructed_scorer_v1.py"


def preflight_source() -> str:
    """Run only the pinned current-env synthetic contract, with GEFF denied."""
    return '''import json,os,pathlib,sys
code=pathlib.Path(%r)
assert code.is_dir()
def audit(event,args):
    if event not in ('open','os.listdir','os.scandir','os.stat','os.remove','os.rename') or not args: return
    raw=args[0]
    if isinstance(raw,(str,bytes,os.PathLike)):
        if any(part.lower().endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
            raise PermissionError('EXP209 launch preflight forbids GEFF')
sys.addaudithook(audit)
sys.path.insert(0,str(code))
from score_current_metric_lightweight import runtime_gate
config={'tracksdata_commit':'e13cf379b5127deeb8301ce56410fda35b5a3cf9',
        'current_metrics_sha256':'cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444',
        'current_division_sha256':'0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9',
        'current_metrics':str(code/'current_official/metrics.py'),
        'current_division':str(code/'current_official/division_metrics.py')}
runtime,contract=runtime_gate(config,config['current_metrics_sha256'],config['current_division_sha256'])
assert runtime['profile']=='remote_py311'
assert contract['status']=='PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT'
print(json.dumps({'status':'PASS_EXP209_SCORER_CURRENT_ENV_SYNTHETIC_NO_GEFF',
                  'runtime':runtime,'synthetic_contract':contract,
                  'geff_opened':False,'target_metric_executed':False},sort_keys=True))
''' % CODE_DIR


def remote_launch_program(expected_hashes: dict[str, str], stage_complete_sha: str,
                          local_intent_sha: str, stage_receipt_sha: str,
                          supervisor_bytes: bytes) -> str:
    supervisor_b64 = base64.b64encode(supervisor_bytes).decode("ascii")
    supervisor_sha = stage_guard.sha_bytes(supervisor_bytes)
    preflight = preflight_source()
    return f'''import base64,hashlib,json,os,pathlib,subprocess,time
if not __debug__: raise RuntimeError('optimized Python disables launch guards')
code=pathlib.Path({CODE_DIR!r});run=pathlib.Path({RUN_ROOT!r})
control=pathlib.Path({CONTROL!r});python=pathlib.Path({PYTHON!r})
stage_complete=pathlib.Path({stage_guard.STAGE_COMPLETE!r})
stage_intent=pathlib.Path({stage_guard.STAGE_INTENT!r})
recon_gate=pathlib.Path({RECON_GATE!r})
assert code.parent==pathlib.Path({(REMOTE+'/code')!r}) and code.name=={NAME!r}
assert run.parent==pathlib.Path({(REMOTE+'/runs')!r}) and run.name=={NAME!r}
assert control.parent==run.parent and control.name=={('.'+NAME+'.control')!r}
assert code.is_dir() and python.is_file() and os.access(python,os.X_OK)
assert not run.exists() and not control.exists(), 'scorer output/control namespace already exists'
assert hashlib.sha256(recon_gate.read_bytes()).hexdigest()=={RECON_GATE_SHA!r}, 'reconstruction graph gate SHA changed'
assert hashlib.sha256(stage_complete.read_bytes()).hexdigest()=={stage_complete_sha!r}, 'remote stage receipt changed'
stage=json.loads(stage_complete.read_text())
assert stage['status']=='STAGED_EXP209_SCORER_V1_NO_RUN' and stage['code_dir']==str(code)
assert stage['run_root']==str(run) and stage['bundle_manifest_sha256']=={MANIFEST_SHA!r}
assert hashlib.sha256(stage_intent.read_bytes()).hexdigest()==stage['remote_stage_intent_sha256']
assert all(not p.is_symlink() for p in code.rglob('*')), 'remote scorer payload symlink'
manifest_raw=(code/'bundle_manifest.json').read_bytes()
assert hashlib.sha256(manifest_raw).hexdigest()=={MANIFEST_SHA!r}
manifest=json.loads(manifest_raw)
expected={expected_hashes!r}
actual={{p.relative_to(code).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in code.rglob('*') if p.is_file()}}
assert actual==expected==stage['file_hashes'], 'remote scorer payload changed after stage'
assert actual['config.json']=={CONFIG_SHA!r} and actual['score_exp209_reconstructed_current_v1.py']=={SCORER_SHA!r}
assert len(manifest['files'])==14 and len(actual)==15
env=dict(os.environ);env.update({{'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1',
                                  'OMP_NUM_THREADS':'8','MKL_NUM_THREADS':'8',
                                  'OPENBLAS_NUM_THREADS':'8'}})
preflight=subprocess.run([str(python),'-c',{preflight!r}],cwd=code,env=env,
                         text=True,capture_output=True,timeout=240,check=True)
lines=preflight.stdout.strip().splitlines()
assert len(lines)==1, 'isolated current-env preflight ambiguous stdout'
checked=json.loads(lines[0])
assert checked['status']=='PASS_EXP209_SCORER_CURRENT_ENV_SYNTHETIC_NO_GEFF'
assert checked['geff_opened'] is False and checked['target_metric_executed'] is False
assert not run.exists() and not control.exists(), 'scorer output/control appeared during preflight'
supervisor=base64.b64decode({supervisor_b64!r},validate=True)
assert hashlib.sha256(supervisor).hexdigest()=={supervisor_sha!r}
control.mkdir(parents=False,exist_ok=False)
def once(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    with os.fdopen(fd,'wb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
    parent=os.open(path.parent,os.O_RDONLY)
    try: os.fsync(parent)
    finally: os.close(parent)
once(control/'supervisor.py',supervisor)
intent={{'status':'LAUNCH_INTENT_EXP209_SCORER_V1_CPU_ONLY','code_dir':str(code),
        'run_root':str(run),'control_dir':str(control),
        'bundle_manifest_sha256':{MANIFEST_SHA!r},'config_sha256':{CONFIG_SHA!r},
        'reconstruction_gate_sha256':{RECON_GATE_SHA!r},
        'remote_stage_complete_sha256':{stage_complete_sha!r},
        'local_stage_receipt_sha256':{stage_receipt_sha!r},
        'local_launch_intent_sha256':{local_intent_sha!r},
        'supervisor_sha256':{supervisor_sha!r},
        'preflight':checked,'labels_read':False,'gpu_used':False}}
once(control/'launch_intent.json',(json.dumps(intent,sort_keys=True,indent=2)+'\\n').encode())
intent_sha=hashlib.sha256((control/'launch_intent.json').read_bytes()).hexdigest()
with (control/'supervisor.log').open('xb') as log:
    proc=subprocess.Popen([str(python),str(control/'supervisor.py'),
                           '--launch-intent-sha256',intent_sha],cwd=control,env=env,
                          stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    stat=pathlib.Path(f'/proc/{{proc.pid}}/stat').read_text()
    tick=int(stat.rsplit(') ',1)[1].split()[19])
worker_start=control/'worker_started.json'
for _ in range(150):
    if worker_start.is_file(): break
    if proc.poll() is not None or (control/'completion.json').exists():
        raise RuntimeError('CPU supervisor exited before worker start; inspect control namespace')
    time.sleep(0.2)
assert worker_start.is_file(), 'CPU worker start not confirmed within 30 seconds'
worker=json.loads(worker_start.read_text())
assert worker['status']=='STARTED_EXP209_SCORER_V1_CPU_ONLY'
assert type(worker['pid']) is int and worker['pid']>0
assert type(worker['start_tick']) is int and worker['start_tick']>0
started={{'status':'STARTED_EXP209_SCORER_V1_CPU_SUPERVISOR',
         'supervisor_pid':proc.pid,'supervisor_start_tick':tick,
         'worker_pid':worker['pid'],'worker_start_tick':worker['start_tick'],
         'control_dir':str(control),'run_root':str(run),
         'bundle_manifest_sha256':{MANIFEST_SHA!r},'config_sha256':{CONFIG_SHA!r},
         'remote_launch_intent_sha256':intent_sha,
         'supervisor_sha256':{supervisor_sha!r},
         'worker_started_sha256':hashlib.sha256(worker_start.read_bytes()).hexdigest(),
         'preflight':checked,'launcher_geff_opened':False,
         'launcher_target_metric_executed':False,'gpu_used':False}}
once(control/'supervisor_started.json',(json.dumps(started,sort_keys=True,indent=2)+'\\n').encode())
print(json.dumps(started,sort_keys=True))
'''


def launch(root: Path, host: str, expected_manifest_sha: str,
           expected_config_sha: str, expected_stage_receipt_sha: str) -> dict:
    root = root.resolve()
    stage_guard.require(expected_manifest_sha == MANIFEST_SHA and
                        expected_config_sha == CONFIG_SHA,
                        "reviewed scorer manifest/config SHA arguments required")
    bundle = root / stage_guard.LOCAL_BUNDLE
    _payload, hashes = stage_guard.pack_checked_bundle(bundle)
    stage_receipt_path = root / stage_guard.LOCAL_RECEIPT
    stage_guard.require(len(expected_stage_receipt_sha) == 64 and
                        stage_receipt_path.is_file() and
                        stage_guard.sha(stage_receipt_path) == expected_stage_receipt_sha,
                        "root-reviewed stage receipt SHA required")
    stage = json.loads(stage_receipt_path.read_text(encoding="utf-8"))
    stage_guard.require(stage["status"] == "PASS_EXP209_SCORER_V1_STAGED_NO_RUN" and
                        stage["code_dir"] == CODE_DIR and stage["run_root"] == RUN_ROOT and
                        stage["file_hashes"] == hashes and
                        stage["bundle_manifest_sha256"] == MANIFEST_SHA and
                        stage["config_sha256"] == CONFIG_SHA and
                        len(stage["remote_stage_intent_sha256"]) == 64 and
                        len(stage["remote_stage_complete_sha256"]) == 64 and
                        stage["labels_read"] is False and
                        stage["metric_executed"] is False and
                        stage["remote_run_created"] is False,
                        "stage receipt does not describe sealed scorer bundle")
    supervisor_path = root / SUPERVISOR_SOURCE
    supervisor_bytes = supervisor_path.read_bytes()
    supervisor_sha = stage_guard.sha_bytes(supervisor_bytes)
    intent_path = root / LOCAL_INTENT
    receipt_path = root / LOCAL_RECEIPT
    stage_guard.require(not intent_path.exists() and not receipt_path.exists(),
                        "scorer launch already attempted; reconcile before any new version")
    local_intent = {"status": "LAUNCH_INTENT_EXP209_SCORER_V1_LOCAL_CPU_ONLY",
                    "code_dir": CODE_DIR, "run_root": RUN_ROOT,
                    "control_dir": CONTROL,
                    "bundle_manifest_sha256": MANIFEST_SHA,
                    "config_sha256": CONFIG_SHA,
                    "stage_receipt_sha256": expected_stage_receipt_sha,
                    "reconstruction_gate_sha256": RECON_GATE_SHA,
                    "supervisor_source_sha256": supervisor_sha,
                    "launcher_source_sha256": stage_guard.sha(Path(__file__)),
                    "remote_action": "UNATTEMPTED", "gpu_used": False}
    stage_guard.write_once_durable(intent_path, local_intent)
    # Never retry after a transport exception: the remote process may be live.
    program = remote_launch_program(hashes, stage["remote_stage_complete_sha256"],
                                    stage_guard.sha(intent_path), expected_stage_receipt_sha,
                                    supervisor_bytes)
    response = stage_guard.ssh_python(host, program, timeout=600)
    stage_guard.require(response.get("status") == "STARTED_EXP209_SCORER_V1_CPU_SUPERVISOR" and
                        response.get("control_dir") == CONTROL and
                        response.get("run_root") == RUN_ROOT and
                        response.get("bundle_manifest_sha256") == MANIFEST_SHA and
                        response.get("config_sha256") == CONFIG_SHA and
                        response.get("supervisor_sha256") == supervisor_sha and
                        type(response.get("supervisor_pid")) is int and
                        type(response.get("supervisor_start_tick")) is int and
                        type(response.get("worker_pid")) is int and
                        type(response.get("worker_start_tick")) is int and
                        response.get("launcher_geff_opened") is False and
                        response.get("launcher_target_metric_executed") is False and
                        response.get("gpu_used") is False and
                        response.get("preflight", {}).get("status") ==
                        "PASS_EXP209_SCORER_CURRENT_ENV_SYNTHETIC_NO_GEFF",
                        "remote launch response is incomplete or ambiguous")
    receipt = {**response,
               "local_launch_intent_sha256": stage_guard.sha(intent_path),
               "local_stage_receipt_sha256": expected_stage_receipt_sha,
               "launcher_source_sha256": stage_guard.sha(Path(__file__)),
               "worker_resources": {"cpu_count": 8, "memory_bytes": 32 * 1024**3,
                                    "wall_timeout_seconds": 8 * 60 * 60},
               "score_result_not_read_by_launcher": True,
               "kaggle_post": False}
    stage_guard.write_once_durable(receipt_path, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="nsu-quadro")
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--expected-stage-receipt-sha256", required=True)
    parser.add_argument("--execute-reviewed-launch", action="store_true", required=True)
    args = parser.parse_args()
    result = launch(args.root, args.host, args.expected_manifest_sha256,
                    args.expected_config_sha256, args.expected_stage_receipt_sha256)
    print(json.dumps({"status": result["status"],
                      "supervisor_pid": result["supervisor_pid"],
                      "control_dir": result["control_dir"]}))


if __name__ == "__main__":
    main()
