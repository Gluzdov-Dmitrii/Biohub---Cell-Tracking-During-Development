"""Evaluate one fixed rank-average ensemble of two external pair classifiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from train_visual_daughter_pair import (
    VisualDaughterPair,
    average_precision,
    batches,
    discover_external_shards,
    enumerate_pair_examples,
    extract_crops,
    normalized_volume,
    select_parent_threshold,
    sha256,
    tensors_for_examples,
)
from train_pretrained_feature_daughter_pair import (
    PretrainedFeaturePairHead,
    extract_node_features,
    feature_tensors,
    load_backbone,
)


def percentile_ranks(scores: np.ndarray) -> np.ndarray:
    if len(scores) <= 1:
        return np.ones_like(scores, dtype=np.float64)
    order = np.argsort(scores, kind="stable")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(len(scores), dtype=np.float64)
    return ranks / (len(scores) - 1)


@torch.no_grad()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--backbone-sha256", required=True)
    parser.add_argument("--scratch-checkpoint", type=Path, required=True)
    parser.add_argument("--scratch-sha256", required=True)
    parser.add_argument("--feature-checkpoint", type=Path, required=True)
    parser.add_argument("--feature-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")
    if sha256(args.scratch_checkpoint) != args.scratch_sha256:
        raise RuntimeError("scratch pair checkpoint SHA mismatch")
    if sha256(args.feature_checkpoint) != args.feature_sha256:
        raise RuntimeError("feature pair checkpoint SHA mismatch")
    scratch_payload = torch.load(args.scratch_checkpoint, map_location="cpu", weights_only=True)
    scratch = VisualDaughterPair().to(device)
    scratch.load_state_dict(scratch_payload["model"], strict=True)
    scratch.eval()
    feature_payload = torch.load(args.feature_checkpoint, map_location="cpu", weights_only=True)
    feature_head = PretrainedFeaturePairHead().to(device)
    feature_head.load_state_dict(feature_payload["head"], strict=True)
    feature_head.eval()
    backbone = load_backbone(args.tracking_scripts, args.backbone, args.backbone_sha256, device)
    paths = discover_external_shards(args.data_dir, "valid_*.npz")
    if len(paths) != 64:
        raise AssertionError({"valid_shards": len(paths)})
    labels_all, scratch_all, feature_all = [], [], []
    keys = []
    totals = {"parents": 0, "division_parents": 0, "division_pairs_covered": 0,
              "positive_pairs": 0, "negative_pairs": 0}
    for path in paths:
        with np.load(path) as shard:
            volumes = shard["volumes"].astype(np.float32)
            coords = shard["coords_tzyx"].astype(np.float32)
            examples, stats = enumerate_pair_examples(
                coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=4,
                include_all_negatives=True, ordinary_parent_fraction=1.0, shard_key=path.name,
            )
        for name, value in stats.items():
            totals[name] += value
        crops = extract_crops(normalized_volume(volumes), coords, radius=5)
        features = extract_node_features(backbone, volumes, coords, device)
        for chunk in batches(examples, args.batch_size):
            p, a, b, geometry, labels = tensors_for_examples(crops, chunk, device)
            scratch_scores = torch.sigmoid(scratch(p, a, b, geometry)).cpu().numpy()
            fp, fa, fb, fg, _ = feature_tensors(features, chunk, device)
            feature_scores = torch.sigmoid(feature_head(fp, fa, fb, fg)).cpu().numpy()
            label_values = labels.cpu().numpy().astype(int)
            labels_all.extend(label_values.tolist())
            scratch_all.extend(scratch_scores.tolist())
            feature_all.extend(feature_scores.tolist())
            keys.extend((path.name, row.source) for row in chunk)
    labels = np.asarray(labels_all, dtype=np.int8)
    scratch_scores = np.asarray(scratch_all, dtype=np.float64)
    feature_scores = np.asarray(feature_all, dtype=np.float64)
    ensemble = 0.5 * percentile_ranks(scratch_scores) + 0.5 * percentile_ranks(feature_scores)
    parent_rows = [
        (shard, source, int(label), float(score))
        for (shard, source), label, score in zip(keys, labels, ensemble)
    ]
    result = {
        "experiment": "EXP161",
        "status": "PASS_EXTERNAL_GATE" if select_parent_threshold(parent_rows)["gate_pass"] else "REJECT_EXTERNAL_GATE",
        "scope": "fixed 50/50 global percentile-rank average on 64 external time-validation shards",
        "checkpoint_sha256": {"scratch": args.scratch_sha256, "pretrained_feature": args.feature_sha256,
                               "backbone": args.backbone_sha256},
        "pair_average_precision": {
            "scratch": average_precision(labels, scratch_scores),
            "pretrained_feature": average_precision(labels, feature_scores),
            "rank_ensemble": average_precision(labels, ensemble),
        },
        "score_correlation": float(np.corrcoef(scratch_scores, feature_scores)[0, 1]),
        "proposal_division_recall_ceiling": totals["division_pairs_covered"] / max(1, totals["division_parents"]),
        "counts": totals,
        "operating_point": select_parent_threshold(parent_rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
