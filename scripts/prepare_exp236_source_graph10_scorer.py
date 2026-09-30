"""Stage the epoch-10 source scorer after all eleven no-label graphs release."""
import hashlib
import json
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
INFERENCE_CODE = REMOTE + "/code/exp236_source_graph10_v2_20260927"
INFERENCE_RUN = REMOTE + "/runs/exp236_source_graph10_v2_20260927"
CODE = REMOTE + "/code/exp236_source_graph10_scorer_v1_20260927"
RUN = REMOTE + "/runs/exp236_source_graph10_official_v1_20260927"
SOURCE_MANIFEST_SHA = "a5c3176ec25d4d75321e6c1fe17b62be2d9e25472ae7fcb677e48fe71478bd87"
SOURCE_BUNDLE_SHA = "90e95a45a4d58a72c18495b48c979de52afdc080b9070892c53e8bf41c2f59b1"
SOURCE_DUPLICATE_MAP_SHA = "d73389f47cc7cbf1c50a01a788827119aa324eebf2fb9222a66243b168ca7d62"
TRAIN_RUN = REMOTE + "/runs/exp236_horaz_source6bba_block04_v2_20260927"
EXPECTED_MOVIES = (
    "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1",
    "6bba_786893ac", "6bba_825bd1c6", "6bba_a5e926bb",
    "6bba_b329af44", "6bba_b693381b", "6bba_bb9f20c3",
    "6bba_f20478e9", "6bba_f4ae811c",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def main():
    prepared_path = ROOT / "reports/exp236_source_graph10_v2_prepare_20260927.json"
    prepared = json.loads(prepared_path.read_text())
    assert prepared["status"] == "PREPARED_EXP236_SOURCE_GRAPH10_V2_NO_LABELS"
    assert prepared["target_labels_read"] is False and prepared["source_labels_read"] is False
    assert prepared["target_data_opened"] is False
    assert prepared["movies"] == 11
    assert prepared["stage"]["status"] == "STAGED_EXP236_SOURCE_GRAPH10_V2"
    assert prepared["stage"]["code"] == INFERENCE_CODE
    assert prepared["stage"]["duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    config = json.loads((ROOT / "reports/exp236_source_graph10_v2_config_20260927.json").read_text())
    assert config["experiment"] == "EXP236"
    assert config["code"] == INFERENCE_CODE and config["run"] == INFERENCE_RUN
    assert config["lease_id"] == "exp236-source-graph10-v2-20260927"
    assert config["script"] == "run_exp236_source_graph10_v2.py"
    assert config["arguments"] == [INFERENCE_CODE + "/plan.json", "--plan-sha256",
                                   prepared["stage"]["plan_sha256"]]
    assert sha(ROOT / "reports/exp236_source_graph10_v2_plan_20260927.json") == prepared["stage"]["plan_sha256"]
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
assert plan['experiment']=='EXP236_SOURCE_GRAPH10' and plan['checkpoint_epoch']==10
assert plan['source_embryo']=='6bba' and plan['target_embryo']=='44b6' and plan['fold']==0
assert plan['source_manifest_sha256']==SOURCE_MANIFEST_SHA
assert plan['source_bundle_sha256']==SOURCE_BUNDLE_SHA
assert sha(code/'source6bba_manifest.json')==SOURCE_MANIFEST_SHA
assert plan['source_duplicate_map_sha256']==SOURCE_DUPLICATE_MAP_SHA
assert sha(code/'horaz/src/src/exp236_source_duplicate_pairs.json')==SOURCE_DUPLICATE_MAP_SHA
assert plan['source_duplicate_policy']=='exclude_all_effective_duplicate_windows_v2'
assert plan['excluded_pairs_by_split']=={'train':824,'inner_validation':103}
assert plan['removed_sampled_windows_by_split']=={'train':809,'inner_validation':101}
assert plan['training_run']==TRAIN_RUN
training_result_path=pathlib.Path(TRAIN_RUN)/'output/result.json'
assert sha(training_result_path)==plan['training_result_sha256']
training_result=json.loads(training_result_path.read_text())
assert training_result['status']=='PASS_EXP236_SOURCE_BLOCK_10_OF_50'
assert training_result['completed_epochs']==10 and training_result['target_data_opened'] is False
assert training_result['source_duplicate_map_sha256']==SOURCE_DUPLICATE_MAP_SHA
assert sha(pathlib.Path(TRAIN_RUN)/'output/fold0/history.json')==plan['training_history_sha256']
source=json.loads((code/'source6bba_manifest.json').read_text())
assert [row['dataset_id'] for row in source['inner_validation']]==names
assert len(source['train'])==115 and not set(names)&{row['dataset_id'] for row in source['train']}
assert [row['dataset'] for row in plan['movies']]==names
assert pathlib.Path(plan['code']).resolve()==code.resolve()
assert pathlib.Path(plan['checkpoint']).name=='last.pt'
assert pathlib.Path(plan['checkpoint']).resolve()==(pathlib.Path(TRAIN_RUN)/'output/fold0/last.pt').resolve()
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
assert status['status']=='PASS_EXP236_SOURCE_GRAPH10_NO_LABELS'
assert status['target_labels_read'] is False and status['source_labels_read'] is False
assert status['target_data_opened'] is False
assert status['source_embryo']=='6bba'
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
print(json.dumps({'status':'PASS_EXP236_SOURCE10_SCORER_PREFLIGHT',
 'inference_status_sha256':sha(run/'output/status.json'),
 'inference_exit_sha256':sha(run/'exit.json'),'hashes':hashes}))
'''.replace("INFERENCE_MANIFEST_SHA", repr(prepared["stage"]["manifest_sha256"])).replace(
        "PLAN_SHA", repr(prepared["stage"]["plan_sha256"])).replace(
        "CHECKPOINT_SHA", repr(prepared["preflight"]["checkpoint_sha256"])).replace(
        "SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "SOURCE_BUNDLE_SHA", repr(SOURCE_BUNDLE_SHA)).replace(
        "SOURCE_DUPLICATE_MAP_SHA", repr(SOURCE_DUPLICATE_MAP_SHA)).replace(
        "TRAIN_RUN", repr(TRAIN_RUN)).replace(
        "EXPECTED_MOVIES", repr(list(EXPECTED_MOVIES))).replace(
        "DATA_DIR", repr(REMOTE + "/data/exp213_source_view_20260912")).replace(
        "INFERENCE_CODE", repr(INFERENCE_CODE)).replace("INFERENCE_RUN", repr(INFERENCE_RUN)).replace(
        "SCORE_CODE", repr(CODE)).replace("SCORE_RUN", repr(RUN))
    gate = ssh("nsu-a100", "python3 -", preflight)
    assert gate["status"] == "PASS_EXP236_SOURCE10_SCORER_PREFLIGHT"
    assert [row["dataset"] for row in gate["hashes"]] == list(EXPECTED_MOVIES)

    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp236_source_graph10.py", "score_exp214_paired.py", "score_exp223_official.py")}
    files["exp223_config.json"] = (ROOT / "reports/exp223_official_score_config_v2_20260922.json").read_text()
    score_config = {"experiment": "EXP236_SOURCE_GRAPH10_OFFICIAL",
                    "inference_code": INFERENCE_CODE,
                    "inference_manifest_sha256": prepared["stage"]["manifest_sha256"],
                    "plan_sha256": prepared["stage"]["plan_sha256"],
                    "checkpoint_sha256": prepared["preflight"]["checkpoint_sha256"],
                    "source_manifest_sha256": SOURCE_MANIFEST_SHA,
                    "source_bundle_sha256": SOURCE_BUNDLE_SHA,
                    "source_duplicate_map_sha256": SOURCE_DUPLICATE_MAP_SHA,
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
print(json.dumps({'status':'STAGED_EXP236_SOURCE10_SCORER','code':str(code),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'score_config_sha256':sha(code/'score_config.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-quadro", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP236_SOURCE10_SCORER"
    assert staged["score_config_sha256"] == sha_bytes(files["score_config.json"].encode())
    receipt = {"status": "PREPARED_EXP236_SOURCE10_OFFICIAL_SCORER_NO_LABELS",
               "preflight": gate, "stage": staged, "config": score_config,
               "inference_prepare_sha256": sha(prepared_path),
               "source_labels_read": False, "target_labels_read": False,
               "target_data_opened": False}
    receipt_path = ROOT / "reports/exp236_source_graph10_scorer_prepare_20260927.json"
    assert not receipt_path.exists()
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "score_config_sha256": staged["score_config_sha256"]}))


if __name__ == "__main__":
    main()
