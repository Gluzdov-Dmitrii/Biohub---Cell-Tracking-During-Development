"""Stage the epoch-20 source scorer after all eight no-label graphs release."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
INFERENCE_CODE = REMOTE + "/code/exp227_source_graph20_v1_20260927"
INFERENCE_RUN = REMOTE + "/runs/exp227_source_graph20_v1_20260927"
CODE = REMOTE + "/code/exp227_source_graph20_scorer_v1_20260927"
RUN = REMOTE + "/runs/exp227_source_graph20_official_v1_20260927"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"
EXPECTED_MOVIES = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    prepared_path = ROOT / "reports/exp227_source_graph20_prepare_20260927.json"
    prepared = json.loads(prepared_path.read_text())
    assert prepared["status"] == "PREPARED_EXP227_SOURCE_GRAPH20_NO_LABELS"
    assert prepared["target_labels_read"] is False
    config = json.loads((ROOT / "reports/exp227_source_graph20_config_20260927.json").read_text())
    assert config["experiment"] == "EXP227"
    assert config["code"] == INFERENCE_CODE and config["run"] == INFERENCE_RUN
    assert config["lease_id"] == "exp227-source-graph20-v1-20260927"
    assert config["arguments"] == [INFERENCE_CODE + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert sha(ROOT / "reports/exp227_source_graph20_plan_20260927.json") == prepared["stage"]["plan_sha256"]
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    leases = [row for row in state["requests"] if row["id"] == config["lease_id"]]
    assert len(leases) == 1 and leases[0]["state"] == "RELEASED"
    assert leases[0]["run_path"] == INFERENCE_RUN

    preflight = '''import csv,hashlib,json,math,pathlib
code=pathlib.Path(INFERENCE_CODE);run=pathlib.Path(INFERENCE_RUN)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=EXPECTED_MOVIES
columns=['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
assert sha(code/'code_manifest.json')==INFERENCE_MANIFEST_SHA
for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
 path=(code/name).resolve();assert path.is_relative_to(code.resolve()) and sha(path)==digest,name
assert sha(code/'plan.json')==PLAN_SHA
plan=json.loads((code/'plan.json').read_text())
assert plan['experiment']=='EXP227_SOURCE_GRAPH20' and plan['checkpoint_epoch']==20
assert plan['source_embryo']=='44b6' and plan['target_embryo']=='6bba' and plan['fold']==1
assert plan['source_manifest_sha256']==SOURCE_MANIFEST_SHA
assert sha(code/'source44_manifest.json')==SOURCE_MANIFEST_SHA
source=json.loads((code/'source44_manifest.json').read_text())
assert [row['dataset_id'] for row in source['inner_validation']]==names
assert [row['dataset'] for row in plan['movies']]==names
assert pathlib.Path(plan['code']).resolve()==code.resolve()
assert pathlib.Path(plan['checkpoint']).name=='epoch_020.pt'
assert plan['checkpoint_sha256']==CHECKPOINT_SHA
assert sha(pathlib.Path(plan['checkpoint']))==CHECKPOINT_SHA
assert pathlib.Path(plan['output']).resolve()==(run/'output').resolve()
assert all(pathlib.Path(row['zarr']).resolve()==(pathlib.Path(DATA_DIR)/(row['dataset']+'.zarr')).resolve() for row in plan['movies'])
assert all(len(row['shape'])==4 and all(isinstance(v,int) and v>0 for v in row['shape']) for row in plan['movies'])
ex=json.loads((run/'exit.json').read_text())
sup=json.loads((run/'supervision/complete.json').read_text())
ctl=json.loads((run/'supervision/control.json').read_text())
assert ex['returncode']==0 and ex['hard_timeout'] is False
assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and sup['exit']==ex
assert ctl['action']=='release' and ctl['queue']['state']=='RELEASED'
assert pathlib.Path(ctl['queue']['run_path']).resolve()==run.resolve()
status=json.loads((run/'output/status.json').read_text())
assert status['status']=='PASS_EXP227_SOURCE_GRAPH20_NO_LABELS'
assert status['target_labels_read'] is False and status['source_labels_read'] is False
assert status['source_embryo']=='44b6'
assert len(status['records'])==len(names)
assert status['checkpoint_sha256']==CHECKPOINT_SHA and status['plan_sha256']==PLAN_SHA
assert status['movies']==names
expected={'status.json'}|{'graph__'+name+suffix for name in status['movies'] for suffix in ('.csv','.json')}
assert {p.name for p in (run/'output').iterdir()}==expected
hashes=[]
for row,record in zip(plan['movies'],status['records']):
 name=row['dataset'];shape=row['shape']
 csv_path=run/'output'/('graph__'+name+'.csv');receipt_path=csv_path.with_suffix('.json')
 assert record['dataset']==name and record['shape']==shape
 assert record['checkpoint_sha256']==CHECKPOINT_SHA and record['plan_sha256']==PLAN_SHA
 assert pathlib.Path(record['csv']).resolve()==csv_path.resolve()
 assert sha(csv_path)==record['csv_sha256']
 assert json.loads(receipt_path.read_text())==record
 ids=set();nodes={};edges=[]
 with csv_path.open(newline='') as handle:
  reader=csv.DictReader(handle);assert reader.fieldnames==columns
  for item in reader:
   assert item['dataset']==name
   idx=int(item['id']);assert idx not in ids;ids.add(idx)
   if item['row_type']=='node':
    node=int(item['node_id']);assert node>=0 and node not in nodes
    point=tuple(float(item[k]) for k in ('t','z','y','x'))
    assert all(math.isfinite(v) and v.is_integer() and 0<=v<bound for v,bound in zip(point,shape))
    assert int(item['source_id'])==int(item['target_id'])==-1
    nodes[node]=tuple(int(v) for v in point)
   else:
    assert item['row_type']=='edge'
    assert all(float(item[k])==-1 for k in ('node_id','t','z','y','x'))
    edges.append((int(item['source_id']),int(item['target_id'])))
 assert nodes and len(edges)==len(set(edges))
 incoming={};outgoing={}
 for parent,child in edges:
  assert parent in nodes and child in nodes and nodes[child][0]==nodes[parent][0]+1
  incoming[child]=incoming.get(child,0)+1;outgoing[parent]=outgoing.get(parent,0)+1
 assert max(incoming.values(),default=0)<=1 and max(outgoing.values(),default=0)<=2
 assert len(nodes)==record['nodes'] and len(edges)==record['edges']
 hashes.append({'dataset':name,'csv_sha256':sha(csv_path),'receipt_sha256':sha(receipt_path)})
assert not pathlib.Path(SCORE_CODE).exists() and not pathlib.Path(SCORE_RUN).exists()
print(json.dumps({'status':'PASS_EXP227_SOURCE20_SCORER_PREFLIGHT',
 'inference_status_sha256':sha(run/'output/status.json'),
 'inference_exit_sha256':sha(run/'exit.json'),'hashes':hashes}))
'''.replace("INFERENCE_MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PLAN_SHA", repr(prepared["stage"]["plan_sha256"])).replace(
        "CHECKPOINT_SHA", repr(prepared["preflight"]["checkpoint_sha256"])).replace(
        "SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "EXPECTED_MOVIES", repr(list(EXPECTED_MOVIES))).replace(
        "DATA_DIR", repr(REMOTE + "/data/exp213_source_view_20260912")).replace(
        "INFERENCE_CODE", repr(INFERENCE_CODE)).replace("INFERENCE_RUN", repr(INFERENCE_RUN)).replace(
        "SCORE_CODE", repr(CODE)).replace("SCORE_RUN", repr(RUN))
    gate = ssh("nsu-a100", "python3 -", preflight)
    assert gate["status"] == "PASS_EXP227_SOURCE20_SCORER_PREFLIGHT"
    assert [row["dataset"] for row in gate["hashes"]] == list(EXPECTED_MOVIES)

    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp227_source_graph20.py", "score_exp214_paired.py", "score_exp223_official.py")}
    files["exp223_config.json"] = (ROOT / "reports/exp223_official_score_config_v2_20260922.json").read_text()
    score_config = {"experiment": "EXP227_SOURCE_GRAPH20_OFFICIAL",
                    "inference_code": INFERENCE_CODE,
                    "inference_manifest_sha256": prepared["stage"]["manifest_sha256"],
                    "plan_sha256": prepared["stage"]["plan_sha256"],
                    "checkpoint_sha256": prepared["preflight"]["checkpoint_sha256"],
                    "inference_run": INFERENCE_RUN,
                    "inference_status_sha256": gate["inference_status_sha256"],
                    "inference_exit_sha256": gate["inference_exit_sha256"],
                    "inference_graph_hashes": gate["hashes"],
                    "evaluator_config": CODE + "/exp223_config.json",
                    "evaluator_config_sha256": sha_bytes(files["exp223_config.json"].encode()),
                    "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
                    "data_dir": REMOTE + "/data/exp213_source_view_20260912",
                    "output": RUN + "/output"}
    files["score_config.json"] = json.dumps(score_config, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir(parents=True)
files=FILES
for name,body in files.items():
 path=code/name;path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP227_SOURCE20_SCORER','code':str(code),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-quadro", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP227_SOURCE20_SCORER"
    assert staged["score_config_sha256"] == sha_bytes(files["score_config.json"].encode())
    receipt = {"status": "PREPARED_EXP227_SOURCE20_OFFICIAL_SCORER_NO_LABELS",
               "preflight": gate, "stage": staged, "config": score_config,
               "inference_prepare_sha256": sha(prepared_path),
               "source_labels_read": False, "target_labels_read": False}
    receipt_path = ROOT / "reports/exp227_source_graph20_scorer_prepare_20260927.json"
    assert not receipt_path.exists()
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "score_config_sha256": staged["score_config_sha256"]}))


if __name__ == "__main__":
    main()
