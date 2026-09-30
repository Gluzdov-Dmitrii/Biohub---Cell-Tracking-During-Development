"""Independently verify the completed source-only error decomposition."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from monitor_exp213_job import ssh


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STAGE = REPORTS / "source_inner_error_decomposition_v2_stage_20260927.json"
LAUNCH = REPORTS / "source_inner_error_decomposition_v2_launch_20260927.json"
OUT = REPORTS / "source_inner_error_decomposition_v2_verified_20260927.json"
MANIFEST_SHA = "3216b95fe675de7b19d0cdb8c592dafa4c84174e26cc9b2b15b5ae3a10a3deec"
CURRENT_METRIC_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
ORGANIZER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote_check() -> dict:
    source = r'''import hashlib,json,math,pathlib
root=pathlib.Path(@@ROOT@@)
code=root/'code/source_inner_error_decomposition_v2_20260927'
run=root/'runs/source_inner_error_decomposition_v2_20260927'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
manifest=json.loads((code/'manifest.json').read_text())
assert sha(code/'manifest.json')==@@MANIFEST_SHA@@
assert len(manifest['files'])==7
assert {name:sha(code/name) for name in manifest['files']}==manifest['files']
launch=json.loads((run/'launch.json').read_text())
exit=json.loads((run/'exit.json').read_text())
assert launch['status']=='LAUNCHED_SOURCE_INNER_AUDIT_CPU'
assert launch['source_manifest_sha256']==@@MANIFEST_SHA@@
assert launch['source_labels_only'] and not launch['gpu_used'] and not launch['kaggle_post']
assert exit['returncode']==0 and exit['timeout'] is False and exit['error'] is None
assert exit['source_labels_only'] and not exit['gpu_used'] and not exit['kaggle_post']
def process_state(pid):
 try:return pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()[0]
 except FileNotFoundError:return None
assert process_state(launch['wrapper_pid']) in (None,'Z')
child=pathlib.Path(f"/proc/{exit['pid']}/stat")
if child.exists():
 fields=child.read_text().split(') ')[1].split()
 assert fields[0]=='Z' or fields[19]!=exit['start']
gate_path=run/'output/no_label_gate.json'
result_path=run/'output/result.json'
gate=json.loads(gate_path.read_text()); result=json.loads(result_path.read_text())
assert gate['status']=='PASS_SOURCE_INNER_19_GRAPH_AND_CURRENT_METRIC_GATE_BEFORE_LABEL_ACCESS'
assert gate['bundle_sha256']==@@MANIFEST_SHA@@ and gate['reciprocal_target_labels_read'] is False
assert result['status']=='PASS_SOURCE_INNER_19_CURRENT_ORGANIZER_DECOMPOSITION'
assert result['no_label_gate_sha256']==sha(gate_path)
assert result['current_metric_source_sha256']['tracking_cellmot_official/metrics.py']==@@METRIC_SHA@@
assert result['organizer_commit']==@@COMMIT@@
assert result['reciprocal_target_labels_read'] is False
assert result['gpu_used'] is False and result['kaggle_post'] is False
assert [c['experiment'] for c in result['cohorts']]==['EXP227','EXP236']
summaries=[]
for cohort,n,old in zip(result['cohorts'],[8,11],[0.8114014924249717,0.8458659187983504]):
 rows=cohort['rows']; assert len(rows)==n and len(cohort['label_hashes'])==n
 assert len({r['dataset'] for r in rows})==n
 assert math.isclose(cohort['legacy_source_score_replayed'],old,abs_tol=1e-12,rel_tol=0)
 s=cohort['current_organizer_summary']; terms=cohort['score_terms']; pooled=cohort['pooled_edges']
 assert s['n']==n and math.isclose(s['score'],old,abs_tol=1e-12,rel_tol=0)
 assert math.isclose(terms['score'],terms['adjusted_edge_jaccard']+terms['weighted_division_term'],abs_tol=1e-12,rel_tol=0)
 assert math.isclose(terms['weighted_division_term'],0.1*terms['division_jaccard'],abs_tol=1e-12,rel_tol=0)
 assert {k:sum(r['edges'][k] for r in rows) for k in pooled}==pooled
 assert pooled['fn_unmatched_endpoint']==pooled['fn_both_unmatched']+pooled['fn_source_unmatched']+pooled['fn_target_unmatched']
 assert pooled['fn_unmatched_endpoint']+pooled['fn_both_matched_link_missing']==sum(r['official']['edge_fn'] for r in rows)
 assert cohort['source_only_detection_proposal_signal'] is False
 summaries.append({'experiment':cohort['experiment'],'movies':n,'score':s['score'],
                   'node_recall':s['node_recall'],'endpoint_fn':pooled['fn_unmatched_endpoint'],
                   'association_fn':pooled['fn_both_matched_link_missing'],
                   'all_frame_pred_nodes':cohort['pooled_nodes']['pred'],
                   'gt_nodes':cohort['pooled_nodes']['gt'],
                   'preregistered_detection_signal':False})
print(json.dumps({'status':'PASS_SOURCE_INNER_V2_INDEPENDENT_READBACK',
 'stage_manifest_sha256':sha(code/'manifest.json'),'launch_sha256':sha(run/'launch.json'),
 'exit_sha256':sha(run/'exit.json'),'gate_sha256':sha(gate_path),
 'result_sha256':sha(result_path),'summaries':summaries,
 'child_absent':True,'target_labels_read':False,'gpu_used':False,'kaggle_post':False}))
'''
    for token, value in {
        "@@ROOT@@": REMOTE,
        "@@MANIFEST_SHA@@": MANIFEST_SHA,
        "@@METRIC_SHA@@": CURRENT_METRIC_SHA,
        "@@COMMIT@@": ORGANIZER_COMMIT,
    }.items():
        source = source.replace(token, repr(value))
    assert "@@" not in source
    compile(source, "remote_source_inner_v2_verify", "exec")
    return ssh("nsu-quadro", "python3 -", source)


def main() -> None:
    assert not OUT.exists(), "Completed verification already exists"
    stage = json.loads(STAGE.read_text())
    launch = json.loads(LAUNCH.read_text())
    assert stage["status"] == "STAGED_SOURCE_INNER_AUDIT_NO_LABELS"
    assert stage["manifest_sha256"] == MANIFEST_SHA
    assert launch["status"] == "LAUNCHED_SOURCE_INNER_AUDIT_CPU"
    assert launch["source_manifest_sha256"] == MANIFEST_SHA
    assert launch["stage_receipt_sha256"] == sha(STAGE)
    assert launch["score_computed_at_launch"] is False
    checked = remote_check()
    assert checked["status"] == "PASS_SOURCE_INNER_V2_INDEPENDENT_READBACK"
    assert checked["stage_manifest_sha256"] == MANIFEST_SHA
    assert checked["launch_sha256"] == launch["launch_readback"]["launch_sha256"]
    receipt = {"status": "PASS_SOURCE_INNER_V2_INDEPENDENT_VERIFICATION",
               "stage_receipt_sha256": sha(STAGE), "launch_receipt_sha256": sha(LAUNCH),
               "remote": checked,
               "interpretation": "Source-inner only; all-frame prediction count does not estimate detector precision on sparsely annotated frames; preregistered proposal signal false.",
               "reciprocal_target_score": None, "kaggle_post": False}
    with OUT.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT),
                      "result_sha256": checked["result_sha256"],
                      "summaries": checked["summaries"]}))


if __name__ == "__main__":
    main()
