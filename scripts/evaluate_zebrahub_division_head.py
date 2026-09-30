"""Teacher-forced edge/division diagnostics on verified Zebrahub shards."""

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
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--pattern", default="valid_*.npz")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.tracking_scripts.resolve()))
    from train_unet_transformer import TemporalUNet3D, UNetNodeTransformer, extract_pos_features

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("GPU is required for the exact model diagnostic")
    model = UNetNodeTransformer(
        unet=TemporalUNet3D(in_channels=1, out_channels=32, layers=[32, 64, 128]),
        unet_out_channels=32,
        pos_feat_dim=32,
    ).to(device)
    state = torch.load(args.checkpoint, map_location=device, weights_only=True)
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        raise AssertionError({"missing": missing, "unexpected": unexpected})
    model.eval()

    thresholds = [0.5, 0.2, 0.1, 0.05, 0.02]
    stats = {
        str(value): {
            "edge_tp": 0,
            "edge_fn": 0,
            "predicted_edges": 0,
            "division_parent_tp": 0,
            "division_parent_fn": 0,
            "predicted_fork_parents": 0,
            "false_fork_parents": 0,
        }
        for value in thresholds
    }
    files = sorted(args.data_dir.glob(args.pattern))
    if not files:
        raise FileNotFoundError({"data_dir": str(args.data_dir), "pattern": args.pattern})
    true_division_parents = 0
    for path in files:
        with np.load(path) as shard:
            volumes = shard["volumes"].astype(np.float32)
            coords = shard["coords_tzyx"].astype(np.float32)
            edges = shard["edges"].astype(np.int64)
        ids = [np.flatnonzero(coords[:, 0] == frame) for frame in (0, 1)]
        offsets = [{int(node): i for i, node in enumerate(frame_ids)} for frame_ids in ids]
        target = np.zeros((len(ids[0]), len(ids[1])), dtype=np.uint8)
        for source, destination in edges:
            if int(source) in offsets[0] and int(destination) in offsets[1]:
                target[offsets[0][int(source)], offsets[1][int(destination)]] = 1
        true_div = target.sum(axis=1) > 1
        true_division_parents += int(true_div.sum())

        q_low, q_high = np.percentile(volumes, [0.1, 99.9])
        normalized = np.clip(
            (volumes - q_low) / (q_high - q_low + 1e-6), 0, None
        ).astype(np.float32)
        images = torch.from_numpy(normalized).to(device)
        unet_out, _ = model.encode(images[None])
        features = []
        positions = []
        masks = []
        for frame in (0, 1):
            xyz = torch.from_numpy(coords[ids[frame], 1:]).to(device)
            mask = torch.ones((1, len(xyz)), dtype=torch.bool, device=device)
            feat = model._index_features(unet_out[:, frame], xyz[None], mask)
            full = coords[ids[frame]]
            pos = torch.from_numpy(extract_pos_features(full, (2, 64, 64, 64))).to(device)
            features.append(feat)
            positions.append(pos[None])
            masks.append(mask)
        scale = torch.tensor((1.0, 4.0, 4.0), device=device)
        logits = model.predict_edges(
            features[0], features[1],
            torch.from_numpy(coords[ids[0], 1:]).to(device)[None] * scale,
            torch.from_numpy(coords[ids[1], 1:]).to(device)[None] * scale,
            positions[0], positions[1], masks[0], masks[1],
        )[0]
        probs = torch.softmax(logits, dim=0).cpu().numpy()
        for threshold in thresholds:
            pred = probs > threshold
            row = stats[str(threshold)]
            row["edge_tp"] += int(np.logical_and(pred, target == 1).sum())
            row["edge_fn"] += int(np.logical_and(~pred, target == 1).sum())
            row["predicted_edges"] += int(pred.sum())
            pred_fork = pred.sum(axis=1) > 1
            row["division_parent_tp"] += int(np.logical_and(pred_fork, true_div).sum())
            row["division_parent_fn"] += int(np.logical_and(~pred_fork, true_div).sum())
            row["predicted_fork_parents"] += int(pred_fork.sum())
            row["false_fork_parents"] += int(np.logical_and(pred_fork, ~true_div).sum())

    for row in stats.values():
        row["edge_recall"] = row["edge_tp"] / max(1, row["edge_tp"] + row["edge_fn"])
        row["division_parent_recall"] = row["division_parent_tp"] / max(1, true_division_parents)
        row["division_parent_precision"] = row["division_parent_tp"] / max(1, row["predicted_fork_parents"])
    result = {
        "status": "PASS_TEACHER_FORCED_EXTERNAL_DIVISION_DIAGNOSTIC",
        "scope": "GT nodes on time-disjoint external validation; diagnostic, not competition OOF",
        "checkpoint_sha256": sha256(args.checkpoint),
        "files": len(files),
        "true_division_parents": true_division_parents,
        "thresholds": stats,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
