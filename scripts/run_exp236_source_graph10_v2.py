"""Freeze eleven EXP236 v2 epoch10 source graphs without opening labels."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from run_exp223_inference import atomic_json, verify_csv


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
TRAIN_RUN = REMOTE + "/runs/exp236_horaz_source6bba_block04_v2_20260927"
CODE = REMOTE + "/code/exp236_source_graph10_v2_20260927"
RUN = REMOTE + "/runs/exp236_source_graph10_v2_20260927"
SOURCE_MANIFEST_SHA = "a5c3176ec25d4d75321e6c1fe17b62be2d9e25472ae7fcb677e48fe71478bd87"
SOURCE_BUNDLE_SHA = "90e95a45a4d58a72c18495b48c979de52afdc080b9070892c53e8bf41c2f59b1"
DUPLICATE_MAP_SHA = "d73389f47cc7cbf1c50a01a788827119aa324eebf2fb9222a66243b168ca7d62"
POLICY = "exclude_all_effective_duplicate_windows_v2"
EPOCHS = (3, 6, 9, 10)
INNER_IDS = (
    "6bba_372c8cb8", "6bba_67ebd073", "6bba_76db78c1", "6bba_786893ac",
    "6bba_825bd1c6", "6bba_a5e926bb", "6bba_b329af44", "6bba_b693381b",
    "6bba_bb9f20c3", "6bba_f20478e9", "6bba_f4ae811c",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def block_paths(block):
    stem = f"exp236_horaz_source6bba_block{block:02d}_v2_20260927"
    return Path(REMOTE) / "code" / stem, Path(REMOTE) / "runs" / stem


def validate(plan):
    assert plan["experiment"] == "EXP236_SOURCE_GRAPH10"
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    assert plan["fold"] == 0 and plan["checkpoint_epoch"] == 10
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert plan["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
    assert plan["source_duplicate_policy"] == POLICY
    assert plan["source_duplicate_map_sha256"] == DUPLICATE_MAP_SHA
    assert plan["excluded_pairs_by_split"] == {"train": 824, "inner_validation": 103}
    assert plan["removed_sampled_windows_by_split"] == {"train": 809, "inner_validation": 101}
    assert plan["training_run"] == TRAIN_RUN
    assert plan["checkpoint"] == TRAIN_RUN + "/output/fold0/last.pt"
    assert plan["code"] == CODE and plan["output"] == RUN + "/output"
    assert plan["data_root"] == REMOTE + "/data/exp213_source_view_20260912"
    chain = plan["training_chain"]
    assert len(chain) == 4
    for block, (row, epoch) in enumerate(zip(chain, EPOCHS), 1):
        code, run = block_paths(block)
        assert row["status"] == "PASS_EXP236_SOURCE_V2_BLOCK_AUDIT"
        assert row["block"] == block and row["completed_epochs"] == epoch
        assert row["code"] == code.as_posix() and row["run"] == run.as_posix()
        assert row["target_data_opened"] is False
        assert all(isinstance(row[key], str) and len(row[key]) == 64
                   for key in ("manifest_sha256", "plan_sha256", "checkpoint_sha256",
                               "history_sha256", "result_sha256", "exit_sha256"))
    assert plan["checkpoint_sha256"] == chain[-1]["checkpoint_sha256"]
    assert plan["training_result_sha256"] == chain[-1]["result_sha256"]
    assert plan["training_history_sha256"] == chain[-1]["history_sha256"]
    assert plan["training_code_manifest_sha256"] == chain[-1]["manifest_sha256"]
    assert plan["training_plan_sha256"] == chain[-1]["plan_sha256"]
    movies = plan["movies"]
    assert len(movies) == 11 and [row["dataset"] for row in movies] == list(INNER_IDS)
    for row in movies:
        assert row["zarr"] == plan["data_root"] + "/" + row["dataset"] + ".zarr"
        assert len(row["shape"]) == 4 and all(isinstance(v, int) and v > 0 for v in row["shape"])


def no_labels_guard(data_root, allowed):
    data_root = Path(data_root).resolve()
    allowed = set(allowed)

    def no_labels(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.lower().endswith(".geff") for part in path.parts):
            raise PermissionError("EXP236 graph inference forbids labels")
        if any(part.startswith("44b6_") for part in path.parts):
            raise PermissionError("EXP236 graph inference forbids target44b6")
        if path.is_relative_to(data_root):
            names = [part.removesuffix(".zarr") for part in path.parts if part.endswith(".zarr")]
            if names and any(name not in allowed for name in names):
                raise PermissionError("EXP236 graph inference outside source inner11")

    return no_labels


def verify_chain(plan):
    """Bind the exact completed source-only 3→6→9→10 resume chain."""
    for block, pin in enumerate(plan["training_chain"], 1):
        code, run = block_paths(block)
        assert sha(code / "code_manifest.json") == pin["manifest_sha256"]
        manifest = json.loads((code / "code_manifest.json").read_text())
        for name, digest in manifest.items():
            path = (code / name).resolve()
            assert path.is_relative_to(code.resolve()) and sha(path) == digest, name
        assert sha(code / "plan.json") == pin["plan_sha256"]
        assert sha(code / "source6bba_manifest.json") == SOURCE_MANIFEST_SHA
        assert sha(code / "horaz/src/src/exp236_source_duplicate_pairs.json") == DUPLICATE_MAP_SHA
        training = json.loads((code / "plan.json").read_text())
        assert training["experiment"] == "EXP236" and training["block_end_epoch"] == EPOCHS[block - 1]
        assert training["source_embryo"] == "6bba" and training["target_embryo"] == "44b6"
        assert training["fold"] == 0 and training["planned_epochs"] == 50
        assert training["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
        assert training["source_bundle_sha256"] == SOURCE_BUNDLE_SHA
        assert training["source_duplicate_policy"] == POLICY
        assert training["source_duplicate_map_sha256"] == DUPLICATE_MAP_SHA
        assert training["excluded_pairs_by_split"] == plan["excluded_pairs_by_split"]
        assert training["removed_sampled_windows_by_split"] == plan["removed_sampled_windows_by_split"]
        assert len(training["train"]) == 115 and len(training["inner_validation"]) == 11
        assert [row["dataset_id"] for row in training["inner_validation"]] == list(INNER_IDS)
        assert all(row["dataset_id"].startswith("6bba_") for row in training["train"])
        if block > 1:
            parent = plan["training_chain"][block - 2]
            assert training["parent_completed_epochs"] == EPOCHS[block - 2]
            assert training["parent_checkpoint_sha256"] == parent["checkpoint_sha256"]
            assert training["parent_history_sha256"] == parent["history_sha256"]
            assert training["parent_result_sha256"] == parent["result_sha256"]
            assert training["parent_plan_sha256"] == parent["plan_sha256"]
            assert training["parent_code_manifest_sha256"] == parent["manifest_sha256"]
        assert sha(run / "output/result.json") == pin["result_sha256"]
        result = json.loads((run / "output/result.json").read_text())
        assert result["status"] == f"PASS_EXP236_SOURCE_BLOCK_{EPOCHS[block - 1]}_OF_50"
        assert result["completed_epochs"] == EPOCHS[block - 1] and result["planned_epochs"] == 50
        assert result["target_data_opened"] is False and result["denied_accesses"] == []
        assert result["source_duplicate_policy"] == POLICY
        assert result["source_duplicate_map_sha256"] == DUPLICATE_MAP_SHA
        assert result["checkpoint_sha256"] == pin["checkpoint_sha256"]
        assert sha(run / "output/fold0/history.json") == pin["history_sha256"]
        history = json.loads((run / "output/fold0/history.json").read_text())
        assert [row["epoch"] for row in history] == list(range(1, EPOCHS[block - 1] + 1))
        assert result["history"] == history
        assert sha(run / "output/fold0/last.pt") == pin["checkpoint_sha256"]
        assert sha(run / "exit.json") == pin["exit_sha256"]
        exit_record = json.loads((run / "exit.json").read_text())
        supervision = json.loads((run / "supervision/complete.json").read_text())
        control = json.loads((run / "supervision/control.json").read_text())
        assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
        assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
        assert supervision["exit"] == exit_record
        assert control["action"] == "release" and control["queue"]["state"] == "RELEASED"
        assert Path(control["queue"]["run_path"]).resolve() == run.resolve()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    validate(plan)
    code = Path(plan["code"])
    manifest = json.loads((code / "code_manifest.json").read_text())
    for name, digest in manifest.items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve()) and sha(path) == digest, name
    assert sha(code / "source6bba_manifest.json") == SOURCE_MANIFEST_SHA
    assert sha(code / "horaz/src/src/exp236_source_duplicate_pairs.json") == DUPLICATE_MAP_SHA
    source = json.loads((code / "source6bba_manifest.json").read_text())
    training = json.loads((block_paths(4)[0] / "plan.json").read_text())
    assert source["train"] == training["train"] and source["inner_validation"] == training["inner_validation"]
    assert [row["dataset_id"] for row in source["inner_validation"]] == list(INNER_IDS)
    assert all(row["zarr"] == expected["zarr_path"]
               for row, expected in zip(plan["movies"], source["inner_validation"]))
    verify_chain(plan)

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    sys.addaudithook(no_labels_guard(plan["data_root"], INNER_IDS))
    sys.path.insert(0, str(code / "horaz/src/src"))
    import torch
    assert torch.cuda.is_available()
    torch.set_num_threads(8)
    meta = torch.load(plan["checkpoint"], map_location="cpu", weights_only=True)
    assert meta["epoch"] == 10 and len(meta["history"]) == 10
    resolved = meta["resolved_config"]
    assert resolved["seed"] == 3406 and resolved["epochs"] == 50
    assert resolved["max_iterations_per_epoch"] is None and resolved["max_frames"] is None
    cfg = SimpleNamespace(**resolved)
    del meta
    from engine import load_checkpoint
    from inference import predict_one, write_submission
    model, model_config = load_checkpoint(Path(plan["checkpoint"]), torch.device("cuda"))
    records = []
    started = time.time()
    for row in plan["movies"]:
        name = row["dataset"]
        t0 = time.time()
        graph, stats = predict_one(model, model_config, Path(row["zarr"]),
                                   torch.device("cuda"), cfg, None)
        final = output / ("graph__" + name + ".csv")
        temporary = final.with_suffix(".tmp")
        write_submission([(name, graph)], temporary)
        with temporary.open(newline="") as handle:
            assert next(csv.reader(handle)) == COLUMNS
        counts = verify_csv(temporary, row)
        temporary.replace(final)
        record = {"dataset": name, "csv": str(final), "csv_sha256": sha(final),
                  "checkpoint_sha256": plan["checkpoint_sha256"],
                  "plan_sha256": args.plan_sha256, "shape": row["shape"],
                  "seconds": time.time() - t0, "stats": stats, **counts}
        atomic_json(final.with_suffix(".json"), record)
        records.append(record)
        print(json.dumps({k: record[k] for k in ("dataset", "seconds", "nodes", "edges")}), flush=True)
    status = {"status": "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS", "source_embryo": "6bba",
              "checkpoint_sha256": plan["checkpoint_sha256"],
              "plan_sha256": args.plan_sha256, "movies": list(INNER_IDS),
              "records": records, "source_labels_read": False, "target_labels_read": False,
              "target_data_opened": False,
              "elapsed_seconds": time.time() - started}
    atomic_json(output / "status.json", status)
    print(json.dumps({"status": status["status"], "movies": len(records),
                      "elapsed_seconds": status["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
