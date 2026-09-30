"""Train a symmetric division-pair head on frozen real-Zebrahub U-Net features."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_visual_daughter_pair import (
    SEED,
    average_precision,
    batches,
    discover_external_shards,
    enumerate_pair_examples,
    normalized_volume,
    select_parent_threshold,
    sha256,
)


class PretrainedFeaturePairHead(nn.Module):
    def __init__(self, embedding_dim: int = 32, geometry_dim: int = 5):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(embedding_dim * 3 + geometry_dim, 96),
            nn.LayerNorm(96),
            nn.SiLU(),
            nn.Dropout(0.1),
            nn.Linear(96, 32),
            nn.SiLU(),
            nn.Linear(32, 1),
        )

    def forward(self, parent, daughter_a, daughter_b, geometry):
        # Sum and absolute difference make daughter order exactly irrelevant.
        symmetric = torch.cat(
            (parent, daughter_a + daughter_b, torch.abs(daughter_a - daughter_b), geometry / 10.0),
            dim=1,
        )
        return self.head(symmetric).squeeze(1)


@torch.no_grad()
def extract_node_features(backbone, volumes, coords, device):
    images = torch.from_numpy(normalized_volume(volumes))[None].to(device)
    encoded, _ = backbone.encode(images)
    feature_dim = int(encoded.shape[2])
    result = torch.empty((len(coords), feature_dim), dtype=torch.float32, device=device)
    for frame in (0, 1):
        ids = np.flatnonzero(coords[:, 0].astype(int) == frame)
        xyz = torch.from_numpy(coords[ids, 1:4].astype(np.float32))[None].to(device)
        mask = torch.ones((1, len(ids)), dtype=torch.bool, device=device)
        values = backbone._index_features(encoded[:, frame], xyz, mask)[0]
        result[torch.from_numpy(ids).to(device)] = values
    return result


def feature_tensors(features, examples, device):
    source = torch.as_tensor([row.source for row in examples], dtype=torch.long, device=device)
    a = torch.as_tensor([row.daughter_a for row in examples], dtype=torch.long, device=device)
    b = torch.as_tensor([row.daughter_b for row in examples], dtype=torch.long, device=device)
    geometry = torch.as_tensor([row.geometry for row in examples], dtype=torch.float32, device=device)
    labels = torch.as_tensor([row.label for row in examples], dtype=torch.float32, device=device)
    return features[source], features[a], features[b], geometry, labels


@torch.no_grad()
def validate(head, backbone, paths, device, nearest_k, batch_size):
    head.eval()
    labels_all, scores_all = [], []
    parent_rows = []
    totals = {"parents": 0, "division_parents": 0, "division_pairs_covered": 0,
              "positive_pairs": 0, "negative_pairs": 0}
    for path in paths:
        with np.load(path) as shard:
            volumes = shard["volumes"].astype(np.float32)
            coords = shard["coords_tzyx"].astype(np.float32)
            examples, stats = enumerate_pair_examples(
                coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=nearest_k,
                include_all_negatives=True, ordinary_parent_fraction=1.0, shard_key=path.name,
            )
        for key, value in stats.items():
            totals[key] += value
        features = extract_node_features(backbone, volumes, coords, device)
        for chunk in batches(examples, batch_size):
            p, a, b, geometry, labels = feature_tensors(features, chunk, device)
            scores = torch.sigmoid(head(p, a, b, geometry)).cpu().numpy()
            label_values = labels.cpu().numpy().astype(int)
            labels_all.extend(label_values.tolist())
            scores_all.extend(scores.tolist())
            parent_rows.extend(
                (path.name, row.source, int(label), float(score))
                for row, label, score in zip(chunk, label_values, scores)
            )
    labels_np = np.asarray(labels_all, dtype=np.int8)
    scores_np = np.asarray(scores_all, dtype=np.float64)
    return {
        "pair_average_precision": average_precision(labels_np, scores_np),
        "proposal_division_recall_ceiling": totals["division_pairs_covered"] / max(1, totals["division_parents"]),
        "counts": totals,
        "operating_point": select_parent_threshold(parent_rows),
    }


def load_backbone(tracking_scripts: Path, checkpoint: Path, expected_sha: str, device):
    if sha256(checkpoint) != expected_sha:
        raise RuntimeError("backbone checkpoint SHA mismatch")
    sys.path.insert(0, str(tracking_scripts.resolve()))
    from train_unet_transformer import TemporalUNet3D, UNetNodeTransformer

    model = UNetNodeTransformer(
        unet=TemporalUNet3D(in_channels=1, out_channels=32, layers=[32, 64, 128]),
        unet_out_channels=32,
        pos_feat_dim=32,
    ).to(device)
    state = torch.load(checkpoint, map_location=device, weights_only=True)
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        raise RuntimeError({"missing": missing, "unexpected": unexpected})
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--nearest-k", type=int, default=4)
    parser.add_argument("--ordinary-parent-fraction", type=float, default=0.05)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    args = parser.parse_args()
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")
    train_paths = discover_external_shards(args.data_dir, "train_*.npz")
    valid_paths = discover_external_shards(args.data_dir, "valid_*.npz")
    if (len(train_paths), len(valid_paths)) != (256, 64):
        raise AssertionError({"train": len(train_paths), "valid": len(valid_paths)})
    backbone = load_backbone(args.tracking_scripts, args.checkpoint, args.checkpoint_sha256, device)
    head = PretrainedFeaturePairHead().to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(12.0, device=device))
    history, best_key, best, best_state = [], None, None, None
    for epoch in range(args.epochs):
        head.train()
        paths = train_paths.copy()
        random.Random(SEED + epoch).shuffle(paths)
        loss_sum = count = positive_count = 0
        for path in paths:
            with np.load(path) as shard:
                volumes = shard["volumes"].astype(np.float32)
                coords = shard["coords_tzyx"].astype(np.float32)
                examples, _ = enumerate_pair_examples(
                    coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=args.nearest_k,
                    include_all_negatives=False, ordinary_parent_fraction=args.ordinary_parent_fraction,
                    shard_key=path.name,
                )
            random.Random(f"{SEED}:{epoch}:{path.name}").shuffle(examples)
            features = extract_node_features(backbone, volumes, coords, device)
            for chunk in batches(examples, args.batch_size):
                p, a, b, geometry, labels = feature_tensors(features, chunk, device)
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(head(p, a, b, geometry), labels)
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.detach()) * len(chunk)
                count += len(chunk)
                positive_count += int(labels.sum().item())
        validation = validate(head, backbone, valid_paths, device, args.nearest_k, args.batch_size)
        row = {"epoch": epoch + 1, "train_loss": loss_sum / max(1, count),
               "train_pairs": count, "train_positive_pairs": positive_count,
               "validation": validation}
        history.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        key = (bool(validation["operating_point"]["gate_pass"]), validation["pair_average_precision"], -(epoch + 1))
        if best_key is None or key > best_key:
            best_key, best = key, row
            best_state = {name: value.detach().cpu().clone() for name, value in head.state_dict().items()}
    assert best is not None and best_state is not None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_out = args.output_dir / "pretrained_feature_pair_head.pt"
    torch.save({"head": best_state, "embedding_dim": 32, "geometry_dim": 5,
                "nearest_k": args.nearest_k, "seed": SEED,
                "backbone_sha256": args.checkpoint_sha256}, checkpoint_out)
    result = {
        "experiment": "EXP160",
        "status": "PASS_EXTERNAL_GATE" if best["validation"]["operating_point"]["gate_pass"] else "REJECT_EXTERNAL_GATE",
        "scope": "frozen real-Zebrahub U-Net features; verified external 256/64 time split",
        "parameters": vars(args) | {"data_dir": str(args.data_dir), "tracking_scripts": str(args.tracking_scripts),
                                      "checkpoint": str(args.checkpoint), "output_dir": str(args.output_dir)},
        "history": history,
        "selected_epoch": best["epoch"],
        "selected_validation": best["validation"],
        "head_checkpoint_sha256": sha256(checkpoint_out),
    }
    (args.output_dir / "external_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "selected_epoch": result["selected_epoch"],
                      "selected_validation": result["selected_validation"],
                      "head_checkpoint_sha256": result["head_checkpoint_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
