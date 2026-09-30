"""Score all sealed EXP234 source arms, then freeze one threshold per source."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from score_exp214_paired import read_graphs
from exp234_source_scope import validate_scope


THRESHOLDS = ("0.900", "0.940", "0.965")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate(config):
    run = Path(config["run"])
    output = run / "output"
    code = Path(config["inference_code"])
    assert sha(code / "code_manifest.json") == config["inference_manifest_sha256"]
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest
    plan = json.loads((code / (config["source_embryo"] + "_plan.json")).read_text())
    assert sha(code / (config["source_embryo"] + "_plan.json")) == config["plan_sha256"]
    assert plan["experiment"] == "EXP234" and plan["source_embryo"] == config["source_embryo"]
    bundle = json.loads(Path(plan["bundle"]).read_text())
    movies = json.loads(Path(plan["movies"]).read_text())
    assert tuple(plan["thresholds"]) == THRESHOLDS
    assert sha(plan["bundle"]) == plan["bundle_sha256"]
    assert sha(plan["movies"]) == plan["movies_sha256"]
    validate_scope(bundle, movies)
    assert movies == config["expected_movies"]
    assert bundle["source_validation_movies"] == movies
    assert len(movies) == plan["movie_count"] == (8 if config["source_embryo"] == "44b6" else 11)
    assert not set(movies).intersection(bundle["source_train_movies"])
    assert not set(movies).intersection(bundle["center_seen_movies"])
    for role in ("primary", "secondary", "center"):
        assert sha(bundle[role]["path"]) == bundle[role]["sha256"], role
        assert bundle[role]["sha256"] == config["expected_model_shas"][role]
    finished = json.loads((run / "exit.json").read_text())
    assert finished["returncode"] == 0 and finished["hard_timeout"] is False
    status = json.loads((output / "status.json").read_text())
    assert status["status"] == "PASS_EXP234_SOURCE_ARMS_NO_LABELS"
    assert status["target_labels_read"] is False and status["movies"] == movies
    assert status["plan_sha256"] == config["plan_sha256"]
    assert tuple(status["thresholds"]) == THRESHOLDS
    assert len(status["records"]) == len(THRESHOLDS)
    graphs = {}
    hashes = []
    for threshold, record in zip(THRESHOLDS, status["records"]):
        assert record["threshold"] == threshold
        csv_path = output / ("threshold_" + threshold.replace(".", "")) / "submission.csv"
        receipt_path = csv_path.with_name("inference_receipt.json")
        assert Path(record["csv"]).resolve() == csv_path.resolve()
        assert sha(csv_path) == record["csv_sha256"]
        assert sha(receipt_path) == record["receipt_sha256"]
        receipt = json.loads(receipt_path.read_text())
        assert receipt["target_labels_read"] is False
        assert receipt["submission_sha256"] == record["csv_sha256"]
        assert receipt["override_env"] == {"BIOHUB_DET_THRESHOLD": threshold}
        assert receipt["movies"] == movies and receipt["bundle"] == bundle
        assert receipt["notebook_sha256"] == plan["notebook_sha256"]
        assert receipt["base_predictor_sha256"] == "c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9"
        arm_graphs = read_graphs(csv_path)
        assert set(arm_graphs) == set(movies)
        graphs[threshold] = arm_graphs
        hashes.append({"threshold": threshold, "csv_sha256": record["csv_sha256"],
                       "receipt_sha256": record["receipt_sha256"]})
    # No labels have been opened above. This immutable gate is written first.
    gate_receipt = {"status": "PASS_ALL_EXP234_SOURCE_ARMS_BEFORE_LABEL_ACCESS",
                    "source_embryo": config["source_embryo"], "movies": movies,
                    "plan_sha256": config["plan_sha256"], "hashes": hashes}
    return graphs, gate_receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.config) == args.config_sha256
    config = json.loads(args.config.read_text())
    assert config["experiment"] == "EXP234_SOURCE_SCORER"
    graphs, gate_receipt = gate(config)
    assert sha(config["exp223_config"]) == config["exp223_config_sha256"]
    from score_exp223_official import evaluator_pins
    official_config = json.loads(Path(config["exp223_config"]).read_text())
    assert official_config["repo_path"] == config["repo"]
    evaluator_pins(official_config)
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "no_metric_gate.json").write_text(json.dumps(gate_receipt, indent=2) + "\n")

    sys.path[:0] = [str(Path(config["repo"]) / "src"), str(Path(config["repo"]) / "scripts")]
    import numpy as np
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    rows = {threshold: [] for threshold in THRESHOLDS}
    for name in gate_receipt["movies"]:
        data_path = Path(config["data_dir"]) / (name + ".zarr")
        ds = open_dataset(data_path, require_tracks=True, load_image=False)
        estimate = (GeffMetadata.read(Path(config["data_dir"]) / (name + ".geff")).extra or {}).get("estimated_number_of_nodes")
        assert estimate is not None and float(estimate) > 0
        for threshold in THRESHOLDS:
            source = graphs[threshold][name]
            ids = sorted(source["nodes"])
            index = {node: i for i, node in enumerate(ids)}
            coords = np.asarray([source["nodes"][i] for i in ids], dtype=float).reshape(-1, 4)
            assert all(np.all((coords[:, j] >= 0) & (coords[:, j] < ds.image_shape[j])) for j in range(4))
            edges = [(index[s], index[t], 1., 0.) for s, t in source["edges"]]
            graph = build_graph(coords, edges)
            metric = evaluate(graph, ds.tracks, scale=ds.scale)
            recall = node_recall(graph, ds.tracks) if graph.num_nodes() and graph.num_edges() else 0.
            rows[threshold].append({"dataset": name, **per_sample_metrics(metric, float(estimate), recall)})
    summary = {threshold: summarise(rows[threshold]) for threshold in THRESHOLDS}
    assert all(math.isfinite(summary[t]["score"]) for t in THRESHOLDS)
    # Python max preserves the preregistered baseline-first tie preference.
    preference = ("0.965", "0.940", "0.900")
    chosen = max(preference, key=lambda t: summary[t]["score"])
    result = {"status": "PASS_EXP234_SOURCE_THRESHOLD_SELECTED",
              "evidence_class": "source-validation selection, not reciprocal OOF",
              "source_embryo": config["source_embryo"], "selected_threshold": chosen,
              "selection_rule": "maximum_official_source_score_tie_baseline_0965",
              "movies": gate_receipt["movies"], "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "summary": summary, "rows": rows}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source": config["source_embryo"],
                      "selected_threshold": chosen,
                      "scores": {t: summary[t]["score"] for t in THRESHOLDS}}))


if __name__ == "__main__":
    main()
