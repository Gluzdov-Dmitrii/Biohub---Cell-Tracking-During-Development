"""Train a regularized top-pair geometry head and test a frozen rank ensemble."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn

from train_parent_calibrated_pair import fixed_split, parent_dataset
from train_pretrained_feature_daughter_pair import PretrainedFeaturePairHead, load_backbone
from train_visual_daughter_pair import average_precision, sha256

SEED = 271828


def percentile_ranks(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(scores, kind="stable")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = (np.arange(len(scores), dtype=np.float64) + 0.5) / max(1, len(scores))
    return ranks


def select_threshold(labels: np.ndarray, scores: np.ndarray, true_parents: int) -> dict:
    order = np.argsort(-scores, kind="stable")
    ranked = labels[order].astype(np.int64)
    tp = np.cumsum(ranked)
    count = np.arange(1, len(ranked) + 1)
    precision = tp / count
    recall = tp / max(1, true_parents)
    valid = np.flatnonzero(precision >= 0.5)
    if not len(valid):
        return {"threshold": float("inf"), "precision": 0.0, "recall": 0.0}
    best = valid[np.lexsort((-precision[valid], -recall[valid]))[0]]
    return {"threshold": float(scores[order[best]]),
            "precision": float(precision[best]), "recall": float(recall[best])}


def apply_threshold(labels: np.ndarray, scores: np.ndarray, threshold: float, true_parents: int) -> dict:
    selected = scores >= threshold
    predicted = int(selected.sum())
    tp = int(labels[selected].sum())
    precision = tp / predicted if predicted else 0.0
    recall = tp / max(1, true_parents)
    return {"threshold": threshold, "precision": precision, "recall": recall,
            "true_positive_parents": tp, "predicted_parents": predicted,
            "true_parents": true_parents,
            "gate_pass": bool(precision >= 0.5 and recall >= 0.2)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--backbone-sha256", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()

    if sha256(args.checkpoint) != args.checkpoint_sha256:
        raise RuntimeError("checkpoint SHA mismatch")
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")

    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    pair_head = PretrainedFeaturePairHead().to(device)
    pair_head.load_state_dict(payload["pair_head"], strict=True)
    pair_head.eval()
    backbone = load_backbone(args.tracking_scripts, args.backbone, args.backbone_sha256, device)
    fit_paths, calibration_paths, evaluation_paths = fixed_split(args.data_dir)

    datasets = {}
    for name, paths in (("fit", fit_paths), ("calibration", calibration_paths),
                        ("prospective", evaluation_paths)):
        x, y, keys, totals, pair_ap = parent_dataset(
            pair_head, backbone, paths, device, payload["nearest_k"], args.batch_size
        )
        datasets[name] = (x[:, 96:101], y, x[:, -2], keys, totals, pair_ap)

    fit_x, fit_y, *_ = datasets["fit"]
    mean = fit_x.mean(axis=0)
    std = np.maximum(fit_x.std(axis=0), 1e-5)
    train_x = torch.from_numpy((fit_x - mean) / std).float()
    train_y = torch.from_numpy(fit_y).float()
    model = nn.Linear(train_x.shape[1], 1).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.1)
    positives = max(1, int(fit_y.sum()))
    pos_weight = torch.tensor((len(fit_y) - positives) / positives, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    generator = torch.Generator().manual_seed(SEED)
    history = []
    for epoch in range(args.epochs):
        model.train()
        order = torch.randperm(len(train_y), generator=generator)
        loss_sum = 0.0
        for start in range(0, len(order), args.batch_size):
            ids = order[start:start + args.batch_size]
            bx, by = train_x[ids].to(device), train_y[ids].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(bx).squeeze(1), by)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.item()) * len(ids)
        history.append({"epoch": epoch + 1, "loss": loss_sum / len(train_y)})

    scored = {}
    model.eval()
    for name, (x, y, raw, keys, totals, pair_ap) in datasets.items():
        with torch.no_grad():
            geometry = torch.sigmoid(model(torch.from_numpy((x - mean) / std).float().to(device)).squeeze(1)).cpu().numpy()
        blend = 0.5 * percentile_ranks(raw) + 0.5 * percentile_ranks(geometry)
        scored[name] = {"labels": y, "raw": raw, "geometry": geometry,
                        "blend": blend, "totals": totals, "pair_ap": pair_ap}

    result = {"experiment": "EXP175", "status": "REJECT_EXTERNAL_GATE",
              "split": {"fit": [10, 449, 182], "calibration": [476, 629, 64],
                        "prospective": [650, 789, 64]},
              "history": history, "arms": {}}
    for arm in ("raw", "geometry", "blend"):
        cal = scored["calibration"]
        ev = scored["prospective"]
        selected = select_threshold(cal["labels"], cal[arm], cal["totals"]["division_pairs_covered"])
        applied = apply_threshold(ev["labels"], ev[arm], selected["threshold"],
                                  ev["totals"]["division_pairs_covered"])
        result["arms"][arm] = {
            "calibration_ap": average_precision(cal["labels"].astype(np.int8), cal[arm]),
            "calibration_selected": selected,
            "prospective_ap": average_precision(ev["labels"].astype(np.int8), ev[arm]),
            "prospective_fixed_threshold": applied,
        }
    result["status"] = "PASS_EXTERNAL_GATE" if result["arms"]["blend"]["prospective_fixed_threshold"]["gate_pass"] else "REJECT_EXTERNAL_GATE"
    result["counts"] = {name: value["totals"] for name, value in scored.items()}
    result["candidate_pair_ap"] = {name: value["pair_ap"] for name, value in scored.items()}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = args.output_dir / "parent_geometry.pt"
    torch.save({"model": model.state_dict(), "mean": mean, "std": std,
                "seed": SEED, "input_dim": 5}, checkpoint)
    result["checkpoint_sha256"] = sha256(checkpoint)
    (args.output_dir / "external_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()


