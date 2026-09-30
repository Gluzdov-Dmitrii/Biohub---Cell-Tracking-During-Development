"""Score sealed EXP227 epoch-10 source validation graphs with official metrics."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, score_one


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate(config):
    code = Path(config["inference_code"])
    assert sha(code / "code_manifest.json") == config["inference_manifest_sha256"]
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest
    plan_path = code / "plan.json"
    assert sha(plan_path) == config["plan_sha256"]
    plan = json.loads(plan_path.read_text())
    assert plan["experiment"] == "EXP227_SOURCE_GRAPH10"
    assert plan["source_embryo"] == "44b6" and plan["checkpoint_epoch"] == 10
    assert plan["checkpoint_sha256"] == config["checkpoint_sha256"]
    assert sha(plan["checkpoint"]) == config["checkpoint_sha256"]
    run = Path(config["inference_run"])
    assert Path(plan["output"]).parent == run
    exit_record = json.loads((run / "exit.json").read_text())
    assert sha(run / "exit.json") == config["inference_exit_sha256"]
    supervision = json.loads((run / "supervision/complete.json").read_text())
    control = json.loads((run / "supervision/control.json").read_text())
    assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
    assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert supervision["exit"] == exit_record
    assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
    assert Path(control["queue"]["run_path"]).resolve() == run.resolve()
    status_path = run / "output/status.json"
    assert sha(status_path) == config["inference_status_sha256"]
    status = json.loads(status_path.read_text())
    assert status["status"] == "PASS_EXP227_SOURCE_GRAPH10_NO_LABELS"
    assert status["target_labels_read"] is False
    assert status["checkpoint_sha256"] == config["checkpoint_sha256"]
    assert status["plan_sha256"] == config["plan_sha256"]
    assert status["movies"] == [row["dataset"] for row in plan["movies"]]
    assert len(status["movies"]) == len(status["records"]) == 8
    expected_outputs = {"status.json"} | {
        "graph__" + name + suffix for name in status["movies"] for suffix in (".csv", ".json")
    }
    assert {path.name for path in (run / "output").iterdir()} == expected_outputs
    graphs = {}
    hashes = []
    for row, record in zip(plan["movies"], status["records"]):
        name = row["dataset"]
        assert record["dataset"] == name and record["shape"] == row["shape"]
        assert record["checkpoint_sha256"] == config["checkpoint_sha256"]
        assert record["plan_sha256"] == config["plan_sha256"]
        csv_path = run / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        assert Path(record["csv"]).resolve() == csv_path.resolve()
        assert sha(csv_path) == record["csv_sha256"]
        assert json.loads(receipt_path.read_text()) == record
        parsed = read_graphs(csv_path)
        assert set(parsed) == {name}
        for point in parsed[name]["nodes"].values():
            assert all(float(value) == int(value) and 0 <= value < bound
                       for value, bound in zip(point, row["shape"]))
        graphs[name] = parsed[name]
        hashes.append({"dataset": name, "csv_sha256": record["csv_sha256"],
                       "receipt_sha256": sha(receipt_path)})
    assert len(graphs) == 8
    return plan, graphs, {"status": "PASS_EXP227_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS",
                          "plan_sha256": config["plan_sha256"],
                          "checkpoint_sha256": config["checkpoint_sha256"],
                          "inference_status_sha256": sha(status_path), "hashes": hashes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.config) == args.config_sha256
    config = json.loads(args.config.read_text())
    assert config["experiment"] == "EXP227_SOURCE_GRAPH10_OFFICIAL"
    plan, graphs, gate_receipt = gate(config)
    assert sha(config["evaluator_config"]) == config["evaluator_config_sha256"]
    official_config = json.loads(Path(config["evaluator_config"]).read_text())
    assert official_config["repo_path"] == config["repo"]
    evaluator_pins(official_config)
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "no_metric_gate.json").write_text(json.dumps(gate_receipt, indent=2) + "\n")
    repo = Path(config["repo"])
    sys.path[:0] = [str(repo / "src"), str(repo / "scripts")]
    from geff import GeffMetadata
    from biohub_tracking.io import open_dataset
    from biohub_tracking.metrics import evaluate, node_recall, per_sample_metrics, summarise
    from predict_unet_transformer import build_graph

    rows = []
    for row in plan["movies"]:
        name = row["dataset"]
        dataset = open_dataset(row["zarr"], require_tracks=True, load_image=False)
        estimate = (GeffMetadata.read(Path(config["data_dir"]) / (name + ".geff")).extra or {}).get(
            "estimated_number_of_nodes")
        assert estimate is not None and float(estimate) > 0
        rows.append(score_one(name, graphs[name], dataset, estimate, evaluate,
                              node_recall, per_sample_metrics, build_graph))
        print(json.dumps({"scored_source_movie": name}), flush=True)
    summary = summarise(rows)
    assert math.isfinite(summary["score"])
    result = {"status": "PASS_EXP227_SOURCE_GRAPH10_OFFICIAL",
              "evidence_class": "source-inner validation used during training monitoring; not target OOF",
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "checkpoint_sha256": config["checkpoint_sha256"],
              "summary": summary, "rows": rows}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source_score": result["summary"]["score"]}), flush=True)


if __name__ == "__main__":
    main()
