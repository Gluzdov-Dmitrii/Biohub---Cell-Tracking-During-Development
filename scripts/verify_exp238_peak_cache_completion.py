"""Independently verify a completed EXP238 source-only peak-cache run.

This command reads sealed local receipts and remote files. It never opens GEFF,
starts inference, requests a GPU, or scores a graph. Use --write-receipt only
after reviewing the printed check-only result.
"""

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import subprocess

from monitor_exp213_job import QUEUE, ssh

if not __debug__ or os.environ.get("PYTHONOPTIMIZE", "0") not in ("", "0"):
    raise RuntimeError("EXP238 verifier requires Python assertions enabled")


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "work/exp238_source_peak_cache_local_20260927"
LOCAL_MANIFEST_SHA = "05589b389985ba1d297d5ae290a1de05414cc80f07fd9e2b67ef626e11549f02"
ORIGINAL_SOURCE44_RECEIPT = ROOT / "reports/exp238_source44_peak_cache_verified_20260927.json"
ORIGINAL_SOURCE44_RECEIPT_SHA = "1b27c1db034c8849ed5221c590b3bf40f53a70e96cee96d8ab973558c9ce7695"
UNGARDED_VERIFIER_SHA = "9640a825cab00263f844fa7aced6b737adf8d199915a4185dbac8cf95f17fd25"
SOURCE44_RECHECK = ROOT / "reports/exp238_source44_peak_cache_guarded_recheck_20260927.json"
SOURCE44_CORRECTION = ROOT / "reports/exp238_source44_peak_cache_verifier_optimization_correction_20260927.json"
PINS = {
    "source44": {
        "stage_sha256": "2275f8ff5593256197af81b95b25a37c8d077c2ec033304ccea776171308da32",
        "launch_sha256": "01356c6bb39194bb7fbe77bfb22f444da5166aa5573d2e29d444041f26cf485b",
        "plan_sha256": "c0dd159d03c4fd3ccd4f64ceb9f624987075a6a353e03ac54a5bedb0dfb6f2a5",
        "manifest_sha256": "f2f0046b532423c50198dd1bf5c8b14d7c9c56c05b972e799139b6f9c1d845fd",
        "movie_count": 8,
        "lease_id": "exp238-source44-peak-cache-v1-20260927",
    },
    "source6": {
        "stage_sha256": "50aad2cabfa71c12ce28a701e9a69e960be5800ea3182d13da149508df0d07cf",
        "launch_sha256": "5708cb91e5224fa421a1d3ef2ae7c5bf0682080c7a92880fabe5a3b770a5e4e8",
        "plan_sha256": "ae920bb9dc217ef058692084137ab4313ac7ef140302f862246452b6b8994aaf",
        "manifest_sha256": "5e6132f2444c405801fb9a450fdcce94ec6c6768f7f88fa517ff95fbfcd20166",
        "movie_count": 11,
        "lease_id": "exp238-source6-peak-cache-v1a01-20260927",
    },
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def local_gate(cohort, launch_path=None, launch_sha=None):
    """Resolve and pin every local input before making a remote read."""
    assert cohort in PINS
    pins = PINS[cohort]
    assert sha(BUNDLE / "local_bundle_manifest.json") == LOCAL_MANIFEST_SHA
    manifest = json.loads((BUNDLE / "local_bundle_manifest.json").read_text())
    for name, expected in manifest.items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == expected, name
    stage_path = ROOT / f"reports/exp238_{cohort}_peak_cache_stage_20260927.json"
    assert sha(stage_path) == pins["stage_sha256"]
    stage = json.loads(stage_path.read_text())
    if launch_path is None:
        launch_path = (ROOT / "reports/exp238_source44_peak_cache_launch_20260927.json"
                       if cohort == "source44" else ROOT /
                       "reports/exp238_source6_peak_cache_launch_a01_20260927_launch.json")
    launch_path = Path(launch_path).resolve(strict=True)
    assert launch_path.is_relative_to((ROOT / "reports").resolve())
    expected_launch_sha = pins["launch_sha256"]
    assert launch_sha is None or launch_sha == expected_launch_sha
    assert isinstance(expected_launch_sha, str) and len(expected_launch_sha) == 64
    assert sha(launch_path) == expected_launch_sha
    launch = json.loads(launch_path.read_text())
    plan_path = BUNDLE / cohort / "exp238_plan.json"
    assert sha(plan_path) == pins["plan_sha256"]
    plan = json.loads(plan_path.read_text())
    assert plan["experiment"] == "EXP238_SOURCE_PEAK_CACHE" and plan["cohort"] == cohort
    assert len(plan["movies"]) == pins["movie_count"]
    assert plan["source_labels_read"] is False and plan["target_data_opened"] is False
    assert plan["floor"] == 0.075 and plan["downsample_zyx"] == [1, 4, 4]
    assert plan["peak_dtype_itemsize"] == 12
    assert stage["status"] == "PREPARED_EXP238_REMOTE_STAGE_NO_LABELS"
    assert stage["cohort"] == cohort and stage["labels_read"] is False
    assert stage["run_started"] is False
    assert stage["local"] == {"manifest_sha256": LOCAL_MANIFEST_SHA,
                              "plan_sha256": pins["plan_sha256"]}
    assert stage["stage"]["status"] == "STAGED_EXP238_SOURCE_PEAK_CACHE_NO_LABELS"
    assert stage["stage"]["manifest_sha256"] == pins["manifest_sha256"]
    assert stage["stage"]["plan_sha256"] == pins["plan_sha256"]
    assert stage["stage"]["runner_sha256"] == plan["runner_sha256"]
    assert stage["stage"]["code"] == plan["code"]
    assert stage["stage"]["movies"] == pins["movie_count"]
    assert stage["stage"]["labels_read"] is False
    assert launch["cohort"] == cohort
    assert launch["status"] in ("LAUNCHED_EXP238_SOURCE_PEAK_CACHE",
                                  "LAUNCHED_EXP238_SOURCE6_PEAK_CACHE_A01")
    assert launch["source_labels_read"] is False and launch["target_data_opened"] is False
    config = launch["config"]
    assert config["experiment"] == "EXP238" and config["cohort"] == cohort
    assert config["code"] == plan["code"] and config["run"] == plan["run"]
    assert config["lease_id"] == pins["lease_id"]
    assert config["token"] == Path(plan["code"]).name
    assert config["script"] == "run_exp238_peak_cache.py"
    assert config["arguments"] == [plan["code"] + "/exp238_plan.json", "--plan-sha256",
                                   pins["plan_sha256"], "--manifest-sha256",
                                   pins["manifest_sha256"]]
    assert launch["lease"]["id"] == pins["lease_id"]
    assert launch["lease"]["run_path"] == plan["run"]
    assert launch["lease"]["token"] == config["token"]
    assert launch["lease"]["gpus"] == [config["gpu"]]
    assert launch["lease"]["state"] == "RESERVED"
    assert launch["launch"]["wrapper"] > 0 and launch["launch"]["observe"] > 0
    assert launch["control"]["controller_pid"] > 0
    if cohort == "source6":
        wait_path = ROOT / "reports/exp238_source6_peak_cache_attempt0_wait_20260927.json"
        assert sha(wait_path) == "2d62c76ef2915a86334f42219d1471c3caaa38205581a249704f05fe41c800f5"
        wait = json.loads(wait_path.read_text())
        assert wait["status"] == "WAITING_RESOURCE_CANCELLED_UNLAUNCHED_EXP238_SOURCE6_ATTEMPT0"
        assert wait["lease"]["id"] == "exp238-source6-peak-cache-v1-20260927"
        assert wait["lease"]["state"] == "CANCELLED" and wait["lease"]["gpus"] == []
        assert wait["lease"]["process"] is None
        assert all(not row["run_exists"] and row["matched_processes"] == []
                   for row in wait["remote_probes"])
    return {"cohort": cohort, "pins": pins, "plan": plan, "stage": stage,
            "launch": launch, "stage_sha256": sha(stage_path),
            "launch_sha256": sha(launch_path), "launch_path": str(launch_path)}


def released_queue(local):
    queue = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    rows = [row for row in queue["requests"]
            if row["id"] == local["launch"]["config"]["lease_id"]]
    assert len(rows) == 1
    row = rows[0]
    config = local["launch"]["config"]
    assert row["state"] == "RELEASED" and row["gpus"] == []
    assert row["owner"] == "biohub-agent"
    assert row["token"] == config["token"] and row["run_path"] == config["run"]
    assert row["project"] == "biohub-cell-tracking-during-development"
    assert row["pool"] == "a100"
    assert isinstance(row["process"], dict)
    return row


REMOTE_PROBE = r'''import ast,hashlib,json,math,os,pathlib,struct,subprocess
if not __debug__ or os.environ.get('PYTHONOPTIMIZE','0') not in ('','0'):
 raise RuntimeError('EXP238 remote verifier requires Python assertions enabled')
local=LOCAL
plan=local['plan'];stage=local['stage'];launched=local['launch']
config=launched['config'];code=pathlib.Path(config['code']);run=pathlib.Path(config['run'])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert code.is_dir() and run.is_dir()
assert sha(code/'code_manifest.json')==local['pins']['manifest_sha256']
manifest=json.loads((code/'code_manifest.json').read_text())
for name,expected in manifest.items():
 path=(code/name).resolve()
 assert path.is_relative_to(code.resolve()) and path.is_file() and sha(path)==expected,name
assert sha(code/'exp238_plan.json')==local['pins']['plan_sha256']
assert json.loads((code/'exp238_plan.json').read_text())==plan
assert sha(code/'exp238_parent_plan.json')==plan['parent_plan_sha256']
assert sha(code/'run_exp238_peak_cache.py')==plan['runner_sha256']
assert sha(code/'horaz/src/src/engine.py')==plan['patched_engine_sha256']
assert sha(code/'horaz/src/src/detection.py')==plan['patched_detection_sha256']
assert sha(plan['checkpoint'])==plan['checkpoint_sha256']
parent_code=pathlib.Path(plan['parent_code']);parent_run=pathlib.Path(plan['parent_run'])
assert sha(parent_code/'code_manifest.json')==plan['parent_manifest_sha256']
parent_manifest=json.loads((parent_code/'code_manifest.json').read_text())
for name,expected in parent_manifest.items():
 path=(parent_code/name).resolve()
 assert path.is_relative_to(parent_code.resolve()) and path.is_file() and sha(path)==expected,name
assert sha(parent_code/'plan.json')==plan['parent_plan_sha256']
assert sha(parent_run/'output/status.json')==plan['parent_status_sha256']
parent_status=json.loads((parent_run/'output/status.json').read_text())
assert parent_status['target_labels_read'] is False
assert [x['dataset'] for x in parent_status['records']]==[x['dataset'] for x in plan['movies']]
for movie,parent_record in zip(plan['movies'],parent_status['records']):
 name=movie['dataset'];p=parent_run/'output'/('graph__'+name+'.csv')
 assert parent_record['dataset']==name and parent_record['csv']==str(p)
 assert parent_record['csv_sha256']==movie['graph_csv_sha256']==sha(p)
 assert sha(p.with_suffix('.json'))==movie['graph_receipt_sha256']
 assert json.loads(p.with_suffix('.json').read_text())==parent_record
assert json.loads((run/'config.json').read_text())==config
remote_launch=json.loads((run/'launch.json').read_text())
assert remote_launch['config']==config
assert remote_launch['command']==['taskset','-c',config['cpu_affinity'],
 str(pathlib.Path(config['code']).parents[1]/'envs/prepost/py3.11-stdlib-v1/bin/python'),
 str(code/'run_exp238_peak_cache.py'),str(code/'exp238_plan.json'),
 '--plan-sha256',local['pins']['plan_sha256'],'--manifest-sha256',local['pins']['manifest_sha256']]
ex=json.loads((run/'exit.json').read_text())
supervision=json.loads((run/'supervision/complete.json').read_text())
control=json.loads((run/'supervision/control.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert ex['pid']==remote_launch['pid'] and ex['start']==remote_launch['start']
assert supervision['status']=='RELEASED_AFTER_VERIFIED_EXIT' and supervision['exit']==ex
assert control['action']=='release' and control['queue']['state']=='RELEASED'
assert control['queue']['id']==config['lease_id']
assert control['queue']['run_path']==str(run)
assert control['queue']['process']=={'pid':ex['pid'],'start':ex['start']}
identity=False;group=False;matches=[]
for stat in pathlib.Path('/proc').glob('[0-9]*/stat'):
 try:
  raw=stat.read_text();f=raw[raw.rfind(')')+2:].split()
  if f[0]=='Z':continue
  pid=int(stat.parent.name)
  if pid==ex['pid'] and f[19]==ex['start']:identity=True
  if int(f[2])==ex['pid']:group=True
  command=(stat.parent/'cmdline').read_bytes().replace(b'\x00',b' ')
  if str(run).encode() in command or str(code/'run_exp238_peak_cache.py').encode() in command:
   matches.append(pid)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert not identity and not group and not matches
gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid',
 '--format=csv,noheader'],text=True)
gpu_pids={int(line.split(',')[0]) for line in gpu.splitlines() if line.strip()}
worker_gpu_pids=sorted(gpu_pids & ({ex['pid']}|set(matches)))
assert worker_gpu_pids==[]
output=run/'output';names=[x['dataset'] for x in plan['movies']]
expected={'status.json'}|{kind+'__'+name+suffix for name in names
 for kind,suffixes in [('graph',['.csv']),('peaks',['.npy','.json']),('record',['.json'])]
 for suffix in suffixes}
assert {p.name for p in output.iterdir()}==expected
status_path=output/'status.json';status=json.loads(status_path.read_text())
assert status['status']=='PASS_EXP238_SOURCE_PEAK_CACHE_NO_LABELS'
assert status['cohort']==local['cohort'] and status['source_labels_read'] is False
assert status['target_data_opened'] is False and status['graph_replay']=='EXACT_OLD_CSV_SHA256'
assert status['checkpoint_sha256']==plan['checkpoint_sha256']
assert status['parent_status_sha256']==plan['parent_status_sha256']
assert status['plan_sha256']==local['pins']['plan_sha256']
assert len(status['records'])==len(names)
assert [x['dataset'] for x in status['records']]==names
def npy(path,count):
 with path.open('rb') as f:
  assert f.read(6)==b'\x93NUMPY'
  major,minor=f.read(2)
  size=int.from_bytes(f.read(2 if major==1 else 4),'little')
  header=ast.literal_eval(f.read(size).decode('latin1'))
  assert header['fortran_order'] is False and header['shape']==(count,)
  assert header['descr']==[('t','<u2'),('z','<u2'),('y','<u2'),('x','<u2'),('probability','<f4')]
  body=f.read()
 assert len(body)==count*12
 return body,header
rows=[];payload_sum=0;peak_sum=0
for movie,record in zip(plan['movies'],status['records']):
 name=movie['dataset'];assert record['dataset']==name
 assert record['source_graph_sha256']==movie['graph_csv_sha256']
 assert record['graph_csv_sha256']==movie['graph_csv_sha256']
 assert record['checkpoint_sha256']==plan['checkpoint_sha256']
 graph=output/('graph__'+name+'.csv')
 assert sha(graph)==movie['graph_csv_sha256']
 with graph.open('rb') as f:assert f.readline().rstrip(b'\r\n')==b'id,dataset,row_type,node_id,t,z,y,x,source_id,target_id'
 record_path=output/('record__'+name+'.json')
 assert json.loads(record_path.read_text())==record
 meta_path=output/('peaks__'+name+'.json');meta=json.loads(meta_path.read_text())
 peak_path=output/('peaks__'+name+'.npy')
 assert meta['dataset']==name and meta['floor']==plan['floor']
 assert meta['source_labels_read'] is False and meta['target_data_opened'] is False
 assert meta['peak_count']==record['peak_count']
 assert meta['peak_payload_bytes']==record['peak_payload_bytes']==12*meta['peak_count']
 assert meta['peak_npy_sha256']==record['peak_npy_sha256']==sha(peak_path)
 assert record['peak_metadata_sha256']==sha(meta_path)
 assert meta['peak_dtype']==[['t','<u2'],['z','<u2'],['y','<u2'],['x','<u2'],['probability','<f4']]
 frames=meta['frames'];assert len(frames)==movie['shape'][0]==100
 assert [x['t'] for x in frames]==list(range(100))
 assert sum(x['count'] for x in frames)==meta['peak_count']
 assert all(0<=x['count']<=plan['max_peaks_per_frame'] and x['floor']==0.075
            and x['downsample_zyx']==[1,4,4] and x['logit_shape_zyx']==[64,64,64]
            and x['selected_threshold'] in (0.075,0.96875)
            and x['tta'] is True and isinstance(x['adaptive_mode'],bool)
            for x in frames)
 body,header=npy(peak_path,meta['peak_count'])
 per_frame=[0]*100
 for t,z,y,x,p in struct.iter_unpack('<HHHHf',body):
  assert t<100 and z<64 and y<64 and x<64
  assert math.isfinite(p) and 0.075<p<=1.0
  per_frame[t]+=1
 assert per_frame==[x['count'] for x in frames]
 assert record['peak_count']<=plan['max_peaks_per_movie']
 payload_sum+=len(body);peak_sum+=record['peak_count']
 rows.append({'dataset':name,'graph_csv_sha256':sha(graph),
              'record_sha256':sha(record_path),'peak_npy_sha256':sha(peak_path),
              'peak_metadata_sha256':sha(meta_path),'peak_count':record['peak_count'],
              'peak_payload_bytes':len(body)})
assert payload_sum==status['peak_payload_bytes']<=plan['max_peak_payload_bytes_all19']
print(json.dumps({'status':'PASS_EXP238_PEAK_CACHE_COMPLETION_NO_LABELS',
 'cohort':local['cohort'],'movie_count':len(rows),'peak_count':peak_sum,
 'peak_payload_bytes':payload_sum,'rows':rows,
 'code_manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':sha(code/'exp238_plan.json'),
 'parent_status_sha256':sha(parent_run/'output/status.json'),
 'status_sha256':sha(status_path),'exit_sha256':sha(run/'exit.json'),
 'supervision_sha256':sha(run/'supervision/complete.json'),
 'control_sha256':sha(run/'supervision/control.json'),
 'remote_launch_sha256':sha(run/'launch.json'),
 'worker_process':{'pid':ex['pid'],'start':ex['start']},
 'source_labels_read':False,'target_data_opened':False,
 'identity_alive':identity,'group_alive':group,'matching_processes':matches,
 'worker_gpu_pids':worker_gpu_pids}))
'''


def remote_source(local):
    compact = {key: local[key] for key in ("cohort", "pins", "plan", "stage", "launch")}
    return REMOTE_PROBE.replace("LOCAL", repr(compact), 1)


def remote_check(local, timeout=300):
    source = remote_source(local)
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                             "nsu-a100", "env PYTHONOPTIMIZE=0 python3 -"], input=source, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Remote EXP238 completion gate exit {result.returncode}: "
                           f"{result.stderr[-2000:]}")
    return json.loads(result.stdout)


def verify(cohort, *, launch_path=None, launch_sha=None, write_receipt=False,
           queue_reader=released_queue, remote_reader=remote_check, receipt_path=None,
           return_full=False):
    local = local_gate(cohort, launch_path, launch_sha)
    receipt_path = Path(receipt_path or
                        ROOT / f"reports/exp238_{cohort}_peak_cache_verified_20260927.json")
    assert not receipt_path.exists(), "Existing receipt requires reconciliation"
    before = queue_reader(local)
    assert before["state"] == "RELEASED" and before["gpus"] == []
    assert before["id"] == local["launch"]["config"]["lease_id"]
    remote = remote_reader(local)
    assert remote["status"] == "PASS_EXP238_PEAK_CACHE_COMPLETION_NO_LABELS"
    assert remote["cohort"] == cohort and remote["movie_count"] == local["pins"]["movie_count"]
    assert remote["code_manifest_sha256"] == local["pins"]["manifest_sha256"]
    assert remote["plan_sha256"] == local["pins"]["plan_sha256"]
    assert remote["parent_status_sha256"] == local["plan"]["parent_status_sha256"]
    assert remote["source_labels_read"] is False and remote["target_data_opened"] is False
    assert remote["identity_alive"] is False and remote["group_alive"] is False
    assert remote["matching_processes"] == [] and remote["worker_gpu_pids"] == []
    assert len(remote["rows"]) == local["pins"]["movie_count"]
    assert [row["dataset"] for row in remote["rows"]] == [row["dataset"]
                                                            for row in local["plan"]["movies"]]
    assert all(row["graph_csv_sha256"] == movie["graph_csv_sha256"]
               for row, movie in zip(remote["rows"], local["plan"]["movies"]))
    assert sum(row["peak_payload_bytes"] for row in remote["rows"]) == remote["peak_payload_bytes"]
    assert sum(row["peak_count"] for row in remote["rows"]) == remote["peak_count"]
    after = queue_reader(local)
    assert before == after and after["process"] == remote["worker_process"]
    receipt = {"status": "PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION",
               "cohort": cohort, "stage_receipt_sha256": local["stage_sha256"],
               "launch_receipt_sha256": local["launch_sha256"],
               "launch_receipt": local["launch_path"],
               "local_bundle_manifest_sha256": LOCAL_MANIFEST_SHA,
               "exit0": True, "released": True, "all_graph_hashes_exact": True,
               "source_only": True, "labels_read": False,
               "status_sha256": remote["status_sha256"],
               "plan_sha256": remote["plan_sha256"],
               "manifest_sha256": remote["code_manifest_sha256"],
               "ordered_ids": [row["dataset"] for row in remote["rows"]],
               "queue_release": {"id": after["id"], "state": after["state"],
                                 "process": after["process"], "gpus": after["gpus"]},
               "remote": remote, "graph_hashes_sha256": digest([
                   {"dataset": row["dataset"], "csv_sha256": row["graph_csv_sha256"]}
                   for row in remote["rows"]]),
               "peak_artifact_hashes_sha256": digest([
                   {"dataset": row["dataset"], "npy": row["peak_npy_sha256"],
                    "metadata": row["peak_metadata_sha256"]}
                   for row in remote["rows"]]),
               "source_labels_read": False, "target_data_opened": False,
               "source_score_computed": False, "kaggle_post": False}
    if write_receipt:
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    if return_full:
        return receipt
    return {"status": receipt["status"], "cohort": cohort,
            "movie_count": remote["movie_count"], "peak_count": remote["peak_count"],
            "peak_payload_bytes": remote["peak_payload_bytes"],
            "graph_hashes_sha256": receipt["graph_hashes_sha256"],
            "peak_artifact_hashes_sha256": receipt["peak_artifact_hashes_sha256"],
            "receipt": str(receipt_path) if write_receipt else None,
            "receipt_sha256": sha(receipt_path) if write_receipt else None}


def _write_once(path, body):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(body, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def recheck_source44(*, write_receipts=False):
    """Repeat the source44 read under explicit assertion guards; retain the original."""
    assert sha(ORIGINAL_SOURCE44_RECEIPT) == ORIGINAL_SOURCE44_RECEIPT_SHA
    original = json.loads(ORIGINAL_SOURCE44_RECEIPT.read_text())
    assert original["status"] == "PASS_EXP238_SOURCE_PEAK_CACHE_INDEPENDENT_VERIFICATION"
    assert original["cohort"] == "source44"
    assert not SOURCE44_RECHECK.exists() and not SOURCE44_CORRECTION.exists()
    fresh = verify("source44", receipt_path=SOURCE44_RECHECK, return_full=True)
    assert fresh == original, "Guarded recheck differs from the sealed original receipt"
    guarded_sha = sha(Path(__file__))
    recheck = {"status": "PASS_EXP238_SOURCE_PEAK_CACHE_GUARDED_RECHECK_NO_LABELS",
               "cohort": "source44", "original_receipt_sha256": ORIGINAL_SOURCE44_RECEIPT_SHA,
               "unguarded_verifier_sha256": UNGARDED_VERIFIER_SHA,
               "guarded_verifier_sha256": guarded_sha,
               "identical_receipt_payload": True, "identical_remote": True,
               "exit0": True, "released": True, "all_graph_hashes_exact": True,
               "source_only": True, "labels_read": False,
               "ordered_ids": fresh["ordered_ids"],
               "status_sha256": fresh["status_sha256"],
               "plan_sha256": fresh["plan_sha256"],
               "manifest_sha256": fresh["manifest_sha256"],
               "graph_hashes_sha256": fresh["graph_hashes_sha256"],
               "peak_artifact_hashes_sha256": fresh["peak_artifact_hashes_sha256"],
               "verification": fresh}
    if write_receipts:
        _write_once(SOURCE44_RECHECK, recheck)
        correction = {"status": "CORRECTED_EXP238_SOURCE44_VERIFIER_OPTIMIZATION_GUARD",
                      "original_receipt_sha256": ORIGINAL_SOURCE44_RECEIPT_SHA,
                      "unguarded_executed_verifier_sha256": UNGARDED_VERIFIER_SHA,
                      "guarded_verifier_sha256": guarded_sha,
                      "guarded_recheck_receipt_sha256": sha(SOURCE44_RECHECK),
                      "original_receipt_preserved": True,
                      "reason": "The original verifier used assertions without an explicit optimization guard; a distinct guarded read-only recheck matched its full receipt payload."}
        _write_once(SOURCE44_CORRECTION, correction)
    return {"status": recheck["status"], "cohort": "source44",
            "identical_receipt_payload": True,
            "guarded_verifier_sha256": guarded_sha,
            "recheck_receipt": str(SOURCE44_RECHECK) if write_receipts else None,
            "recheck_receipt_sha256": sha(SOURCE44_RECHECK) if write_receipts else None,
            "correction_receipt": str(SOURCE44_CORRECTION) if write_receipts else None,
            "correction_receipt_sha256": sha(SOURCE44_CORRECTION) if write_receipts else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=tuple(PINS), required=True)
    parser.add_argument("--launch-receipt", type=Path)
    parser.add_argument("--launch-sha256")
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--recheck-source44", action="store_true")
    args = parser.parse_args()
    if args.recheck_source44:
        assert args.cohort == "source44"
        print(json.dumps(recheck_source44(write_receipts=args.write_receipt), sort_keys=True))
        return
    print(json.dumps(verify(args.cohort, launch_path=args.launch_receipt,
                            launch_sha=args.launch_sha256,
                            write_receipt=args.write_receipt), sort_keys=True))


if __name__ == "__main__":
    main()
