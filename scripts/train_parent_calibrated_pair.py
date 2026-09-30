"""Train a leak-resistant two-stage daughter-pair and parent propensity model."""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_pretrained_feature_daughter_pair import (
    PretrainedFeaturePairHead,
    extract_node_features,
    feature_tensors,
    load_backbone,
)
from train_visual_daughter_pair import (
    SEED,
    average_precision,
    batches,
    discover_external_shards,
    enumerate_pair_examples,
    sha256,
)


class ParentPropensityHead(nn.Module):
    def __init__(self, input_dim: int = 103):
        super().__init__()
        self.layers = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, 64),
            nn.SiLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 16),
            nn.SiLU(),
            nn.Linear(16, 1),
        )

    def forward(self, values):
        return self.layers(values).squeeze(1)


def shard_time(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    if match is None:
        raise ValueError(path.name)
    return int(match.group(1))


def fixed_split(data_dir: Path):
    train = discover_external_shards(data_dir, "train_*.npz")
    valid = discover_external_shards(data_dir, "valid_*.npz")
    fit = [path for path in train if shard_time(path) <= 450]
    gap = [path for path in train if 451 <= shard_time(path) <= 475]
    calibration = [path for path in train if shard_time(path) >= 476]
    if (len(fit), len(gap), len(calibration), len(valid)) != (182, 10, 64, 64):
        raise AssertionError({"fit": len(fit), "gap": len(gap),
                              "calibration": len(calibration), "evaluation": len(valid)})
    if max(map(shard_time, fit)) + 21 > min(map(shard_time, calibration)):
        raise AssertionError("fit/calibration time gap is below 21")
    if max(map(shard_time, calibration)) + 21 > min(map(shard_time, valid)):
        raise AssertionError("calibration/evaluation time gap is below 21")
    return fit, calibration, valid


def symmetric_pair_features(parent, daughter_a, daughter_b, geometry):
    return torch.cat(
        (parent, daughter_a + daughter_b, torch.abs(daughter_a - daughter_b), geometry / 10.0),
        dim=1,
    )


def choose_top_candidates(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[0]].append(row)
    chosen = []
    for source, values in sorted(grouped.items()):
        values.sort(key=lambda row: (-row[2], row[1]))
        top = values[0]
        margin = top[2] - values[1][2] if len(values) > 1 else top[2]
        chosen.append((source, top[1], top[2], margin, top[3]))
    return chosen


def select_parent_operating(keys, labels, scores, true_parent_count):
    ranked = sorted(
        zip(keys, labels, scores),
        key=lambda row: (-float(row[2]), row[0]),
    )
    tp = 0
    selected = None
    for count, (_key, label, score) in enumerate(ranked, 1):
        tp += int(label)
        precision = tp / count
        recall = tp / max(1, true_parent_count)
        candidate = (recall, precision, -float(score), count, tp, float(score))
        if precision >= 0.5 and (selected is None or candidate > selected):
            selected = candidate
    if selected is None:
        return {"gate_pass": False, "threshold": 1.0, "precision": 0.0, "recall": 0.0,
                "true_positive_parents": 0, "predicted_parents": 0,
                "true_parents": true_parent_count}
    recall, precision, _negative_score, predicted, true_positive, threshold = selected
    return {"gate_pass": bool(recall >= 0.2), "threshold": threshold,
            "precision": precision, "recall": recall,
            "true_positive_parents": true_positive, "predicted_parents": predicted,
            "true_parents": true_parent_count}


@torch.no_grad()
def parent_dataset(pair_head, backbone, paths, device, nearest_k, batch_size):
    pair_head.eval()
    features_all, labels_all, keys = [], [], []
    totals = {"parents": 0, "division_parents": 0, "division_pairs_covered": 0,
              "positive_pairs": 0, "negative_pairs": 0}
    pair_labels, pair_scores = [], []
    for path in paths:
        with np.load(path) as shard:
            volumes = shard["volumes"].astype(np.float32)
            coords = shard["coords_tzyx"].astype(np.float32)
            examples, stats = enumerate_pair_examples(
                coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=nearest_k,
                include_all_negatives=True, ordinary_parent_fraction=1.0, shard_key=path.name,
            )
        for name, value in stats.items():
            totals[name] += value
        node_features = extract_node_features(backbone, volumes, coords, device)
        candidate_rows = []
        for chunk in batches(examples, batch_size):
            p, a, b, geometry, labels = feature_tensors(node_features, chunk, device)
            logits = pair_head(p, a, b, geometry)
            scores = torch.sigmoid(logits)
            vectors = symmetric_pair_features(p, a, b, geometry)
            for row, label, score, vector in zip(chunk, labels, scores, vectors):
                candidate_rows.append((row.source, int(label.item()), float(score.item()), vector.cpu().numpy()))
                pair_labels.append(int(label.item()))
                pair_scores.append(float(score.item()))
        for source, label, score, margin, vector in choose_top_candidates(candidate_rows):
            features_all.append(np.concatenate((vector, np.asarray([score, margin], dtype=np.float32))))
            labels_all.append(label)
            keys.append((path.name, source))
    return (
        np.asarray(features_all, dtype=np.float32),
        np.asarray(labels_all, dtype=np.float32),
        keys,
        totals,
        average_precision(np.asarray(pair_labels, dtype=np.int8), np.asarray(pair_scores, dtype=np.float64)),
    )


def train_pair_head(head, backbone, paths, device, args):
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.pair_learning_rate, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(12.0, device=device))
    history = []
    for epoch in range(args.pair_epochs):
        head.train()
        ordered = paths.copy()
        random.Random(SEED + epoch).shuffle(ordered)
        loss_sum = count = positives = 0
        for path in ordered:
            with np.load(path) as shard:
                volumes = shard["volumes"].astype(np.float32)
                coords = shard["coords_tzyx"].astype(np.float32)
                examples, _ = enumerate_pair_examples(
                    coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=args.nearest_k,
                    include_all_negatives=False, ordinary_parent_fraction=args.ordinary_parent_fraction,
                    shard_key=path.name,
                )
            random.Random(f"{SEED}:{epoch}:{path.name}").shuffle(examples)
            node_features = extract_node_features(backbone, volumes, coords, device)
            for chunk in batches(examples, args.batch_size):
                p, a, b, geometry, labels = feature_tensors(node_features, chunk, device)
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(head(p, a, b, geometry), labels)
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.detach()) * len(chunk)
                count += len(chunk)
                positives += int(labels.sum().item())
        row = {"epoch": epoch + 1, "loss": loss_sum / max(1, count),
               "pairs": count, "positive_pairs": positives}
        history.append(row)
        print(json.dumps({"pair_train": row}), flush=True)
    return history


def train_parent_head(head, features, labels, device, epochs, batch_size, learning_rate):
    x = torch.from_numpy(features).to(device)
    y = torch.from_numpy(labels).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=learning_rate, weight_decay=1e-3)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(64.0, device=device))
    history = []
    for epoch in range(epochs):
        head.train()
        generator = torch.Generator(device="cpu").manual_seed(SEED + 1000 + epoch)
        order = torch.randperm(len(y), generator=generator)
        loss_sum = 0.0
        for start in range(0, len(y), batch_size):
            ids = order[start:start + batch_size].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(head(x[ids]), y[ids])
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * len(ids)
        history.append({"epoch": epoch + 1, "loss": loss_sum / len(y)})
    print(json.dumps({"parent_train_final": history[-1]}), flush=True)
    return history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--backbone-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pair-epochs", type=int, default=10)
    parser.add_argument("--parent-epochs", type=int, default=30)
    parser.add_argument("--nearest-k", type=int, default=4)
    parser.add_argument("--ordinary-parent-fraction", type=float, default=0.05)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--pair-learning-rate", type=float, default=3e-4)
    parser.add_argument("--parent-learning-rate", type=float, default=1e-3)
    args = parser.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")
    fit_paths, calibration_paths, evaluation_paths = fixed_split(args.data_dir)
    backbone = load_backbone(args.tracking_scripts, args.backbone, args.backbone_sha256, device)
    pair_head = PretrainedFeaturePairHead().to(device)
    pair_history = train_pair_head(pair_head, backbone, fit_paths, device, args)
    cal_x, cal_y, _cal_keys, cal_totals, cal_pair_ap = parent_dataset(
        pair_head, backbone, calibration_paths, device, args.nearest_k, args.batch_size
    )
    parent_head = ParentPropensityHead(cal_x.shape[1]).to(device)
    parent_history = train_parent_head(
        parent_head, cal_x, cal_y, device, args.parent_epochs, args.batch_size,
        args.parent_learning_rate,
    )
    eval_x, eval_y, eval_keys, eval_totals, eval_pair_ap = parent_dataset(
        pair_head, backbone, evaluation_paths, device, args.nearest_k, args.batch_size
    )
    parent_head.eval()
    with torch.no_grad():
        parent_scores = torch.sigmoid(parent_head(torch.from_numpy(eval_x).to(device))).cpu().numpy()
    operating = select_parent_operating(
        eval_keys, eval_y, parent_scores, eval_totals["division_pairs_covered"]
    )
    result = {
        "experiment": "EXP168",
        "status": "PASS_EXTERNAL_GATE" if operating["gate_pass"] else "REJECT_EXTERNAL_GATE",
        "split": {"fit": [10, 449, 182], "gap_1": [451, 473, 10],
                  "calibration": [476, 629, 64], "gap_2": [630, 649],
                  "evaluation": [650, 789, 64]},
        "fixed_parameters": vars(args) | {"data_dir": str(args.data_dir),
                                            "tracking_scripts": str(args.tracking_scripts),
                                            "backbone": str(args.backbone),
                                            "output_dir": str(args.output_dir)},
        "fit_history": pair_history,
        "calibration": {"counts": cal_totals, "pair_average_precision": cal_pair_ap,
                        "top_pair_positive_parents": int(cal_y.sum()),
                        "parent_history": parent_history},
        "prospective_external_evaluation": {
            "counts": eval_totals,
            "pair_average_precision": eval_pair_ap,
            "parent_average_precision": average_precision(eval_y.astype(np.int8), parent_scores),
            "operating_point": operating,
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.output_dir / "parent_calibrated_pair.pt"
    torch.save({"pair_head": pair_head.state_dict(), "parent_head": parent_head.state_dict(),
                "input_dim": cal_x.shape[1], "backbone_sha256": args.backbone_sha256,
                "nearest_k": args.nearest_k, "seed": SEED}, checkpoint)
    result["checkpoint_sha256"] = sha256(checkpoint)
    (args.output_dir / "external_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "evaluation": result["prospective_external_evaluation"],
                      "checkpoint_sha256": result["checkpoint_sha256"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
