"""Stage target175 plans only after both source thresholds are sealed."""
import ast
import hashlib
import json
from pathlib import Path

from monitor_exp213_job import ssh
from run_exp234_source_scorer_guarded import released_success


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
SOURCE_CODE = REMOTE + "/code/exp234_source_threshold_v2_20260926"
TARGET_CODE = REMOTE + "/code/exp234_target_rollout_v1_20260926"
ASSIGNMENT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
SOURCE_MANIFEST_SHA = "8c85ae484ed5ed02dac88f9d6ab7ce701ed2a0d5cc81372af56a9ffcb6d7050a"
NOTEBOOK_SHA = "5389953eb7c2f68b6e3664985ceb252d0eac391b65821b0ced692693003cbcba"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def local_freeze():
    assert sha(ASSIGNMENT) == ASSIGNMENT_SHA
    assignment = json.loads(ASSIGNMENT.read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["thresholds_selected"] is False
    assert assignment["canonical_cohort_manifest_sha256"] == COHORT_SHA
    choices = {}
    for source in ("44b6", "6bba"):
        monitor = json.loads((ROOT / f"reports/exp234_source_{source}_config_v2_20260926_monitor.json").read_text())
        assert released_success(monitor), source
        scored = json.loads((ROOT / f"reports/exp234_source_{source}_score_v3_20260926.json").read_text())
        assert scored["status"] == "VERIFIED_EXP234_SOURCE_SELECTION"
        assert scored["source_embryo"] == source
        assert scored["selected_threshold"] in ("0.900", "0.940", "0.965")
        assert scored["monitor_receipt_sha256"] == sha(
            ROOT / f"reports/exp234_source_{source}_config_v2_20260926_monitor.json")
        choices[source] = scored
    return assignment, choices


def remote_preflight(assignment, choices):
    selection = {source: {"result_sha256": item["result_sha256"],
                          "gate_sha256": item["gate_sha256"],
                          "selected_threshold": item["selected_threshold"]}
                 for source, item in choices.items()}
    source = '''import hashlib,json,pathlib
r=pathlib.Path(ROOT);code=r/'code/exp234_source_threshold_v2_20260926'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==SOURCE_MANIFEST_SHA
manifest=json.loads((code/'code_manifest.json').read_text())
assert all(sha(code/name)==digest for name,digest in manifest.items())
cohort=r/'code/exp228_horaz_ensemble_quadro_v2_20260923/heldout175_manifest.json'
assert sha(cohort)==COHORT_SHA
rows=json.loads(cohort.read_text())['rows']
out={'source_bundles':{},'source_bundle_shas':{},'selection':{}}
for embryo in ('44b6','6bba'):
 bpath=code/(embryo+'_bundle.json');bundle=json.loads(bpath.read_text())
 result=r/'runs'/('exp234_source_'+embryo+'_v2_20260926/score/result.json')
 gate=result.with_name('no_metric_gate.json')
 expected=SELECTION[embryo]
 assert sha(result)==expected['result_sha256'] and sha(gate)==expected['gate_sha256']
 selected=json.loads(result.read_text())
 assert selected['status']=='PASS_EXP234_SOURCE_THRESHOLD_SELECTED'
 assert selected['source_embryo']==embryo and selected['selected_threshold']==expected['selected_threshold']
 assert bundle['source_embryo']==embryo
 for role in ('primary','secondary','center'):
  assert sha(pathlib.Path(bundle[role]['path']))==bundle[role]['sha256']
 out['source_bundles'][embryo]=bundle
 out['source_bundle_shas'][embryo]=sha(bpath)
 out['selection'][embryo]={'result_sha256':sha(result),'gate_sha256':sha(gate),'selected_threshold':selected['selected_threshold']}
six={row['dataset'] for row in rows if row['dataset'].startswith('6bba_')}
four={row['dataset'] for row in rows if row['dataset'].startswith('44b6_')}
assert six==set(ASSIGNMENT['44b6']) and four==set(ASSIGNMENT['6bba'])
assert len(six)==116 and len(four)==59 and len(rows)==175
assert sha(r/'code/exp214_inference_v7_20260912/compact47_v20.ipynb')==NOTEBOOK_SHA
out['cohort_sha256']=sha(cohort)
print(json.dumps(out))
'''.replace("ROOT", repr(REMOTE)).replace("SOURCE_MANIFEST_SHA", repr(SOURCE_MANIFEST_SHA)).replace(
        "COHORT_SHA", repr(COHORT_SHA)).replace("NOTEBOOK_SHA", repr(NOTEBOOK_SHA)).replace(
        "SELECTION", repr(selection)).replace("ASSIGNMENT", repr({
            source: sorted({name for chunk in assignment["directions"][source]["chunks"] for name in chunk})
            for source in ("44b6", "6bba")}))
    return ssh("nsu-a100", "python3 -", source)


def main():
    assignment, choices = local_freeze()
    remote = remote_preflight(assignment, choices)
    assert remote["cohort_sha256"] == COHORT_SHA
    for source in ("44b6", "6bba"):
        assert remote["selection"][source] == {
            "result_sha256": choices[source]["result_sha256"],
            "gate_sha256": choices[source]["gate_sha256"],
            "selected_threshold": choices[source]["selected_threshold"]}

    wrapper = (ROOT / "scripts/exp214_inference_job.py").read_text()
    old = "assert config['script'] in ('run_exp214_public_fold.py','run_exp214_local_graph.py','run_exp214_paired_fold.py')"
    assert wrapper.count(old) == 1
    wrapper = wrapper.replace(old, "assert config['script'] == 'run_exp234_target_chunk.py'")
    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "run_exp234_target_chunk.py", "score_exp214_paired.py")}
    files["exp214_inference_job.py"] = wrapper
    files["assignment.json"] = ASSIGNMENT.read_text()
    configs = {}
    for source in ("44b6", "6bba"):
        bundle = dict(remote["source_bundles"][source])
        bundle["evaluation_mode"] = "EXP234_TARGET_ROLLOUT"
        bundle["selected_threshold"] = choices[source]["selected_threshold"]
        bundle_name = source + "_target_bundle.json"
        files[bundle_name] = json.dumps(bundle, indent=2) + "\n"
        configs[source] = []
        chunks = assignment["directions"][source]["chunks"]
        for index, movies in enumerate(chunks):
            token = source + "_chunk" + f"{index:02d}"
            movies_name = token + "_movies.json"
            plan_name = token + "_plan.json"
            run = REMOTE + "/runs/exp234_target_" + token + "_v1_20260926"
            files[movies_name] = json.dumps(movies, indent=2) + "\n"
            plan = {"experiment": "EXP234_TARGET_CHUNK", "source_embryo": source,
                    "target_embryo": "6bba" if source == "44b6" else "44b6",
                    "chunk_index": index, "chunk_count": len(chunks),
                    "selected_threshold": choices[source]["selected_threshold"],
                    "code": TARGET_CODE, "output": run + "/output",
                    "assignment": TARGET_CODE + "/assignment.json", "assignment_sha256": ASSIGNMENT_SHA,
                    "cohort_sha256": COHORT_SHA,
                    "movies": TARGET_CODE + "/" + movies_name,
                    "movies_sha256": sha_bytes(files[movies_name].encode()),
                    "source_selection_result": REMOTE + "/runs/exp234_source_" + source +
                                               "_v2_20260926/score/result.json",
                    "source_selection_result_sha256": choices[source]["result_sha256"],
                    "source_bundle": SOURCE_CODE + "/" + source + "_bundle.json",
                    "source_bundle_sha256": remote["source_bundle_shas"][source],
                    "bundle": TARGET_CODE + "/" + bundle_name,
                    "bundle_sha256": sha_bytes(files[bundle_name].encode()),
                    "notebook": REMOTE + "/code/exp214_inference_v7_20260912/compact47_v20.ipynb",
                    "notebook_sha256": NOTEBOOK_SHA,
                    "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
                    "data_dir": REMOTE + "/data/exp213_source_view_20260912"}
            files[plan_name] = json.dumps(plan, indent=2) + "\n"
            configs[source].append({"experiment": "EXP234_TARGET_CHUNK",
                                    "lease_id": "exp234-target-" + source + "-chunk" + f"{index:02d}" + "-20260926",
                                    "token": "exp234_target_" + token + "_20260926",
                                    "pool": "a100", "code": TARGET_CODE, "run": run,
                                    "max_seconds": 10800,
                                    "cpu_affinity": "0-7" if source == "44b6" else "8-15",
                                    "script": "run_exp234_target_chunk.py",
                                    "arguments": [TARGET_CODE + "/" + plan_name,
                                                  "--plan-sha256", sha_bytes(files[plan_name].encode())],
                                    "resources": {"cpu": 8, "ram_gib": 64, "disk_growth_gib": 3}})

    stage = '''import ast,hashlib,json,pathlib
code=pathlib.Path(TARGET_CODE);source=pathlib.Path(SOURCE_CODE)
assert not code.exists();assert hashlib.sha256((source/'code_manifest.json').read_bytes()).hexdigest()==SOURCE_SHA
source_manifest=json.loads((source/'code_manifest.json').read_text())
code.mkdir(parents=True)
files=FILES
for name in ('run_exp214_public_fold.py','exp234_source_scope.py','bound_exp214_submission.py','exp223_supervisor.py','monitor_exp213_job.py'):
 body=(source/name).read_text();assert hashlib.sha256(body.encode()).hexdigest()==source_manifest[name]
 files[name]=body
for name,body in files.items():
 path=code/name;path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP234_TARGET_ROLLOUT','code':str(code),'files':len(files),
 'manifest_sha256':sha(code/'code_manifest.json'),
 'plan_sha256':{name:manifest[name] for name in manifest if name.endswith('_plan.json')}}))
'''.replace("TARGET_CODE", repr(TARGET_CODE)).replace("SOURCE_CODE", repr(SOURCE_CODE)).replace(
        "SOURCE_SHA", repr(SOURCE_MANIFEST_SHA)).replace("FILES", repr(files))
    staged = ssh("nsu-a100", "python3 -", stage)
    for source in ("44b6", "6bba"):
        for index, config in enumerate(configs[source]):
            path = ROOT / f"reports/exp234_target_{source}_chunk{index:02d}_config_20260926.json"
            path.write_text(json.dumps(config, indent=2) + "\n")
    receipt = {"status": "PREPARED_EXP234_TARGET175_NO_LABELS", "stage": staged,
               "assignment_sha256": ASSIGNMENT_SHA,
               "source_choices": {source: {"selected_threshold": choices[source]["selected_threshold"],
                                           "result_sha256": choices[source]["result_sha256"],
                                           "gate_sha256": choices[source]["gate_sha256"]}
                                  for source in ("44b6", "6bba")},
               "chunks": {source: len(configs[source]) for source in configs},
               "target_labels_read": False}
    (ROOT / "reports/exp234_target_prepare_20260926.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "manifest_sha256": staged["manifest_sha256"],
                      "chunks": receipt["chunks"]}))


if __name__ == "__main__":
    main()
