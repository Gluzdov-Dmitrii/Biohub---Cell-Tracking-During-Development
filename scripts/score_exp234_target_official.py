"""Official EXP234 target175 score, after all frozen no-label chunks are released."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, rows_close, score_one


SOURCES = ("44b6", "6bba")
CHUNKS = {"44b6": 8, "6bba": 4}
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path, expected):
    assert sha(path) == expected, str(path)


def released(state, run, code, plan_path, plan_sha, status):
    """Check the independently observed process and queue state for one chunk."""
    assert state["monitor_status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert state["queue"]["state"] == "RELEASED"
    assert state["exit"]["returncode"] == 0 and state["exit"]["hard_timeout"] is False
    assert state["identity_alive"] is False and state["group_alive"] is False
    assert state["gpu_pids"] == []
    assert state["status"] == status
    launch = state["launch"]
    assert launch["config"]["run"] == str(run)
    assert launch["config"]["code"] == str(code)
    assert launch["config"]["script"] == "run_exp234_target_chunk.py"
    assert launch["config"]["arguments"] == [str(plan_path), "--plan-sha256", plan_sha]
    assert state["queue"]["id"] == launch["config"]["lease_id"]
    assert json.loads((run / "exit.json").read_text()) == state["exit"]
    assert json.loads((run / "launch.json").read_text()) == launch


def checked_graphs(path, expected, cohort):
    graphs = read_graphs(path)
    assert set(graphs) == set(expected)
    for name, graph in graphs.items():
        shape = cohort[name]["shape"]
        assert len(shape) == 4
        for point in graph["nodes"].values():
            assert all(float(value) == int(value) and 0 <= value < limit
                       for value, limit in zip(point, shape)), name
    return graphs


def gate(config):
    code = Path(config["inference_code"])
    pinned(code / "code_manifest.json", config["inference_manifest_sha256"])
    manifest = json.loads((code / "code_manifest.json").read_text())
    for name, digest in manifest.items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve())
        pinned(path, digest)
    pinned(config["assignment"], config["assignment_sha256"])
    assignment = json.loads(Path(config["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["thresholds_selected"] is False
    pinned(config["cohort"], config["cohort_sha256"])
    cohort_rows = json.loads(Path(config["cohort"]).read_text())["rows"]
    cohort = {row["dataset"]: row for row in cohort_rows}
    assert len(cohort_rows) == len(cohort) == 175
    assert sum(name.startswith("44b6_") for name in cohort) == 59
    assert sum(name.startswith("6bba_") for name in cohort) == 116
    pinned(config["release_manifest"], config["release_manifest_sha256"])
    releases = json.loads(Path(config["release_manifest"]).read_text())
    assert releases["status"] == "PASS_EXP234_ALL_CHUNKS_VERIFIED_RELEASED"
    assert len(releases["entries"]) == 12

    selections = {}
    for source in SOURCES:
        item = config["source_selection"][source]
        pinned(item["result"], item["result_sha256"])
        pinned(item["gate"], item["gate_sha256"])
        result = json.loads(Path(item["result"]).read_text())
        assert result["status"] == "PASS_EXP234_SOURCE_THRESHOLD_SELECTED"
        assert result["source_embryo"] == source
        assert result["selected_threshold"] == item["selected_threshold"]
        assert result["no_metric_gate_sha256"] == item["gate_sha256"]
        selections[source] = item["selected_threshold"]

    candidate = {}
    prediction_hashes = []
    for source in SOURCES:
        chunks = assignment["directions"][source]["chunks"]
        assert len(chunks) == CHUNKS[source]
        assert assignment["directions"][source]["target_embryo"] == (
            "6bba" if source == "44b6" else "44b6")
        for index, movies in enumerate(chunks):
            token = f"{source}_chunk{index:02d}"
            plan_path = code / f"{token}_plan.json"
            plan_sha = sha(plan_path)
            plan = json.loads(plan_path.read_text())
            assert plan["experiment"] == "EXP234_TARGET_CHUNK"
            assert plan["source_embryo"] == source and plan["chunk_index"] == index
            assert plan["chunk_count"] == CHUNKS[source]
            assert plan["selected_threshold"] == selections[source]
            assert plan["assignment_sha256"] == config["assignment_sha256"]
            assert plan["cohort_sha256"] == config["cohort_sha256"]
            assert plan["source_selection_result_sha256"] == (
                config["source_selection"][source]["result_sha256"])
            pinned(plan["movies"], plan["movies_sha256"])
            assert json.loads(Path(plan["movies"]).read_text()) == movies
            run = Path(plan["output"]).parent
            status_path = run / "output/status.json"
            status = json.loads(status_path.read_text())
            assert status["status"] == "PASS_EXP234_TARGET_CHUNK_NO_LABELS"
            assert status["source_embryo"] == source and status["chunk_index"] == index
            assert status["movies"] == movies
            assert status["selected_threshold"] == selections[source]
            assert status["plan_sha256"] == plan_sha
            assert status["source_selection_result_sha256"] == plan["source_selection_result_sha256"]
            assert status["target_labels_read"] is False
            released(releases["entries"][token], run, code, plan_path, plan_sha, status)
            receipt_path = run / "output/inference_receipt.json"
            csv_path = run / "output/submission.csv"
            pinned(receipt_path, status["receipt_sha256"])
            pinned(csv_path, status["csv_sha256"])
            receipt = json.loads(receipt_path.read_text())
            assert receipt["status"] == "PASS_FROZEN_PUBLIC_FAMILY_INFERENCE"
            assert receipt["target_labels_read"] is False
            assert receipt["movies"] == movies
            assert receipt["submission_sha256"] == status["csv_sha256"]
            assert receipt["override_env"] == {"BIOHUB_DET_THRESHOLD": selections[source]}
            assert receipt["notebook_sha256"] == config["notebook_sha256"]
            assert len(movies) in (14, 15)
            assert set(movies) <= set(cohort)
            graphs = checked_graphs(csv_path, movies, cohort)
            assert not set(candidate).intersection(graphs)
            candidate.update(graphs)
            prediction_hashes.append({"token": token, "plan_sha256": plan_sha,
                                      "status_sha256": sha(status_path),
                                      "csv_sha256": status["csv_sha256"],
                                      "receipt_sha256": status["receipt_sha256"]})
    assert len(candidate) == 175 and set(candidate) == set(cohort)

    pinned(config["baseline_metrics"], config["baseline_metrics_sha256"])
    baseline = json.loads(Path(config["baseline_metrics"]).read_text())
    assert baseline["status"] == "PASS_HONEST_PAIRED_CV"
    assert abs(baseline["summary"]["public"]["score"] - 0.7427291486246141) < 1e-12
    baseline_rows = {row["dataset"]: row for row in baseline["rows"]["public"]}
    assert len(baseline_rows) == 175 and set(baseline_rows) == set(cohort)
    old_graphs = {}
    baseline_hashes = []
    for part in baseline["input_hashes"]["public"]:
        csv_path = Path(part["csv"])
        pinned(csv_path, part["sha256"])
        receipt_path = csv_path.parent / "inference_receipt.json"
        pinned(receipt_path, part["receipt_sha256"])
        receipt = json.loads(receipt_path.read_text())
        assert receipt["submission_sha256"] == part["sha256"]
        graphs = checked_graphs(csv_path, receipt["movies"], cohort)
        assert not set(old_graphs).intersection(graphs)
        old_graphs.update(graphs)
        baseline_hashes.append(part)
    assert len(baseline_hashes) == 8 and set(old_graphs) == set(cohort)
    return cohort, candidate, old_graphs, baseline_rows, baseline, {
        "status": "PASS_EXP234_ALL_175_GRAPHS_BEFORE_LABEL_ACCESS",
        "candidate_count": 175, "baseline_count": 175,
        "cohort_sha256": config["cohort_sha256"],
        "assignment_sha256": config["assignment_sha256"],
        "release_manifest_sha256": config["release_manifest_sha256"],
        "source_selection": config["source_selection"],
        "prediction_hashes": prediction_hashes,
        "baseline_hashes": baseline_hashes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    pinned(args.config, args.config_sha256)
    config = json.loads(args.config.read_text())
    assert config["experiment"] == "EXP234_OFFICIAL_TARGET175"
    cohort, candidate, old_graphs, baseline_rows, baseline, gate_receipt = gate(config)
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "no_metric_gate.json").write_text(json.dumps(gate_receipt, indent=2) + "\n")

    evaluator_pins(json.loads(Path(config["evaluator_config"]).read_text()))
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    old_rows, new_rows = [], []
    for name in sorted(cohort):
        movie = cohort[name]
        dataset = open_dataset(movie["zarr"], require_tracks=True, load_image=False)
        estimate = (GeffMetadata.read(Path(config["data_dir"]) / (name + ".geff")).extra or {}).get(
            "estimated_number_of_nodes")
        assert estimate is not None and float(estimate) > 0
        old = score_one(name, old_graphs[name], dataset, estimate, evaluate,
                        node_recall, per_sample_metrics, build_graph)
        rows_close(old, baseline_rows[name], tol=1e-12)
        old_rows.append(old)
        new_rows.append(score_one(name, candidate[name], dataset, estimate, evaluate,
                                  node_recall, per_sample_metrics, build_graph))
        print(json.dumps({"scored_movie": name}), flush=True)
    old_summary = summarise(old_rows)
    rows_close(old_summary, baseline["summary"]["public"], tol=1e-12)
    new_summary = summarise(new_rows)
    by_embryo = {prefix: summarise([r for r in new_rows if r["dataset"].startswith(prefix + "_")])
                 for prefix in SOURCES}
    result = {"status": "PASS_EXP234_SOURCE_SELECTED_TARGET175",
              "evidence_class": "prospective source selection on historically exposed embryo domains; development-adapted, not pristine unbiased OOF",
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "baseline_replay": "PASS_1e-12", "baseline_summary": old_summary,
              "candidate_summary": new_summary, "candidate_by_embryo": by_embryo,
              "delta_vs_exp214": new_summary["score"] - old_summary["score"],
              "rows": new_rows}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "score": new_summary["score"],
                      "delta": result["delta_vs_exp214"]}), flush=True)


if __name__ == "__main__":
    main()
