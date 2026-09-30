"""EXP212: hidden-compatible production form of the EXP209 pooled-OOF frontier."""

from __future__ import annotations

import csv
import gc
import hashlib
import importlib.metadata
import json
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

SEED = 314159
COMPETITION = "biohub-cell-tracking-during-development"
FORWARD_SHA = "dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb"
REVERSE_SHA = "5c0f8358389af40a646a0fe3b4e8e88fb1b1c155da12e92efa3c944eeb499366"
DEEPCENTER_SHA = "ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e"
OOF_SCORE = 0.6815218332750073

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working")
TEST_DIR = INPUT / "competitions" / COMPETITION / "test"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_one(candidates: list[Path], label: str) -> Path:
    found = [path for path in candidates if path.exists()]
    if len(found) != 1:
        raise FileNotFoundError({"label": label, "candidates": list(map(str, candidates)), "found": list(map(str, found))})
    return found[0]


SUPPORT = locate_one(
    [
        INPUT / "datasets" / "pilkwang" / "biohub-tracking-support-pack-50ep-v1",
        INPUT / "biohub-tracking-support-pack-50ep-v1",
    ],
    "support pack",
)
ARTIFACTS = locate_one(
    [
        INPUT / "datasets" / "dmitriigluzdov" / "biohub-exp209-pooled-oof-frontier-models",
        INPUT / "biohub-exp209-pooled-oof-frontier-models",
    ],
    "EXP209 artifacts",
)

NUMERICAL_PACKAGES = ("numpy", "scipy", "numba", "llvmlite", "torch")
numerical_versions_before = {name: importlib.metadata.version(name) for name in NUMERICAL_PACKAGES}
subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--quiet",
        "--no-index",
        "--no-deps",
        "--force-reinstall",
        "--find-links",
        str(SUPPORT / "wheels"),
        "-r",
        str(SUPPORT / "requirements-unet-ilp-kaggle-predownload.txt"),
    ]
)
numerical_versions_after = {name: importlib.metadata.version(name) for name in NUMERICAL_PACKAGES}
if numerical_versions_before != numerical_versions_after:
    raise RuntimeError("Offline support installation changed the preserved numerical stack")
print(json.dumps({"preserved_numerical_stack": numerical_versions_after}), flush=True)

REPO = WORK / "tracking_repo"
if REPO.exists():
    shutil.rmtree(REPO)
shutil.copytree(SUPPORT / "repo", REPO)
sys.path[:0] = [str(ARTIFACTS), str(REPO / "src"), str(REPO / "scripts")]

# Import binary packages only after offline installation has completed.
# Importing NumPy before pip replaces its files caused the v3 mixed-module failure.
import numpy as np
import torch
import zarr
from scipy.spatial import cKDTree
from biohub_tracking.io import open_dataset
from predict_unet_transformer import PredictConfig, load_model, predict_video
from evaluate_cached_intensity_centroid_refinement import refine_movie
from evaluate_cached_short_track_family import filter_family
from evaluate_coordinate_consensus import registered_links
from evaluate_synthetic_gap_deepcenter import close_synthetic_gaps, load_bundle


FORWARD_WEIGHT = ARTIFACTS / "forward_44b6_model" / "edge_predictor_best.pth"
REVERSE_WEIGHT = ARTIFACTS / "reverse_6bba_model" / "edge_predictor_best.pth"
DEEPCENTER_WEIGHT = ARTIFACTS / "reverse_6bba_model" / "deepcenter_best.pt"
for path, expected in (
    (FORWARD_WEIGHT, FORWARD_SHA),
    (REVERSE_WEIGHT, REVERSE_SHA),
    (DEEPCENTER_WEIGHT, DEEPCENTER_SHA),
):
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"artifact SHA mismatch: {path}: {actual} != {expected}")

test_paths = sorted(TEST_DIR.glob("*.zarr"))
if not test_paths:
    raise RuntimeError(f"no runtime test datasets under {TEST_DIR}")
test_names = [path.stem for path in test_paths]
if len(test_names) != len(set(test_names)):
    raise RuntimeError("duplicate runtime dataset IDs")

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.backends.cudnn.benchmark = False
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    torch.backends.cuda.enable_math_sdp(True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
unet_batch_size = 4
cfg = PredictConfig(
    det_threshold=0.985,
    det_tta=True,
    pool_kernel_um=3.0,
    edge_activation="softmax",
    threshold=0.02,
    use_ilp=True,
)

arm_dir = WORK / "exp209_arms"
chosen_dir = WORK / "exp209_chosen"
arm_dir.mkdir(exist_ok=True)
chosen_dir.mkdir(exist_ok=True)


def predict(model, window_size, downsample, path: Path) -> tuple[np.ndarray, list]:
    coords, edges = predict_video(
        model,
        path,
        device,
        cfg=cfg,
        window_size=window_size,
        unet_batch_size=unet_batch_size,
        downsample=downsample,
    )
    return np.asarray(coords, dtype=np.float64), list(edges)


def save_arm(path: Path, coords: np.ndarray, edges: list) -> None:
    edge_array = np.asarray(edges, dtype=np.float64).reshape((-1, 4)) if edges else np.empty((0, 4), dtype=np.float64)
    np.savez_compressed(
        path,
        coords=np.asarray(coords, dtype=np.float64),
        edge_source=edge_array[:, 0].astype(np.int64),
        edge_target=edge_array[:, 1].astype(np.int64),
        edge_score=edge_array[:, 2].astype(np.float64),
        edge_distance=edge_array[:, 3].astype(np.float64),
    )


def load_arm(path: Path) -> tuple[np.ndarray, list[tuple[int, int, float, float]]]:
    with np.load(path, allow_pickle=False) as payload:
        coords = payload["coords"].astype(np.float64)
        edges = [
            (int(s), int(t), float(p), float(d))
            for s, t, p, d in zip(payload["edge_source"], payload["edge_target"], payload["edge_score"], payload["edge_distance"])
        ]
    return coords, edges


def agreement_count(a: np.ndarray, b: np.ndarray, scale: np.ndarray, radius_um: float = 2.0) -> int:
    matched = 0
    times = sorted(set(a[:, 0].astype(int)).intersection(set(b[:, 0].astype(int)))) if len(a) and len(b) else []
    for timepoint in times:
        ai = np.flatnonzero(a[:, 0].astype(int) == timepoint)
        bi = np.flatnonzero(b[:, 0].astype(int) == timepoint)
        if not len(ai) or not len(bi):
            continue
        ap = a[ai, 1:4] * scale
        bp = b[bi, 1:4] * scale
        distance, a_to_b = cKDTree(bp).query(ap, k=1)
        _, b_to_a = cKDTree(ap).query(bp, k=1)
        matched += sum(
            float(dist) < radius_um and int(b_to_a[int(j)]) == i
            for i, (dist, j) in enumerate(zip(distance, a_to_b))
        )
    return int(matched)


def selector(a: tuple[np.ndarray, list], b: tuple[np.ndarray, list], scale: np.ndarray) -> tuple[str, dict]:
    a_coords, a_edges = a
    b_coords, b_edges = b
    matched = agreement_count(a_coords, b_coords, scale)
    a_agreement = matched / max(len(a_coords), 1)
    b_agreement = matched / max(len(b_coords), 1)
    a_continuity = len(a_edges) / max(len(a_coords), 1)
    b_continuity = len(b_edges) / max(len(b_coords), 1)
    # Frozen label-free precision proxy: prefer the arm with fewer unmatched
    # detections relative to its own size, then the less fragmented graph.
    choice = "forward" if (a_agreement, a_continuity, -len(a_coords)) >= (b_agreement, b_continuity, -len(b_coords)) else "reverse"
    return choice, {
        "mutual_matches_2um": matched,
        "forward_agreement_fraction": a_agreement,
        "reverse_agreement_fraction": b_agreement,
        "forward_continuity": a_continuity,
        "reverse_continuity": b_continuity,
    }


telemetry = []

# EXP209 forward arm: model trained on 44b6, centroid (3,5,5), min8.
model, window_size, downsample = load_model(FORWARD_WEIGHT, device)
model.eval()
for path in test_paths:
    prefix = path.stem.split("_", 1)[0]
    if prefix == "44b6":
        continue
    raw_coords, _ = predict(model, window_size, downsample, path)
    scale = np.asarray(open_dataset(path, require_tracks=False, load_image=False).scale, dtype=np.float64)
    image = zarr.open(str(path), mode="r")["0"]
    refined_coords, _ = refine_movie(image, raw_coords, scale, (3, 5, 5))
    links = registered_links(refined_coords, scale)
    coords, edges, stats = filter_family(refined_coords, links, {}, 8)
    save_arm(arm_dir / f"{path.stem}__forward.npz", coords, edges)
    telemetry.append({"dataset": path.stem, "arm": "forward", "raw_nodes": len(raw_coords), "nodes": len(coords), "edges": len(edges), "filter": stats})
del model
gc.collect()
if device.type == "cuda":
    torch.cuda.empty_cache()

# EXP209 reverse arm: model trained on 6bba, EXP191 gap gate, min6.
deepcenter = load_bundle(DEEPCENTER_WEIGHT, DEEPCENTER_SHA)
model, window_size, downsample = load_model(REVERSE_WEIGHT, device)
model.eval()
for path in test_paths:
    prefix = path.stem.split("_", 1)[0]
    if prefix == "6bba":
        continue
    raw_coords, _ = predict(model, window_size, downsample, path)
    scale = np.asarray(open_dataset(path, require_tracks=False, load_image=False).scale, dtype=np.float64)
    base_edges = registered_links(raw_coords, scale)
    gap_coords, gap_edges, gap_stats = close_synthetic_gaps(
        raw_coords,
        base_edges,
        scale,
        path,
        deepcenter,
        gap_close_um=4.5,
        deepcenter_threshold=0.20,
        deepcenter_confirm_min_span_um=8.5,
        synthetic_max_fraction=0.05,
    )
    coords, edges, stats = filter_family(gap_coords, gap_edges, {}, 6)
    reverse_path = arm_dir / f"{path.stem}__reverse.npz"
    save_arm(reverse_path, coords, edges)
    telemetry.append({"dataset": path.stem, "arm": "reverse", "raw_nodes": len(raw_coords), "nodes": len(coords), "edges": len(edges), "gap": gap_stats, "filter": stats})

    forward_path = arm_dir / f"{path.stem}__forward.npz"
    if prefix == "44b6":
        choice, selection = "reverse", {"reason": "exact reciprocal OOF route"}
    else:
        forward = load_arm(forward_path)
        reverse = (coords, edges)
        choice, selection = selector(forward, reverse, scale)
    chosen = load_arm(forward_path) if choice == "forward" else (coords, edges)
    save_arm(chosen_dir / f"{path.stem}.npz", *chosen)
    telemetry.append({"dataset": path.stem, "selected_arm": choice, "selection": selection})
del model, deepcenter
gc.collect()
if device.type == "cuda":
    torch.cuda.empty_cache()

# Public placeholder 6bba IDs take the exact forward OOF route and were not
# visited in the reverse loop, so materialize them now.
for path in test_paths:
    if path.stem.split("_", 1)[0] == "6bba":
        source = arm_dir / f"{path.stem}__forward.npz"
        shutil.copy2(source, chosen_dir / f"{path.stem}.npz")
        telemetry.append({"dataset": path.stem, "selected_arm": "forward", "selection": {"reason": "exact reciprocal OOF route"}})

columns = ["id", "dataset", "row_type", "node_id", "t", "z", "y", "x", "source_id", "target_id"]
submission_path = WORK / "submission.csv"
row_id = 0
total_nodes = total_edges = 0
with submission_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for path in test_paths:
        coords, edges = load_arm(chosen_dir / f"{path.stem}.npz")
        shape = open_dataset(path, require_tracks=False, load_image=False).image_shape
        indegree: dict[int, int] = {}
        outdegree: dict[int, int] = {}
        for node_id, row in enumerate(coords):
            t = int(row[0])
            point = [float(value) for value in row[1:4]]
            if not all(math.isfinite(value) for value in point):
                raise AssertionError(f"{path.stem}: non-finite coordinate")
            if not (0 <= t < shape[0] and all(0 <= value < limit for value, limit in zip(point, shape[1:4]))):
                raise AssertionError(f"{path.stem}: coordinate outside runtime volume")
            writer.writerow({"id": row_id, "dataset": path.stem, "row_type": "node", "node_id": node_id, "t": t, "z": format(point[0], ".17g"), "y": format(point[1], ".17g"), "x": format(point[2], ".17g"), "source_id": -1, "target_id": -1})
            row_id += 1
        for source, target, _, _ in sorted(edges, key=lambda edge: (int(edge[0]), int(edge[1]))):
            source, target = int(source), int(target)
            if not (0 <= source < len(coords) and 0 <= target < len(coords)):
                raise AssertionError(f"{path.stem}: dangling edge")
            if int(coords[target, 0]) != int(coords[source, 0]) + 1:
                raise AssertionError(f"{path.stem}: nonconsecutive edge")
            outdegree[source] = outdegree.get(source, 0) + 1
            indegree[target] = indegree.get(target, 0) + 1
            writer.writerow({"id": row_id, "dataset": path.stem, "row_type": "edge", "node_id": -1, "t": -1, "z": -1, "y": -1, "x": -1, "source_id": source, "target_id": target})
            row_id += 1
        if max(indegree.values(), default=0) > 1 or max(outdegree.values(), default=0) > 1:
            raise AssertionError(f"{path.stem}: degree contract failed")
        total_nodes += len(coords)
        total_edges += len(edges)

receipt = {
    "status": "PASS_EXP212_EXP209_OOF_FRONTIER_PRODUCTION",
    "runtime_dataset_ids": test_names,
    "runtime_dataset_count": len(test_names),
    "submission_sha256": sha256(submission_path),
    "rows": row_id,
    "nodes": total_nodes,
    "edges": total_edges,
    "oof_reference": {"experiment": "EXP209", "pooled_score": OOF_SCORE, "scope": "175-movie reciprocal embryo-held-out cross-fit OOF; not a score claim for the unknown-embryo selector"},
    "hidden_dataflow": "dynamic runtime competition test/*.zarr -> two reciprocal models for unseen embryo IDs -> fixed label-free 2um agreement selector -> one root submission.csv",
    "weights": {"forward": FORWARD_SHA, "reverse": REVERSE_SHA, "deepcenter": DEEPCENTER_SHA},
    "telemetry": telemetry,
}
(WORK / "exp212_runtime_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: receipt[key] for key in ("status", "runtime_dataset_count", "submission_sha256", "rows", "nodes", "edges")}, indent=2))
