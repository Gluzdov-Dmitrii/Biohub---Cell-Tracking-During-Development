"""Independent read-only completion check for the EXP238 source19 CPU audit.

Default is a local plan. --execute requires sealed stage/launch receipts and a
finished remote CPU run; it never starts a process or mutates remote data.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh
from stage_exp238_source_peak_cpu_audit import (
    BUNDLE, CODE, MANIFEST, RECEIPT as STAGE_RECEIPT, ROOT, RUN,
    exclusive_json, local_gate, sha,
)
from launch_exp238_source_peak_cpu_audit import (
    PYTHON, RECEIPT as LAUNCH_RECEIPT, command,
)

if not __debug__:
    raise RuntimeError("EXP238 verification requires assertions; PYTHONOPTIMIZE must be 0")

OUT = ROOT / "reports/exp238_source_peak_cpu_audit_verified_20260927.json"
BASELINE_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
BASELINE_MANIFEST_SHA = "3216b95fe675de7b19d0cdb8c592dafa4c84174e26cc9b2b15b5ae3a10a3deec"
EXPECTED_ENDPOINT = {"EXP227": 153, "EXP236": 514}


def recount(rows: list[dict]) -> tuple[list[dict], str]:
    """Recompute every published 40% rate from per-movie integer counts."""
    assert len(rows) == 19
    summaries = []
    for experiment, count in (("EXP227", 8), ("EXP236", 11)):
        group = [row for row in rows if row["experiment"] == experiment]
        assert len(group) == count and len({row["dataset"] for row in group}) == count
        edge_d = sum(row["endpoint_fn_edges"] for row in group)
        edge_n = sum(row["recoverable_endpoint_fn_edges"] for row in group)
        node_d = sum(row["distinct_missed_endpoint_nodes"] for row in group)
        node_n = sum(row["qualified_distinct_missed_nodes"] for row in group)
        assert edge_d == EXPECTED_ENDPOINT[experiment] and node_d > 0
        assert all(0 <= row["recoverable_endpoint_fn_edges"] <= row["endpoint_fn_edges"]
                   and 0 <= row["qualified_distinct_missed_nodes"] <=
                   row["distinct_missed_endpoint_nodes"] and
                   0 <= row["offgraph_peak_count"] <= row["peak_count"] for row in group)
        assert 0 <= edge_n <= edge_d and 0 <= node_n <= node_d
        summaries.append({"experiment": experiment, "movies": count,
                          "endpoint_fn_edges": edge_d,
                          "recoverable_endpoint_fn_edges": edge_n,
                          "edge_recoverability": edge_n / edge_d,
                          "distinct_missed_endpoint_nodes": node_d,
                          "qualified_distinct_missed_nodes": node_n,
                          "node_recoverability": node_n / node_d,
                          "edge_gate_40pct": 5 * edge_n >= 2 * edge_d,
                          "node_gate_40pct": 5 * node_n >= 2 * node_d})
    passed = all(row["edge_gate_40pct"] and row["node_gate_40pct"] for row in summaries)
    return summaries, ("SUPPORT_TRACK_SEEDED_REDETECTION" if passed
                       else "REJECT_TRACK_SEEDED_REDETECTION")


def remote_source(manifest_sha: str, launch: dict) -> str:
    """Code runs on prepost with GEFF locked until process and result checks pass."""
    source = r'''import hashlib,json,math,os,pathlib,sys
if not __debug__:raise RuntimeError('EXP238 verifier requires assertions')
root=pathlib.Path(@@ROOT@@);code=pathlib.Path(@@CODE@@);run=pathlib.Path(@@RUN@@)
data=root/'data/exp213_source_view_20260912'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert os.uname().nodename=='prepost'
assert os.environ.get('PYTHONOPTIMIZE')=='0'
assert code.is_dir() and run.is_dir()
assert sha(code/'manifest.json')==@@MANIFEST@@
manifest=json.loads((code/'manifest.json').read_text())
assert manifest['status']=='SEALED_EXP238_SOURCE_PEAK_CPU_AUDIT_LOCAL_ONLY'
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed=={**manifest['files'],'manifest.json':@@MANIFEST@@}
assert sha(code/'baseline/manifest.json')==@@BASELINE_MANIFEST@@
config=json.loads((code/'config.json').read_text())
baseline_config=json.loads((code/'baseline/config.json').read_text())
ids=[name for cohort in baseline_config['cohorts'] for name in cohort['ids']]
assert len(ids)==len(set(ids))==19
assert ids==[name for cohort in config['cohorts'] for name in cohort['ids']]
assert config['output']==str(run/'output') and config['floor']==0.075
assert config['radius_um']==7.0 and config['minimum_recoverability']==0.4
allowed={(data/(name+'.geff')).resolve() for name in ids}
state={'geff_open':False}
def deny(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if not isinstance(raw,(str,bytes,os.PathLike)):return
 path=pathlib.Path(os.fsdecode(raw)).resolve()
 if any(part.lower().endswith('.geff') for part in path.parts):
  if not state['geff_open'] or not any(path.is_relative_to(root) for root in allowed):
   raise PermissionError('Verifier GEFF outside source19 or before process/result gate')
 if path.is_relative_to(data):
  names=[part.removesuffix('.zarr') for part in path.parts if part.endswith('.zarr')]
  if any(name not in ids for name in names):
   raise PermissionError('Verifier image outside source19')
sys.addaudithook(deny)
remote_launch=json.loads((run/'launch.json').read_text())
assert remote_launch==@@LAUNCH@@
assert remote_launch['status']=='LAUNCHED_EXP238_SOURCE_PEAK_CPU_AUDIT'
assert remote_launch['manifest_sha256']==@@MANIFEST@@
assert remote_launch['code']==str(code) and remote_launch['run']==str(run)
assert remote_launch['command']==@@COMMAND@@
assert remote_launch['pythonoptimize']=='0'
assert remote_launch['cuda_visible_devices']=='' and remote_launch['gpu_used'] is False
assert remote_launch['source_labels_only'] is True and remote_launch['kaggle_post'] is False
assert sha(run/'cpu_wrapper.py')==remote_launch['wrapper_sha256']
wrapper=(run/'cpu_wrapper.py').read_text()
assert "PYTHONOPTIMIZE='0'" in wrapper and "if not __debug__" in wrapper
exit_record=json.loads((run/'exit.json').read_text())
assert exit_record['returncode']==0 and exit_record['timeout'] is False
assert exit_record['error'] is None and exit_record['pythonoptimize']=='0'
assert exit_record['source_labels_only'] is True and exit_record['gpu_used'] is False
assert exit_record['kaggle_post'] is False
child=json.loads((run/'child.json').read_text())
assert child['command']==@@COMMAND@@ and child['pythonoptimize']=='0'
assert child['cuda_visible_devices']=='' and child['ram_bytes']==16*1024**3
assert child['cpu_affinity']==[24,25,26,27]
assert exit_record['pid']==child['pid'] and exit_record['start']==child['start']
def process_state(pid):
 try:fields=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()
 except FileNotFoundError:return None
 return fields[0],fields[19]
wrapper_process=process_state(remote_launch['wrapper_pid'])
assert wrapper_process is None or wrapper_process[0]=='Z'
child_process=process_state(child['pid'])
assert child_process is None or child_process[0]=='Z' or child_process[1]!=child['start']
output=run/'output'
assert {p.name for p in output.iterdir()}=={'no_label_gate.json','result.json'}
gate_path=output/'no_label_gate.json';result_path=output/'result.json'
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
assert gate['status']=='PASS_EXP238_ALL19_CACHE_AND_GRAPH_GATE_BEFORE_SOURCE_LABELS'
assert gate['bundle_sha256']==@@MANIFEST@@ and gate['ids']==ids
assert gate['source_labels_read'] is False and gate['target_data_opened'] is False
assert gate['graph_replay']=='EXACT_OLD_CSV_SHA256' and gate['peak_floor']==0.075
assert gate['baseline_manifest_sha256']==@@BASELINE_MANIFEST@@
assert gate['baseline_result_sha256']==@@BASELINE_RESULT@@
assert gate['runtime']['profile']=='remote_py311'
assert gate['runtime']['tracksdata_commit']=='e13cf379b5127deeb8301ce56410fda35b5a3cf9'
assert gate['synthetic_contract']['status']=='PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT'
assert gate['source44_guarded_recheck_sha256']==config['cohorts'][0]['guarded_recheck_receipt_sha256']
assert gate['cache_status_sha256']=={c['cache_cohort']:c['status_sha256'] for c in config['cohorts']}
assert gate['independent_receipt_sha256']=={c['cache_cohort']:c['independent_receipt_sha256'] for c in config['cohorts']}
assert result['status']=='PASS_EXP238_SOURCE_PEAK_RECOVERABILITY_AUDIT'
assert result['no_label_gate_sha256']==sha(gate_path)
assert gate_path.stat().st_mtime_ns<=result_path.stat().st_mtime_ns
assert result['evidence_class']=='source-inner training-monitor diagnostic; not reciprocal target OOF'
assert result['reciprocal_target_score'] is None
assert result['target_data_opened'] is False and result['gpu_used'] is False
assert result['kaggle_post'] is False
assert result['matching_caveat'].startswith('Nearby peaks may lose official one-to-one')
rows=result['rows'];assert len(rows)==19 and [r['dataset'] for r in rows]==ids
assert [r['experiment'] for r in rows]==['EXP227']*8+['EXP236']*11
baseline_path=root/'runs/source_inner_error_decomposition_v2_20260927/output/result.json'
assert sha(baseline_path)==@@BASELINE_RESULT@@
prior=json.loads(baseline_path.read_text())
prior_rows={r['dataset']:r for c in prior['cohorts'] for r in c['rows']}
prior_labels={r['dataset']:r for c in prior['cohorts'] for r in c['label_hashes']}
prior_graphs={r['dataset']:r for c in baseline_config['cohorts'] for r in c['graph_hashes']}
for row in rows:
 name=row['dataset'];old=prior_rows[name]
 assert row['graph_csv_sha256']==prior_graphs[name]['csv_sha256']
 assert row['official_edge_tp_replayed']==old['official']['edge_tp']
 assert row['official_edge_fn_replayed']==old['official']['edge_fn']
 assert row['endpoint_fn_edges']==old['edges']['fn_unmatched_endpoint']
 assert row['label_tree_sha256']==prior_labels[name]['tree_sha256']
 assert row['label_files']==prior_labels[name]['files']
def recount(rows):
 out=[]
 for experiment,count,expected in [('EXP227',8,153),('EXP236',11,514)]:
  group=[r for r in rows if r['experiment']==experiment]
  assert len(group)==count and len({r['dataset'] for r in group})==count
  ed=sum(r['endpoint_fn_edges'] for r in group)
  en=sum(r['recoverable_endpoint_fn_edges'] for r in group)
  nd=sum(r['distinct_missed_endpoint_nodes'] for r in group)
  nn=sum(r['qualified_distinct_missed_nodes'] for r in group)
  assert ed==expected and nd>0
  assert all(0<=r['recoverable_endpoint_fn_edges']<=r['endpoint_fn_edges'] and
   0<=r['qualified_distinct_missed_nodes']<=r['distinct_missed_endpoint_nodes'] and
   0<=r['offgraph_peak_count']<=r['peak_count'] for r in group)
  out.append({'experiment':experiment,'movies':count,'endpoint_fn_edges':ed,
   'recoverable_endpoint_fn_edges':en,'edge_recoverability':en/ed,
   'distinct_missed_endpoint_nodes':nd,'qualified_distinct_missed_nodes':nn,
   'node_recoverability':nn/nd,'edge_gate_40pct':5*en>=2*ed,
   'node_gate_40pct':5*nn>=2*nd})
 return out
summary=recount(rows)
assert result['cohorts']==summary
decision='SUPPORT_TRACK_SEEDED_REDETECTION' if all(c['edge_gate_40pct'] and c['node_gate_40pct'] for c in summary) else 'REJECT_TRACK_SEEDED_REDETECTION'
assert result['preregistered_decision']==decision
# Only now open the exact source19 GEFF trees, twice, using prior tree-hash rules.
state['geff_open']=True
def tree_sha(path):
 files=sorted((p for p in path.rglob('*') if p.is_file()),
  key=lambda p:p.relative_to(path).as_posix())
 digest=hashlib.sha256()
 for p in files:
  digest.update(p.relative_to(path).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return digest.hexdigest(),len(files)
label_rows=[]
for name in ids:
 path=data/(name+'.geff')
 before,count=tree_sha(path)
 assert before==prior_labels[name]['tree_sha256'] and count==prior_labels[name]['files']
 assert before==next(r for r in rows if r['dataset']==name)['label_tree_sha256']
 after,after_count=tree_sha(path)
 assert (after,after_count)==(before,count)
 label_rows.append({'dataset':name,'before_sha256':before,'after_sha256':after,'files':count})
assert len(label_rows)==19
print(json.dumps({'status':'PASS_EXP238_SOURCE_PEAK_CPU_INDEPENDENT_READBACK',
 'manifest_sha256':sha(code/'manifest.json'),'remote_launch_sha256':sha(run/'launch.json'),
 'remote_exit_sha256':sha(run/'exit.json'),'no_label_gate_sha256':sha(gate_path),
 'result_sha256':sha(result_path),'baseline_result_sha256':sha(baseline_path),
 'decision':decision,'cohorts':summary,'labels':label_rows,
 'child_absent':True,'source_labels_only':True,'target_labels_read':False,
 'gpu_used':False,'kaggle_post':False}))
'''
    for token, value in {
        "@@ROOT@@": CODE.rsplit("/code/", 1)[0], "@@CODE@@": CODE,
        "@@RUN@@": RUN, "@@MANIFEST@@": manifest_sha,
        "@@BASELINE_MANIFEST@@": BASELINE_MANIFEST_SHA,
        "@@BASELINE_RESULT@@": BASELINE_RESULT_SHA,
        "@@LAUNCH@@": launch, "@@COMMAND@@": command(manifest_sha),
    }.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "exp238_cpu_independent_remote_verifier", "exec")
    return source


def local_completion_gate() -> tuple[str, dict]:
    local_gate()
    stage = json.loads(STAGE_RECEIPT.read_text())
    launch = json.loads(LAUNCH_RECEIPT.read_text())
    manifest_sha = sha(MANIFEST)
    assert stage["status"] == "STAGED_EXP238_CPU_AUDIT_NO_LABELS"
    assert stage["manifest_sha256"] == manifest_sha
    assert launch["status"] == "LAUNCHED_EXP238_SOURCE_PEAK_CPU_AUDIT"
    assert launch["manifest_sha256"] == manifest_sha
    assert launch["stage_receipt_sha256"] == sha(STAGE_RECEIPT)
    assert launch["source_labels_only"] is True
    assert launch["gpu_used"] is False and launch["kaggle_post"] is False
    assert launch["remote"]["command"] == command(manifest_sha)
    assert launch["remote"]["pythonoptimize"] == "0"
    return manifest_sha, launch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"status": "EXP238_CPU_VERIFY_LOCAL_REVIEW_ONLY",
                          "stage_receipt_present": STAGE_RECEIPT.exists(),
                          "launch_receipt_present": LAUNCH_RECEIPT.exists(),
                          "remote_read": False, "source_labels_read": False}))
        return
    assert not OUT.exists(), "One-shot verification receipt already exists"
    manifest_sha, launch = local_completion_gate()
    checked = ssh("nsu-quadro", "env PYTHONOPTIMIZE=0 python3 -B -",
                  remote_source(manifest_sha, launch["remote"]))
    assert checked["status"] == "PASS_EXP238_SOURCE_PEAK_CPU_INDEPENDENT_READBACK"
    assert checked["manifest_sha256"] == manifest_sha
    assert checked["child_absent"] is True and checked["target_labels_read"] is False
    assert checked["gpu_used"] is False and checked["kaggle_post"] is False
    exclusive_json(OUT, {"status": "PASS_EXP238_SOURCE_PEAK_CPU_INDEPENDENT_VERIFICATION",
                         "source_manifest_sha256": manifest_sha,
                         "stage_receipt_sha256": sha(STAGE_RECEIPT),
                         "launch_receipt_sha256": sha(LAUNCH_RECEIPT),
                         "verifier_source_sha256": sha(Path(__file__)),
                         "remote": checked, "reciprocal_target_score": None,
                         "kaggle_post": False})
    print(json.dumps({"status": "PASS_EXP238_SOURCE_PEAK_CPU_INDEPENDENT_VERIFICATION",
                      "decision": checked["decision"], "receipt_sha256": sha(OUT)}))


if __name__ == "__main__":
    main()
