"""Nested time-block calibration for the frozen EXP175 geometry blend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_parent_calibrated_pair import fixed_split, parent_dataset
from train_parent_geometry_rank_ensemble import apply_threshold, percentile_ranks
from train_pretrained_feature_daughter_pair import PretrainedFeaturePairHead, load_backbone
from train_visual_daughter_pair import average_precision, sha256

Z_ONE_SIDED_95 = 1.6448536269514722


def wilson_lower(tp: np.ndarray, count: np.ndarray) -> np.ndarray:
    n = count.astype(np.float64)
    p = tp / n
    z2 = Z_ONE_SIDED_95 ** 2
    return (p + z2 / (2 * n) - Z_ONE_SIDED_95 * np.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / (1 + z2 / n)


def select_robust_threshold(labels: np.ndarray, scores: np.ndarray, true_parents: int) -> dict:
    order = np.argsort(-scores, kind="stable")
    ranked = labels[order].astype(np.int64)
    tp = np.cumsum(ranked)
    count = np.arange(1, len(ranked) + 1)
    lower = wilson_lower(tp, count)
    valid = np.flatnonzero(lower >= 0.5)
    if not len(valid):
        return {"threshold": 2.0, "precision": 0.0, "precision_wilson_lower": 0.0,
                "recall": 0.0, "true_positive_parents": 0, "predicted_parents": 0,
                "true_parents": true_parents}
    recall = tp[valid] / max(1, true_parents)
    best = valid[np.argmax(recall)]
    return {"threshold": float(scores[order[best]]), "precision": float(tp[best] / count[best]),
            "precision_wilson_lower": float(lower[best]), "recall": float(tp[best] / max(1, true_parents)),
            "true_positive_parents": int(tp[best]), "predicted_parents": int(count[best]),
            "true_parents": true_parents}


def scores_for(x: np.ndarray, geometry_model: nn.Module, mean: np.ndarray, std: np.ndarray,
               device: torch.device) -> dict[str, np.ndarray]:
    raw = x[:, -2].astype(np.float64)
    with torch.no_grad():
        geometry = torch.sigmoid(geometry_model(torch.from_numpy((x[:, 96:101] - mean) / std).float().to(device)).squeeze(1)).cpu().numpy()
    blend = 0.5 * percentile_ranks(raw) + 0.5 * percentile_ranks(geometry)
    return {"raw": raw, "geometry": geometry, "blend": blend}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--backbone-sha256", required=True)
    parser.add_argument("--pair-checkpoint", type=Path, required=True)
    parser.add_argument("--pair-checkpoint-sha256", required=True)
    parser.add_argument("--geometry-checkpoint", type=Path, required=True)
    parser.add_argument("--geometry-checkpoint-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    if sha256(args.pair_checkpoint) != args.pair_checkpoint_sha256:
        raise RuntimeError("pair checkpoint SHA mismatch")
    if sha256(args.geometry_checkpoint) != args.geometry_checkpoint_sha256:
        raise RuntimeError("geometry checkpoint SHA mismatch")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")
    pair_payload = torch.load(args.pair_checkpoint, map_location="cpu", weights_only=True)
    pair_head = PretrainedFeaturePairHead().to(device)
    pair_head.load_state_dict(pair_payload["pair_head"], strict=True)
    pair_head.eval()
    # The SHA guard above binds this owned checkpoint. EXP175 stores NumPy
    # mean/std arrays, which PyTorch's weights-only loader intentionally rejects.
    geometry_payload = torch.load(args.geometry_checkpoint, map_location="cpu", weights_only=False)
    geometry_model = nn.Linear(int(geometry_payload["input_dim"]), 1).to(device)
    geometry_model.load_state_dict(geometry_payload["model"], strict=True)
    geometry_model.eval()
    mean = np.asarray(geometry_payload["mean"], dtype=np.float32)
    std = np.asarray(geometry_payload["std"], dtype=np.float32)
    backbone = load_backbone(args.tracking_scripts, args.backbone, args.backbone_sha256, device)
    _fit, calibration, _consumed_prospective = fixed_split(args.data_dir)
    if len(calibration) != 64:
        raise AssertionError("Expected exactly 64 calibration shards")
    blocks = [calibration[i:i + 16] for i in range(0, 64, 16)]
    payloads = []
    for block in blocks:
        x, labels, keys, totals, pair_ap = parent_dataset(
            pair_head, backbone, block, device, pair_payload["nearest_k"], args.batch_size
        )
        payloads.append({"x": x, "labels": labels, "keys": keys, "totals": totals,
                         "pair_ap": pair_ap, "times": [int(p.stem.split("_")[-1]) for p in block]})
    folds = []
    for held in range(4):
        train_x = np.concatenate([p["x"] for i, p in enumerate(payloads) if i != held])
        train_y = np.concatenate([p["labels"] for i, p in enumerate(payloads) if i != held])
        train_true = sum(p["totals"]["division_pairs_covered"] for i, p in enumerate(payloads) if i != held)
        held_x, held_y = payloads[held]["x"], payloads[held]["labels"]
        held_true = payloads[held]["totals"]["division_pairs_covered"]
        train_scores = scores_for(train_x, geometry_model, mean, std, device)["blend"]
        held_scores = scores_for(held_x, geometry_model, mean, std, device)["blend"]
        selected = select_robust_threshold(train_y, train_scores, train_true)
        applied = apply_threshold(held_y, held_scores, selected["threshold"], held_true)
        folds.append({"held_block": held + 1, "held_times": payloads[held]["times"],
                      "selected": selected, "held": applied,
                      "held_ap": average_precision(held_y.astype(np.int8), held_scores)})
    all_x = np.concatenate([p["x"] for p in payloads])
    all_y = np.concatenate([p["labels"] for p in payloads])
    all_true = sum(p["totals"]["division_pairs_covered"] for p in payloads)
    all_scores = scores_for(all_x, geometry_model, mean, std, device)
    final = select_robust_threshold(all_y, all_scores["blend"], all_true)
    pass_gate = all(f["held"]["precision"] >= 0.5 and f["held"]["recall"] > 0 for f in folds)
    pass_gate = pass_gate and sum(f["held"]["true_positive_parents"] for f in folds) / all_true >= 0.15
    result = {"experiment": "EXP177", "status": "PASS_EXTERNAL_NESTED_GATE" if pass_gate else "REJECT_EXTERNAL_NESTED_GATE",
              "scope": "64 pre-prospective calibration shards only; consumed prospective and competition data unopened",
              "folds": folds, "final_blend_threshold": final,
              "all_calibration_ap": {name: average_precision(all_y.astype(np.int8), values) for name, values in all_scores.items()},
              "gate": {"all_four_held_precision_at_least_0_5": all(f["held"]["precision"] >= 0.5 for f in folds),
                       "all_four_nonzero_recall": all(f["held"]["recall"] > 0 for f in folds),
                       "micro_recall_at_least_0_15": sum(f["held"]["true_positive_parents"] for f in folds) / all_true >= 0.15,
                       "pass": pass_gate}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
