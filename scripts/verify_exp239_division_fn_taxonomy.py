"""One-shot, read-only remote completion check for EXP239's source-only audit.

The verifier never opens GEFF or recomputes metrics. It compares the 19 label
tree digests recorded by EXP239 to the independently completed SOURCE-INNER v2
receipt, then writes one exclusive *local* verification receipt on success.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path

from monitor_exp213_job import ssh

if not __debug__:
    raise RuntimeError("EXP239 verifier requires active assertions")


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
BUNDLE = ROOT / "work/exp239_source_division_fn_taxonomy_20260927/bundle"
STAGE = REPORTS / "exp239_division_fn_taxonomy_stage_20260927.json"
LAUNCH = REPORTS / "exp239_division_fn_taxonomy_launch_20260927.json"
STAGE_INTENT = REPORTS / "exp239_division_fn_taxonomy_stage_intent_20260927.json"
LAUNCH_INTENT = REPORTS / "exp239_division_fn_taxonomy_launch_intent_20260927.json"
OUT = REPORTS / "exp239_division_fn_taxonomy_verified_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
NAME = "exp239_source_division_fn_taxonomy_v1_20260927"
MANIFEST_SHA = "22e5679b66462bad6662c1e98384e9bec9c4a656e7bfd7caec145b5ac8e3abaf"
STAGE_SHA = "4bfefb36c03df9b38b662235d7b4ad7498180677b241d905e381f4623e9c641b"
LAUNCH_SHA = "c91403141f9b624554b3b029de7aed1496828a4c4f4ebc42abbb2e63fb6ce5aa"
REMOTE_LAUNCH_SHA = "af8e878a7100cf67910abb8bce2e2f2f8eeca0c9df9345255be1ff144b5f1b7b"
REMOTE_EXIT_SHA = "7511d8ba51150b5ce378e31401604b2185fbb96da870e4bf6c4ad3142054e9ae"
GATE_SHA = "5adbe69e49c72540b982c5403369367db54f7d64032c209d720359484fea178c"
RESULT_SHA = "f6b8859e308862090567af53b5fdd68c59c0c0907aa2f357d54a471e9386cd85"
PRIOR_SOURCE_RESULT_SHA = "4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f"
ORGANIZER_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
METRIC_SHAS = {
    "tracking_cellmot_official/__init__.py": "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    "tracking_cellmot_official/metrics.py": "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444",
    "tracking_cellmot_official/division_metrics.py": "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9",
}
STAGES = (
    "no_parent_side_match", "fewer_than_two_daughter_lineages",
    "no_local_fork", "directed_branch_failure", "organizer_veto_or_pairing",
)
EXPECTED_CATEGORIES = (
    {"recovered": 2, "no_parent_side_match": 0,
     "fewer_than_two_daughter_lineages": 0, "no_local_fork": 3,
     "directed_branch_failure": 0, "organizer_veto_or_pairing": 0},
    {"recovered": 1, "no_parent_side_match": 0,
     "fewer_than_two_daughter_lineages": 2, "no_local_fork": 6,
     "directed_branch_failure": 0, "organizer_veto_or_pairing": 0},
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_taxonomy(config: dict, gate: dict, result: dict, prior: dict) -> dict:
    """Check all event arithmetic and independently recorded source tree hashes.

    Pure JSON validation: no graph, GEFF, image, or score computation occurs.
    This function is embedded byte-for-byte in the remote readback source.
    """
    assert gate["status"] == "PASS_EXP239_SOURCE19_GRAPH_METRIC_GATE_BEFORE_LABEL_ACCESS"
    assert gate["bundle_sha256"] == MANIFEST_SHA
    assert gate["reciprocal_target_labels_read"] is False
    assert gate["runtime"]["profile"] == "remote_py311"
    assert gate["runtime"]["tracksdata_commit"] == TRACKSDATA_COMMIT
    assert gate["synthetic_contract"]["status"] == "PASS_CURRENT_ORGANIZER_LOCAL_FORK_CONTRACT"
    assert result["status"] == "PASS_EXP239_SOURCE19_DIVISION_FN_TAXONOMY"
    assert result["organizer_commit"] == ORGANIZER_COMMIT
    assert result["metric_shas"] == METRIC_SHAS
    assert result["source_division_events"] == 14
    assert result["source_division_fns"] == 11
    assert result["reciprocal_target_labels_read"] is False
    assert result["gpu_used"] is False and result["kaggle_post"] is False
    assert [c["experiment"] for c in config["cohorts"]] == ["EXP227", "EXP236"]
    assert [c["experiment"] for c in gate["cohorts"]] == ["EXP227", "EXP236"]
    assert [c["experiment"] for c in result["cohorts"]] == ["EXP227", "EXP236"]
    assert [c["experiment"] for c in prior["cohorts"]] == ["EXP227", "EXP236"]
    summaries = []
    label_digest_input = []
    total_events = total_fn = 0
    for index, (source, gated, cohort, old) in enumerate(zip(
            config["cohorts"], gate["cohorts"], result["cohorts"],
            prior["cohorts"], strict=True)):
        names = source["ids"]
        assert len(names) == (8 if index == 0 else 11)
        assert [row["dataset"] for row in source["graph_hashes"]] == names
        assert gated["ids"] == names
        assert gated["graph_hashes"] == source["graph_hashes"]
        assert gated["prior_no_metric_gate_sha256"] == source["score_gate_sha256"]
        assert [row["dataset"] for row in cohort["movies"]] == names
        assert [row["dataset"] for row in cohort["label_hashes"]] == names
        assert [row["dataset"] for row in old["label_hashes"]] == names
        assert cohort["counts"] == source["expected_division_counts"]
        assert cohort["category_counts"] == EXPECTED_CATEGORIES[index]
        old_labels = [(row["dataset"], row["tree_sha256"], row["files"])
                      for row in old["label_hashes"]]
        new_labels = [(row["dataset"], row["tree_sha256"], row["files"])
                      for row in cohort["label_hashes"]]
        assert new_labels == old_labels
        for label in cohort["label_hashes"]:
            digest = label["tree_sha256"]
            assert isinstance(digest, str) and len(digest) == 64
            assert all(char in "0123456789abcdef" for char in digest)
            assert isinstance(label["files"], int) and label["files"] > 0
            pinned = source["geff_tree_hashes"].get(label["dataset"])
            assert label["previously_pinned"] is (pinned is not None)
            if pinned is not None:
                assert digest == pinned
            label_digest_input.append((label["dataset"], digest))
        movie_counts = Counter()
        cohort_categories = Counter()
        for movie in cohort["movies"]:
            counts = movie["counts"]
            assert set(counts) == {"tp", "fp", "fn"}
            assert all(isinstance(value, int) and value >= 0 for value in counts.values())
            events = movie["events"]
            assert len(events) == counts["tp"] + counts["fn"]
            assert len({event["gt_divider_id"] for event in events}) == len(events)
            categories = Counter()
            for event in events:
                assert event["dataset"] == movie["dataset"]
                assert isinstance(event["gt_divider_id"], int)
                category = event["category"]
                assert category in ("recovered", *STAGES)
                parents = event["matched_parent_side_nodes"]
                daughters = event["represented_daughter_lineages"]
                local = event["local_forks"]
                directed = event["directed_forks"]
                valid = event["valid_forks"]
                assert all(isinstance(v, int) and v >= 0 for v in
                           (parents, daughters, local, directed, valid))
                assert local >= directed >= valid
                subtype = event["subtype"]
                if category == "recovered":
                    assert valid > 0 and subtype is None
                elif category == STAGES[0]:
                    assert parents == 0 and subtype is None
                elif category == STAGES[1]:
                    assert parents > 0 and daughters < 2 and subtype is None
                elif category == STAGES[2]:
                    assert parents > 0 and daughters >= 2 and local == 0 and subtype is None
                elif category == STAGES[3]:
                    assert parents > 0 and daughters >= 2 and local > 0 and directed == 0 and subtype is None
                else:
                    assert parents > 0 and daughters >= 2 and directed > 0
                    assert subtype in ("organizer_invalid_fork", "bipartite_collision")
                    assert (valid == 0) is (subtype == "organizer_invalid_fork")
                categories[category] += 1
            assert movie["category_counts"] == {
                key: categories[key] for key in ("recovered", *STAGES)}
            assert categories["recovered"] == counts["tp"]
            assert sum(categories[key] for key in STAGES) == counts["fn"]
            for key in ("tp", "fp", "fn"):
                movie_counts[key] += counts[key]
            cohort_categories.update(categories)
        assert dict(movie_counts) == cohort["counts"]
        assert cohort["category_counts"] == {
            key: cohort_categories[key] for key in ("recovered", *STAGES)}
        total_events += sum(len(movie["events"]) for movie in cohort["movies"])
        total_fn += cohort["counts"]["fn"]
        summaries.append({"experiment": cohort["experiment"],
                          "movies": len(names), "counts": cohort["counts"],
                          "category_counts": cohort["category_counts"],
                          "label_trees_match_prior": True})
    assert total_events == 14 and total_fn == 11
    label_digest = hashlib.sha256(json.dumps(label_digest_input,
                         separators=(",", ":")).encode()).hexdigest()
    return {"summaries": summaries, "source19_label_tree_digest": label_digest,
            "source_division_events": total_events, "source_division_fns": total_fn}


def local_gate() -> tuple[dict, dict, dict]:
    assert not OUT.exists(), "EXP239 verification receipt exists; do not repeat"
    assert sha(STAGE) == STAGE_SHA
    assert sha(LAUNCH) == LAUNCH_SHA
    assert sha(BUNDLE / "manifest.json") == MANIFEST_SHA
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    assert manifest["status"] == "SEALED_EXP239_LOCAL_ONLY"
    assert len(manifest["files"]) == 8
    for relative, digest in manifest["files"].items():
        path = (BUNDLE / relative).resolve()
        assert path.is_relative_to(BUNDLE.resolve()) and sha(path) == digest
    stage = json.loads(STAGE.read_text())
    launch = json.loads(LAUNCH.read_text())
    assert stage["status"] == "STAGED_EXP239_AUDIT_NO_LABELS"
    assert stage["manifest_sha256"] == MANIFEST_SHA
    assert stage["intent_sha256"] == sha(STAGE_INTENT)
    assert stage["run_started"] is False
    assert stage["source_labels_read"] is False
    assert stage["reciprocal_target_labels_read"] is False
    assert stage["gpu_used"] is False and stage["kaggle_post"] is False
    expected_files = {**manifest["files"], "manifest.json": MANIFEST_SHA}
    assert stage["stage"]["file_hashes"] == expected_files
    assert stage["readback"]["file_hashes"] == expected_files
    assert stage["readback"]["run_absent"] is True
    assert launch["status"] == "LAUNCHED_EXP239_AUDIT_CPU"
    assert launch["source_manifest_sha256"] == MANIFEST_SHA
    assert launch["stage_receipt_sha256"] == STAGE_SHA
    assert launch["intent_sha256"] == sha(LAUNCH_INTENT)
    assert launch["import_preflight"]["labels_read"] is False
    assert launch["import_preflight"]["run_absent"] is True
    assert launch["stage_readback"]["file_hashes"] == expected_files
    assert launch["stage_readback"]["run_absent"] is True
    assert launch["launch"]["source_manifest_sha256"] == MANIFEST_SHA
    assert launch["launch"]["cpu_affinity"] == [24, 25, 26, 27]
    assert launch["launch"]["ram_gib"] == 16
    assert launch["launch"]["max_seconds"] == 2700
    assert launch["launch"]["cuda_visible_devices"] == ""
    assert launch["launch"]["gpu_used"] is False
    assert launch["launch_readback"]["launch_sha256"] == REMOTE_LAUNCH_SHA
    assert launch["launch_readback"]["gpu_used"] is False
    assert launch["score_computed_at_launch"] is False
    return manifest, stage, launch


def remote_check_source() -> str:
    function = inspect.getsource(verify_taxonomy)
    source = r'''import ast,hashlib,json,os,pathlib,sys
from collections import Counter
if not __debug__:raise RuntimeError('EXP239 readback requires active assertions')
root=pathlib.Path(@@ROOT@@)
code=root/'code'/@@NAME@@
run=root/'runs'/@@NAME@@
prior_path=root/'runs/source_inner_error_decomposition_v2_20260927/output/result.json'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def deny_geff(event,args):
 if event not in ('open','os.listdir','os.scandir') or not args:return
 raw=args[0]
 if isinstance(raw,(str,bytes,os.PathLike)) and any(
  part.endswith('.geff') for part in pathlib.Path(os.fsdecode(raw)).parts):
  raise PermissionError('EXP239 verifier must not open GEFF')
sys.addaudithook(deny_geff)
assert os.uname().nodename=='prepost'
manifest_path=code/'manifest.json'
assert sha(manifest_path)==@@MANIFEST_SHA@@
manifest=json.loads(manifest_path.read_text())
assert manifest['status']=='SEALED_EXP239_LOCAL_ONLY' and len(manifest['files'])==8
observed={p.relative_to(code).as_posix():sha(p) for p in code.rglob('*') if p.is_file()}
assert observed=={**manifest['files'],'manifest.json':@@MANIFEST_SHA@@}
for name in observed:
 if name.endswith('.py'):ast.parse((code/name).read_bytes().decode('utf-8'),filename=name)
config=json.loads((code/'config.json').read_text())
assert config['status']=='PREREGISTERED_EXP239_SOURCE_DIVISION_FN_TAXONOMY'
assert config['organizer_commit']==ORGANIZER_COMMIT
assert config['tracksdata_commit']==TRACKSDATA_COMMIT
assert config['source19_image_receipt_sha256']==manifest['files']['source_inner19_image_scale_audit_v2_20260927.json']
launch_path=run/'launch.json';exit_path=run/'exit.json';child_path=run/'child.json'
wrapper_path=run/'cpu_wrapper.py';gate_path=run/'output/no_label_gate.json'
result_path=run/'output/result.json'
assert sha(launch_path)==@@REMOTE_LAUNCH_SHA@@
assert sha(exit_path)==@@REMOTE_EXIT_SHA@@
assert sha(gate_path)==@@GATE_SHA@@
assert sha(result_path)==@@RESULT_SHA@@
assert sha(prior_path)==@@PRIOR_SHA@@
assert {p.name for p in (run/'output').iterdir()}=={'no_label_gate.json','result.json'}
assert launch_path.stat().st_mtime_ns < gate_path.stat().st_mtime_ns < result_path.stat().st_mtime_ns < exit_path.stat().st_mtime_ns
launch=json.loads(launch_path.read_text());exit=json.loads(exit_path.read_text())
child=json.loads(child_path.read_text())
assert launch['status']=='LAUNCHED_EXP239_AUDIT_CPU'
assert launch['source_manifest_sha256']==@@MANIFEST_SHA@@
assert launch['code']==str(code) and launch['run']==str(run)
assert launch['cpu_affinity']==[24,25,26,27]
assert launch['ram_gib']==16 and launch['max_seconds']==2700
assert launch['cuda_visible_devices']=='' and launch['gpu_used'] is False
assert launch['kaggle_post'] is False and launch['source_labels_only'] is True
assert sha(wrapper_path)==launch['wrapper_sha256']
ast.parse(wrapper_path.read_bytes().decode('utf-8'),filename='cpu_wrapper.py')
assert child['pid']==exit['pid'] and child['start']==exit['start']
assert child['command']==launch['command']
assert child['cpu_affinity']==[24,25,26,27]
assert child['ram_bytes']==16*1024**3 and child['cuda_visible_devices']==''
assert exit['returncode']==0 and exit['timeout'] is False and exit['error'] is None
assert exit['source_labels_only'] is True and exit['gpu_used'] is False and exit['kaggle_post'] is False
def state_and_start(pid):
 try:
  fields=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ')[1].split()
  return fields[0],fields[19]
 except FileNotFoundError:return None,None
wrapper_state,_=state_and_start(launch['wrapper_pid'])
child_state,child_start=state_and_start(exit['pid'])
assert wrapper_state in (None,'Z')
assert child_state in (None,'Z') or child_start!=exit['start']
gate=json.loads(gate_path.read_text());result=json.loads(result_path.read_text())
prior=json.loads(prior_path.read_text())
assert gate['manifest']==manifest
assert result['no_label_gate_sha256']==sha(gate_path)
@@VERIFY_TAXONOMY@@
checked=verify_taxonomy(config,gate,result,prior)
print(json.dumps({'status':'PASS_EXP239_INDEPENDENT_READBACK',
 'manifest_sha256':sha(manifest_path),'launch_sha256':sha(launch_path),
 'exit_sha256':sha(exit_path),'gate_sha256':sha(gate_path),
 'result_sha256':sha(result_path),'prior_source_result_sha256':sha(prior_path),
 'gate_precedes_result':True,'wrapper_absent':True,'child_absent':True,
 'source_labels_opened_by_verifier':False,'reciprocal_target_labels_read':False,
 'gpu_used':False,'kaggle_post':False,**checked}))
'''
    source = source.replace("@@VERIFY_TAXONOMY@@", function)
    replacements = {
        "@@ROOT@@": REMOTE, "@@NAME@@": NAME,
        "@@MANIFEST_SHA@@": MANIFEST_SHA,
        "@@REMOTE_LAUNCH_SHA@@": REMOTE_LAUNCH_SHA,
        "@@REMOTE_EXIT_SHA@@": REMOTE_EXIT_SHA,
        "@@GATE_SHA@@": GATE_SHA,
        "@@RESULT_SHA@@": RESULT_SHA,
        "@@PRIOR_SHA@@": PRIOR_SOURCE_RESULT_SHA,
    }
    for token, value in replacements.items():
        assert token in source, token
        source = source.replace(token, repr(value))
    assert "@@" not in source
    # The embedded pure validator needs only these two constant blocks.
    source = source.replace("root=pathlib.Path(",
        f"MANIFEST_SHA={MANIFEST_SHA!r}\nTRACKSDATA_COMMIT={TRACKSDATA_COMMIT!r}\n"
        f"ORGANIZER_COMMIT={ORGANIZER_COMMIT!r}\nMETRIC_SHAS={METRIC_SHAS!r}\n"
        f"STAGES={STAGES!r}\nEXPECTED_CATEGORIES={EXPECTED_CATEGORIES!r}\n"
        "root=pathlib.Path(", 1)
    compile(source, "exp239_remote_completion_verify", "exec")
    return source


def remote_check() -> dict:
    source = remote_check_source()
    result = ssh("nsu-quadro", "env PYTHONDONTWRITEBYTECODE=1 PYTHONOPTIMIZE=0 CUDA_VISIBLE_DEVICES= python3 -B -", source)
    assert result["status"] == "PASS_EXP239_INDEPENDENT_READBACK"
    assert result["manifest_sha256"] == MANIFEST_SHA
    assert result["launch_sha256"] == REMOTE_LAUNCH_SHA
    assert result["exit_sha256"] == REMOTE_EXIT_SHA
    assert result["gate_sha256"] == GATE_SHA
    assert result["result_sha256"] == RESULT_SHA
    assert result["prior_source_result_sha256"] == PRIOR_SOURCE_RESULT_SHA
    assert result["source_labels_opened_by_verifier"] is False
    assert result["reciprocal_target_labels_read"] is False
    assert result["gpu_used"] is False and result["kaggle_post"] is False
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest, stage, launch = local_gate()
    if args.dry_run:
        source = remote_check_source()
        print(json.dumps({"status": "DRY_RUN_EXP239_VERIFIER_NO_REMOTE_CALL",
                          "remote_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                          "manifest_sha256": MANIFEST_SHA, "stage_sha256": STAGE_SHA,
                          "launch_sha256": LAUNCH_SHA, "remote_mutation": False,
                          "receipt_write": False}))
        return
    checked = remote_check()
    assert checked["source_division_events"] == 14 and checked["source_division_fns"] == 11
    receipt = {
        "status": "PASS_EXP239_INDEPENDENT_COMPLETION_VERIFICATION",
        "manifest_sha256": MANIFEST_SHA,
        "stage_receipt_sha256": STAGE_SHA,
        "launch_receipt_sha256": LAUNCH_SHA,
        "remote": checked,
        "interpretation": "Source-inner descriptive taxonomy only; 14 events are too sparse for threshold selection or promotion.",
        "reciprocal_target_score": None,
        "kaggle_post": False,
    }
    with OUT.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT),
                      "result_sha256": checked["result_sha256"],
                      "summaries": checked["summaries"]}))


if __name__ == "__main__":
    main()
