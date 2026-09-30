"""Independent read-only EXP241 scorer completion verifier; GEFF is forbidden."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp241_source_paired_scorer import (
    BUNDLE, CODE, CONFIG_SHA, GRAPH_RUN, MANIFEST_SHA, PYTHON,
    RECEIPT as STAGE_RECEIPT, ROOT, RUN, local_bundle, render, sha,
)
from launch_exp241_source_paired_scorer import (
    AFFINITY, CPU_SECONDS, RAM_BYTES, RECEIPT as LAUNCH_RECEIPT,
    WRAPPER_WALL_SECONDS, command,
)


if not __debug__:
    raise RuntimeError("EXP241 independent verifier requires assertions")

OUT = ROOT / "reports/exp241_source_paired_scorer_verified_20260927.json"
SOURCE_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
SOURCE_GATE_SHA = "735496f5cf6d2a24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e"
SOURCE_RESULT = ROOT / "runs/source_inner_error_decomposition_v2_20260927/output/result.json"


def close_value(actual, expected, label):
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys(), label
        for key in expected:
            close_value(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), label
        for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
            close_value(a, b, f"{label}[{index}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if not math.isfinite(float(expected)):
            assert actual is None or (isinstance(actual, (int, float)) and
                                      not math.isfinite(float(actual))), label
            return
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), label
        assert math.isfinite(float(actual)), label
        assert math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-12), label
    else:
        assert actual == expected, label


def fixed_gate(baseline, candidate):
    def delta(key):
        a, b = baseline["official"][key], candidate["official"][key]
        return b - a if isinstance(a, (int, float)) and isinstance(b, (int, float)) and all(
            math.isfinite(float(v)) for v in (a, b)) else None

    score = delta("score")
    edge = delta("adj_edge_jaccard")
    division = delta("division_jaccard")
    official_node = delta("node_recall")
    old_micro = baseline["nodes"]["recall_micro"]
    new_micro = candidate["nodes"]["recall_micro"]
    micro_node = new_micro - old_micro if old_micro is not None and new_micro is not None else None
    checks = {"score_gain_at_least_0p005": score is not None and score >= 0.005,
              "adjusted_edge_jaccard_nonregression": edge is not None and edge >= -1e-12,
              "division_jaccard_nonregression": division is not None and division >= -1e-12,
              "official_node_recall_nonregression": official_node is not None and official_node >= -1e-12,
              "micro_node_recall_nonregression": micro_node is not None and micro_node >= -1e-12}
    return {"delta": {"score": score, "adj_edge_jaccard": edge,
                       "division_jaccard": division, "official_node_recall": official_node,
                       "micro_node_recall": micro_node},
            "checks": checks, "pass": all(checks.values())}


def remote_source(stage_sha: str, launch_sha: str, launch_remote_sha: str) -> str:
    helpers = inspect.getsource(close_value) + "\n" + inspect.getsource(fixed_gate)
    source = r'''import hashlib,json,math,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP241 read-only verification requires assertions')
root=pathlib.Path(@@ROOT@@);code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
graph=pathlib.Path(@@GRAPH_RUN@@);source_result=root/'runs/source_inner_error_decomposition_v2_20260927/output/result.json'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP241 verifier denies all GEFF')
sys.addaudithook(deny)
assert os.uname().nodename=='prepost' and os.environ.get('PYTHONOPTIMIZE')=='0'
assert pathlib.Path(sys.executable).resolve()==pathlib.Path(@@PYTHON@@).resolve()
@@HELPERS@@
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
manifest=json.loads((code/'manifest.json').read_text())
assert manifest['status']=='SEALED_EXP241_SOURCE_PAIRED_SCORER_V1'
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed=={**manifest['files'],'manifest.json':@@MANIFEST_SHA@@}
assert sha(code/'config.json')==@@CONFIG_SHA@@
config=json.loads((code/'config.json').read_text())
assert config['status']=='SEALED_EXP241_SOURCE_PAIRED_SCORER_V1'
assert config['output']==str(run/'output') and config['graph_run']==str(graph)
assert config['source_inner_result_sha256']==@@SOURCE_RESULT_SHA@@
assert sha(code/'graph_verified.json')==config['graph_verified_receipt_sha256']
assert sha(graph/'output/result.json')==config['graph_result_sha256']
assert sha(graph/'output/no_label_gate.json')==config['graph_no_label_gate_sha256']
graph_result=json.loads((graph/'output/result.json').read_text())
assert graph_result['status']=='BUILT_EXP241_FIXED_SOURCE19_LABEL_FREE_GRAPHS'
assert graph_result['no_label_gate_sha256']==config['graph_no_label_gate_sha256']
assert not any(graph_result[k] for k in ('source_labels_read','target_data_opened',
 'metric_computed','gpu_used','kaggle_post'))
assert graph_result['selected_chains']=={'source44':835,'source6':358}
ids=graph_result['ordered_ids'];assert len(ids)==len(set(ids))==19
assert [r['dataset'] for r in graph_result['rows']]==ids
for row in graph_result['rows']:
 assert sha(graph/'output'/('graph__'+row['dataset']+'.csv'))==row['candidate_csv_sha256']
assert sha(source_result)==@@SOURCE_RESULT_SHA@@
prior=json.loads(source_result.read_text())
assert prior['status']=='PASS_SOURCE_INNER_19_CURRENT_ORGANIZER_DECOMPOSITION'
assert prior['no_label_gate_sha256']==@@SOURCE_GATE_SHA@@

launch=json.loads((run/'launch.json').read_text())
assert launch['status']=='LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU'
assert launch['code']==str(code) and launch['run']==str(run)
assert launch['manifest_sha256']==@@MANIFEST_SHA@@
assert launch['command']==@@COMMAND@@ and launch['cpu_affinity']==@@AFFINITY@@
assert launch['ram_bytes']==@@RAM@@ and launch['cpu_seconds']==@@CPU@@
assert launch['max_seconds']==@@WALL@@ and launch['cuda_visible_devices']==''
assert launch['pythonoptimize']=='0' and launch['gpu_used'] is False
assert sha(run/'launch.json')==@@LAUNCH_REMOTE_SHA@@
assert sha(run/'cpu_wrapper.py')==launch['wrapper_sha256']
exit=json.loads((run/'exit.json').read_text())
child=json.loads((run/'child.json').read_text())
assert exit['returncode']==0 and exit['timeout'] is False and exit['error'] is None
assert exit['source_labels_only'] and not any(exit[k] for k in
 ('target_data_opened','gpu_used','kaggle_post'))
assert child['pid']==exit['pid'] and child['start']==exit['start']
assert child['command']==@@COMMAND@@ and child['cpu_affinity']==@@AFFINITY@@
assert child['ram_bytes']==@@RAM@@ and child['cpu_seconds']==@@CPU@@
assert child['pythonoptimize']=='0' and child['cuda_visible_devices']==''
def proc(pid):
 try:fields=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()
 except FileNotFoundError:return None
 return fields[0],fields[19]
wrapper_proc=proc(launch['wrapper_pid']);assert wrapper_proc is None or wrapper_proc[0]=='Z'
child_proc=proc(child['pid'])
assert child_proc is None or child_proc[0]=='Z' or (
 child['start'] is not None and child_proc[1]!=child['start'])
output=run/'output'
assert {p.name for p in output.iterdir()}=={
 'no_label_gate.json','parent_replay_pass.json','result.json'}
gate_path=output/'no_label_gate.json';parent_path=output/'parent_replay_pass.json'
result_path=output/'result.json'
assert gate_path.stat().st_mtime_ns<=parent_path.stat().st_mtime_ns<=result_path.stat().st_mtime_ns
gate=json.loads(gate_path.read_text());parent=json.loads(parent_path.read_text())
result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP241_SOURCE19_GRAPH_AND_RUNTIME_BEFORE_GEFF'
assert gate['manifest_sha256']==@@MANIFEST_SHA@@
assert gate['graph_verified_receipt_sha256']==config['graph_verified_receipt_sha256']
assert gate['graph_result_sha256']==config['graph_result_sha256']
assert gate['graph_no_label_gate_sha256']==config['graph_no_label_gate_sha256']
assert gate['source_inner_result_sha256']==@@SOURCE_RESULT_SHA@@
assert gate['ids']==ids and gate['candidate_graph_rows']==graph_result['rows']
assert not any(gate[k] for k in ('source_labels_read','target_data_opened',
 'gpu_used','kaggle_post'))
assert parent['status']=='PASS_EXP241_PARENT_19_ROWS_AND_COHORTS_1E_MINUS_12'
assert parent['no_label_gate_sha256']==sha(gate_path)
assert parent['source_inner_result_sha256']==@@SOURCE_RESULT_SHA@@
assert result['status']=='PASS_EXP241_SOURCE19_PAIRED_SCORE_RECORDED'
assert result['no_label_gate_sha256']==sha(gate_path)
assert result['parent_replay_pass_sha256']==sha(parent_path)
assert result['source_inner_result_sha256']==@@SOURCE_RESULT_SHA@@
assert result['graph_verified_receipt_sha256']==config['graph_verified_receipt_sha256']
assert result['target_labels_read'] is False and result['target_data_opened'] is False
assert result['gpu_used'] is False and result['kaggle_post'] is False
assert result['source_label_tree_hashes_before_after_equal'] is True
before=result['source_label_tree_hashes_before'];after=result['source_label_tree_hashes_after']
assert before==after and [r['dataset'] for r in before]==ids
prior_hash={r['dataset']:r for c in prior['cohorts'] for r in c['label_hashes']}
assert len(prior_hash)==19
for row in before:
 name=row['dataset'];assert row['sha256']==prior_hash[name]['tree_sha256']
 assert row['files']==prior_hash[name]['files']
assert len(parent['cohorts'])==2
for replay,old in zip(parent['cohorts'],prior['cohorts'],strict=True):
 assert replay['experiment']==old['experiment']
 close_value(replay['summary'],old['current_organizer_summary'],'parent summary')
 assert replay['label_hashes']==old['label_hashes']

sys.path.insert(0,str(code))
from check_current_organizer_metric_runtime import load_metric,validate_runtime
runtime=validate_runtime('remote_py311');metric=load_metric(code)
rows=result['rows'];assert [row['dataset'] for row in rows]==ids
assert [row['cohort'] for row in rows]==['EXP227']*8+['EXP236']*11
old_rows=[r for c in prior['cohorts'] for r in c['rows']]
for current,old,graph_row in zip(rows,old_rows,graph_result['rows'],strict=True):
 close_value(current['baseline'],old['official'],current['dataset']+' parent row')
 assert current['label_tree_sha256']==prior_hash[current['dataset']]['tree_sha256']
 assert current['candidate']['num_pred_nodes']==current['baseline']['num_pred_nodes']+graph_row['added_nodes']
 for arm in ('baseline','candidate'):
  metric_row=current[arm]
  assert all(isinstance(metric_row[k],int) and metric_row[k]>=0 for k in
   ('edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn','num_pred_nodes'))
  denom=sum(metric_row[k] for k in ('edge_tp','edge_fp','edge_fn'))
  if denom:close_value(metric_row['edge_jaccard'],metric_row['edge_tp']/denom,'edge jaccard')
  nodes=current[arm+'_nodes']
  assert nodes['tp']+nodes['fn']==nodes['gt']
  assert nodes['tp']+nodes['fp_annotated']==nodes['pred_annotated']
  assert nodes['pred_annotated']<=nodes['pred_all_frames']==metric_row['num_pred_nodes']
  close_value(nodes['recall'],nodes['tp']/nodes['gt'],'node recall')
  close_value(metric_row['node_recall'],nodes['recall'],'official node recall')
 added=current['added_annotated_audit']
 assert added['nodes_all_frames']==graph_row['added_nodes']
 assert added['edges_all_frames']==graph_row['added_edges']
 assert added['nodes_annotated']==added['nodes_annotated_matched']+added['nodes_annotated_unmatched']
 for scope in ('both_annotated','any_annotated'):
  assert added['edges_'+scope]==sum(added['edges_'+scope+'_'+k] for k in
   ('matched','unmatched_valid','unmatched_ignored'))

for key,subset in (('EXP227',rows[:8]),('EXP236',rows[8:]),('pooled19',rows)):
 observed=result['summaries'][key]
 for arm in ('baseline','candidate'):
  block=observed[arm]
  official=metric.summarise([row[arm] for row in subset])
  close_value(block['official'],official,key+' '+arm+' official pool')
  counts={k:sum(row[arm][k] for row in subset) for k in
   ('edge_tp','edge_fp','edge_fn','division_tp','division_fp','division_fn')}
  assert block['counts']==counts
  keys=('tp','fp_annotated','fn','gt','pred_all_frames','pred_annotated')
  nodes={k:sum(row[arm+'_nodes'][k] for row in subset) for k in keys}
  nodes['recall_micro']=nodes['tp']/nodes['gt'] if nodes['gt'] else None
  close_value(block['nodes'],nodes,key+' '+arm+' node pool')
 if key!='pooled19':
  old=next(c for c in prior['cohorts'] if c['experiment']==key)
  close_value(observed['baseline']['official'],old['current_organizer_summary'],key+' parent pool')
 gate_recomputed=fixed_gate(observed['baseline'],observed['candidate'])
 close_value(observed['promotion'],gate_recomputed,key+' promotion')
 added={k:sum(row['added_annotated_audit'][k] for row in subset)
        for k in subset[0]['added_annotated_audit']}
 assert result['added_annotated_totals'][key]==added
overall=all(result['summaries'][k]['promotion']['pass'] for k in ('EXP227','EXP236','pooled19'))
assert result['promotion_gate_pass'] is overall
assert result['decision']==('PERMIT_SEPARATE_PREREGISTERED_RECIPROCAL_TEST' if overall else
 'STOP_FIXED_ADDITIVE_REPAIR_FAMILY_NO_RETUNE')
print(json.dumps({'status':'PASS_EXP241_SOURCE_PAIRED_INDEPENDENT_READBACK',
 'manifest_sha256':@@MANIFEST_SHA@@,'launch_sha256':sha(run/'launch.json'),
 'stage_receipt_sha256':@@STAGE_SHA@@,'launch_receipt_sha256':@@LAUNCH_SHA@@,
 'exit_sha256':sha(run/'exit.json'),'no_label_gate_sha256':sha(gate_path),
 'parent_replay_sha256':sha(parent_path),'result_sha256':sha(result_path),
 'movies':19,'scores':{key:{arm:result['summaries'][key][arm]['official']['score']
 for arm in ('baseline','candidate')} for key in ('EXP227','EXP236','pooled19')},
 'promotion_gate_pass':overall,'decision':result['decision'],
 'source_gt_hashes_equal':True,'child_absent':True,'source_geff_reopened':False,
 'target_labels_read':False,'gpu_used':False,'kaggle_post':False}))
'''
    source = source.replace("@@HELPERS@@", helpers)
    return render(source, {"@@ROOT@@": str(Path(CODE).parents[1]),
                           "@@CODE@@": CODE, "@@RUN@@": RUN,
                           "@@GRAPH_RUN@@": GRAPH_RUN, "@@PYTHON@@": PYTHON,
                           "@@MANIFEST_SHA@@": MANIFEST_SHA,
                           "@@CONFIG_SHA@@": CONFIG_SHA,
                           "@@SOURCE_RESULT_SHA@@": SOURCE_RESULT_SHA,
                           "@@SOURCE_GATE_SHA@@": SOURCE_GATE_SHA,
                           "@@STAGE_SHA@@": stage_sha,
                           "@@LAUNCH_SHA@@": launch_sha,
                           "@@LAUNCH_REMOTE_SHA@@": launch_remote_sha,
                           "@@COMMAND@@": command(), "@@AFFINITY@@": AFFINITY,
                           "@@RAM@@": RAM_BYTES, "@@CPU@@": CPU_SECONDS,
                           "@@WALL@@": WRAPPER_WALL_SECONDS})


def local_gate() -> tuple[dict, dict]:
    local_bundle()
    stage = json.loads(STAGE_RECEIPT.read_text())
    launch = json.loads(LAUNCH_RECEIPT.read_text())
    assert stage["status"] == "STAGED_EXP241_SOURCE_PAIRED_SCORER_NO_LABELS"
    assert stage["manifest_sha256"] == MANIFEST_SHA
    assert launch["status"] == "LAUNCHED_EXP241_SOURCE_PAIRED_SCORER_CPU"
    assert launch["manifest_sha256"] == MANIFEST_SHA
    assert launch["stage_receipt_sha256"] == sha(STAGE_RECEIPT)
    assert launch["remote"]["command"] == command()
    assert launch["remote"]["manifest_sha256"] == MANIFEST_SHA
    assert launch["launch_readback"]["launch_sha256"]
    assert launch["score_computed_at_launch"] is False
    return stage, launch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        local_bundle()
        remote_source("0" * 64, "0" * 64, "0" * 64)
        print(json.dumps({"status": "EXP241_SCORER_VERIFIER_LOCAL_REVIEW_ONLY",
                          "manifest_sha256": MANIFEST_SHA,
                          "stage_receipt_present": STAGE_RECEIPT.exists(),
                          "launch_receipt_present": LAUNCH_RECEIPT.exists(),
                          "remote_read": False, "source_geff_read": False}))
        return
    assert not OUT.exists(), "Reconcile existing EXP241 verification receipt first"
    stage, launch = local_gate()
    source = remote_source(sha(STAGE_RECEIPT), sha(LAUNCH_RECEIPT),
                           launch["launch_readback"]["launch_sha256"])
    checked = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 CUDA_VISIBLE_DEVICES= " +
                  PYTHON + " -B -", source)
    assert checked["status"] == "PASS_EXP241_SOURCE_PAIRED_INDEPENDENT_READBACK"
    assert checked["manifest_sha256"] == MANIFEST_SHA
    assert checked["launch_sha256"] == launch["launch_readback"]["launch_sha256"]
    assert checked["stage_receipt_sha256"] == sha(STAGE_RECEIPT)
    assert checked["launch_receipt_sha256"] == sha(LAUNCH_RECEIPT)
    assert checked["source_geff_reopened"] is False
    assert checked["child_absent"] and checked["target_labels_read"] is False
    receipt = {"status": "PASS_EXP241_SOURCE_PAIRED_INDEPENDENT_VERIFICATION",
               "manifest_sha256": MANIFEST_SHA,
               "stage_receipt_sha256": sha(STAGE_RECEIPT),
               "launch_receipt_sha256": sha(LAUNCH_RECEIPT),
               "verifier_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "remote": checked,
               "source_geff_reopened": False, "target_labels_read": False,
               "gpu_used": False, "kaggle_post": False}
    with OUT.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "receipt_sha256": sha(OUT),
                      "promotion_gate_pass": checked["promotion_gate_pass"],
                      "scores": checked["scores"]}))


if __name__ == "__main__":
    main()
