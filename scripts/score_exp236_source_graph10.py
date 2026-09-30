"""Score sealed EXP236 epoch-10 source6bba graphs with pinned official metrics."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from score_exp214_paired import read_graphs
from score_exp223_official import evaluator_pins, score_one


EXPECTED_MOVIES = (
    "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1",
    "6bba_786893ac", "6bba_825bd1c6", "6bba_a5e926bb",
    "6bba_b329af44", "6bba_b693381b", "6bba_bb9f20c3",
    "6bba_f20478e9", "6bba_f4ae811c",
)
SOURCE_MANIFEST_SHA = "a5c3176ec25d4d75321e6c1fe17b62be2d9e25472ae7fcb677e48fe71478bd87"
SOURCE_BUNDLE_SHA = "90e95a45a4d58a72c18495b48c979de52afdc080b9070892c53e8bf41c2f59b1"
SOURCE_DUPLICATE_MAP_SHA = "d73389f47cc7cbf1c50a01a788827119aa324eebf2fb9222a66243b168ca7d62"
TRAIN_RUN = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp236_horaz_source6bba_block04_v2_20260927"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_only_guard(data_dir):
    """Allow label reads only inside the eleven sealed source movie roots."""
    root = Path(data_dir).resolve()
    allowed = set(EXPECTED_MOVIES)

    def guard(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.startswith("44b6_") for part in path.parts):
            raise PermissionError("EXP236 source scorer forbids target44b6")
        if path.is_relative_to(root):
            names = [part.rsplit(".", 1)[0] for part in path.parts
                     if part.endswith((".zarr", ".geff"))]
            if names and any(name not in allowed for name in names):
                raise PermissionError("EXP236 scorer outside sealed source inner11")

    return guard


def gate(config):
    code = Path(config["inference_code"])
    run = Path(config["inference_run"])
    assert sha(code / "code_manifest.json") == config["inference_manifest_sha256"]
    for name, digest in json.loads((code / "code_manifest.json").read_text()).items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest
    plan_path = code / "plan.json"
    assert sha(plan_path) == config["plan_sha256"]
    plan = json.loads(plan_path.read_text())
    assert plan["experiment"] == "EXP236_SOURCE_GRAPH10"
    assert plan["source_embryo"] == "6bba" and plan["checkpoint_epoch"] == 10
    assert plan["target_embryo"] == "44b6" and plan["fold"] == 0
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert sha(code / "source6bba_manifest.json") == SOURCE_MANIFEST_SHA
    source = json.loads((code / "source6bba_manifest.json").read_text())
    assert [row["dataset_id"] for row in source["inner_validation"]] == list(EXPECTED_MOVIES)
    assert len(source["train"]) == 115
    assert not set(EXPECTED_MOVIES) & {row["dataset_id"] for row in source["train"]}
    assert plan["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert sha(code / "horaz/src/src/exp236_source_duplicate_pairs.json") == SOURCE_DUPLICATE_MAP_SHA
    assert plan["source_duplicate_policy"] == "exclude_all_effective_duplicate_windows_v2"
    assert plan["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert plan["removed_sampled_windows_by_split"] == {"train": 809, "inner_validation": 101}
    assert plan["training_run"] == TRAIN_RUN
    training_result_path = Path(TRAIN_RUN, "output/result.json")
    assert sha(training_result_path) == plan["training_result_sha256"]
    training_result = json.loads(training_result_path.read_text())
    assert training_result["status"] == "PASS_EXP236_SOURCE_BLOCK_10_OF_50"
    assert training_result["completed_epochs"] == 10
    assert training_result["target_data_opened"] is False
    assert training_result["source_duplicate_map_sha256"] == SOURCE_DUPLICATE_MAP_SHA
    assert sha(Path(TRAIN_RUN, "output/fold0/history.json")) == plan["training_history_sha256"]
    assert Path(plan["code"]).resolve() == code.resolve()
    assert [row["dataset"] for row in plan["movies"]] == list(EXPECTED_MOVIES)
    assert all(Path(row["zarr"]).resolve() ==
               (Path(config["data_dir"]) / (row["dataset"] + ".zarr")).resolve()
               for row in plan["movies"])
    assert all(len(row["shape"]) == 4 and all(isinstance(v, int) and v > 0
               for v in row["shape"]) for row in plan["movies"])
    assert Path(plan["checkpoint"]).name == "last.pt"
    assert Path(plan["checkpoint"]).resolve() == Path(TRAIN_RUN, "output/fold0/last.pt").resolve()
    assert plan["checkpoint_sha256"] == config["checkpoint_sha256"]
    assert sha(plan["checkpoint"]) == config["checkpoint_sha256"]
    assert Path(plan["output"]).resolve() == (run / "output").resolve()
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
    assert status["status"] == "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS"
    assert status["target_labels_read"] is False and status["source_labels_read"] is False
    assert status["target_data_opened"] is False
    assert status["source_embryo"] == "6bba"
    assert status["checkpoint_sha256"] == config["checkpoint_sha256"]
    assert status["plan_sha256"] == config["plan_sha256"]
    assert status["movies"] == list(EXPECTED_MOVIES)
    assert len(status["records"]) == len(EXPECTED_MOVIES)
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
        assert parsed[name]["nodes"]
        for point in parsed[name]["nodes"].values():
            assert all(float(value) == int(value) and 0 <= value < bound
                       for value, bound in zip(point, row["shape"]))
        assert len(parsed[name]["nodes"]) == record["nodes"]
        assert len(parsed[name]["edges"]) == record["edges"]
        graphs[name] = parsed[name]
        hashes.append({"dataset": name, "csv_sha256": record["csv_sha256"],
                       "receipt_sha256": sha(receipt_path)})
    assert tuple(graphs) == EXPECTED_MOVIES
    assert hashes == config["inference_graph_hashes"]
    return plan, graphs, {"status": "PASS_EXP236_SOURCE_GRAPH10_BEFORE_LABEL_ACCESS",
                          "source_labels_read": False, "target_labels_read": False,
                          "plan_sha256": config["plan_sha256"],
                          "checkpoint_sha256": config["checkpoint_sha256"],
                          "inference_manifest_sha256": config["inference_manifest_sha256"],
                          "inference_exit_sha256": config["inference_exit_sha256"],
                          "inference_status_sha256": sha(status_path), "hashes": hashes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.config) == args.config_sha256
    config = json.loads(args.config.read_text())
    assert config["experiment"] == "EXP236_SOURCE_GRAPH10_OFFICIAL"
    plan, graphs, gate_receipt = gate(config)
    sys.addaudithook(source_only_guard(config["data_dir"]))
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
    result = {"status": "PASS_EXP236_SOURCE_GRAPH10_OFFICIAL",
              "evidence_class": "source6bba inner validation used during training monitoring; not target OOF",
              "source_labels_read": True, "target_labels_read": False,
              "target_data_opened": False,
              "no_metric_gate_sha256": sha(output / "no_metric_gate.json"),
              "checkpoint_sha256": config["checkpoint_sha256"],
              "summary": summary, "rows": rows}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "source_score": result["summary"]["score"]}), flush=True)


if __name__ == "__main__":
    main()
