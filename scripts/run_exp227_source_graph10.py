"""Freeze eight source-only Horaz epoch-10 graphs before opening any labels."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from run_exp223_inference import atomic_json, verify_csv


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(plan):
    assert plan["experiment"] == "EXP227_SOURCE_GRAPH10"
    assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
    assert plan["fold"] == 1 and plan["checkpoint_epoch"] == 10
    assert plan["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert Path(plan["checkpoint"]).name == "epoch_010.pt"
    assert Path(plan["output"]).name == "output"
    movies = plan["movies"]
    assert len(movies) == 8
    names = [row["dataset"] for row in movies]
    assert len(set(names)) == 8 and all(name.startswith("44b6_") for name in names)
    for row in movies:
        assert Path(row["zarr"]).name == row["dataset"] + ".zarr"
        assert len(row["shape"]) == 4 and all(isinstance(v, int) and v > 0 for v in row["shape"])


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
    source_manifest = code / "source44_manifest.json"
    assert sha(source_manifest) == SOURCE_MANIFEST_SHA
    source = json.loads(source_manifest.read_text())
    inner = source["inner_validation"]
    train_names = {row["dataset_id"] for row in source["train"]}
    assert [row["dataset"] for row in plan["movies"]] == [row["dataset_id"] for row in inner]
    assert not set(row["dataset"] for row in plan["movies"]).intersection(train_names)
    assert all(row["zarr"] == expected["zarr_path"]
               for row, expected in zip(plan["movies"], inner))

    run = Path(plan["training_run"])
    result_path = run / "output/result.json"
    assert sha(result_path) == plan["training_result_sha256"]
    result = json.loads(result_path.read_text())
    assert result["status"] == "PASS_FULL_SOURCE_BLOCK_10_OF_50"
    assert result["target_data_opened"] is False and result["completed_epochs"] == 10
    exit_record = json.loads((run / "exit.json").read_text())
    supervision = json.loads((run / "supervision/complete.json").read_text())
    assert exit_record["returncode"] == 0 and exit_record["hard_timeout"] is False
    assert supervision["status"] == "RELEASED_AFTER_VERIFIED_EXIT"
    assert sha(plan["checkpoint"]) == plan["checkpoint_sha256"]

    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    data_root = Path(plan["data_root"]).resolve()
    allowed = {row["dataset"] for row in plan["movies"]}

    def no_labels(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes)):
            return
        path = Path(raw.decode() if isinstance(raw, bytes) else raw).resolve()
        if any(part.lower().endswith(".geff") for part in path.parts):
            raise PermissionError("EXP227 source graph inference forbids labels")
        if path.is_relative_to(data_root):
            names = [part.removesuffix(".zarr") for part in path.parts if part.endswith(".zarr")]
            if names and any(name not in allowed for name in names):
                raise PermissionError("EXP227 source graph inference outside eight images")

    sys.addaudithook(no_labels)
    sys.path.insert(0, str(code / "horaz/src/src"))
    import torch
    assert torch.cuda.is_available()
    torch.set_num_threads(8)
    meta = torch.load(plan["checkpoint"], map_location="cpu", weights_only=True)
    assert meta["epoch"] == 10 and len(meta["history"]) == 10
    resolved = meta["resolved_config"]
    assert resolved["seed"] == 3407 and resolved["epochs"] == 50
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
    status = {"status": "PASS_EXP227_SOURCE_GRAPH10_NO_LABELS", "source_embryo": "44b6",
              "checkpoint_sha256": plan["checkpoint_sha256"],
              "plan_sha256": args.plan_sha256, "movies": [row["dataset"] for row in plan["movies"]],
              "records": records, "target_labels_read": False,
              "elapsed_seconds": time.time() - started}
    atomic_json(output / "status.json", status)
    print(json.dumps({"status": status["status"], "movies": len(records),
                      "elapsed_seconds": status["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
