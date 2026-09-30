"""Score fixed detector coordinates with a second model's edge head."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@torch.no_grad()
def score_movie(model, ds_path, fixed_coords, device, downsample, threshold):
    from biohub_tracking.io import open_dataset
    from predict_unet_transformer import _load_frame, extract_pos_features
    import zarr

    ds = open_dataset(ds_path, normalize=False, load_image=False, downsample=downsample)
    zarr_arr = zarr.open_group(str(ds.zarr_path), mode="r")["0"]
    q_low = float(ds.quantiles["0.001"])
    q_high = float(ds.quantiles["0.999"])
    image_shape = ds.image_shape
    target_shape = list(image_shape[1:])
    ds_arr = np.asarray(downsample, dtype=np.float32)
    ds_tensor = torch.from_numpy(ds_arr).to(device)
    by_time = {
        time: np.flatnonzero(fixed_coords[:, 0].astype(int) == time)
        for time in range(image_shape[0])
    }
    edges = []
    for time in range(image_shape[0] - 1):
        source_ids = by_time[time]
        target_ids = by_time[time + 1]
        if not len(source_ids) or not len(target_ids):
            continue
        images = torch.stack([
            _load_frame(zarr_arr, time, target_shape, downsample),
            _load_frame(zarr_arr, time + 1, target_shape, downsample),
        ])
        images = ((images - q_low) / (q_high - q_low + 1e-6)).clamp(0.0)
        unet_out, _ = model.encode(images[None].to(device, dtype=torch.float32))
        grid_coords = []
        pos_features = []
        masks = []
        for frame_index, node_ids in enumerate((source_ids, target_ids)):
            original = fixed_coords[node_ids].astype(np.float32)
            grid = original[:, 1:] / ds_arr
            relative = np.column_stack([
                np.full(len(original), frame_index, dtype=np.float32), grid
            ])
            grid_coords.append(torch.from_numpy(grid)[None].to(device))
            pos_features.append(
                torch.from_numpy(extract_pos_features(relative, (2,) + image_shape[1:]))[None].to(device)
            )
            masks.append(torch.ones((1, len(node_ids)), dtype=torch.bool, device=device))
        features = [
            model._index_features(unet_out[:, frame], grid_coords[frame], masks[frame])
            for frame in (0, 1)
        ]
        logits = model.predict_edges(
            features[0], features[1],
            grid_coords[0] * ds_tensor, grid_coords[1] * ds_tensor,
            pos_features[0], pos_features[1], masks[0], masks[1],
        )[0]
        probs = torch.softmax(logits, dim=0).cpu().numpy()
        candidates = sorted(
            ((float(probs[i, j]), i, j) for i in range(len(source_ids))
             for j in range(len(target_ids)) if probs[i, j] > threshold),
            reverse=True,
        )
        child_count = {}
        parent_count = {}
        for probability, i, j in candidates:
            if child_count.get(i, 0) >= 2 or parent_count.get(j, 0) >= 1:
                continue
            source = int(source_ids[i])
            target = int(target_ids[j])
            distance = float(np.linalg.norm(fixed_coords[source, 1:4] - fixed_coords[target, 1:4]))
            edges.append((source, target, probability, distance))
            child_count[i] = child_count.get(i, 0) + 1
            parent_count[j] = 1
    return edges


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--fixed-cache-dir", type=Path, required=True)
    parser.add_argument("--movies-json", type=Path, required=True)
    parser.add_argument("--movie-key", required=True)
    parser.add_argument("--output-cache-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.02)
    args = parser.parse_args()

    sys.path.insert(0, str(args.repo.resolve() / "src"))
    sys.path.insert(0, str(args.repo.resolve() / "scripts"))
    from predict_unet_transformer import load_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("GPU required")
    model, window_size, downsample = load_model(args.weights, device)
    if window_size != 2:
        raise AssertionError({"window_size": window_size})
    model.eval()
    movies = json.loads(args.movies_json.read_text(encoding="utf-8"))[args.movie_key]
    args.output_cache_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for movie in movies:
        fixed_path = args.fixed_cache_dir / f"{Path(movie).stem}.npz"
        with np.load(fixed_path) as cache:
            coords = cache["coords"].astype(np.float32)
        edges = score_movie(
            model, args.data_dir / movie, coords, device, tuple(downsample), args.threshold
        )
        edge_array = np.asarray(edges, dtype=np.float64).reshape(-1, 4)
        output = args.output_cache_dir / f"{Path(movie).stem}.npz"
        np.savez_compressed(
            output,
            coords=coords,
            edges=edge_array,
            edge_source=edge_array[:, 0].astype(np.int64),
            edge_target=edge_array[:, 1].astype(np.int64),
            edge_probability=edge_array[:, 2].astype(np.float32),
            edge_distance=edge_array[:, 3].astype(np.float32),
        )
        manifest.append({"dataset": movie, "edges": len(edges), "bytes": output.stat().st_size, "sha256": sha256(output)})
    receipt = {
        "status": "PASS_FIXED_COORDINATE_EDGE_SCORING",
        "weights_sha256": sha256(args.weights),
        "fixed_cache_dir": str(args.fixed_cache_dir),
        "threshold": args.threshold,
        "movies": manifest,
    }
    receipt_path = args.output_cache_dir.parent / f"{args.output_cache_dir.name}_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
