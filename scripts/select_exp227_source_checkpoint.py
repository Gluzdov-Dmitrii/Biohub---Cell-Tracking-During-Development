"""Select EXP227 epoch10/20 using only sealed official source8 evidence.

This is a read-only remote audit until its final, one-shot local receipt write.
It does not stage inference, claim a GPU, or open target data.
"""
import hashlib
import json
import math
from pathlib import Path
import shlex

from monitor_exp213_job import QUEUE, ssh


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "reports/EXP227_SOURCE44_TARGET6BBA_PREREG_20260927.md"
RECEIPT = ROOT / "reports/exp227_source_checkpoint_selection_20260927.json"
SOURCE8 = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
)
EPOCH10_SCORE = 0.8114014924249717


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def choose(score10, score20):
    assert all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)
               for v in (score10, score20))
    assert score10 == EPOCH10_SCORE
    return 20 if score20 > score10 else 10


def local_evidence(epoch):
    assert epoch in (10, 20)
    tag = f"exp227_source_graph{epoch}"
    graph_prepare_path = ROOT / f"reports/{tag}_prepare_20260927.json"
    graph_plan_path = ROOT / f"reports/{tag}_plan_20260927.json"
    graph_config_path = ROOT / f"reports/{tag}_config_20260927.json"
    score_prepare_path = ROOT / f"reports/{tag}_scorer_prepare_20260927.json"
    score_launch_path = ROOT / f"reports/{tag}_scorer_launch_20260927.json"
    score_receipt_path = ROOT / f"reports/{tag}_score_20260927.json"
    gp, plan, gc, sp, sl, sr = (read(path) for path in (
        graph_prepare_path, graph_plan_path, graph_config_path,
        score_prepare_path, score_launch_path, score_receipt_path))
    assert gp["status"] == f"PREPARED_EXP227_SOURCE_GRAPH{epoch}_NO_LABELS"
    assert gp["target_labels_read"] is False
    assert sp["status"] == f"PREPARED_EXP227_SOURCE{epoch}_OFFICIAL_SCORER_NO_LABELS"
    assert sp["target_labels_read"] is False
    assert sl["status"] == f"EXP227_SOURCE{epoch}_OFFICIAL_SCORER_LAUNCHED"
    assert sr["status"] == f"VERIFIED_EXP227_SOURCE{epoch}_OFFICIAL"
    assert sr["target_labels_read"] is False and sr["rows"] == 8
    assert math.isfinite(sr["source_score"])
    if epoch == 10:
        assert sr["source_score"] == EPOCH10_SCORE
    assert sr["prepare_receipt_sha256"] == sha(score_prepare_path)
    assert sr["launch_receipt_sha256"] == sha(score_launch_path)
    assert sp["inference_prepare_sha256"] == sha(graph_prepare_path)
    # Local Windows text has CRLF; the immutable remote plan was staged with LF.
    assert hashlib.sha256(graph_plan_path.read_text().encode()).hexdigest() == gp["stage"]["plan_sha256"]
    assert plan["experiment"] == f"EXP227_SOURCE_GRAPH{epoch}"
    assert plan["checkpoint_epoch"] == epoch
    assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
    assert [row["dataset"] for row in plan["movies"]] == list(SOURCE8)
    assert gc["code"] == gp["stage"]["code"] == plan["code"]
    assert gc["run"] + "/output" == plan["output"]
    assert gc["arguments"] == [gc["code"] + "/plan.json", "--plan-sha256",
                               gp["stage"]["plan_sha256"]]
    sc = sp["config"]
    assert sc["experiment"] == f"EXP227_SOURCE_GRAPH{epoch}_OFFICIAL"
    assert sc["inference_code"] == gc["code"]
    assert sc["inference_run"] == gc["run"]
    assert sc["inference_manifest_sha256"] == gp["stage"]["manifest_sha256"]
    assert sc["plan_sha256"] == gp["stage"]["plan_sha256"]
    assert sc["checkpoint_sha256"] == gp["preflight"]["checkpoint_sha256"]
    assert sc["checkpoint_sha256"] == plan["checkpoint_sha256"] == sr["checkpoint_sha256"]
    assert sl["score_config_sha256"] == sp["stage"]["score_config_sha256"]
    assert sl["run"] + "/output" == sc["output"]
    return {
        "epoch": epoch, "source_score": sr["source_score"],
        "checkpoint": plan["checkpoint"], "checkpoint_sha256": sr["checkpoint_sha256"],
        "graph_code": gc["code"], "graph_run": gc["run"], "graph_lease_id": gc["lease_id"],
        "graph_manifest_sha256": gp["stage"]["manifest_sha256"],
        "graph_plan_sha256": gp["stage"]["plan_sha256"],
        "graph_status_sha256": sc["inference_status_sha256"],
        "graph_exit_sha256": sc["inference_exit_sha256"],
        "score_code": sp["stage"]["code"], "score_run": sl["run"],
        "score_manifest_sha256": sp["stage"]["manifest_sha256"],
        "score_config_sha256": sp["stage"]["score_config_sha256"],
        "score_result_sha256": sr["result_sha256"], "score_gate_sha256": sr["gate_sha256"],
        "evaluator_config_sha256": sc["evaluator_config_sha256"],
        "local_hashes": {str(path.relative_to(ROOT)).replace("\\", "/"): sha(path) for path in (
            graph_prepare_path, graph_plan_path, graph_config_path,
            score_prepare_path, score_launch_path, score_receipt_path)},
    }


REMOTE_PROBE = r'''import csv,hashlib,json,math,pathlib
items=ITEMS
names=NAMES
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
out=[]
for e in items:
 epoch=e['epoch'];code=pathlib.Path(e['graph_code']);run=pathlib.Path(e['graph_run'])
 scode=pathlib.Path(e['score_code']);srun=pathlib.Path(e['score_run'])
 assert sha(code/'code_manifest.json')==e['graph_manifest_sha256']
 for name,digest in json.loads((code/'code_manifest.json').read_text()).items():
  p=(code/name).resolve();assert p.is_relative_to(code.resolve()) and sha(p)==digest,name
 assert sha(code/'plan.json')==e['graph_plan_sha256']
 plan=json.loads((code/'plan.json').read_text())
 assert plan['experiment']=='EXP227_SOURCE_GRAPH'+str(epoch)
 assert plan['checkpoint_epoch']==epoch and plan['source_embryo']=='44b6' and plan['target_embryo']=='6bba'
 assert [row['dataset'] for row in plan['movies']]==names
 assert all(row['zarr'].endswith('/'+row['dataset']+'.zarr') and row['dataset'].startswith('44b6_') for row in plan['movies'])
 assert pathlib.Path(plan['checkpoint'])==pathlib.Path(e['checkpoint'])
 assert plan['checkpoint_sha256']==e['checkpoint_sha256']==sha(plan['checkpoint'])
 assert pathlib.Path(plan['output'])==run/'output'
 ex=json.loads((run/'exit.json').read_text());sup=json.loads((run/'supervision/complete.json').read_text())
 ctl=json.loads((run/'supervision/control.json').read_text())
 assert sha(run/'exit.json')==e['graph_exit_sha256']
 assert ex['returncode']==0 and ex['hard_timeout'] is False
 assert sup['status']=='RELEASED_AFTER_VERIFIED_EXIT' and sup['exit']==ex
 assert ctl['action']=='release' and ctl['queue']['state']=='RELEASED'
 assert pathlib.Path(ctl['queue']['run_path'])==run
 assert sha(run/'output/status.json')==e['graph_status_sha256']
 status=json.loads((run/'output/status.json').read_text())
 assert status['status']=='PASS_EXP227_SOURCE_GRAPH'+str(epoch)+'_NO_LABELS'
 assert status['target_labels_read'] is False and status['checkpoint_sha256']==e['checkpoint_sha256']
 assert status['plan_sha256']==e['graph_plan_sha256'] and status['movies']==names
 assert len(status['records'])==8
 expected={'status.json'}|{'graph__'+name+suffix for name in names for suffix in ('.csv','.json')}
 assert {p.name for p in (run/'output').iterdir()}==expected
 hashes=[]
 for row,record in zip(plan['movies'],status['records']):
  name=row['dataset'];csvpath=run/'output'/('graph__'+name+'.csv');receipt=csvpath.with_suffix('.json')
  assert record['dataset']==name and record['shape']==row['shape']
  assert record['checkpoint_sha256']==e['checkpoint_sha256']
  assert record['plan_sha256']==e['graph_plan_sha256']
  assert pathlib.Path(record['csv'])==csvpath and sha(csvpath)==record['csv_sha256']
  assert json.loads(receipt.read_text())==record
  nodes={};edges=[];ids=set()
  with csvpath.open(newline='') as handle:
   reader=csv.DictReader(handle)
   assert reader.fieldnames==['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
   for item in reader:
    assert item['dataset']==name
    idx=int(item['id']);assert idx not in ids;ids.add(idx)
    if item['row_type']=='node':
     node=int(item['node_id']);assert node>=0 and node not in nodes
     point=tuple(float(item[k]) for k in ('t','z','y','x'))
     assert all(math.isfinite(v) and v.is_integer() and 0<=v<bound for v,bound in zip(point,row['shape']))
     nodes[node]=tuple(int(v) for v in point)
    else:
     assert item['row_type']=='edge';edges.append((int(item['source_id']),int(item['target_id'])))
  assert nodes and len(edges)==len(set(edges))
  incoming={};outgoing={}
  for parent,child in edges:
   assert parent in nodes and child in nodes and nodes[child][0]==nodes[parent][0]+1
   incoming[child]=incoming.get(child,0)+1;outgoing[parent]=outgoing.get(parent,0)+1
  assert max(incoming.values(),default=0)<=1 and max(outgoing.values(),default=0)<=2
  assert len(nodes)==record['nodes'] and len(edges)==record['edges']
  hashes.append({'dataset':name,'csv_sha256':sha(csvpath),'receipt_sha256':sha(receipt)})
 assert sha(scode/'code_manifest.json')==e['score_manifest_sha256']
 sman=json.loads((scode/'code_manifest.json').read_text())
 for name,digest in sman.items():
  p=(scode/name).resolve();assert p.is_relative_to(scode.resolve()) and sha(p)==digest,name
 assert sha(scode/'score_config.json')==e['score_config_sha256']
 config=json.loads((scode/'score_config.json').read_text())
 assert config['experiment']=='EXP227_SOURCE_GRAPH'+str(epoch)+'_OFFICIAL'
 assert config['plan_sha256']==e['graph_plan_sha256']
 assert config['checkpoint_sha256']==e['checkpoint_sha256']
 assert config['inference_manifest_sha256']==e['graph_manifest_sha256']
 assert config['inference_status_sha256']==e['graph_status_sha256']
 assert config['inference_exit_sha256']==e['graph_exit_sha256']
 assert config['evaluator_config_sha256']==e['evaluator_config_sha256']
 assert sha(config['evaluator_config'])==e['evaluator_config_sha256']
 assert pathlib.Path(config['output'])==srun/'output'
 sex=json.loads((srun/'exit.json').read_text())
 assert sex['returncode']==0 and sex['timeout'] is False
 gatepath=srun/'output/no_metric_gate.json';resultpath=srun/'output/result.json'
 assert sha(gatepath)==e['score_gate_sha256'] and sha(resultpath)==e['score_result_sha256']
 gate=json.loads(gatepath.read_text());result=json.loads(resultpath.read_text())
 assert gate['status']=='PASS_EXP227_SOURCE_GRAPH'+str(epoch)+'_BEFORE_LABEL_ACCESS'
 assert gate['hashes']==hashes and gate['plan_sha256']==e['graph_plan_sha256']
 assert gate['checkpoint_sha256']==e['checkpoint_sha256']
 assert result['status']=='PASS_EXP227_SOURCE_GRAPH'+str(epoch)+'_OFFICIAL'
 assert result['no_metric_gate_sha256']==e['score_gate_sha256']
 assert result['checkpoint_sha256']==e['checkpoint_sha256']
 assert [row['dataset'] for row in result['rows']]==names
 assert math.isfinite(result['summary']['score']) and result['summary']['score']==e['source_score']
 out.append({'epoch':epoch,'source_score':e['source_score'],'checkpoint':e['checkpoint'],
             'checkpoint_sha256':e['checkpoint_sha256'],'graph_hashes':hashes,
             'official_helper_sha256':sha(scode/'score_exp223_official.py'),
             'evaluator_config_sha256':e['evaluator_config_sha256']})
print(json.dumps({'status':'PASS_EXP227_SOURCE10_20_SELECTION_AUDIT','epochs':out}))
'''


def main():
    assert not RECEIPT.exists(), "Selection already sealed; reconcile rather than overwrite"
    assert PREREG.exists()
    evidence = [local_evidence(epoch) for epoch in (10, 20)]
    assert evidence[0]["evaluator_config_sha256"] == evidence[1]["evaluator_config_sha256"]
    assert evidence[0]["checkpoint_sha256"] != evidence[1]["checkpoint_sha256"]
    state = ssh("nsu-quadro", shlex.join(["python3", QUEUE, "status"]))
    for item in evidence:
        matches = [row for row in state["requests"] if row["id"] == item["graph_lease_id"]]
        assert len(matches) == 1 and matches[0]["state"] == "RELEASED"
        assert matches[0]["run_path"] == item["graph_run"]
    source = REMOTE_PROBE.replace("ITEMS", repr(evidence)).replace("NAMES", repr(list(SOURCE8)))
    remote = ssh("nsu-a100", "python3 -", source)
    assert remote["status"] == "PASS_EXP227_SOURCE10_20_SELECTION_AUDIT"
    assert [row["epoch"] for row in remote["epochs"]] == [10, 20]
    assert [row["source_score"] for row in remote["epochs"]] == [row["source_score"] for row in evidence]
    assert len({row["official_helper_sha256"] for row in remote["epochs"]}) == 1
    selected_epoch = choose(evidence[0]["source_score"], evidence[1]["source_score"])
    selected = evidence[0 if selected_epoch == 10 else 1]
    receipt = {"status": "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT", "selected_epoch": selected_epoch,
               "rule": "epoch20 only if official source8 score strictly greater than epoch10; tie epoch10",
               "source8": list(SOURCE8), "scores": {str(row["epoch"]): row["source_score"] for row in evidence},
               "checkpoint": selected["checkpoint"], "checkpoint_sha256": selected["checkpoint_sha256"],
               "prereg_sha256": sha(PREREG), "epochs": evidence, "remote_audit": remote,
               "target_labels_read": False, "evidence_class": "source-inner training monitor",
               "future_target_evidence_class": "leakage-controlled reciprocal evaluation; broader research previously inspected target labels"}
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "selected_epoch": selected_epoch,
                      "source_scores": receipt["scores"], "checkpoint_sha256": selected["checkpoint_sha256"]}))


if __name__ == "__main__":
    main()
