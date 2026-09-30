"""Read-only CPU microbenchmark. Run from stdin with a verified SNAPSHOT prefix.

SNAPSHOT contains exact immutable EXP227 staged module text and two source44
manifest records. The three paths call the same staged __getitem__; only the
object returned by its zarr.open call changes. No model or CUDA is used.
"""

import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
assert sorted(os.sched_getaffinity(0)) == [24, 25, 26, 27]

import numpy as np
import torch
import zarr

torch.set_num_threads(4)
assert SNAPSHOT["downsample"] == [1, 4, 4]
assert SNAPSHOT["window_size"] == 2
assert len(SNAPSHOT["records"]) == 2
assert len({row["dataset_id"] for row in SNAPSHOT["records"]}) == 2
assert all(row["dataset_id"].startswith("44b6_") for row in SNAPSHOT["records"])
assert all("6bba" not in str(row) for row in SNAPSHOT["records"])

for name in ("utils", "const", "datasets"):
    source = SNAPSHOT["sources"][name + ".py"]
    assert hashlib.sha256(source.encode("utf-8")).hexdigest() == SNAPSHOT["source_sha256"][name + ".py"]
    module = types.ModuleType(name)
    module.__file__ = SNAPSHOT["stage_code"] + "/horaz/src/src/" + name + ".py"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)

loader = sys.modules["datasets"]
downsample = tuple(SNAPSHOT["downsample"])
videos = [loader.load_video_windows(row, 2, downsample, None) for row in SNAPSHOT["records"]]
window_counts = [len(windows) for _, windows in videos]
assert min(window_counts) > 34, window_counts
max_nodes = max(max(window.node_counts) for _, windows in videos for window in windows)
dataset = loader.FrameWindowDataset(videos, max_nodes=max_nodes, augment=False)
assert len(dataset) == sum(window_counts)

offsets = (0, 1, 2, 3, 5, 8, 13, 21, 34)
sequence = []
base = 0
for count in window_counts:
    assert max(offsets) < count
    sequence.extend(base + offset for offset in offsets)
    sequence.extend(base + offset for offset in reversed(offsets))
    base += count
assert len(sequence) == 36 and len(set(sequence)) == 18

def rss_mib():
    status = Path("/proc/self/status").read_text()
    fields = {}
    for line in status.splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, value = line.split(":", 1)
            fields[key] = int(value.strip().split()[0]) / 1024
    return {"rss_mib": fields["VmRSS"], "peak_rss_mib": fields["VmHWM"]}

original_open = zarr.open
paths = [str(metadata.zarr_path) for metadata, _ in videos]
assert len(set(paths)) == 2
memory_before_setup = rss_mib()
started = time.perf_counter()
cached_groups = {path: original_open(path, mode="r") for path in paths}
cached_setup_seconds = time.perf_counter() - started
cached_setup_rss = rss_mib()

started = time.perf_counter()
preloaded = {}
raw_shapes = {}
for path in paths:
    raw_array = cached_groups[path]["0"]
    assert np.dtype(raw_array.dtype) == np.dtype("uint16")
    raw_shapes[path] = tuple(int(v) for v in raw_array.shape)
    frames = raw_array[:, ::downsample[0], ::downsample[1], ::downsample[2]]
    assert frames.dtype == np.uint16
    preloaded[path] = np.ascontiguousarray(frames)
preload_setup_seconds = time.perf_counter() - started
preload_setup_rss = rss_mib()

class MemoryArray:
    def __init__(self, frames):
        self.frames = frames

    def __getitem__(self, key):
        assert isinstance(key, tuple) and len(key) == 4
        assert isinstance(key[0], slice) and key[0].step in (None, 1)
        assert all(isinstance(part, slice) and part.start is None and part.stop is None
                   and part.step == stride for part, stride in zip(key[1:], downsample))
        return self.frames[key[0]]

class MemoryGroup:
    def __init__(self, frames):
        self.frames = frames

    def __getitem__(self, key):
        assert key == "0"
        return MemoryArray(self.frames)

memory_groups = {path: MemoryGroup(preloaded[path]) for path in paths}

def cached_open(path, mode="r"):
    assert mode == "r" and path in cached_groups
    return cached_groups[path]

def memory_open(path, mode="r"):
    assert mode == "r" and path in memory_groups
    return memory_groups[path]

openers = {"baseline_zarr_per_sample": original_open,
           "cached_zarr_handle": cached_open,
           "preloaded_uint16": memory_open}

def fetch(mode, index):
    zarr.open = openers[mode]
    try:
        return dataset[index]
    finally:
        zarr.open = original_open

def tensor_equal(left, right):
    assert left.dtype == right.dtype and tuple(left.shape) == tuple(right.shape)
    assert torch.equal(left, right)

equality_fields = None
image_hashes = {mode: hashlib.sha256() for mode in openers}
for index in sequence:
    baseline = fetch("baseline_zarr_per_sample", index)
    fields = tuple(sorted(baseline))
    equality_fields = fields if equality_fields is None else equality_fields
    assert fields == equality_fields
    for mode in ("baseline_zarr_per_sample", "cached_zarr_handle", "preloaded_uint16"):
        output = baseline if mode == "baseline_zarr_per_sample" else fetch(mode, index)
        assert tuple(sorted(output)) == fields
        for field in fields:
            if isinstance(baseline[field], torch.Tensor):
                tensor_equal(baseline[field], output[field])
            else:
                assert baseline[field] == output[field]
        image_hashes[mode].update(output["images"].numpy().tobytes())
assert len({digest.hexdigest() for digest in image_hashes.values()}) == 1

timings = {mode: [] for mode in openers}
checksums = {mode: [] for mode in openers}
for order in (
    ("baseline_zarr_per_sample", "cached_zarr_handle", "preloaded_uint16"),
    ("preloaded_uint16", "cached_zarr_handle", "baseline_zarr_per_sample"),
):
    for mode in order:
        zarr.open = openers[mode]
        started = time.perf_counter()
        checksum = 0.0
        try:
            for index in sequence:
                output = dataset[index]
                checksum += float(output["images"][0, 0, 0, 0].item())
        finally:
            zarr.open = original_open
        timings[mode].append(time.perf_counter() - started)
        checksums[mode].append(checksum)
        assert checksum == checksums["baseline_zarr_per_sample"][0] if checksums["baseline_zarr_per_sample"] else True

assert all(len(rows) == 2 for rows in timings.values())
assert len({value for rows in checksums.values() for value in rows}) == 1
result = {
    "status": "PASS_EXP227_HORAZ_LOADER_CPU_MICROBENCH",
    "host": "nsu-quadro",
    "cpu_affinity": sorted(os.sched_getaffinity(0)),
    "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
    "torch_num_threads": torch.get_num_threads(),
    "source_dataset_ids": [row["dataset_id"] for row in SNAPSHOT["records"]],
    "source_paths": [{"dataset_id": row["dataset_id"], "zarr_path": row["zarr_path"],
                      "geff_path": row["geff_path"]} for row in SNAPSHOT["records"]],
    "raw_shapes": {row["dataset_id"]: raw_shapes[row["zarr_path"]] for row in SNAPSHOT["records"]},
    "downsampled_shapes": {metadata.dataset_id: metadata.image_shape for metadata, _ in videos},
    "window_counts": window_counts,
    "max_nodes_subset": max_nodes,
    "sequence_indices": sequence,
    "sequence_length": len(sequence),
    "unique_windows": len(set(sequence)),
    "augmentation": False,
    "batch_size_runner": SNAPSHOT["batch_size"],
    "num_workers_runner": SNAPSHOT["num_workers"],
    "loader_fields_bitwise_equal": list(equality_fields),
    "equality_checks_per_alternative": len(sequence) * len(equality_fields),
    "image_tensor_sha256": {mode: digest.hexdigest() for mode, digest in image_hashes.items()},
    "cached_setup_seconds": cached_setup_seconds,
    "preload_setup_seconds": preload_setup_seconds,
    "preloaded_bytes": sum(array.nbytes for array in preloaded.values()),
    "memory_mib": {"before_setup": memory_before_setup,
                   "after_cached_open": cached_setup_rss,
                   "after_preload": preload_setup_rss,
                   "after_benchmark": rss_mib()},
    "elapsed_seconds_per_36_windows": timings,
    "checksums": checksums,
    "stage_code": SNAPSHOT["stage_code"],
    "source_sha256": SNAPSHOT["source_sha256"],
    "stage_manifest_sha256": SNAPSHOT["stage_manifest_sha256"],
    "source44_manifest_sha256": SNAPSHOT["source44_manifest_sha256"],
    "target6bba_access": False,
    "gpu_used": False,
    "active_run_mutation": False,
    "kaggle_post": False,
}
print(json.dumps(result, sort_keys=True, allow_nan=False))
