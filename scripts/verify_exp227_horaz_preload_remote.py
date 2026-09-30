"""CPU-only, read-only parity and one-pass loader check; run with verified SNAPSHOT prefix."""

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
from torch.utils.data import DataLoader, Subset
import zarr

torch.set_num_threads(4)
assert len(SNAPSHOT["records"]) == 2
assert all(row["dataset_id"].startswith("44b6_") and "6bba" not in str(row)
           for row in SNAPSHOT["records"])
assert SNAPSHOT["estimated_preload_bytes"] < 1 * 2**30

for name in ("utils", "const", "baseline_datasets", "dev_datasets"):
    source = SNAPSHOT["sources"][name]
    assert hashlib.sha256(source.encode()).hexdigest() == SNAPSHOT["source_sha256"][name]
    module = types.ModuleType(name)
    module.__file__ = SNAPSHOT["file_origins"][name]
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)

baseline_module = sys.modules["baseline_datasets"]
dev_module = sys.modules["dev_datasets"]
assert baseline_module.FrameWindowDataset.__getitem__.__code__.co_filename.endswith("datasets.py")
downsample = (1, 4, 4)

def rss_mib():
    fields = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, value = line.split(":", 1)
            fields[key] = int(value.strip().split()[0]) / 1024
    return {"rss_mib": fields["VmRSS"], "peak_rss_mib": fields["VmHWM"]}

memory_before = rss_mib()
started = time.perf_counter()
videos = [baseline_module.load_video_windows(row, 2, downsample, None)
          for row in SNAPSHOT["records"]]
video_setup_seconds = time.perf_counter() - started
window_counts = [len(windows) for _, windows in videos]
assert min(window_counts) >= 4, window_counts
max_nodes = max(max(window.node_counts) for _, windows in videos for window in windows)
memory_after_videos = rss_mib()

torch.manual_seed(3407)
rng_before_constructors = torch.get_rng_state().clone()
started = time.perf_counter()
baseline = baseline_module.FrameWindowDataset(videos, max_nodes=max_nodes, augment=False)
baseline_setup_seconds = time.perf_counter() - started
started = time.perf_counter()
dev_default = dev_module.FrameWindowDataset(videos, max_nodes=max_nodes, augment=False)
dev_default_setup_seconds = time.perf_counter() - started
memory_before_preload = rss_mib()
started = time.perf_counter()
preload = dev_module.FrameWindowDataset(
    videos, max_nodes=max_nodes, augment=False, preload_uint16_frames=True,
    preload_max_bytes=1 * 2**30,
)
preload_setup_seconds = time.perf_counter() - started
memory_after_preload = rss_mib()
assert torch.equal(rng_before_constructors, torch.get_rng_state())
assert dev_default.preloaded_bytes == 0 and dev_default._preloaded_frames == {}
assert preload.preloaded_bytes == SNAPSHOT["estimated_preload_bytes"]
assert memory_after_preload["peak_rss_mib"] < 8 * 1024
assert len(baseline) == len(dev_default) == len(preload) == sum(window_counts)

raw_frame_checks = []
for (metadata, _), row in zip(videos, SNAPSHOT["records"]):
    original_array = zarr.open(str(metadata.zarr_path), mode="r")["0"]
    frames = preload._preloaded_frames[metadata.zarr_path]
    assert frames.dtype == np.uint16 and frames.flags.c_contiguous
    assert tuple(frames.shape) == metadata.image_shape
    for time_index in (0, metadata.image_shape[0] // 2, metadata.image_shape[0] - 1):
        source_frame = original_array[time_index, ::1, ::4, ::4]
        assert np.array_equal(source_frame, frames[time_index])
        raw_frame_checks.append({"dataset_id": row["dataset_id"], "time": time_index,
                                 "sha256": hashlib.sha256(source_frame.tobytes()).hexdigest()})

sequence = []
base = 0
for count in window_counts:
    sequence.extend(base + offset for offset in
                    (0, 1, count // 2, count - 2, count - 1,
                     count - 1, 0, count // 2))
    base += count
assert len(sequence) == 16 and len(set(sequence)) >= 8

def assert_same(left, right):
    assert tuple(sorted(left)) == tuple(sorted(right))
    for field in left:
        if isinstance(left[field], torch.Tensor):
            assert left[field].dtype == right[field].dtype
            assert tuple(left[field].shape) == tuple(right[field].shape)
            assert torch.equal(left[field], right[field]), field
        else:
            assert left[field] == right[field], field

def sample_sequence(dataset, seed):
    torch.manual_seed(seed)
    outputs = [dataset[index] for index in sequence]
    return outputs, torch.get_rng_state().clone()

sample_checks = 0
sample_image_hashes = {}
for augment in (False, True):
    for dataset in (baseline, dev_default, preload):
        dataset.augment = augment
    for seed in (0, 3407, 209):
        baseline_outputs, baseline_rng = sample_sequence(baseline, seed)
        digest = hashlib.sha256()
        for output in baseline_outputs:
            digest.update(output["images"].numpy().tobytes())
        sample_image_hashes[f"augment={augment},seed={seed}"] = digest.hexdigest()
        for candidate in (dev_default, preload):
            candidate_outputs, candidate_rng = sample_sequence(candidate, seed)
            assert torch.equal(baseline_rng, candidate_rng)
            for left, right in zip(baseline_outputs, candidate_outputs):
                assert_same(left, right)
                sample_checks += len(left)
            del candidate_outputs
        del baseline_outputs

def batch_subset(dataset, augment, seed):
    dataset.augment = augment
    # Cross the two-movie boundary and include both valid-window endpoints.
    chosen = [sequence[0], sequence[4], sequence[8], sequence[12]]
    torch.manual_seed(seed)
    batch = next(iter(DataLoader(Subset(dataset, chosen), batch_size=4,
                                 shuffle=False, num_workers=0, pin_memory=False)))
    return batch, torch.get_rng_state().clone()

batch_checks = 0
for augment in (False, True):
    baseline_batch, baseline_rng = batch_subset(baseline, augment, 7331)
    for candidate in (dev_default, preload):
        candidate_batch, candidate_rng = batch_subset(candidate, augment, 7331)
        assert torch.equal(baseline_rng, candidate_rng)
        assert_same(baseline_batch, candidate_batch)
        batch_checks += len(baseline_batch)

def batch_digest(batch, digest):
    for field in sorted(batch):
        value = batch[field]
        digest.update(field.encode())
        if isinstance(value, torch.Tensor):
            digest.update(str(value.dtype).encode())
            digest.update(repr(tuple(value.shape)).encode())
            digest.update(value.numpy().tobytes())
        else:
            digest.update(json.dumps(value, sort_keys=True).encode())

def make_training_loader(dataset, seed):
    return DataLoader(dataset, batch_size=4, shuffle=True, num_workers=0,
                      persistent_workers=False, pin_memory=False,
                      generator=torch.Generator().manual_seed(seed))

def full_pass_digest(dataset, seed):
    dataset.augment = True
    torch.manual_seed(seed)
    digest = hashlib.sha256()
    batch_count = 0
    for batch in make_training_loader(dataset, seed):
        batch_digest(batch, digest)
        batch_count += 1
    return digest.hexdigest(), batch_count, hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest()

full_pass_audit = {name: full_pass_digest(dataset, 3408)
                   for name, dataset in (("baseline", baseline), ("dev_default", dev_default),
                                         ("preloaded", preload))}
assert len(set(full_pass_audit.values())) == 1, full_pass_audit

def timed_pass(dataset, seed):
    dataset.augment = True
    torch.manual_seed(seed)
    started = time.perf_counter()
    checksum = 0.0
    batches = 0
    for batch in make_training_loader(dataset, seed):
        checksum += float(batch["images"][0, 0, 0, 0, 0].item())
        batches += 1
    return {"seconds": time.perf_counter() - started,
            "checksum": checksum, "batches": batches,
            "rss_after_mib": rss_mib()["rss_mib"]}

timings = {"baseline": [], "dev_default": [], "preloaded": []}
datasets = {"baseline": baseline, "dev_default": dev_default, "preloaded": preload}
for seed, order in ((3408, ("baseline", "dev_default", "preloaded")),
                    (3409, ("preloaded", "dev_default", "baseline"))):
    for name in order:
        timings[name].append(timed_pass(datasets[name], seed))
for round_index in (0, 1):
    checksums = [timings[name][round_index]["checksum"] for name in timings]
    assert len(set(checksums)) == 1
    assert all(timings[name][round_index]["batches"] == full_pass_audit[name][1]
               for name in timings)
assert rss_mib()["peak_rss_mib"] < 8 * 1024

result = {
    "status": "PASS_EXP227_HORAZ_PRELOAD_CPU_VALIDATION",
    "source_dataset_ids": [row["dataset_id"] for row in SNAPSHOT["records"]],
    "source_records": SNAPSHOT["records"],
    "source_manifest_sha256": SNAPSHOT["source_manifest_sha256"],
    "stage_manifest_sha256": SNAPSHOT["stage_manifest_sha256"],
    "source_sha256": SNAPSHOT["source_sha256"],
    "cpu_affinity": sorted(os.sched_getaffinity(0)),
    "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
    "torch_num_threads": torch.get_num_threads(),
    "window_counts": window_counts,
    "max_nodes_subset": max_nodes,
    "sequence_indices": sequence,
    "sample_field_comparisons": sample_checks,
    "sample_image_hashes_baseline": sample_image_hashes,
    "batch_field_comparisons": batch_checks,
    "full_one_pass_digest": full_pass_audit,
    "raw_frame_checks": raw_frame_checks,
    "video_setup_seconds": video_setup_seconds,
    "dataset_setup_seconds": {"baseline": baseline_setup_seconds,
                              "dev_default": dev_default_setup_seconds,
                              "preloaded": preload_setup_seconds},
    "preloaded_bytes": preload.preloaded_bytes,
    "one_pass_timings": timings,
    "memory_mib": {"before_videos": memory_before, "after_videos": memory_after_videos,
                   "before_preload": memory_before_preload,
                   "after_preload": memory_after_preload,
                   "after_benchmark": rss_mib()},
    "rng_constructor_unchanged": True,
    "rng_augmentation_equal": True,
    "batch_size": 4,
    "num_workers": 0,
    "augmentation_timed": True,
    "shuffle_timed": True,
    "target6bba_access": False,
    "gpu_used": False,
    "training_run_started": False,
    "active_run_mutation": False,
    "kaggle_post": False,
}
print(json.dumps(result, sort_keys=True, allow_nan=False))
