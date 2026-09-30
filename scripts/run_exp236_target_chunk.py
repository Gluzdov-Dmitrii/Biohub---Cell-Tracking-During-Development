"""Fixed EXP236 source6bba checkpoint over one assigned target44b6 image chunk.

No target GEFF, scorer, or frozen submission is opened. The parent checkpoint
and source-only evidence are pinned before any target image is read.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace

from run_exp223_inference import atomic_json, verify_csv


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
ASSIGNMENT_SHA = "9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4"
PREREG_SHA = "a36787c0187284e07f465097153a30575c4a5ef722e4d627b955084eb1b8c400"
TRAINING_SHA = "266732c9cbbaea76a45ad9a4706b3b025b11d36be0762b00f0838c0d8b8efcdb"
HANDOFF_SHA = "9d8c37c1d3b1d14e2e7589704d3899b678f2398cd16f120d89c09e3e16d9ba07"
SCORE_SHA = "5b0e87506e6d95a7c8175825b9a122292ee664fa71bc7994e507969b81ac4737"
SOURCE_PLAN_SHA = "3633711ba0a3706be43c71907261afa5904db93d26cb1b29fb3dc19294474421"
SOURCE_MANIFEST_SHA = "92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2"
CHECKPOINT_SHA = "d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813"
CHECKPOINT = REMOTE + "/runs/exp236_horaz_source6bba_block04_v2_20260927/output/fold0/last.pt"
SOURCE_GRAPH_CODE = REMOTE + "/code/exp236_source_graph10_v2_20260927"
DATA_ROOT = REMOTE + "/data/exp213_source_view_20260912"
DATASET = re.compile(r"44b6_[0-9a-f]{8}\Z")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_json(plan, name, digest):
    path = Path(plan["code"]) / name
    assert path == Path(plan[name.removesuffix(".json")])
    assert sha(path) == digest
    return json.loads(path.read_text())


def validate_plan(plan):
    assert plan["experiment"] == "EXP236_TARGET44B6_CHUNK"
    assert plan["source_embryo"] == "6bba" and plan["target_embryo"] == "44b6"
    index = plan["chunk_index"]
    assert isinstance(index, int) and 0 <= index < 4 and plan["chunk_count"] == 4
    assert plan["assignment_sha256"] == ASSIGNMENT_SHA
    assert sha(plan["assignment"]) == ASSIGNMENT_SHA
    assignment = json.loads(Path(plan["assignment"]).read_text())
    assert assignment["status"] == "PREREGISTERED_EXP234_TARGET_PARTITIONS_NO_METRICS"
    assert assignment["thresholds_selected"] is False and assignment["target_labels_read"] is False
    direction = assignment["directions"]["6bba"]
    assert direction["target_embryo"] == "44b6" and direction["movie_count"] == 59
    chunks = direction["chunks"]
    assert len(chunks) == 4 and [len(chunk) for chunk in chunks] == [15, 15, 15, 14]
    all_names = [name for chunk in chunks for name in chunk]
    assert len(all_names) == len(set(all_names)) == 59
    assert all(isinstance(name, str) and DATASET.fullmatch(name) for name in all_names)
    assert plan["movies"] == chunks[index]
    assert plan["prereg_sha256"] == PREREG_SHA
    assert plan["source_training_sha256"] == TRAINING_SHA
    assert plan["source_handoff_sha256"] == HANDOFF_SHA
    assert plan["source_score_sha256"] == SCORE_SHA
    assert plan["source_graph_plan_sha256"] == SOURCE_PLAN_SHA
    training = checked_json(plan, "source_training.json", TRAINING_SHA)
    handoff = checked_json(plan, "source_handoff.json", HANDOFF_SHA)
    score = checked_json(plan, "source_score.json", SCORE_SHA)
    source_plan = checked_json(plan, "source_graph_plan.json", SOURCE_PLAN_SHA)
    assert training["status"] == "PASS_EXP236_SOURCE_V2_EPOCH10_RELEASED"
    assert handoff["status"] == "PASS_EXP236_SOURCE11_OFFICIAL_HANDOFF"
    assert handoff["training_verified"]["controller_sha256"] == TRAINING_SHA
    assert handoff["training_verified"]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert handoff["graph_stage"]["graph_manifest_sha256"] == SOURCE_MANIFEST_SHA
    assert handoff["graph_stage"]["graph_plan_sha256"] == SOURCE_PLAN_SHA
    assert handoff["target_data_opened"] is False
    assert handoff["score_verified"]["target_labels_read"] is False
    assert handoff["score_verified"]["source_score"] == score["source_score"] == 0.8458659187983504
    assert score["status"] == "VERIFIED_EXP236_SOURCE10_OFFICIAL"
    assert score["checkpoint_sha256"] == CHECKPOINT_SHA and score["target_labels_read"] is False
    assert source_plan["experiment"] == "EXP236_SOURCE_GRAPH10"
    assert source_plan["checkpoint"] == CHECKPOINT
    assert source_plan["checkpoint_sha256"] == CHECKPOINT_SHA
    assert source_plan["code"] == SOURCE_GRAPH_CODE
    assert source_plan["training_chain"][-1]["checkpoint_sha256"] == CHECKPOINT_SHA
    assert plan["checkpoint_epoch"] == 10
    assert plan["checkpoint"] == CHECKPOINT and plan["checkpoint_sha256"] == CHECKPOINT_SHA
    assert plan["data_root"] == DATA_ROOT
    token = f"exp236_target44b6_chunk{index:02d}_v1_20260927"
    assert plan["code"] == REMOTE + "/code/" + token
    assert plan["output"] == REMOTE + "/runs/" + token + "/output"
    return source_plan


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
            raise PermissionError("EXP236 target inference forbids every GEFF label")
        if path.name.lower() == "submission.csv":
            raise PermissionError("EXP236 target inference forbids submission replay")
        images = [part.removesuffix(".zarr") for part in path.parts if part.endswith(".zarr")]
        if images and any(name not in allowed for name in images):
            raise PermissionError("EXP236 target inference outside frozen target chunk")
        if path.is_relative_to(root):
            if path != root and not images:
                raise PermissionError("EXP236 target inference requires assigned Zarr image paths")
            if any(part.startswith("6bba_") for part in path.parts):
                raise PermissionError("EXP236 target inference forbids source images")
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
    assert sha(plan["checkpoint"]) == CHECKPOINT_SHA
    root = Path(plan["data_root"])
    movies = [{"dataset": name, "zarr": root / (name + ".zarr")} for name in plan["movies"]]
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
                  "checkpoint_sha256": CHECKPOINT_SHA, "plan_sha256": args.plan_sha256,
                  "shape": row["shape"], "seconds": time.time() - t0, "stats": stats, **counts}
        atomic_json(final.with_suffix(".json"), record)
        records.append(record)
        print(json.dumps({"dataset": name, "nodes": record["nodes"], "edges": record["edges"]}), flush=True)
    status = {"status": f"PASS_EXP236_TARGET44B6_CHUNK{plan['chunk_index']:02d}_NO_LABELS",
              "source_embryo": "6bba", "target_embryo": "44b6", "chunk_index": plan["chunk_index"],
              "assignment_sha256": ASSIGNMENT_SHA, "source_handoff_sha256": HANDOFF_SHA,
              "checkpoint_sha256": CHECKPOINT_SHA, "plan_sha256": args.plan_sha256,
              "movies": plan["movies"], "records": records, "target_labels_read": False,
              "elapsed_seconds": time.time() - started}
    atomic_json(output / "status.json", status)
    print(json.dumps({"status": status["status"], "movies": len(records)}), flush=True)


if __name__ == "__main__":
    main()
