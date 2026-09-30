"""Torch-free current-metric EXP227 scorer after all 116 graph/release gates.

The source44 checkpoint was selected on source-inner movies. The target
evaluation is embryo-disjoint in model training/selection, but these embryo
labels were historically exposed elsewhere in the research program.
"""
import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, rows_close, score_one
from score_current_metric_lightweight import (
    IMAGE_AUDIT_SHA, TRACKSDATA_COMMIT, build_graph, image_metadata,
    label_manifest, runtime_gate,
)


REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
QUEUE = "/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
CHECKPOINT_SHA = "df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79"
COHORT_SHA = "001c07019077794c1c33706cba5d0178f464aad07cf985650b2d55c3ebaa72d4"
BASELINE_SHA = "c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5"
CURRENT_METRICS_SHA = "cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444"
CURRENT_DIVISION_SHA = "0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, digest):
    assert sha(path) == digest, str(path)


def state_digest(value):
    body = {key: item for key, item in value.items() if key != "state_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def live_queue():
    result = subprocess.run(["python3", QUEUE, "status"], capture_output=True, text=True,
                            check=True, timeout=30)
    return json.loads(result.stdout)


def checked_graph(path, name, shape, expected_nodes=None, expected_edges=None):
    graphs = read_graphs(path)
    assert set(graphs) == {name}, (path, set(graphs))
    graph = graphs[name]
    if expected_nodes is not None:
        assert len(graph["nodes"]) == expected_nodes
    if expected_edges is not None:
        assert len(graph["edges"]) == expected_edges
    assert len(shape) == 4 and all(isinstance(n, int) and n > 0 for n in shape)
    for point in graph["nodes"].values():
        assert all(math.isfinite(float(value)) and float(value) == int(value)
                   and 0 <= value < limit for value, limit in zip(point, shape)), name
    return graph


def _manifest(code, digest):
    pinned(code / "code_manifest.json", digest)
    files = json.loads((code / "code_manifest.json").read_text())
    assert isinstance(files, dict) and files
    for name, item_sha in files.items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve()) and path.is_file()
        pinned(path, item_sha)


def current_import_gate(config):
    """Fail before label access if the pinned current evaluator cannot import."""
    return runtime_gate(config, CURRENT_METRICS_SHA, CURRENT_DIVISION_SHA)


def _baseline(config, cohort):
    pinned(config["baseline_metrics"], config["baseline_metrics_sha256"])
    baseline = json.loads(Path(config["baseline_metrics"]).read_text())
    assert baseline["status"] == "PASS_HONEST_PAIRED_CV"
    assert abs(baseline["summary"]["public"]["score"] - 0.7427291486246141) <= 1e-12
    rows = baseline["rows"]["public"]
    baseline_rows = {row["dataset"]: row for row in rows}
    assert len(rows) == len(baseline_rows) == 175 and set(baseline_rows) == set(cohort)
    target_rows = [row for row in rows if row["dataset"] in set(config["target_ids"])]
    assert len(target_rows) == 116
    target_sha = hashlib.sha256(json.dumps(target_rows, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    assert target_sha == config["baseline_target_rows_sha256"]
    old = {}
    hashes = []
    for part in baseline["input_hashes"]["public"]:
        csv_path = Path(part["csv"])
        pinned(csv_path, part["sha256"])
        receipt_path = csv_path.parent / "inference_receipt.json"
        pinned(receipt_path, part["receipt_sha256"])
        receipt = json.loads(receipt_path.read_text())
        assert receipt["submission_sha256"] == part["sha256"]
        graphs = read_graphs(csv_path)
        assert set(graphs) == set(receipt["movies"])
        assert not set(old).intersection(graphs)
        old.update(graphs)
        hashes.append(part)
    assert len(hashes) == 8 and set(old) == set(cohort)
    assert hashes == config["baseline_input_hashes"]
    assert len([part for part in hashes if "_6bba_" in part["csv"]]) == 3
    return {name: old[name] for name in config["target_ids"]}, baseline_rows, baseline, hashes


def gate(config, queue_state=None):
    """All checks here are label-free. This function never touches GEFF paths."""
    assert config["experiment"] == "EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3"
    assert config["evidence_class"] == "leakage-controlled reciprocal evaluation; historically exposed target labels"
    assert config["assignment_sha256"] == ASSIGNMENT_SHA
    assert config["checkpoint_sha256"] == CHECKPOINT_SHA
    assert config["cohort_sha256"] == COHORT_SHA
    assert config["baseline_metrics_sha256"] == BASELINE_SHA
    assert config["current_metrics_sha256"] == CURRENT_METRICS_SHA
    assert config["current_division_sha256"] == CURRENT_DIVISION_SHA
    assert config["tracksdata_commit"] == TRACKSDATA_COMMIT
    assert config["image_scale_audit_sha256"] == IMAGE_AUDIT_SHA
    assert Path(sys.executable).resolve() == Path(config["python"]).resolve()
    assert sys.prefix != sys.base_prefix
    pinned(config["current_metrics"], CURRENT_METRICS_SHA)
    pinned(config["current_division"], CURRENT_DIVISION_SHA)
    assert Path(config["current_metrics"]).parent == Path(config["current_division"]).parent
    pinned(config["assignment"], ASSIGNMENT_SHA)
    assignment = json.loads(Path(config["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["target_labels_read"] is False and assignment["thresholds_selected"] is False
    chunks = assignment["directions"]["44b6"]["chunks"]
    assert assignment["directions"]["44b6"]["target_embryo"] == "6bba"
    assert assignment["directions"]["44b6"]["movie_count"] == 116
    assert len(chunks) == 8 and [len(group) for group in chunks] == [15] * 4 + [14] * 4
    names = [name for group in chunks for name in group]
    assert len(names) == len(set(names)) == 116
    assert all(name.startswith("6bba_") and len(name) == 13 for name in names)
    assert config["target_ids"] == names
    pinned(config["selection"], config["selection_sha256"])
    selection = json.loads(Path(config["selection"]).read_text())
    assert selection["status"] == "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT"
    assert selection["selected_epoch"] == 10 and selection["target_labels_read"] is False
    assert selection["checkpoint_sha256"] == CHECKPOINT_SHA
    assert selection["scores"]["10"] > selection["scores"]["20"]
    pinned(config["coordinator"], config["coordinator_sha256"])
    coordinator = json.loads(Path(config["coordinator"]).read_text())
    assert coordinator["state_sha256"] == state_digest(coordinator)
    assert coordinator["status"] == "PASS_EXP227_TARGET6BBA_116_GRAPHS_NO_LABELS_RELEASED"
    assert coordinator["movie_count"] == coordinator["graph_count"] == 116
    assert coordinator["all_leases_released"] is True
    assert coordinator["target_labels_read"] is False and coordinator["target_score_computed"] is False
    assert coordinator["frozen"]["assignment_sha256"] == ASSIGNMENT_SHA
    assert coordinator["frozen"]["selection_sha256"] == config["selection_sha256"]
    assert coordinator["frozen"]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert coordinator["frozen"]["prereg_sha256"] == selection["prereg_sha256"]
    assert coordinator["frozen"]["chunks"] == chunks
    assert len(coordinator["chunks"]) == 8
    pinned(config["cohort"], COHORT_SHA)
    cohort_rows = json.loads(Path(config["cohort"]).read_text())["rows"]
    cohort = {row["dataset"]: row for row in cohort_rows}
    assert len(cohort_rows) == len(cohort) == 175
    assert {name for name in cohort if name.startswith("6bba_")} == set(names)
    pinned(config["evaluator_config"], config["evaluator_config_sha256"])
    queue_state = live_queue() if queue_state is None else queue_state
    requests = queue_state["requests"]
    assert isinstance(requests, list)
    candidate, graph_hashes, release_rows = {}, [], []
    for index, movies in enumerate(chunks):
        token = f"exp227_target6bba_chunk{index:02d}_v1_20260927"
        code = Path(REMOTE) / "code" / token
        run = Path(REMOTE) / "runs" / token
        entry = coordinator["chunks"][index]
        assert entry["stage"]["validated"] is True
        assert entry["launch"]["validated"] is True
        assert entry["postrun"]["validated"] is True
        stage = entry["stage"]["result"]
        post = entry["postrun"]["gate"]
        assert stage["code"] == str(code) and stage["run"] == str(run)
        assert stage["movies"] == movies and stage["checkpoint_sha256"] == CHECKPOINT_SHA
        assert stage["selection_sha256"] == config["selection_sha256"]
        assert stage["lease_id"] == f"exp227-target6bba-chunk{index:02d}-v1-20260927"
        assert post["status"] == "PASS_EXP227_TARGET6BBA_CHUNK_POSTRUN_NO_LABELS"
        assert post["chunk_index"] == index and post["movies"] == movies
        assert post["target_labels_read"] is False and post["queue_state_in_control"] == "RELEASED"
        for key in ("manifest_sha256", "plan_sha256", "checkpoint_sha256"):
            assert post[key] == stage[key]
        assert [row["dataset"] for row in post["graph_hashes"]] == movies
        _manifest(code, stage["manifest_sha256"])
        plan_path = code / "plan.json"
        pinned(plan_path, stage["plan_sha256"])
        plan = json.loads(plan_path.read_text())
        assert plan["experiment"] == "EXP227_TARGET6BBA_CHUNK"
        assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
        assert plan["chunk_index"] == index and plan["chunk_count"] == 8
        assert plan["movies"] == movies and plan["assignment_sha256"] == ASSIGNMENT_SHA
        assert plan["selection_sha256"] == config["selection_sha256"]
        assert plan["checkpoint_sha256"] == CHECKPOINT_SHA and plan["checkpoint_epoch"] == 10
        assert plan["checkpoint"] == selection["checkpoint"]
        assert plan["data_root"] == REMOTE + "/data/exp213_source_view_20260912"
        assert sha(plan["assignment"]) == ASSIGNMENT_SHA
        assert sha(plan["selection"]) == config["selection_sha256"]
        assert Path(plan["code"]).resolve() == code.resolve()
        assert Path(plan["output"]).resolve() == (run / "output").resolve()
        for filename, key in (("exit.json", "exit_sha256"),
                              ("supervision/complete.json", "supervision_sha256"),
                              ("supervision/control.json", "control_sha256"),
                              ("output/status.json", "status_sha256")):
            pinned(run / filename, post[key])
        exit_record = json.loads((run / "exit.json").read_text())
        supervision = json.loads((run / "supervision/complete.json").read_text())
        control = json.loads((run / "supervision/control.json").read_text())
        assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
        assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT" and supervision["exit"] == exit_record
        assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
        assert control["queue"]["id"] == stage["lease_id"]
        assert control["queue"]["run_path"] == str(run)
        live = [row for row in requests if row["id"] == stage["lease_id"]]
        assert len(live) == 1 and live[0]["state"] == "RELEASED" and live[0]["run_path"] == str(run)
        assert live[0]["owner"] == "biohub-agent"
        release_rows.append({"chunk_index": index, "lease_id": stage["lease_id"], "run": str(run),
                             "state": live[0]["state"]})
        status = json.loads((run / "output/status.json").read_text())
        assert status["status"] == f"PASS_EXP227_TARGET6BBA_CHUNK{index:02d}_NO_LABELS"
        assert status["target_labels_read"] is False and status["movies"] == movies
        assert status["chunk_index"] == index and status["assignment_sha256"] == ASSIGNMENT_SHA
        assert status["selection_sha256"] == config["selection_sha256"]
        assert status["checkpoint_sha256"] == CHECKPOINT_SHA
        assert status["plan_sha256"] == stage["plan_sha256"]
        assert len(status["records"]) == len(movies)
        output = run / "output"
        expected = {"status.json"} | {"graph__" + name + suffix for name in movies
                                      for suffix in (".csv", ".json")}
        assert {path.name for path in output.iterdir()} == expected
        for name, record, graph_hash in zip(movies, status["records"], post["graph_hashes"]):
            csv_path = output / ("graph__" + name + ".csv")
            rec_path = csv_path.with_suffix(".json")
            shape = json.loads((Path(plan["data_root"]) / (name + ".zarr/0/zarr.json")).read_text())["shape"]
            assert record["dataset"] == name and record["shape"] == shape == cohort[name]["shape"]
            assert record["csv"] == str(csv_path)
            assert record["checkpoint_sha256"] == CHECKPOINT_SHA
            assert record["plan_sha256"] == stage["plan_sha256"]
            assert json.loads(rec_path.read_text()) == record
            pinned(csv_path, record["csv_sha256"])
            assert graph_hash == {"dataset": name, "csv_sha256": record["csv_sha256"],
                                  "receipt_sha256": sha(rec_path)}
            candidate[name] = checked_graph(csv_path, name, shape, record["nodes"], record["edges"])
            graph_hashes.append({"dataset": name, "csv_sha256": record["csv_sha256"],
                                 "receipt_sha256": graph_hash["receipt_sha256"]})
    assert len(candidate) == 116 and list(candidate) == names
    pinned(selection["checkpoint"], CHECKPOINT_SHA)
    old, baseline_rows, baseline, baseline_hashes = _baseline(config, cohort)
    runtime, contract = current_import_gate(config)
    images = image_metadata(config, cohort, names)
    gate_receipt = {"status": "PASS_EXP227_ALL_116_GRAPHS_BEFORE_LABEL_ACCESS",
                    "candidate_count": 116, "baseline_count": 116,
                    "assignment_sha256": ASSIGNMENT_SHA,
                    "selection_sha256": config["selection_sha256"],
                    "checkpoint_sha256": CHECKPOINT_SHA,
                    "coordinator_sha256": config["coordinator_sha256"],
                    "cohort_sha256": COHORT_SHA,
                    "evaluator_config_sha256": config["evaluator_config_sha256"],
                    "current_metrics_sha256": CURRENT_METRICS_SHA,
                    "current_division_sha256": CURRENT_DIVISION_SHA,
                    "tracksdata_commit": TRACKSDATA_COMMIT,
                    "runtime": runtime, "synthetic_contract": contract,
                    "image_metadata": images, "image_scale_audit_sha256": IMAGE_AUDIT_SHA,
                    "baseline_target_rows_sha256": config["baseline_target_rows_sha256"],
                    "graph_hashes": graph_hashes, "live_release": release_rows,
                    "baseline_hashes": baseline_hashes, "target_labels_read": False}
    return cohort, candidate, old, baseline_rows, baseline, gate_receipt


def score_with_labels(config, cohort, candidate, old, baseline_rows, baseline, images):
    """Only called after the no_metric_gate file is durably written."""
    evaluator_pins(json.loads(Path(config["evaluator_config"]).read_text()))
    repo = Path(config["repo"])
    sys.path.insert(0, str(repo / "src"))
    from geff import GeffMetadata
    from biohub_tracking.metrics import evaluate as legacy_evaluate
    from biohub_tracking.metrics import node_recall as legacy_node_recall
    from biohub_tracking.metrics import per_sample_metrics as legacy_per_sample_metrics
    from biohub_tracking.metrics import summarise as legacy_summarise
    import tracksdata as td
    from types import SimpleNamespace
    from current_official.metrics import evaluate, node_recall, per_sample_metrics, summarise

    def evaluate_current(graph, gt, *, scale):
        return evaluate(graph, gt, scale=scale, max_distance=7.0)

    scales = {row["dataset"]: tuple(row["scale"]) for row in images}
    legacy_rows, old_rows, new_rows = [], [], []
    for name in sorted(config["target_ids"]):
        label_path = Path(cohort[name]["zarr"]).with_suffix(".geff")
        loaded = td.graph.IndexedRXGraph.from_geff(label_path)
        gt = loaded[0] if isinstance(loaded, tuple) else loaded
        estimate = (GeffMetadata.read(label_path).extra or {}).get(
            "estimated_number_of_nodes")
        assert estimate is not None and math.isfinite(float(estimate)) and float(estimate) > 0
        dataset = SimpleNamespace(tracks=gt, scale=scales[name])
        legacy_row = score_one(name, old[name], dataset, estimate, legacy_evaluate,
                               legacy_node_recall, legacy_per_sample_metrics, build_graph)
        rows_close(legacy_row, baseline_rows[name], tol=1e-12)
        legacy_rows.append(legacy_row)
        old_rows.append(score_one(name, old[name], dataset, estimate, evaluate_current,
                                  node_recall, per_sample_metrics, build_graph))
        new_rows.append(score_one(name, candidate[name], dataset, estimate, evaluate_current,
                                  node_recall, per_sample_metrics, build_graph))
        assert old_rows[-1]["num_pred_nodes"] == baseline_rows[name]["num_pred_nodes"]
        assert new_rows[-1]["num_pred_nodes"] == len(candidate[name]["nodes"])
        print(json.dumps({"scored_movie": name}), flush=True)
    legacy_summary = legacy_summarise(legacy_rows)
    old_summary = summarise(old_rows)
    new_summary = summarise(new_rows)
    assert math.isfinite(old_summary["score"]) and math.isfinite(new_summary["score"])
    assert old_summary["n"] == new_summary["n"] == 116
    return legacy_rows, old_rows, new_rows, legacy_summary, old_summary, new_summary


def run(config, config_sha, *, queue_state=None, gate_only=False):
    pinned(config, config_sha)
    config = json.loads(Path(config).read_text())
    cohort, candidate, old, baseline_rows, baseline, gate_receipt = gate(config, queue_state)
    if gate_only:
        return gate_receipt
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    gate_path = output / "no_metric_gate.json"
    with gate_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(gate_receipt, indent=2) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    labels_before = label_manifest(cohort, config["target_ids"])
    label_path = output / "label_tree_hashes.json"
    with label_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(labels_before, indent=2) + "\n")
        stream.flush()
        import os
        os.fsync(stream.fileno())
    legacy_rows, old_rows, new_rows, legacy_summary, old_summary, new_summary = score_with_labels(
        config, cohort, candidate, old, baseline_rows, baseline, gate_receipt["image_metadata"])
    assert label_manifest(cohort, config["target_ids"]) == labels_before
    result = {"status": "PASS_EXP227_SOURCE44_TARGET6BBA_CURRENT116_V3",
              "evidence_class": config["evidence_class"],
              "no_metric_gate_sha256": sha(gate_path), "baseline_replay": "PASS_1e-12",
              "label_tree_hashes_sha256": sha(label_path),
              "metric_source": "current organizer commit 075fc5f5a52d11077f9dc2b074644618f26939e2",
              "current_metrics_sha256": CURRENT_METRICS_SHA,
              "current_division_sha256": CURRENT_DIVISION_SHA,
              "legacy_exp214_baseline_summary": legacy_summary,
              "baseline_summary": old_summary, "candidate_summary": new_summary,
              "delta_vs_current_baseline": new_summary["score"] - old_summary["score"],
              "legacy_exp214_baseline_rows": legacy_rows,
              "baseline_rows": old_rows, "candidate_rows": new_rows,
              "target_labels_read_after_graph_gate": True}
    with (output / "result.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--gate-only", action="store_true")
    args = parser.parse_args()
    result = run(args.config, args.config_sha256, gate_only=args.gate_only)
    print(json.dumps({"status": result["status"],
                      "score": result.get("candidate_summary", {}).get("score")}))


if __name__ == "__main__":
    main()
