"""Stage the EXP234 official175 scorer only after every target chunk is released."""
import hashlib
import json
from pathlib import Path, PurePosixPath

from monitor_exp213_job import ssh
from prepare_exp234_target_rollout_v2 import local_freeze


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
CODE = REMOTE + "/code/exp234_target_official_scorer_v1_20260927"
TARGET_CODE = REMOTE + "/code/exp234_target_rollout_v2_20260927"
COHORT = REMOTE + "/code/exp228_horaz_ensemble_quadro_v2_20260923/heldout175_manifest.json"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"
BASELINE = REMOTE + "/runs/exp214_gapfix_score175_20260914/output/new90/metrics.json"
BASELINE_SHA = "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
TARGET_MANIFEST_SHA = "0cba3b0e3240d9e5b755d67fdd85a9d7166670fb919a65d4b69f3ccf705c1ee4"
NOTEBOOK_SHA = "5389953eb7c2f68b6e3664985ceb252d0eac391b65821b0ced692693003cbcba"
SEQUENCE = [("6bba", i) for i in range(4)] + [("44b6", i) for i in range(8)]


def sha_bytes(body):
    return hashlib.sha256(body).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def main():
    assignment, choices = local_freeze()
    original_path = ROOT / "reports/exp234_target_coordinator_v2_20260927.json"
    original = json.loads(original_path.read_text())
    assert original["status"] == "STOPPED_EXP234_TARGET_ROLLOUT"
    assert original["target_labels_read"] is False
    assert len(original["completed"]) == 5
    coordinator_path = ROOT / "reports/exp234_target_recovery_v2_20260927.json"
    coordinator = json.loads(coordinator_path.read_text())
    assert coordinator["status"] == "PASS_EXP234_TARGET175_RECOVERED_NO_LABELS_RELEASED"
    assert coordinator["target_labels_read"] is False
    assert coordinator["original_coordinator_sha256"] == sha(original_path)
    assert coordinator["completed"][:5] == original["completed"]
    assert len(coordinator["completed"]) == 12
    assert sum(item["movies"] for item in coordinator["completed"]) == 175
    prepared = json.loads((ROOT / "reports/exp234_target_prepare_v2_20260927.json").read_text())
    assert prepared["status"] == "PREPARED_EXP234_TARGET175_NO_LABELS"
    assert prepared["stage"]["manifest_sha256"] == TARGET_MANIFEST_SHA
    assert prepared["assignment_sha256"] == ASSIGNMENT_SHA
    assert assignment["canonical_cohort_manifest_sha256"] == COHORT_SHA

    entries = {}
    for (source, index), completed in zip(SEQUENCE, coordinator["completed"]):
        token = f"{source}_chunk{index:02d}"
        assert completed["source"] == source and completed["chunk"] == index
        assert completed["movies"] == len(assignment["directions"][source]["chunks"][index])
        path = ROOT / f"reports/exp234_target_{token}_config_v2_20260927_monitor.json"
        assert sha(path) == completed["monitor_sha256"]
        state = json.loads(path.read_text())
        assert state["monitor_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert state["exit"]["returncode"] == 0 and state["exit"]["hard_timeout"] is False
        assert state["queue"]["state"] == "RELEASED"
        assert state["identity_alive"] is False and state["group_alive"] is False
        assert state["gpu_pids"] == []
        assert state["status"]["status"] == "PASS_EXP234_TARGET_CHUNK_NO_LABELS"
        assert state["status"]["csv_sha256"] == completed["csv_sha256"]
        assert state["status"]["receipt_sha256"] == completed["receipt_sha256"]
        entries[token] = state
    releases = {"status": "PASS_EXP234_ALL_CHUNKS_VERIFIED_RELEASED",
                "entries": entries, "target_labels_read": False}
    release_text = json.dumps(releases, indent=2) + "\n"
    release_sha = sha_bytes(release_text.encode())
    release_local = ROOT / "reports/exp234_target_release_manifest_v2_20260927.json"
    assert not release_local.exists()
    release_local.write_bytes(release_text.encode())

    selections = {}
    for source in ("44b6", "6bba"):
        item = choices[source]
        selections[source] = {
            "result": REMOTE + f"/runs/exp234_source_{source}_v2_20260926/score/result.json",
            "result_sha256": item["result_sha256"],
            "gate": REMOTE + f"/runs/exp234_source_{source}_v2_20260926/score/no_metric_gate.json",
            "gate_sha256": item["gate_sha256"],
            "selected_threshold": item["selected_threshold"]}
    config = {"experiment": "EXP234_OFFICIAL_TARGET175",
              "inference_code": TARGET_CODE,
              "inference_manifest_sha256": TARGET_MANIFEST_SHA,
              "assignment": TARGET_CODE + "/assignment.json",
              "assignment_sha256": ASSIGNMENT_SHA,
              "cohort": COHORT, "cohort_sha256": COHORT_SHA,
              "release_manifest": CODE + "/release_manifest.json",
              "release_manifest_sha256": release_sha,
              "source_selection": selections,
              "baseline_metrics": BASELINE,
              "baseline_metrics_sha256": BASELINE_SHA,
              "notebook_sha256": NOTEBOOK_SHA,
              "evaluator_config": CODE + "/exp223_config.json",
              "repo": REMOTE + "/code/exp214_honest_refit_v4_20260912/tracking_repo",
              "data_dir": REMOTE + "/data/exp213_source_view_20260912",
              "output": REMOTE + "/runs/exp234_target_official_score175_20260927/output"}

    preflight = '''import hashlib,json,pathlib
r=pathlib.Path(ROOT);code=pathlib.Path(TARGET_CODE)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(code/'code_manifest.json')==TARGET_MANIFEST_SHA
assert sha(code/'assignment.json')==ASSIGNMENT_SHA
assert sha(COHORT)==COHORT_SHA
assert sha(BASELINE)==BASELINE_SHA
assert not pathlib.Path(SCORE_CODE).exists() and not pathlib.Path(SCORE_RUN).exists()
for source,choice in SELECTIONS.items():
 assert sha(choice['result'])==choice['result_sha256']
 assert sha(choice['gate'])==choice['gate_sha256']
print(json.dumps({'status':'PASS_EXP234_OFFICIAL_STAGE_PREFLIGHT'}))
'''.replace("TARGET_MANIFEST_SHA", repr(TARGET_MANIFEST_SHA)).replace(
        "ASSIGNMENT_SHA", repr(ASSIGNMENT_SHA)).replace("COHORT_SHA", repr(COHORT_SHA)).replace(
        "BASELINE_SHA", repr(BASELINE_SHA)).replace("SCORE_CODE", repr(CODE)).replace(
        "SCORE_RUN", repr(str(PurePosixPath(config["output"]).parent))).replace(
        "SELECTIONS", repr(selections)).replace("TARGET_CODE", repr(TARGET_CODE)).replace(
        "COHORT", repr(COHORT)).replace("BASELINE", repr(BASELINE)).replace("ROOT", repr(REMOTE))
    gate = ssh("nsu-quadro", "python3 -", preflight)
    assert gate["status"] == "PASS_EXP234_OFFICIAL_STAGE_PREFLIGHT"

    files = {name: (ROOT / "scripts" / name).read_text() for name in (
        "score_exp234_target_official.py", "score_exp214_paired.py", "score_exp223_official.py")}
    files["exp223_config.json"] = (ROOT / "reports/exp223_official_score_config_v2_20260922.json").read_text()
    files["release_manifest.json"] = release_text
    files["score_config.json"] = json.dumps(config, indent=2) + "\n"
    stage = '''import ast,hashlib,json,pathlib
code=pathlib.Path(CODE);assert not code.exists();code.mkdir(parents=True)
files=FILES
for name,body in files.items():
 path=code/name;path.write_text(body)
 if name.endswith('.py'):ast.parse(body,filename=name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={name:sha(code/name) for name in sorted(files)}
(code/'code_manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
print(json.dumps({'status':'STAGED_EXP234_OFFICIAL_SCORER','code':str(code),
                  'manifest_sha256':sha(code/'code_manifest.json'),
                  'score_config_sha256':sha(code/'score_config.json'),
                  'release_manifest_sha256':sha(code/'release_manifest.json')}))
'''.replace("CODE", repr(CODE)).replace("FILES", repr(files))
    staged = ssh("nsu-quadro", "python3 -", stage)
    assert staged["status"] == "STAGED_EXP234_OFFICIAL_SCORER"
    assert staged["release_manifest_sha256"] == release_sha
    assert staged["score_config_sha256"] == sha_bytes(files["score_config.json"].encode())
    receipt = {"status": "PREPARED_EXP234_OFFICIAL_TARGET175_SCORER_NO_LABELS",
               "preflight": gate, "stage": staged, "config": config,
               "release_manifest_local_sha256": sha(release_local),
               "coordinator_receipt_sha256": sha(coordinator_path),
               "original_coordinator_receipt_sha256": sha(original_path),
               "target_labels_read": False}
    (ROOT / "reports/exp234_target_official_scorer_prepare_20260927.json").write_text(
        json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "manifest_sha256": staged["manifest_sha256"],
                      "score_config_sha256": staged["score_config_sha256"]}))


if __name__ == "__main__":
    main()
