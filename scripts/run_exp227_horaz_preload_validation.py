"""Audit an isolated Horaz preload development copy with a bounded source44 CPU run."""

import ast
import difflib
import hashlib
import json
from pathlib import Path
import statistics
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "work/horaz_development_20260922/exp227/loader_preload_dev_20260927"
BASELINE = ROOT / "work/horaz_development_20260922/exp227/loader_benchmark_snapshot_20260927"
SELECTION = ROOT / "reports/exp227_horaz_loader_movie_selection_20260927.json"
REMOTE_SCRIPT = ROOT / "scripts/verify_exp227_horaz_preload_remote.py"
RECEIPT = ROOT / "reports/exp227_horaz_preload_validation_20260927.json"
FAILURE = ROOT / "reports/exp227_horaz_preload_validation_failure_20260927.json"
REPORT = ROOT / "reports/EXP227_HORAZ_PRELOAD_VALIDATION_20260927.md"
PATCH = ROOT / "reports/exp227_horaz_preload_development_20260927.patch"
FOOTPRINT = ROOT / "reports/exp227_source44_preload_footprint_20260927.json"
REMOTE = "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
STAGE = REMOTE + "/code/exp227_horaz_source_block02_20260927"
INTERPRETER = REMOTE + "/envs/prepost/py3.11-stdlib-v1/bin/python"
STAGE_MANIFEST_SHA = "c469c62da6cc058b60f0c12ddb800321c37094036b8e68f404ec039df8ec7b26"
SOURCE_MANIFEST_SHA = "455cc9d546b1ea0f05e9674f9513800c70bf8faf851f8cb303397d27af1129f5"
CHANGED_FILES = {"horaz/src/src/datasets.py", "horaz/src/src/train.py"}


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def prepare_dev_manifest() -> tuple[dict, str, dict]:
    parent_file = DEV / "parent_code_manifest.json"
    current_manifest_file = DEV / "code_manifest.json"
    assert not parent_file.exists()
    original_bytes = current_manifest_file.read_bytes()
    assert sha(original_bytes) == STAGE_MANIFEST_SHA
    original = json.loads(original_bytes)
    changed = {name for name, digest in original.items()
               if sha((DEV / name).read_bytes()) != digest}
    assert changed == CHANGED_FILES, changed
    assert all(sha((BASELINE / name).read_bytes()) == original[name]
               for name in ("horaz/src/src/datasets.py", "horaz/src/src/const.py",
                            "horaz/src/src/utils.py"))
    train_text = (DEV / "horaz/src/src/train.py").read_text()
    dataset_text = (DEV / "horaz/src/src/datasets.py").read_text()
    ast.parse(train_text)
    ast.parse(dataset_text)
    assert 'getattr(cfg, "preload_uint16_frames", False)' in train_text
    assert train_text.count("preload_uint16_frames=preload_uint16_frames") == 2
    assert "preload_uint16_frames: bool = False" in dataset_text
    assert "preload_max_bytes: int = 8 * 1024**3" in dataset_text
    parent_file.write_bytes(original_bytes)
    new_manifest = {
        path.relative_to(DEV).as_posix(): sha(path.read_bytes())
        for path in sorted(DEV.rglob("*")) if path.is_file() and path.name != "code_manifest.json"
    }
    current_manifest_file.write_text(json.dumps(new_manifest, indent=2) + "\n")
    new_sha = sha(current_manifest_file.read_bytes())
    assert all(sha((DEV / name).read_bytes()) == digest for name, digest in new_manifest.items())
    return original, new_sha, new_manifest


def make_patch():
    parts = []
    for name in sorted(CHANGED_FILES):
        before = (BASELINE / name).read_text() if (BASELINE / name).exists() else None
        if before is None:
            # train.py was absent from the earlier seven-file snapshot; use the
            # parent-stage version fetched read-only for this one diff.
            remote = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                 "nsu-a100", "cat " + STAGE + "/" + name],
                capture_output=True, timeout=45, check=True,
            ).stdout
            parent = json.loads((DEV / "parent_code_manifest.json").read_text())
            assert sha(remote) == parent[name]
            before = remote.decode("utf-8")
        after = (DEV / name).read_text()
        parts.extend(difflib.unified_diff(before.splitlines(keepends=True),
                                          after.splitlines(keepends=True),
                                          fromfile="stage/" + name,
                                          tofile="dev/" + name))
    PATCH.write_text("".join(parts))
    assert PATCH.stat().st_size > 0


def build_snapshot(new_manifest_sha: str, new_manifest: dict) -> dict:
    selection = json.loads(SELECTION.read_text())
    assert selection["status"] == "PASS_SOURCE44_LOADER_MOVIE_SELECTION_METADATA_ONLY"
    assert selection["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
    ids = selection["selected_ids_sparse_then_dense"]
    assert ids == ["44b6_33b596bf", "44b6_d29c9ab2"]
    manifest_bytes = (DEV / "source44_manifest.json").read_bytes()
    assert sha(manifest_bytes) == SOURCE_MANIFEST_SHA
    source = json.loads(manifest_bytes)
    record_by_id = {row["dataset_id"]: row for row in source["train"]}
    records = [record_by_id[name] for name in ids]
    assert all(row["dataset_id"].startswith("44b6_") for row in records)
    assert selection["estimated_preload_bytes"] < 1 * 2**30
    sources = {
        "utils": (DEV / "horaz/src/src/utils.py").read_text(),
        "const": (DEV / "horaz/src/src/const.py").read_text(),
        "baseline_datasets": (BASELINE / "horaz/src/src/datasets.py").read_text(),
        "dev_datasets": (DEV / "horaz/src/src/datasets.py").read_text(),
    }
    assert sha(sources["baseline_datasets"].encode()) == json.loads(
        (DEV / "parent_code_manifest.json").read_text())["horaz/src/src/datasets.py"]
    assert sha(sources["dev_datasets"].encode()) == new_manifest["horaz/src/src/datasets.py"]
    return {"records": records,
            "estimated_preload_bytes": selection["estimated_preload_bytes"],
            "stage_manifest_sha256": STAGE_MANIFEST_SHA,
            "dev_manifest_sha256": new_manifest_sha,
            "source_manifest_sha256": SOURCE_MANIFEST_SHA,
            "sources": sources,
            "source_sha256": {name: sha(body.encode()) for name, body in sources.items()},
            "file_origins": {
                "utils": STAGE + "/horaz/src/src/utils.py",
                "const": STAGE + "/horaz/src/src/const.py",
                "baseline_datasets": STAGE + "/horaz/src/src/datasets.py",
                "dev_datasets": str(DEV / "horaz/src/src/datasets.py"),
            }}


def render_report(r: dict) -> str:
    times = r["one_pass_timings"]
    med = {name: statistics.median(row["seconds"] for row in values)
           for name, values in times.items()}
    setup = r["dataset_setup_seconds"]
    mem = r["memory_mib"]
    footprint = json.loads(FOOTPRINT.read_text()) if FOOTPRINT.exists() else None
    footprint_note = (
        f"A separate source44-train metadata-only estimate for all 63 movies is "
        f"{footprint['total_array_bytes'] / 2**30:.2f} GiB of uint16 arrays under the "
        f"8 GiB option cap (`reports/exp227_source44_preload_footprint_20260927.json`). "
        "Full-source process RSS and GPU training remain unmeasured.\n\n"
        if footprint is not None else ""
    )
    return f"""# EXP227 Horaz uint16 preload development check — 2026-09-27

An isolated development copy of immutable EXP227 block02 adds an optional `preload_uint16_frames` argument to `FrameWindowDataset` and connects it to both train and validation loaders through `getattr(cfg, "preload_uint16_frames", False)`. The default path keeps per-sample Zarr access. The option stores downsampled uint16 frames, converts only each requested window to float32, and leaves duplicate-frame checks, interpolation, normalization, augmentation, metadata and output fields in the original order. The isolated code manifest SHA256 is `{r['dev_manifest_sha256']}`; parent stage manifest SHA256 is `{r['stage_manifest_sha256']}`. This copy has not been launched for training.

Source44 training movies `{r['source_dataset_ids'][0]}` (sparse) and `{r['source_dataset_ids'][1]}` (dense) were selected by reading GEFF and image **metadata only** across the pinned 63-movie source manifest. They produced {r['window_counts']} valid windows and maximum {r['max_nodes_subset']} nodes/window. All validation ran on nsu-quadro CPU24–27 with CUDA hidden, 32 GiB virtual limit and no target6bba data.

Parity passed: six raw uint16 frames at start/middle/end matched byte for byte; {r['sample_field_comparisons']} direct field comparisons across repeated and first/last valid windows passed with augmentation off/on and seeds 0, 3407 and 209. Constructor and augmentation Torch RNG states matched. Two batch4 collations passed (augmentation off/on; {r['batch_field_comparisons']} field comparisons). A full shuffled, augmented, `num_workers=0` one-pass digest and final RNG state matched among original, new default and preloaded paths across all {sum(r['window_counts'])} windows.

| Loader path | Dataset setup (s) | One-pass A (s) | Reverse-order one-pass B (s) | Median one-pass (s) |
| --- | ---: | ---: | ---: | ---: |
| Original staged | {setup['baseline']:.3f} | {times['baseline'][0]['seconds']:.3f} | {times['baseline'][1]['seconds']:.3f} | {med['baseline']:.3f} |
| New default | {setup['dev_default']:.3f} | {times['dev_default'][0]['seconds']:.3f} | {times['dev_default'][1]['seconds']:.3f} | {med['dev_default']:.3f} |
| New preloaded | {setup['preloaded']:.3f} | {times['preloaded'][0]['seconds']:.3f} | {times['preloaded'][1]['seconds']:.3f} | {med['preloaded']:.3f} |

The preloaded arrays hold {r['preloaded_bytes'] / 2**20:.1f} MiB. RSS was {mem['before_preload']['rss_mib']:.1f} MiB before preload, {mem['after_preload']['rss_mib']:.1f} MiB after, and peak {mem['after_benchmark']['peak_rss_mib']:.1f} MiB. Median preload setup plus one pass was {setup['preloaded'] + med['preloaded']:.3f} s versus {setup['baseline'] + med['baseline']:.3f} s for original. The timed passes include batch collation, shuffle and augmentation; model/GPU compute and all other movies are excluded. These numbers support consideration of a separately registered GPU pilot, not a full-epoch speedup or OOF quality claim.

{footprint_note}Evidence: `reports/exp227_horaz_preload_validation_20260927.json`; exact source diff: `reports/exp227_horaz_preload_development_20260927.patch`; isolated copy: `work/horaz_development_20260922/exp227/loader_preload_dev_20260927/`.
"""


def main() -> None:
    assert not any(path.exists() for path in (RECEIPT, FAILURE, REPORT, PATCH))
    parent_manifest, dev_manifest_sha, dev_manifest = prepare_dev_manifest()
    assert len(parent_manifest) == 32
    make_patch()
    snapshot = build_snapshot(dev_manifest_sha, dev_manifest)
    remote_source = REMOTE_SCRIPT.read_bytes()
    ast.parse(remote_source.decode())
    bundle = ("SNAPSHOT = " + repr(snapshot) + "\n").encode() + remote_source
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "nsu-quadro",
               "ulimit -v 33554432; env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=4 "
               "MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 PYTHONDONTWRITEBYTECODE=1 "
               "timeout 900s taskset -c 24-27 " + INTERPRETER + " -"]
    process = None
    try:
        process = subprocess.run(command, input=bundle, capture_output=True, timeout=960)
        if process.returncode:
            raise RuntimeError(f"remote CPU validation exit {process.returncode}: "
                               + process.stderr[-4000:].decode(errors="replace"))
        result = json.loads(process.stdout)
        assert result["status"] == "PASS_EXP227_HORAZ_PRELOAD_CPU_VALIDATION"
        assert result["source_dataset_ids"] == [row["dataset_id"] for row in snapshot["records"]]
        assert result["source_manifest_sha256"] == SOURCE_MANIFEST_SHA
        assert result["stage_manifest_sha256"] == STAGE_MANIFEST_SHA
        assert result["preloaded_bytes"] == snapshot["estimated_preload_bytes"]
        assert result["cpu_affinity"] == [24, 25, 26, 27]
        assert result["cuda_visible_devices"] == ""
        assert result["num_workers"] == 0 and result["batch_size"] == 4
        assert result["rng_constructor_unchanged"] and result["rng_augmentation_equal"]
        assert result["target6bba_access"] is False and result["gpu_used"] is False
        assert result["training_run_started"] is False and result["active_run_mutation"] is False
        assert result["kaggle_post"] is False
        assert len(set(tuple(row) for row in result["full_one_pass_digest"].values())) == 1
        assert result["memory_mib"]["after_benchmark"]["peak_rss_mib"] < 8 * 1024
    except BaseException as exc:
        FAILURE.write_text(json.dumps({
            "status": "FAILED_EXP227_HORAZ_PRELOAD_CPU_VALIDATION",
            "error": repr(exc), "bundle_sha256": sha(bundle),
            "dev_manifest_sha256": dev_manifest_sha,
            "stderr_tail": process.stderr[-4000:].decode(errors="replace") if process else None,
            "stdout_tail": process.stdout[-4000:].decode(errors="replace") if process else None,
        }, indent=2) + "\n")
        raise
    result["dev_manifest_sha256"] = dev_manifest_sha
    result["dev_changed_file_sha256"] = {name: dev_manifest[name] for name in sorted(CHANGED_FILES)}
    result["selection_receipt_sha256"] = sha(SELECTION.read_bytes())
    result["patch_sha256"] = sha(PATCH.read_bytes())
    result["remote_script_sha256"] = sha(remote_source)
    result["bundle_sha256"] = sha(bundle)
    result["virtual_memory_limit_gib"] = 32
    result["timeout_seconds"] = 900
    RECEIPT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    REPORT.write_text(render_report(result))
    print(json.dumps({"status": result["status"], "receipt": str(RECEIPT),
                      "report": str(REPORT), "timings": result["one_pass_timings"],
                      "peak_rss_mib": result["memory_mib"]["after_benchmark"]["peak_rss_mib"]}))


if __name__ == "__main__":
    main()
