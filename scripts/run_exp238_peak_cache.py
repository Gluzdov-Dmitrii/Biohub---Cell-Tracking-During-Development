"""Replay frozen source graphs and cache selected-branch Horaz maxima without labels.

This runner is staged into a new derived code tree. It never reads GEFF or target
images, and it stops if any of the 19 sealed source graph hashes changes.
"""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np

from run_exp223_inference import atomic_json, verify_csv


COLUMNS = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
PEAK_DTYPE = np.dtype([("t", "<u2"), ("z", "<u2"), ("y", "<u2"),
                       ("x", "<u2"), ("probability", "<f4")], align=False)
FLOOR = 0.075
MAX_FRAME = 16_384
MAX_MOVIE = 1_000_000
REMOTE = Path("/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development")
NAMESPACES = {
    "source44": ("EXP227", "44b6", "exp238_source44_peak_cache_v1_20260927", 8,
                 "df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79",
                 "1f079e658a5dd0b505e469ac2f9251dd4ebc00db9010240742e7a913508832b1",
                 "d445f1858ca5efe9561667a6e21362d753f047bb5bd7d507c209f076193cde7d"),
    "source6": ("EXP236", "6bba", "exp238_source6_peak_cache_v1_20260927", 11,
                "d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813",
                "92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2",
                "de1a4ca38f7d9f470eab6a993322e301b016e05f2175a6407559764633537acf"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_graph_replay(path: Path, expected_sha256: str) -> str:
    observed = sha(path)
    if observed != expected_sha256:
        raise RuntimeError("Frozen source graph replay mismatch")
    return observed


def validate_plan(plan: dict) -> None:
    assert plan["experiment"] == "EXP238_SOURCE_PEAK_CACHE"
    assert plan["cohort"] in NAMESPACES
    experiment, prefix, namespace, count, checkpoint_sha, manifest_sha, status_sha = NAMESPACES[plan["cohort"]]
    assert plan["parent_experiment"] == experiment
    assert plan["source_embryo"] == prefix
    assert plan["code"] == (REMOTE / "code" / namespace).as_posix()
    assert plan["run"] == (REMOTE / "runs" / namespace).as_posix()
    assert plan["parent_code"] == (REMOTE / "code" / plan["parent_code_name"]).as_posix()
    assert plan["parent_run"] == (REMOTE / "runs" / plan["parent_run_name"]).as_posix()
    assert plan["checkpoint_sha256"] == checkpoint_sha
    assert plan["parent_manifest_sha256"] == manifest_sha
    assert plan["parent_status_sha256"] == status_sha
    assert plan["floor"] == FLOOR and plan["max_peaks_per_frame"] == MAX_FRAME
    assert plan["max_peaks_per_movie"] == MAX_MOVIE
    assert plan["peak_dtype_itemsize"] == PEAK_DTYPE.itemsize == 12
    assert plan["downsample_zyx"] == [1, 4, 4]
    assert len(plan["movies"]) == count
    ids = [row["dataset"] for row in plan["movies"]]
    assert len(set(ids)) == count and all(value.startswith(prefix + "_") for value in ids)
    for row in plan["movies"]:
        assert row["zarr"] == (REMOTE / "data" / "exp213_source_view_20260912" /
                               (row["dataset"] + ".zarr")).as_posix()
        assert row["shape"] == [100, 64, 256, 256]
        assert len(row["graph_csv_sha256"]) == len(row["graph_receipt_sha256"]) == 64


def verify_sealed_parent(plan: dict, code: Path) -> dict:
    parent_code = Path(plan["parent_code"])
    parent_run = Path(plan["parent_run"])
    parent_plan_path = parent_code / "plan.json"
    assert sha(parent_code / "code_manifest.json") == plan["parent_manifest_sha256"]
    parent_manifest = json.loads((parent_code / "code_manifest.json").read_text())
    for name, digest in parent_manifest.items():
        path = (parent_code / name).resolve()
        assert path.is_relative_to(parent_code.resolve()) and sha(path) == digest, name
    assert sha(parent_plan_path) == plan["parent_plan_sha256"]
    assert sha(code / "exp238_parent_plan.json") == plan["parent_plan_sha256"]
    parent_plan = json.loads(parent_plan_path.read_text())
    assert parent_plan == json.loads((code / "exp238_parent_plan.json").read_text())
    assert parent_plan["code"] == str(parent_code)
    assert parent_plan["output"] == str(parent_run / "output")
    assert parent_plan["checkpoint"] == plan["checkpoint"]
    assert parent_plan["checkpoint_sha256"] == plan["checkpoint_sha256"]
    assert [row["dataset"] for row in parent_plan["movies"]] == [row["dataset"] for row in plan["movies"]]
    for row, original in zip(plan["movies"], parent_plan["movies"]):
        assert row["zarr"] == original["zarr"] and row["shape"] == original["shape"]
    assert sha(Path(plan["checkpoint"])) == plan["checkpoint_sha256"]
    status_path = parent_run / "output/status.json"
    assert sha(status_path) == plan["parent_status_sha256"]
    status = json.loads(status_path.read_text())
    assert status["status"] in ("PASS_EXP227_SOURCE_GRAPH10_NO_LABELS",
                                "PASS_EXP236_SOURCE_GRAPH10_NO_LABELS")
    assert status["checkpoint_sha256"] == plan["checkpoint_sha256"]
    assert status["target_labels_read"] is False
    assert len(status["records"]) == len(plan["movies"])
    for row, record in zip(plan["movies"], status["records"]):
        name = row["dataset"]
        assert record["dataset"] == name
        csv_path = parent_run / "output" / ("graph__" + name + ".csv")
        receipt_path = csv_path.with_suffix(".json")
        assert record["csv"] == str(csv_path)
        assert record["csv_sha256"] == row["graph_csv_sha256"] == sha(csv_path)
        assert row["graph_receipt_sha256"] == sha(receipt_path)
        assert json.loads(receipt_path.read_text()) == record
    if plan["cohort"] == "source44":
        from run_exp227_source_graph10 import validate as parent_validate
        parent_validate(parent_plan)
    else:
        from run_exp236_source_graph10_v2 import validate as parent_validate, verify_chain
        parent_validate(parent_plan)
        verify_chain(parent_plan)
    return parent_plan


def no_labels_guard(data_root: Path, allowed: set[str], source_prefix: str):
    data_root = data_root.resolve()
    other_prefix = "6bba_" if source_prefix == "44b6" else "44b6_"

    def deny(event, values):
        if event not in ("open", "os.listdir", "os.scandir") or not values:
            return
        raw = values[0]
        if not isinstance(raw, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.lower().endswith(".geff") for part in path.parts):
            raise PermissionError("EXP238 forbids all GEFF labels")
        if path.is_relative_to(data_root):
            if any(part.startswith(other_prefix) for part in path.parts):
                raise PermissionError("EXP238 forbids reciprocal target images")
            names = [part.removesuffix(".zarr") for part in path.parts if part.endswith(".zarr")]
            if names and any(name not in allowed for name in names):
                raise PermissionError("EXP238 image outside frozen inner cohort")

    return deny


class PeakCollector:
    def __init__(self, name: str, raw_shape: list[int]):
        self.name = name
        self.raw_shape = raw_shape
        self.parts: list[np.ndarray] = []
        self.frames: list[dict] = []
        self.total = 0

    def add(self, time_index: int, lowres: np.ndarray, scores: np.ndarray, metadata: dict) -> None:
        assert time_index == len(self.frames) and 0 <= time_index < self.raw_shape[0]
        assert lowres.ndim == 2 and lowres.shape[1] == 3
        assert scores.shape == (len(lowres),) and len(lowres) <= MAX_FRAME
        assert lowres.dtype == np.dtype("uint16") and scores.dtype == np.dtype("float32")
        assert np.isfinite(scores).all() and ((scores > FLOOR) & (scores <= 1)).all()
        assert metadata["floor"] == FLOOR and metadata["downsample_zyx"] == [1, 4, 4]
        assert metadata["logit_shape_zyx"] == [64, 64, 64]
        assert len(metadata["pool_kernel_zyx"]) == 3
        assert all(int(value) > 0 and int(value) % 2 == 1 for value in metadata["pool_kernel_zyx"])
        assert metadata["selected_threshold"] in (0.075, 0.96875)
        assert isinstance(metadata["adaptive_mode"], bool) and metadata["tta"] is True
        assert math.isfinite(metadata["gamma"]) and metadata["gamma"] > 0
        if len(lowres):
            assert np.all(lowres < np.asarray(metadata["logit_shape_zyx"], dtype=np.uint16))
        self.total += len(lowres)
        if self.total > MAX_MOVIE:
            raise RuntimeError("EXP238 peak-per-movie cap exceeded; refusing truncation")
        part = np.empty(len(lowres), dtype=PEAK_DTYPE)
        part["t"] = time_index
        for index, axis in enumerate(("z", "y", "x")):
            part[axis] = lowres[:, index]
        part["probability"] = scores
        self.parts.append(part)
        self.frames.append({"t": time_index, "count": len(lowres), **metadata})

    def save(self, output: Path) -> dict:
        assert len(self.frames) == self.raw_shape[0] == 100
        values = np.concatenate(self.parts)
        assert len(values) == self.total and values.dtype == PEAK_DTYPE
        assert values.nbytes <= MAX_MOVIE * PEAK_DTYPE.itemsize
        path = output / ("peaks__" + self.name + ".npy")
        temporary = path.with_suffix(".tmp")
        with temporary.open("wb") as handle:
            np.save(handle, values, allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        metadata_path = output / ("peaks__" + self.name + ".json")
        payload = {"dataset": self.name, "floor": FLOOR, "peak_count": self.total,
                   "peak_dtype": PEAK_DTYPE.descr, "peak_payload_bytes": values.nbytes,
                   "peak_npy_sha256": sha(path), "frames": self.frames,
                   "source_labels_read": False, "target_data_opened": False}
        atomic_json(metadata_path, payload)
        return {"dataset": self.name, "peak_count": self.total,
                "peak_payload_bytes": values.nbytes, "peak_npy_sha256": sha(path),
                "peak_metadata_sha256": sha(metadata_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    assert sha(args.plan) == args.plan_sha256
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    code = Path(plan["code"])
    assert args.plan == code / "exp238_plan.json"
    manifest_path = code / "code_manifest.json"
    assert sha(manifest_path) == args.manifest_sha256
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest.items():
        path = (code / name).resolve()
        assert path.is_relative_to(code.resolve()) and sha(path) == digest, name
    assert sha(code / "horaz/src/src/engine.py") == plan["patched_engine_sha256"]
    assert sha(code / "horaz/src/src/detection.py") == plan["patched_detection_sha256"]
    assert sha(code / "run_exp238_peak_cache.py") == plan["runner_sha256"]
    sys.addaudithook(no_labels_guard(Path(plan["data_root"]),
                                      {row["dataset"] for row in plan["movies"]},
                                      plan["source_embryo"]))
    parent_plan = verify_sealed_parent(plan, code)
    output = Path(plan["run"]) / "output"
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(code / "horaz/src/src"))
    import torch
    import detection
    from engine import load_checkpoint
    from inference import predict_one, write_submission
    assert torch.cuda.is_available() and detection.EXP238_PEAK_HOOK is None
    torch.set_num_threads(8)
    meta = torch.load(plan["checkpoint"], map_location="cpu", weights_only=True)
    assert meta["epoch"] == 10 and len(meta["history"]) == 10
    resolved = meta["resolved_config"]
    assert resolved["seed"] == (3407 if plan["cohort"] == "source44" else 3406)
    assert resolved["max_frames"] is None and resolved["max_iterations_per_epoch"] is None
    cfg = SimpleNamespace(**resolved)
    del meta
    model, model_config = load_checkpoint(Path(plan["checkpoint"]), torch.device("cuda"))
    assert tuple(model_config.downsample) == (1, 4, 4)
    records = []
    started = time.time()
    total_payload = 0
    for row in plan["movies"]:
        name = row["dataset"]
        collector = PeakCollector(name, row["shape"])
        t0 = time.time()
        assert detection.EXP238_PEAK_HOOK is None
        detection.EXP238_PEAK_HOOK = collector.add
        try:
            graph, stats = predict_one(model, model_config, Path(row["zarr"]),
                                       torch.device("cuda"), cfg, None)
        finally:
            detection.EXP238_PEAK_HOOK = None
        final = output / ("graph__" + name + ".csv")
        temporary = final.with_suffix(".tmp")
        write_submission([(name, graph)], temporary)
        with temporary.open(newline="") as handle:
            assert next(csv.reader(handle)) == COLUMNS
        counts = verify_csv(temporary, row)
        require_graph_replay(temporary, row["graph_csv_sha256"])
        temporary.replace(final)
        peak_record = collector.save(output)
        total_payload += peak_record["peak_payload_bytes"]
        assert total_payload <= 228_000_000
        record = {"dataset": name, "graph_csv_sha256": sha(final),
                  "source_graph_sha256": row["graph_csv_sha256"],
                  "checkpoint_sha256": plan["checkpoint_sha256"],
                  "seconds": time.time() - t0, "stats": stats,
                  **counts, **peak_record}
        records.append(record)
        atomic_json(output / ("record__" + name + ".json"), record)
        print(json.dumps({"dataset": name, "graph_replay": "PASS",
                          "peak_count": collector.total, "seconds": record["seconds"]}), flush=True)
    assert [row["dataset"] for row in parent_plan["movies"]] == [row["dataset"] for row in records]
    status = {"status": "PASS_EXP238_SOURCE_PEAK_CACHE_NO_LABELS", "cohort": plan["cohort"],
              "checkpoint_sha256": plan["checkpoint_sha256"],
              "parent_status_sha256": plan["parent_status_sha256"],
              "plan_sha256": args.plan_sha256, "records": records,
              "peak_payload_bytes": total_payload, "elapsed_seconds": time.time() - started,
              "source_labels_read": False, "target_data_opened": False,
              "graph_replay": "EXACT_OLD_CSV_SHA256"}
    atomic_json(output / "status.json", status)
    print(json.dumps({"status": status["status"], "movies": len(records)}), flush=True)


if __name__ == "__main__":
    main()
