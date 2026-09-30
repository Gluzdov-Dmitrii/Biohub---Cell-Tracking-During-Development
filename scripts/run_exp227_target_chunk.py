"""One sealed EXP227 source44 Horaz checkpoint over a frozen target6bba chunk.

No metric or GEFF path is opened. This module is prepared locally only; no
remote stage or GPU run is created by importing or validating it.
"""
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
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
SOURCE8 = (
    "44b6_996155de", "44b6_c50204e0", "44b6_c96cfa10", "44b6_551a5dba",
    "44b6_90724892", "44b6_f28707c6", "44b6_deabac95", "44b6_341df25f",
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(plan):
    assert plan["experiment"] == "EXP227_TARGET6BBA_CHUNK"
    assert plan["source_embryo"] == "44b6" and plan["target_embryo"] == "6bba"
    assert isinstance(plan["chunk_index"], int) and 0 <= plan["chunk_index"] < 8
    assert plan["chunk_count"] == 8
    assert plan["assignment_sha256"] == ASSIGNMENT_SHA
    assert sha(plan["assignment"]) == ASSIGNMENT_SHA
    assignment = json.loads(Path(plan["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    direction = assignment["directions"]["44b6"]
    assert direction["target_embryo"] == "6bba" and direction["movie_count"] == 116
    chunks = direction["chunks"]
    assert len(chunks) == 8
    all_names = [name for chunk in chunks for name in chunk]
    assert len(all_names) == len(set(all_names)) == 116
    assert all(name.startswith("6bba_") for name in all_names)
    assert plan["movies"] == chunks[plan["chunk_index"]]
    assert len(plan["movies"]) in (14, 15)
    assert sha(plan["selection"]) == plan["selection_sha256"]
    selection = json.loads(Path(plan["selection"]).read_text())
    assert selection["status"] == "SELECTED_EXP227_SOURCE_ONLY_CHECKPOINT"
    assert selection["target_labels_read"] is False
    assert selection["source8"] == list(SOURCE8)
    assert selection["selected_epoch"] in (10, 20)
    assert plan["checkpoint_epoch"] == selection["selected_epoch"]
    assert plan["checkpoint"] == selection["checkpoint"]
    assert plan["checkpoint_sha256"] == selection["checkpoint_sha256"]
    assert plan["prereg_sha256"] == selection["prereg_sha256"]
    assert plan["checkpoint_epoch"] == (20 if selection["scores"]["20"] > selection["scores"]["10"] else 10)
    assert selection["scores"]["10"] == 0.8114014924249717
    assert plan["data_root"].endswith("/data/exp213_source_view_20260912")
    token = f"exp227_target6bba_chunk{plan['chunk_index']:02d}_v1_20260927"
    assert plan["code"].endswith("/code/" + token)
    assert plan["output"].endswith("/runs/" + token + "/output")
    return selection


def no_labels_guard(data_root, assigned):
    root = Path(data_root).resolve()
    allowed = set(assigned)

    def audit(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.lower().endswith(".geff") for part in path.parts):
            raise PermissionError("EXP227 target inference forbids every GEFF label")
        if path.name.lower() == "submission.csv":
            raise PermissionError("EXP227 target inference forbids submission replay")
        images = [part.removesuffix(".zarr") for part in path.parts if part.endswith(".zarr")]
        if images and any(name not in allowed for name in images):
            raise PermissionError("EXP227 target inference outside frozen target chunk")
        if path.is_relative_to(root):
            if path != root and not images:
                raise PermissionError("EXP227 target inference requires assigned Zarr image paths")
            if any(part.startswith("44b6_") for part in path.parts):
                raise PermissionError("EXP227 target inference forbids source images")
    return audit


def image_shape(path):
    path = Path(path)
    assert set(p.name for p in path.iterdir()) == {"0", "zarr.json"}
    shape = json.loads((path / "0/zarr.json").read_text())["shape"]
    assert len(shape) == 4 and all(isinstance(v, int) and v > 0 for v in shape)
    return shape


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    code = Path(plan["code"])
    manifest = json.loads((code / "code_manifest.json").read_text())
    for name, digest in manifest.items():
        staged = (code / name).resolve()
        assert staged.is_relative_to(code.resolve()) and sha(staged) == digest, name
    assert sha(plan["checkpoint"]) == plan["checkpoint_sha256"]
    root = Path(plan["data_root"])
    movies = [{"dataset": name, "zarr": root / (name + ".zarr")} for name in plan["movies"]]
    # Metadata is image-only. Install the audit hook before opening any image.
    sys.addaudithook(no_labels_guard(root, plan["movies"]))
    for row in movies:
        row["shape"] = image_shape(row["zarr"])
    output = Path(plan["output"])
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(code / "horaz/src/src"))
    import torch
    assert torch.cuda.is_available()
    torch.set_num_threads(8)
    meta = torch.load(plan["checkpoint"], map_location="cpu", weights_only=True)
    assert meta["epoch"] == plan["checkpoint_epoch"]
    assert len(meta["history"]) == plan["checkpoint_epoch"]
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
    for row in movies:
        name = row["dataset"]
        t0 = time.time()
        graph, stats = predict_one(model, model_config, row["zarr"], torch.device("cuda"), cfg, None)
        final = output / ("graph__" + name + ".csv")
        temporary = final.with_suffix(".tmp")
        write_submission([(name, graph)], temporary)
        with temporary.open(newline="") as handle:
            assert next(csv.reader(handle)) == COLUMNS
        counts = verify_csv(temporary, row)
        temporary.replace(final)
        record = {"dataset": name, "csv": str(final), "csv_sha256": sha(final),
                  "checkpoint_sha256": plan["checkpoint_sha256"], "plan_sha256": args.plan_sha256,
                  "shape": row["shape"], "seconds": time.time() - t0, "stats": stats, **counts}
        atomic_json(final.with_suffix(".json"), record)
        records.append(record)
        print(json.dumps({"dataset": name, "nodes": record["nodes"], "edges": record["edges"]}), flush=True)
    status = {"status": f"PASS_EXP227_TARGET6BBA_CHUNK{plan['chunk_index']:02d}_NO_LABELS",
              "source_embryo": "44b6", "target_embryo": "6bba", "chunk_index": plan["chunk_index"],
              "assignment_sha256": ASSIGNMENT_SHA, "selection_sha256": plan["selection_sha256"],
              "checkpoint_sha256": plan["checkpoint_sha256"], "plan_sha256": args.plan_sha256,
              "movies": plan["movies"], "records": records, "target_labels_read": False,
              "elapsed_seconds": time.time() - started}
    atomic_json(output / "status.json", status)
    print(json.dumps({"status": status["status"], "movies": len(records)}), flush=True)


if __name__ == "__main__":
    main()
