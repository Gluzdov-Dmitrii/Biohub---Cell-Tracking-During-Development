"""Read-only pooled current-organizer result from independently verified folds.

Reads only existing JSON receipts/results over a read-only SSH probe. It never
opens GEFF, scores a graph, launches a worker, or changes a remote file.
Default mode checks and prints; --write-receipt creates one local receipt.
"""

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
import warnings


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
OUTPUT = ROOT / "reports/exp227_exp236_current175_pooled_20260927.json"
ASSIGNMENT = ROOT / "reports/exp234_target_chunk_assignment_20260926.json"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"
BASELINE_SHA = "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5"
METRIC_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
DIVISION_SHA = "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"
METRIC_COMMIT = "075fc5f5a52d11077f9dc2b074644618f26939e2"
TRACKSDATA_COMMIT = "e13cf379b5127deeb8301ce56410fda35b5a3cf9"
EVIDENCE_CLASS = "leakage-controlled reciprocal evaluation; historically exposed target labels"
EXP214_SCORE = 0.7427291486246141
EXP209_SCORE = 0.6815218332750073
EXP209_VERIFY = ROOT / "reports/exp209_reconstructed_scorer_v1_readonly_verify_20260927.json"
EXP209_VERIFY_SHA = "54aa103c7b8799196b2068e43c8d80e43fc216771671066a497b8b21c60f4d5c"
EXP234_VERIFY = ROOT / "reports/exp234_current_organizer_score_verified_20260927.json"
EXP234_VERIFY_SHA = "04caea78971c9d749e8868036818a38f32d53c28943dd81eccb6269d2b1a009e"
METRIC_SOURCE = ROOT / "work/x138_provenance/official_metric/metrics_pinned.py"
DIVISION_SOURCE = ROOT / "work/x138_provenance/official_metric/division_metrics_pinned.py"

FOLDS = {
    "exp227_target6bba": {
        "n": 116, "assignment_direction": "44b6", "prefix": "6bba_",
        "verify": ROOT / "reports/exp227_target6bba_current_score_v4_20260927.json",
        "verify_sha": "4d6bdde3cf06b26255009db9ab3cbff5c81cb4827851ca0a63c5423fed56c550",
        "verify_status": "VERIFIED_EXP227_TARGET116_CURRENT_V4",
        "stage": ROOT / "reports/exp227_target6bba_scorer_stage_v4_20260927.json",
        "stage_status": "STAGED_EXP227_TARGET116_CURRENT_SCORER_V4_NO_LABELS",
        "launch": ROOT / "reports/exp227_target6bba_scorer_launch_v4_20260927.json",
        "launch_status": "LAUNCHED_EXP227_TARGET116_CURRENT_SCORER_V4",
        "coordinator": ROOT / "reports/exp227_target6bba_all116_waitsafe_v3_final_20260927.json",
        "coordinator_sha": "69f110c302a4a3fed21993f5ce7083e036b345ee2e53e917cc4382c3291effa3",
        "coordinator_status": "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED",
        "remote_code": REMOTE + "/code/exp227_target6bba_current_scorer_v4_20260927",
        "remote_run": REMOTE + "/runs/exp227_target6bba_current116_v4_20260927",
        "gate_status": "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS",
        "result_status": "PASS_EXP227_SOURCE44_TARGET6BBA_CURRENT116_V4",
        "expected_result_sha": "eb13954f1cc98d84f8b40c69bd31b595e51fef8d1fffdd8639d2f8d20622ae24",
    },
    "exp236_target44b6": {
        "n": 59, "assignment_direction": "6bba", "prefix": "44b6_",
        "verify": ROOT / "reports/exp236_target44b6_current_score_v2_20260927.json",
        "verify_sha": "cc34349e766aa339888ee0ecdbeaa0bb9e3447c97d8a9f08cdc843c48bcef77c",
        "verify_status": "VERIFIED_EXP236_TARGET59_OFFICIAL",
        "stage": ROOT / "reports/exp236_target44b6_scorer_stage_v2_20260927.json",
        "stage_status": "STAGED_EXP236_TARGET59_SCORER_NO_LABELS",
        "launch": ROOT / "reports/exp236_target44b6_scorer_launch_v2_20260927.json",
        "launch_status": "LAUNCHED_EXP236_TARGET59_OFFICIAL_SCORER",
        "coordinator": ROOT / "reports/exp236_target44b6_four_chunk_coordinator_20260927.json",
        "coordinator_sha": "0ccc0b6a10f141ae3e356b9970ff0062242493cb0163f186fea4a11caef7a545",
        "coordinator_status": "PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED",
        "remote_code": REMOTE + "/code/exp236_target44b6_current_scorer_v2_20260927",
        "remote_run": REMOTE + "/runs/exp236_target44b6_current59_v2_20260927",
        "gate_status": "PASS_EXP236_ALL_59_GRAPHS_BEFORE_LABEL_ACCESS",
        "result_status": "PASS_EXP236_SOURCE6BBA_TARGET44B6_CURRENT59",
        "expected_result_sha": "f846ee8e6a554551373bc3a853bde14c2e7b3f5fd12a5a13159216de2ce9cae6",
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"))
                           .encode()).hexdigest()


def pinned_json(path, expected_sha):
    require(sha(path) == expected_sha, f"SHA mismatch: {path}")
    return json.loads(Path(path).read_text())


def close(left, right, *, tol=1e-12):
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return (math.isnan(left) and math.isnan(right)) or math.isclose(
            float(left), float(right), rel_tol=0, abs_tol=tol)
    return left == right


def rows_close(actual, expected):
    require(set(actual) == set(expected), "Baseline row keys changed")
    require(all(close(actual[k], expected[k]) for k in expected),
            f"Historical EXP214 row replay changed: {expected['dataset']}")


def organizer_summarise():
    """Compile exact pinned summarise and its two helpers, without label imports."""
    require(sha(METRIC_SOURCE) == METRIC_SHA, "Organizer metrics.py changed")
    require(sha(DIVISION_SOURCE) == DIVISION_SHA, "Organizer division_metrics.py changed")
    tree = ast.parse(METRIC_SOURCE.read_text())
    names = {"SCORE_DIVISION_WEIGHT", "COUNT_COLUMNS", "_jaccard", "summarise"}
    selected = []
    for node in tree.body:
        name = (node.name if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else
                node.target.id if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                else None)
        if name in names:
            selected.append(node)
            names.remove(name)
    require(not names, f"Missing pinned organiser summarise dependency: {names}")
    namespace = {"warnings": warnings}
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])),
                 str(METRIC_SOURCE), "exec"), namespace)
    require(namespace["SCORE_DIVISION_WEIGHT"] == 0.1, "Organizer score weight changed")
    return namespace["summarise"]


def frozen_ids(assignment, direction):
    return [name for chunk in assignment["directions"][direction]["chunks"] for name in chunk]


def local_inputs():
    """Reject absent or changed verified receipts before any SSH call."""
    assignment = pinned_json(ASSIGNMENT, ASSIGNMENT_SHA)
    require(assignment["canonical_cohort_manifest_sha256"] == COHORT_SHA,
            "Frozen cohort changed")
    exp209 = pinned_json(EXP209_VERIFY, EXP209_VERIFY_SHA)
    require(exp209["status"] == "VERIFIED_EXP209_RECONSTRUCTED175_CURRENT_ORGANIZER_V1" and
            exp209["rows"] == 175 and close(exp209["current_score"], EXP209_SCORE) and
            exp209["graph_identity"].startswith("new reconstructed graphs"),
            "EXP209 comparison changed")
    exp234 = pinned_json(EXP234_VERIFY, EXP234_VERIFY_SHA)
    require(close(exp234["verification"]["baseline"], EXP214_SCORE),
            "Current-organizer EXP214 comparison changed")
    baseline_paths = [ROOT / "work/exp227_target6bba_scorer_local_v4_20260927/baseline_reference.json",
                      ROOT / "work/exp236_target44b6_scorer_local_v2_20260927/baseline_reference.json"]
    baseline = pinned_json(baseline_paths[0], BASELINE_SHA)
    require(sha(baseline_paths[1]) == BASELINE_SHA, "Two EXP214 references differ")
    require(close(baseline["summary"]["public"]["score"], EXP214_SCORE),
            "Archived EXP214 baseline score changed")
    archive_rows = baseline["rows"]["public"]
    require(len(archive_rows) == len({r["dataset"] for r in archive_rows}) == 175,
            "Archived EXP214 rows are not all175")
    archive = {row["dataset"]: row for row in archive_rows}
    require(set(archive) == set(frozen_ids(assignment, "44b6")) | set(frozen_ids(assignment, "6bba")),
            "Archived EXP214 IDs differ from frozen cohort")
    folds = {}
    for name, spec in FOLDS.items():
        verified = pinned_json(spec["verify"], spec["verify_sha"])
        require(verified["status"] == spec["verify_status"] and
                verified["rows"] == spec["n"] and
                verified["baseline_replay"] == "PASS_1e-12" and
                verified["target_labels_read_after_graph_gate"] is True and
                verified["kaggle_post"] is False and
                verified["evidence_class"] == EVIDENCE_CLASS and
                verified["result_sha256"] == spec["expected_result_sha"],
                f"{name} verified score receipt changed")
        stage = pinned_json(spec["stage"], verified["stage_receipt_sha256"])
        launch = pinned_json(spec["launch"], verified["launch_receipt_sha256"])
        coordinator = pinned_json(spec["coordinator"], spec["coordinator_sha"])
        require(verified["coordinator_local_sha256"] == spec["coordinator_sha"] and
                stage["coordinator_local_sha256"] == spec["coordinator_sha"] and
                stage["status"] == spec["stage_status"] and
                stage["gate_only"] == {"status": spec["gate_status"], "score": None} and
                launch["status"] == spec["launch_status"] and
                launch["stage_receipt_sha256"] == sha(spec["stage"]) and
                launch["score_config_sha256"] == stage["stage"]["score_config_sha256"] and
                launch["run"] == spec["remote_run"],
                f"{name} scorer stage/launch chain changed")
        require(coordinator["status"] == spec["coordinator_status"] and
                coordinator["movie_count"] == coordinator["graph_count"] == spec["n"] and
                coordinator["all_leases_released"] is True and
                coordinator["target_labels_read"] is False and
                coordinator["target_score_computed"] is False,
                f"{name} no-label coordinator changed")
        config = stage["config"]
        ids = frozen_ids(assignment, spec["assignment_direction"])
        require(len(ids) == len(set(ids)) == spec["n"] and
                all(movie.startswith(spec["prefix"]) for movie in ids) and
                config["target_ids"] == ids and
                [movie for chunk in coordinator["frozen"]["chunks"] for movie in chunk] == ids,
                f"{name} IDs differ from frozen assignment")
        require(config["assignment_sha256"] == coordinator["frozen"]["assignment_sha256"] == ASSIGNMENT_SHA and
                config["cohort_sha256"] == COHORT_SHA and
                config["baseline_metrics_sha256"] == BASELINE_SHA and
                config["baseline_input_hashes"] == baseline["input_hashes"]["public"] and
                config["current_metrics_sha256"] == METRIC_SHA and
                config["current_division_sha256"] == DIVISION_SHA and
                config["tracksdata_commit"] == TRACKSDATA_COMMIT and
                config["coordinator_sha256"] == spec["coordinator_sha"] and
                config["evidence_class"] == EVIDENCE_CLASS and
                config["output"] == spec["remote_run"] + "/output" and
                stage["stage"]["code"] == spec["remote_code"],
                f"{name} metric/config pin changed")
        target_archive = [row for row in archive_rows if row["dataset"] in set(ids)]
        require(digest(target_archive) == config["baseline_target_rows_sha256"],
                f"{name} archived baseline row digest changed")
        graph_hashes = [row for chunk in coordinator["chunks"]
                        for row in chunk["postrun"]["gate"]["graph_hashes"]]
        require(len(graph_hashes) == spec["n"] and
                [row["dataset"] for row in graph_hashes] == ids and
                all(set(row) == {"dataset", "csv_sha256", "receipt_sha256"} for row in graph_hashes),
                f"{name} coordinator graph hashes changed")
        if name == "exp227_target6bba":
            audit = coordinator["successor_audit"]
            require(verified["successor_actual_attempt"] == audit["actual_attempt"] == 1 and
                    verified["successor_actual_lease_id"] == audit["actual_lease_id"] ==
                    "exp227-target6bba-chunk07-v3a01-20260927" and
                    verified["successor_launch_result_sha256"] ==
                    audit["attempt_receipts"]["result_sha256"] ==
                    "800c78e010bef37eac0f6f167f9ddb28fca819577b2aa41c6a1092c30599b9bf" and
                    config["final_graph_hashes_sha256"] == digest(graph_hashes),
                    "EXP227 v3 attempt1 or graph digest changed")
        folds[name] = {"spec": spec, "verified": verified, "stage": stage,
                       "launch": launch, "coordinator": coordinator,
                       "graph_hashes": graph_hashes, "ids": ids}
    require(not set(folds["exp227_target6bba"]["ids"]) &
            set(folds["exp236_target44b6"]["ids"]), "Fold IDs overlap")
    require(len(set(folds["exp227_target6bba"]["ids"]) |
                set(folds["exp236_target44b6"]["ids"])) == 175,
            "Fold union is not all175")
    return folds, archive, baseline, assignment


def remote_probe_source(specs):
    """Return the bounded, JSON-only remote readback program."""
    return '''import hashlib,json,pathlib
specs=json.loads(@@SPECS@@)
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
out={}
for name,s in specs.items():
 code=pathlib.Path(s['code']);output=pathlib.Path(s['output'])
 assert sha(code/'code_manifest.json')==s['manifest_sha']
 manifest=json.loads((code/'code_manifest.json').read_text())
 for part,digest in manifest.items():
  path=(code/part).resolve()
  assert path.is_relative_to(code.resolve()) and sha(path)==digest,part
 assert sha(code/'score_config.json')==s['config_sha']
 assert {p.name for p in output.iterdir()}=={'no_metric_gate.json','label_tree_hashes.json','result.json'}
 gate=output/'no_metric_gate.json';result=output/'result.json';labels=output/'label_tree_hashes.json'
 assert sha(gate)==s['gate_sha'] and sha(result)==s['result_sha']
 data=json.loads(result.read_text())
 assert data['label_tree_hashes_sha256']==sha(labels)
 out[name]={'config':json.loads((code/'score_config.json').read_text()),
            'gate':json.loads(gate.read_text()),'result':data,
            'manifest_sha256':sha(code/'code_manifest.json'),
            'config_sha256':sha(code/'score_config.json'),
            'gate_sha256':sha(gate),'result_sha256':sha(result),
            'label_tree_hashes_sha256':sha(labels)}
print(json.dumps(out))
'''.replace("@@SPECS@@", repr(json.dumps(specs)))


def fetch_remote(folds):
    """Fetch exact JSON outputs; probe reads no image, graph CSV, or GEFF."""
    specs = {name: {"code": fold["spec"]["remote_code"],
                    "output": fold["spec"]["remote_run"] + "/output",
                    "manifest_sha": fold["stage"]["stage"]["manifest_sha256"],
                    "config_sha": fold["stage"]["stage"]["score_config_sha256"],
                    "gate_sha": fold["verified"]["gate_sha256"],
                    "result_sha": fold["verified"]["result_sha256"]}
             for name, fold in folds.items()}
    source = remote_probe_source(specs)
    process = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                              "nsu-quadro", "python3 -"], input=source,
                             text=True, capture_output=True, timeout=90)
    require(process.returncode == 0, f"Read-only remote probe failed: {process.stderr[-1200:]}")
    return json.loads(process.stdout)


def summary_matches(actual, expected, n):
    require(actual["n"] == expected["n"] == n and
            set(actual) == set(expected) and
            all(close(actual[key], expected[key]) for key in expected),
            "Fold current-organizer summary does not replay")


def validate_remote_fold(name, fold, payload, archive, summarise):
    spec, verified, stage = fold["spec"], fold["verified"], fold["stage"]
    config, gate, result = payload["config"], payload["gate"], payload["result"]
    require(config == stage["config"] and
            payload["manifest_sha256"] == stage["stage"]["manifest_sha256"] and
            payload["config_sha256"] == stage["stage"]["score_config_sha256"] and
            payload["gate_sha256"] == verified["gate_sha256"] and
            payload["result_sha256"] == verified["result_sha256"] and
            payload["label_tree_hashes_sha256"] == result["label_tree_hashes_sha256"],
            f"{name} remote source/output hashes changed")
    require(gate["status"] == spec["gate_status"] and
            gate["candidate_count"] == gate["baseline_count"] == spec["n"] and
            gate["target_labels_read"] is False and
            gate["graph_hashes"] == fold["graph_hashes"] and
            gate["baseline_hashes"] == config["baseline_input_hashes"] and
            gate["coordinator_sha256"] == spec["coordinator_sha"] and
            gate["current_metrics_sha256"] == METRIC_SHA and
            gate["current_division_sha256"] == DIVISION_SHA and
            gate["tracksdata_commit"] == TRACKSDATA_COMMIT and
            len(gate["live_release"]) == len(fold["coordinator"]["chunks"]) and
            all(row["state"] == "RELEASED" for row in gate["live_release"]),
            f"{name} durable no-metric gate changed")
    require(result["status"] == spec["result_status"] and
            result["baseline_replay"] == "PASS_1e-12" and
            result["target_labels_read_after_graph_gate"] is True and
            result["evidence_class"] == EVIDENCE_CLASS and
            result["no_metric_gate_sha256"] == verified["gate_sha256"] and
            result["metric_source"] == "current organizer commit " + METRIC_COMMIT and
            result["current_metrics_sha256"] == METRIC_SHA and
            result["current_division_sha256"] == DIVISION_SHA,
            f"{name} scored result provenance changed")
    ids = set(fold["ids"])
    for key in ("legacy_exp214_baseline_rows", "baseline_rows", "candidate_rows"):
        rows = result[key]
        require(len(rows) == len({r["dataset"] for r in rows}) == spec["n"] and
                {r["dataset"] for r in rows} == ids,
                f"{name} {key} ID coverage changed")
        require(all(math.isfinite(float(r["edge_tp"])) and
                    math.isfinite(float(r["adj_edge_jaccard"])) for r in rows),
                f"{name} {key} has invalid sufficient statistics")
    for row in result["legacy_exp214_baseline_rows"]:
        rows_close(row, archive[row["dataset"]])
    old_summary = summarise(result["baseline_rows"])
    new_summary = summarise(result["candidate_rows"])
    summary_matches(old_summary, result["baseline_summary"], spec["n"])
    summary_matches(new_summary, result["candidate_summary"], spec["n"])
    require(close(old_summary["score"], verified["baseline_score"]) and
            close(new_summary["score"], verified["official_score"]) and
            close(new_summary["score"] - old_summary["score"],
                  verified["delta_vs_current_baseline"]),
            f"{name} independently verified fold score changed")
    return result


def combine(folds, archive, baseline, assignment, remote, summarise):
    require(set(remote) == set(FOLDS), "Remote fold keys changed")
    results = {name: validate_remote_fold(name, folds[name], remote[name], archive, summarise)
               for name in FOLDS}
    candidate = sorted((row for result in results.values() for row in result["candidate_rows"]),
                       key=lambda row: row["dataset"])
    paired_base = sorted((row for result in results.values() for row in result["baseline_rows"]),
                         key=lambda row: row["dataset"])
    historical = sorted((row for result in results.values()
                         for row in result["legacy_exp214_baseline_rows"]),
                        key=lambda row: row["dataset"])
    ids = [row["dataset"] for row in candidate]
    require(len(ids) == len(set(ids)) == 175 and
            ids == sorted(archive) and
            [row["dataset"] for row in paired_base] == ids and
            [row["dataset"] for row in historical] == ids,
            "Pooled rows are not the exact frozen 175 IDs")
    candidate_summary = summarise(candidate)
    baseline_summary = summarise(paired_base)
    historical_summary = summarise(historical)
    require(candidate_summary["n"] == baseline_summary["n"] ==
            historical_summary["n"] == 175 and
            close(baseline_summary["score"], EXP214_SCORE) and
            close(historical_summary["score"], EXP214_SCORE),
            "Pooled EXP214 baseline does not replay")
    graph_hashes = sorted((row for fold in folds.values() for row in fold["graph_hashes"]),
                          key=lambda row: row["dataset"])
    require([row["dataset"] for row in graph_hashes] == ids,
            "Pooled graph hash lineage does not cover exact IDs")
    score = candidate_summary["score"]
    return {
        "status": "VERIFIED_EXP227_EXP236_CURRENT175_POOLED_READ_ONLY",
        "evidence_class": EVIDENCE_CLASS,
        "interpretation": "historically exposed reciprocal development estimate; not untouched OOF or hidden Kaggle validation",
        "metric_source": "current organizer commit " + METRIC_COMMIT,
        "current_metrics_sha256": METRIC_SHA,
        "current_division_sha256": DIVISION_SHA,
        "tracksdata_commit": TRACKSDATA_COMMIT,
        "assignment_sha256": ASSIGNMENT_SHA,
        "cohort_sha256": COHORT_SHA,
        "movie_count": 175,
        "fold_counts": {name: folds[name]["spec"]["n"] for name in FOLDS},
        "fold_verification_receipt_sha256": {name: folds[name]["spec"]["verify_sha"] for name in FOLDS},
        "fold_result_sha256": {name: folds[name]["verified"]["result_sha256"] for name in FOLDS},
        "fold_gate_sha256": {name: folds[name]["verified"]["gate_sha256"] for name in FOLDS},
        "pooled_graph_hashes_sha256": digest(graph_hashes),
        "pooled_candidate_rows_sha256": digest(candidate),
        "pooled_baseline_rows_sha256": digest(paired_base),
        "pooled_historical_exp214_rows_sha256": digest(historical),
        "candidate_summary": candidate_summary,
        "paired_exp214_current_summary": baseline_summary,
        "exp214_historical_rows_current_summarise": historical_summary,
        "score": score,
        "exp214_paired_baseline_score": baseline_summary["score"],
        "delta_vs_exp214_paired": score - baseline_summary["score"],
        "exp209_reconstructed_score": EXP209_SCORE,
        "exp209_reconstructed_verify_sha256": EXP209_VERIFY_SHA,
        "delta_vs_exp209_reconstructed": score - EXP209_SCORE,
        "target_geff_read_by_combiner": False,
        "remote_mutation": False,
        "kaggle_post": False,
    }


def run(*, write_receipt=False, remote_payload=None):
    require(not write_receipt or not OUTPUT.exists(),
            "Existing pooled receipt requires reconciliation")
    folds, archive, baseline, assignment = local_inputs()
    summarise = organizer_summarise()
    remote = fetch_remote(folds) if remote_payload is None else remote_payload
    receipt = combine(folds, archive, baseline, assignment, remote, summarise)
    if write_receipt:
        with OUTPUT.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true",
                        help="One-shot local pooled receipt after reviewed check-only run")
    args = parser.parse_args()
    receipt = run(write_receipt=args.write_receipt)
    print(json.dumps({"status": receipt["status"], "mode":
                      "WRITE_RECEIPT" if args.write_receipt else "CHECK_ONLY",
                      "score": receipt["score"],
                      "baseline": receipt["exp214_paired_baseline_score"],
                      "delta": receipt["delta_vs_exp214_paired"],
                      "exp209_reconstructed_score": receipt["exp209_reconstructed_score"],
                      "pooled_graph_hashes_sha256": receipt["pooled_graph_hashes_sha256"]}))


if __name__ == "__main__":
    main()
