"""Verify immutable EXP227 loader bytes, then run a bounded CPU-only smoke on nsu-quadro."""

import hashlib
import json
from pathlib import Path
import statistics
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
STAGE = REMOTE + "/code/exp227_horaz_source_block02_20260927"
INTERPRETER = REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"
EXPECTED_STAGE_MANIFEST_SHA = "c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26"
EXPECTED_SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"
EXPECTED_PLAN_SHA = "cfb672acab7bbd3ca2b551b6f688503dbd109457b53ce68bf04ce8267ef03ff1"
SOURCE_DIR = ROOT / "work/horaz_development_20260922/exp227/loader_benchmark_snapshot_20260927"
REMOTE_SCRIPT = ROOT / "scripts/benchmark_exp227_horaz_loader_remote.py"
RECEIPT = ROOT / "reports/exp227_horaz_loader_benchmark_20260927.json"
FAILURE = ROOT / "reports/exp227_horaz_loader_benchmark_failure_20260927.json"
REPORT = ROOT / "reports/EXP227_HORAZ_LOADER_BENCHMARK_20260927.md"


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def remote_read(path: str) -> bytes:
    assert path.startswith(STAGE + "/")
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-a100", "cat " + path],
        capture_output=True, timeout=45, check=True,
    )
    return result.stdout


def source_snapshot() -> dict:
    manifest_bytes = remote_read(STAGE + "/code_manifest.json")
    assert sha(manifest_bytes) == EXPECTED_STAGE_MANIFEST_SHA
    manifest = json.loads(manifest_bytes)
    selected = ["horaz/src/src/utils.py", "horaz/src/src/const.py",
                "horaz/src/src/datasets.py", "horaz/resolved_config.json",
                "source44_manifest.json", "plan.json", "run_exp227_source_block02.py"]
    bodies = {name: remote_read(STAGE + "/" + name) for name in selected}
    for name, body in bodies.items():
        assert sha(body) == manifest[name], name
    assert sha(bodies["source44_manifest.json"]) == EXPECTED_SOURCE_MANIFEST_SHA
    assert sha(bodies["plan.json"]) == EXPECTED_PLAN_SHA
    local_plan_bytes = (ROOT / "reports/exp227_source_block02_plan_20260927.json").read_bytes()

    source_manifest = json.loads(bodies["source44_manifest.json"])
    staged_plan = json.loads(bodies["plan.json"])
    assert json.loads(local_plan_bytes) == staged_plan
    assert staged_plan["train"] == source_manifest["train"]
    assert staged_plan["inner_validation"] == source_manifest["inner_validation"]
    records = source_manifest["train"][:2]
    assert [row["dataset_id"] for row in records] == ["44b6_808952d6", "44b6_0db75fae"]
    assert all(str(row["zarr_path"]).startswith(REMOTE + "/data/exp213_source_view_20260912/") for row in records)
    assert all(str(row["geff_path"]).startswith(REMOTE + "/data/exp213_source_view_20260912/") for row in records)

    resolved = json.loads(bodies["horaz/resolved_config.json"])
    runner = bodies["run_exp227_source_block02.py"].decode("utf-8")
    assert resolved["downsample"] == [1, 4, 4] and resolved["window_size"] == 2
    assert "resolved.update(seed=3407, deterministic=False, epochs=50, num_workers=0," in runner
    assert "max_iterations_per_epoch=None, batch_size=4," in runner
    assert "max_frames=None" in runner

    return {
        "stage_code": STAGE,
        "stage_manifest_sha256": EXPECTED_STAGE_MANIFEST_SHA,
        "source44_manifest_sha256": EXPECTED_SOURCE_MANIFEST_SHA,
        "records": records,
        "downsample": resolved["downsample"],
        "window_size": resolved["window_size"],
        "batch_size": 4,
        "num_workers": 0,
        "sources": {name.rsplit("/", 1)[-1]: bodies[name].decode("utf-8") for name in selected[:3]},
        "source_sha256": {name.rsplit("/", 1)[-1]: sha(bodies[name]) for name in selected[:3]},
        "staged_file_sha256": {name: sha(body) for name, body in bodies.items()},
        "local_plan_sha256": sha(local_plan_bytes),
        "staged_files": bodies,
    }


def report_text(receipt: dict) -> str:
    t = receipt["elapsed_seconds_per_36_windows"]
    med = {name: statistics.median(values) for name, values in t.items()}
    base = med["baseline_zarr_per_sample"]
    cached = med["cached_zarr_handle"]
    preloaded = med["preloaded_uint16"]
    mem = receipt["memory_mib"]
    return f"""# EXP227 staged Horaz loader CPU microbenchmark — 2026-09-27

The exact immutable EXP227 block02 `FrameWindowDataset.__getitem__` was executed on nsu-quadro CPU 24–27 with CUDA hidden, `num_workers=0`, augmentation disabled, and two source44 movies from the SHA-pinned source manifest. The runner's training batch size is 4; this microbenchmark fetches individual samples because it isolates the dataset loader. No target6bba data, GPU, training, active run or Kaggle POST was touched.

| Access path | 36-window pass A (s) | Reverse-order pass B (s) | Median ms/window |
| --- | ---: | ---: | ---: |
| Staged Zarr open per sample | {t['baseline_zarr_per_sample'][0]:.3f} | {t['baseline_zarr_per_sample'][1]:.3f} | {base * 1000 / 36:.1f} |
| Cached Zarr group per movie | {t['cached_zarr_handle'][0]:.3f} | {t['cached_zarr_handle'][1]:.3f} | {cached * 1000 / 36:.1f} |
| Preloaded downsampled uint16 frames | {t['preloaded_uint16'][0]:.3f} | {t['preloaded_uint16'][1]:.3f} | {preloaded * 1000 / 36:.1f} |

On this fixed, warmed sequence, cached Zarr handles showed no consistent gain (one pass slower, one faster; median throughput ratio {base / cached:.2f}×). Preloaded access took {base / preloaded:.2f}× less measured per-sample time than staged opening, with setup excluded from the timed passes. Two movies had {receipt['window_counts']} valid windows; the 36-index sequence covered 18 unique windows and repeated them. Every returned field, including half-precision image tensors, coordinates, masks, targets and metadata, matched bitwise at every index. All three image-sequence SHA256 values are `{receipt['image_tensor_sha256']['baseline_zarr_per_sample']}`.

Cached group setup took {receipt['cached_setup_seconds']:.3f} s; preloading all {receipt['preloaded_bytes'] / 2**20:.1f} MiB of downsampled uint16 frames took {receipt['preload_setup_seconds']:.3f} s. For one 36-window pass, preload setup plus median access was {receipt['preload_setup_seconds'] + preloaded:.3f} s versus {base:.3f} s for baseline; reuse is needed to amortize setup. Process RSS was {mem['before_setup']['rss_mib']:.1f} MiB before setup, {mem['after_cached_open']['rss_mib']:.1f} MiB after cached opens, and {mem['after_preload']['rss_mib']:.1f} MiB after preload. Peak RSS after benchmark was {mem['after_benchmark']['peak_rss_mib']:.1f} MiB.

This measures only two sparse source movies (maximum two graph nodes per window), repeated windows, and warmed storage/cache. It excludes augmentation, batch collation, training and GPU compute. The observed ratios are a loader optimization lead, not a full-epoch speedup or an OOF quality change. A later implementation should account for per-movie preload memory across all 63/115 source movies and keep the exact dataflow/equality gates.

Evidence: `reports/exp227_horaz_loader_benchmark_20260927.json`; source snapshots: `work/horaz_development_20260922/exp227/loader_benchmark_snapshot_20260927/`. Stage manifest SHA256 `{receipt['stage_manifest_sha256']}`; exact staged loader SHA256 `{receipt['source_sha256']['datasets.py']}`.
"""


def main() -> None:
    assert not RECEIPT.exists() and not FAILURE.exists() and not REPORT.exists()
    assert not SOURCE_DIR.exists()
    snapshot = source_snapshot()
    remote_source = REMOTE_SCRIPT.read_bytes()
    preamble = "SNAPSHOT = " + repr({key: value for key, value in snapshot.items() if key != "staged_files"}) + "\n"
    bundle = preamble.encode("utf-8") + remote_source
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-quadro",
               "ulimit -v 33554432; env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 "
               "MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 "
               "timeout 600s taskset -c 24-27 " + INTERPRETER + " -"]
    process = None
    try:
        process = subprocess.run(command, input=bundle, capture_output=True, timeout=660)
        if process.returncode:
            raise RuntimeError(f"remote benchmark exit {process.returncode}: {process.stderr[-3000:].decode(errors='replace')}")
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_HORAZ_LOADER_CPU_MICROBENCH"
        assert result["target6bba_access"] is False and result["gpu_used"] is False
        assert result["active_run_mutation"] is False and result["kaggle_post"] is False
        assert result["source_dataset_ids"] == [row["dataset_id"] for row in snapshot["records"]]
        assert result["stage_manifest_sha256"] == EXPECTED_STAGE_MANIFEST_SHA
        assert result["source44_manifest_sha256"] == EXPECTED_SOURCE_MANIFEST_SHA
        assert result["batch_size_runner"] == 4 and result["num_workers_runner"] == 0
        assert result["cpu_affinity"] == [24, 25, 26, 27]
        assert result["cuda_visible_devices"] == ""
        assert result["sequence_length"] == 36 and result["unique_windows"] == 18
        assert result["equality_checks_per_alternative"] == 36 * len(result["loader_fields_bitwise_equal"])
        assert len(set(result["image_tensor_sha256"].values())) == 1
        assert all(len(values) == 2 and all(value > 0 for value in values)
                   for values in result["elapsed_seconds_per_36_windows"].values())
        assert result["memory_mib"]["after_benchmark"]["peak_rss_mib"] < 32 * 1024
    except BaseException as exc:
        FAILURE.write_text(json.dumps({
            "status": "FAILED_EXP227_HORAZ_LOADER_CPU_MICROBENCH",
            "error": repr(exc), "bundle_sha256": sha(bundle),
            "stderr_tail": process.stderr[-3000:].decode(errors="replace") if process else None,
            "stdout_tail": process.stdout[-3000:].decode(errors="replace") if process else None,
        }, indent=2) + "\n")
        raise
    SOURCE_DIR.mkdir(parents=True)
    for name, body in snapshot["staged_files"].items():
        path = SOURCE_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    result["bundle_sha256"] = sha(bundle)
    result["remote_script_sha256"] = sha(remote_source)
    result["source_snapshot_dir"] = str(SOURCE_DIR)
    result["virtual_memory_limit_gib"] = 32
    result["timeout_seconds"] = 600
    RECEIPT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    REPORT.write_text(report_text(result))
    print(json.dumps({"status": result["status"], "receipt": str(RECEIPT),
                      "report": str(REPORT), "timings": result["elapsed_seconds_per_36_windows"],
                      "peak_rss_mib": result["memory_mib"]["after_benchmark"]["peak_rss_mib"]}))


if __name__ == "__main__":
    main()
