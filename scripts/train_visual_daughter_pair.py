"""Train an explicit, daughter-swap-invariant visual division classifier.

This program is intentionally restricted to the verified external two-frame
Zebrahub shards.  Competition data are scored by a separate frozen program
only after the external gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn


SEED = 158031


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_fraction(key: str) -> float:
    value = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return value / float(2**64)


def discover_external_shards(data_dir: Path, pattern: str) -> list[Path]:
    if pattern not in {"train_*.npz", "valid_*.npz"}:
        raise ValueError("Only frozen external train/valid shard patterns are allowed")
    paths = sorted(data_dir.glob(pattern))
    if not paths:
        raise FileNotFoundError({"data_dir": str(data_dir), "pattern": pattern})
    forbidden = {"target", "competition", "test"}
    for path in paths:
        lowered = {part.lower() for part in path.parts}
        if lowered & forbidden:
            raise ValueError(f"Forbidden competition/target path: {path}")
    return paths


@dataclass(frozen=True)
class PairExample:
    source: int
    daughter_a: int
    daughter_b: int
    label: int
    geometry: tuple[float, ...]


def enumerate_pair_examples(
    coords_tzyx: np.ndarray,
    edges: np.ndarray,
    voxel_um_zyx: np.ndarray,
    *,
    nearest_k: int,
    include_all_negatives: bool,
    ordinary_parent_fraction: float,
    shard_key: str,
) -> tuple[list[PairExample], dict[str, int]]:
    """Enumerate deterministic nearest-neighbour daughter pairs.

    All division parents are included. During training, ordinary parents are
    hash-sampled; validation must set ``include_all_negatives=True``.
    """
    coords = np.asarray(coords_tzyx, dtype=np.float32)
    edge_array = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    scale = np.asarray(voxel_um_zyx, dtype=np.float32)
    source_ids = np.flatnonzero(coords[:, 0].astype(int) == 0)
    target_ids = np.flatnonzero(coords[:, 0].astype(int) == 1)
    true_by_source: dict[int, set[int]] = {}
    for source, target in edge_array:
        if source in source_ids and target in target_ids:
            true_by_source.setdefault(int(source), set()).add(int(target))
    examples: list[PairExample] = []
    stats = {
        "parents": int(len(source_ids)),
        "division_parents": 0,
        "division_pairs_covered": 0,
        "positive_pairs": 0,
        "negative_pairs": 0,
    }
    physical = coords[:, 1:4] * scale[None]
    for source in source_ids.tolist():
        truth = true_by_source.get(source, set())
        is_division = len(truth) == 2
        stats["division_parents"] += int(is_division)
        if not is_division and not include_all_negatives:
            if stable_fraction(f"{shard_key}:{source}") >= ordinary_parent_fraction:
                continue
        delta = physical[target_ids] - physical[source]
        distances = np.linalg.norm(delta, axis=1)
        order = np.lexsort((target_ids, distances))[: min(nearest_k, len(target_ids))]
        nearest = target_ids[order].tolist()
        covered = is_division and truth.issubset(nearest)
        stats["division_pairs_covered"] += int(covered)
        for left in range(len(nearest)):
            for right in range(left + 1, len(nearest)):
                a, b = int(nearest[left]), int(nearest[right])
                pair = {a, b}
                label = int(is_division and pair == truth)
                da = float(np.linalg.norm(physical[a] - physical[source]))
                db = float(np.linalg.norm(physical[b] - physical[source]))
                sister = float(np.linalg.norm(physical[a] - physical[b]))
                midpoint = float(np.linalg.norm((physical[a] + physical[b]) / 2 - physical[source]))
                radial_gap = abs(da - db)
                geometry = (min(da, db), max(da, db), sister, midpoint, radial_gap)
                examples.append(PairExample(source, a, b, label, geometry))
                stats["positive_pairs" if label else "negative_pairs"] += 1
    return examples, stats


def normalized_volume(volumes: np.ndarray) -> np.ndarray:
    array = np.asarray(volumes, dtype=np.float32)
    low, high = np.percentile(array, [0.1, 99.9])
    return np.clip((array - low) / (high - low + 1e-6), 0.0, 2.0).astype(np.float32)


def extract_crops(volumes: np.ndarray, coords: np.ndarray, radius: int) -> np.ndarray:
    width = 2 * radius + 1
    padded = np.pad(volumes, ((0, 0), (radius, radius), (radius, radius), (radius, radius)))
    crops = np.empty((len(coords), 1, width, width, width), dtype=np.float32)
    shape = np.asarray(volumes.shape[1:], dtype=int)
    for index, row in enumerate(coords):
        time = int(row[0])
        center = np.rint(row[1:4]).astype(int)
        center = np.clip(center, 0, shape - 1) + radius
        z, y, x = center.tolist()
        crops[index, 0] = padded[
            time,
            z - radius : z + radius + 1,
            y - radius : y + radius + 1,
            x - radius : x + radius + 1,
        ]
    return crops


class VisualDaughterPair(nn.Module):
    def __init__(self, geometry_dim: int = 5, channels: int = 12):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv3d(1, channels, 3, padding=1),
            nn.GroupNorm(3, channels),
            nn.SiLU(),
            nn.AvgPool3d(2),
            nn.Conv3d(channels, channels * 2, 3, padding=1),
            nn.GroupNorm(3, channels * 2),
            nn.SiLU(),
            nn.AdaptiveAvgPool3d(1),
            nn.Flatten(),
        )
        embedding = channels * 2
        self.head = nn.Sequential(
            nn.Linear(embedding * 3 + geometry_dim, 64),
            nn.SiLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
        )

    def forward(self, parent, daughter_a, daughter_b, geometry):
        parent_embedding = self.encoder(parent)
        a = self.encoder(daughter_a)
        b = self.encoder(daughter_b)
        symmetric = torch.cat((parent_embedding, a + b, torch.abs(a - b), geometry), dim=1)
        return self.head(symmetric).squeeze(1)


def batches(values: list[PairExample], batch_size: int):
    for start in range(0, len(values), batch_size):
        yield values[start : start + batch_size]


def tensors_for_examples(crops, examples, device):
    source = torch.as_tensor([row.source for row in examples], dtype=torch.long)
    a = torch.as_tensor([row.daughter_a for row in examples], dtype=torch.long)
    b = torch.as_tensor([row.daughter_b for row in examples], dtype=torch.long)
    geometry = torch.as_tensor([row.geometry for row in examples], dtype=torch.float32)
    labels = torch.as_tensor([row.label for row in examples], dtype=torch.float32)
    crop_tensor = torch.from_numpy(crops)
    return (
        crop_tensor[source].to(device),
        crop_tensor[a].to(device),
        crop_tensor[b].to(device),
        geometry.to(device),
        labels.to(device),
    )


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = int(labels.sum())
    if not positives:
        return 0.0
    order = np.argsort(-scores, kind="stable")
    ranked = labels[order]
    precision = np.cumsum(ranked) / np.arange(1, len(ranked) + 1)
    return float((precision * ranked).sum() / positives)


def select_parent_threshold(rows: list[tuple[str, int, int, float]]) -> dict[str, float | int | bool]:
    """Select one pair per parent and the lowest threshold at the best gated recall."""
    best_by_parent: dict[tuple[str, int], tuple[int, float]] = {}
    true_parents: set[tuple[str, int]] = set()
    for shard, source, label, score in rows:
        key = (shard, source)
        if label:
            true_parents.add(key)
        old = best_by_parent.get(key)
        if old is None or score > old[1]:
            best_by_parent[key] = (label, score)
    ranked = sorted(best_by_parent.items(), key=lambda item: (-item[1][1], item[0]))
    tp = 0
    selected = None
    for rank, (_key, (label, score)) in enumerate(ranked, 1):
        tp += int(label)
        precision = tp / rank
        recall = tp / max(1, len(true_parents))
        candidate = (recall, precision, -score, rank, tp, score)
        if precision >= 0.50 and (selected is None or candidate > selected):
            selected = candidate
    if selected is None:
        return {"gate_pass": False, "threshold": 1.0, "precision": 0.0, "recall": 0.0,
                "true_positive_parents": 0, "predicted_parents": 0, "true_parents": len(true_parents)}
    recall, precision, _neg_score, predicted, tp, threshold = selected
    return {
        "gate_pass": bool(precision >= 0.50 and recall >= 0.20),
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "true_positive_parents": int(tp),
        "predicted_parents": int(predicted),
        "true_parents": int(len(true_parents)),
    }


@torch.no_grad()
def validate(model, paths, device, radius, nearest_k, batch_size):
    model.eval()
    all_labels: list[int] = []
    all_scores: list[float] = []
    parent_rows: list[tuple[str, int, int, float]] = []
    totals = {"parents": 0, "division_parents": 0, "division_pairs_covered": 0,
              "positive_pairs": 0, "negative_pairs": 0}
    for path in paths:
        with np.load(path) as shard:
            volumes = normalized_volume(shard["volumes"])
            coords = shard["coords_tzyx"].astype(np.float32)
            examples, stats = enumerate_pair_examples(
                coords, shard["edges"], shard["output_voxel_um_zyx"], nearest_k=nearest_k,
                include_all_negatives=True, ordinary_parent_fraction=1.0, shard_key=path.name,
            )
        for key, value in stats.items():
            totals[key] += value
        crops = extract_crops(volumes, coords, radius)
        for chunk in batches(examples, batch_size):
            p, a, b, geometry, labels = tensors_for_examples(crops, chunk, device)
            scores = torch.sigmoid(model(p, a, b, geometry)).cpu().numpy()
            label_values = labels.cpu().numpy().astype(int)
            all_labels.extend(label_values.tolist())
            all_scores.extend(scores.tolist())
            parent_rows.extend(
                (path.name, row.source, int(label), float(score))
                for row, label, score in zip(chunk, label_values, scores)
            )
    labels = np.asarray(all_labels, dtype=np.int8)
    scores = np.asarray(all_scores, dtype=np.float64)
    selection = select_parent_threshold(parent_rows)
    coverage = totals["division_pairs_covered"] / max(1, totals["division_parents"])
    return {
        "pair_average_precision": average_precision(labels, scores),
        "proposal_division_recall_ceiling": coverage,
        "counts": totals,
        "operating_point": selection,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--nearest-k", type=int, default=4)
    parser.add_argument("--ordinary-parent-fraction", type=float, default=0.05)
    parser.add_argument("--batch-size", type=int, default=192)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    args = parser.parse_args()
    if not (0 < args.ordinary_parent_fraction <= 1):
        raise ValueError("ordinary-parent-fraction must be in (0, 1]")
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True, warn_only=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("EXP158 exact training requires a leased GPU")
    train_paths = discover_external_shards(args.data_dir, "train_*.npz")
    valid_paths = discover_external_shards(args.data_dir, "valid_*.npz")
    if len(train_paths) != 256 or len(valid_paths) != 64:
        raise AssertionError({"train": len(train_paths), "valid": len(valid_paths)})
    if set(train_paths) & set(valid_paths):
        raise AssertionError("train/valid shard overlap")
    model = VisualDaughterPair().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(12.0, device=device))
    history = []
    best_key = None
    best_state = None
    best = None
    for epoch in range(args.epochs):
        model.train()
        epoch_paths = train_paths.copy()
        random.Random(SEED + epoch).shuffle(epoch_paths)
        loss_sum = 0.0
        count = 0
        positive_count = 0
        for path in epoch_paths:
            with np.load(path) as shard:
                volumes = normalized_volume(shard["volumes"])
                coords = shard["coords_tzyx"].astype(np.float32)
                examples, _stats = enumerate_pair_examples(
                    coords, shard["edges"], shard["output_voxel_um_zyx"],
                    nearest_k=args.nearest_k, include_all_negatives=False,
                    ordinary_parent_fraction=args.ordinary_parent_fraction, shard_key=path.name,
                )
            random.Random(f"{SEED}:{epoch}:{path.name}").shuffle(examples)
            crops = extract_crops(volumes, coords, args.radius)
            for chunk in batches(examples, args.batch_size):
                p, a, b, geometry, labels = tensors_for_examples(crops, chunk, device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(p, a, b, geometry)
                loss = criterion(logits, labels)
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.detach()) * len(chunk)
                count += len(chunk)
                positive_count += int(labels.sum().item())
        valid = validate(model, valid_paths, device, args.radius, args.nearest_k, args.batch_size)
        row = {
            "epoch": epoch + 1,
            "train_loss": loss_sum / max(1, count),
            "train_pairs": count,
            "train_positive_pairs": positive_count,
            "validation": valid,
        }
        history.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)
        candidate_key = (
            bool(row["validation"]["operating_point"]["gate_pass"]),
            row["validation"]["pair_average_precision"],
            -row["epoch"],
        )
        if best_key is None or candidate_key > best_key:
            best_key = candidate_key
            best = row
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
    assert best is not None and best_state is not None
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_status = (
        "PASS_EXTERNAL_GATE"
        if best["validation"]["operating_point"]["gate_pass"]
        else "REJECT_EXTERNAL_GATE"
    )
    checkpoint = args.output_dir / "visual_daughter_pair_final.pt"
    torch.save({"model": best_state, "radius": args.radius, "nearest_k": args.nearest_k,
                "geometry_dim": 5, "seed": SEED}, checkpoint)
    result = {
        "experiment": "EXP158",
        "status": checkpoint_status,
        "scope": "verified external 256-train/64-valid time-disjoint shards only",
        "parameters": vars(args) | {"data_dir": str(args.data_dir), "output_dir": str(args.output_dir)},
        "train_manifest_sha256": hashlib.sha256("\n".join(p.name for p in train_paths).encode()).hexdigest(),
        "valid_manifest_sha256": hashlib.sha256("\n".join(p.name for p in valid_paths).encode()).hexdigest(),
        "history": history,
        "selected_epoch": best["epoch"],
        "selected_validation": best["validation"],
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
    }
    result_path = args.output_dir / "external_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "selected_epoch", "selected_validation", "checkpoint_sha256")}, indent=2))


if __name__ == "__main__":
    main()
