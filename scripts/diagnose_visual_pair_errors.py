"""Export external-only per-parent errors for the two daughter-pair heads.

This is a diagnosis program, not a competition evaluator. It deliberately
accepts only the frozen ``valid_*.npz`` Zebrahub shard set.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

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


def top_parent_rows(keys, labels, scores):
    grouped = defaultdict(list)
    for index, (key, label, score) in enumerate(zip(keys, labels, scores)):
        grouped[key].append((index, int(label), float(score)))
    result = {}
    for key, values in grouped.items():
        values.sort(key=lambda row: (-row[2], row[0]))
        result[key] = {
            "top_index": values[0][0],
            "top_label": values[0][1],
            "top_score": values[0][2],
            "positive_rank": next((rank for rank, row in enumerate(values, 1) if row[1]), None),
        }
    return result


def selected_parent_keys(top_rows, true_parent_count):
    ranked = sorted(top_rows.items(), key=lambda item: (-item[1]["top_score"], item[0]))
    tp = 0
    selected = None
    for count, (key, row) in enumerate(ranked, 1):
        tp += row["top_label"]
        precision = tp / count
        recall = tp / max(1, true_parent_count)
        candidate = (recall, precision, -row["top_score"], count, tp, row["top_score"])
        if precision >= 0.5 and (selected is None or candidate > selected[0]):
            selected = (candidate, count)
    count = 0 if selected is None else selected[1]
    return {key for key, _row in ranked[:count]}


def geometry_bins(rows):
    edges = (0.0, 2.0, 4.0, 6.0, 8.0, float("inf"))
    output = []
    for left, right in zip(edges[:-1], edges[1:]):
        selected = [row for row in rows if left <= row["positive_sister_um"] < right]
        output.append(
            {
                "sister_um": [left, None if np.isinf(right) else right],
                "division_parents": len(selected),
                "scratch_top_pair_recall": sum(row["scratch_positive_rank"] == 1 for row in selected)
                / max(1, len(selected)),
                "feature_top_pair_recall": sum(row["feature_positive_rank"] == 1 for row in selected)
                / max(1, len(selected)),
                "ensemble_top_pair_recall": sum(row["ensemble_positive_rank"] == 1 for row in selected)
                / max(1, len(selected)),
            }
        )
    return output


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
    parser.add_argument("--output-dir", type=Path, required=True)
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
    keys, labels_all, geometries, scratch_all, feature_all = [], [], [], [], []
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
            keys.extend((path.name, row.source) for row in chunk)
            geometries.extend(row.geometry for row in chunk)
            labels_all.extend(label_values.tolist())
            scratch_all.extend(scratch_scores.tolist())
            feature_all.extend(feature_scores.tolist())

    labels = np.asarray(labels_all, dtype=np.int8)
    geometry = np.asarray(geometries, dtype=np.float32)
    scratch_scores = np.asarray(scratch_all, dtype=np.float64)
    feature_scores = np.asarray(feature_all, dtype=np.float64)
    ensemble_scores = 0.5 * percentile_ranks(scratch_scores) + 0.5 * percentile_ranks(feature_scores)
    score_map = {"scratch": scratch_scores, "feature": feature_scores, "ensemble": ensemble_scores}
    tops = {name: top_parent_rows(keys, labels, scores) for name, scores in score_map.items()}
    true_parent_count = totals["division_pairs_covered"]
    selected = {name: selected_parent_keys(rows, true_parent_count) for name, rows in tops.items()}

    positive_geometry = {
        key: geometry[index]
        for index, (key, label) in enumerate(zip(keys, labels))
        if label
    }
    parent_keys = sorted(tops["scratch"])
    parent_rows = []
    for key in parent_keys:
        positive = positive_geometry.get(key)
        row = {"shard": key[0], "source": key[1], "is_covered_division": int(positive is not None)}
        for name in score_map:
            row[f"{name}_top_score"] = tops[name][key]["top_score"]
            row[f"{name}_positive_rank"] = tops[name][key]["positive_rank"]
            row[f"{name}_selected"] = int(key in selected[name])
        row["positive_sister_um"] = None if positive is None else float(positive[2])
        row["positive_midpoint_um"] = None if positive is None else float(positive[3])
        parent_rows.append(row)

    division_rows = [row for row in parent_rows if row["is_covered_division"]]
    union = selected["scratch"] | selected["feature"]
    intersection = selected["scratch"] & selected["feature"]
    true_keys = {key for key in parent_keys if tops["scratch"][key]["positive_rank"] is not None}
    result = {
        "experiment": "EXP165",
        "status": "DIAGNOSTIC_COMPLETE_NO_COMPETITION_EVALUATION",
        "scope": "64 frozen external time-validation shards only",
        "checkpoint_sha256": {"scratch": args.scratch_sha256, "pretrained_feature": args.feature_sha256,
                              "backbone": args.backbone_sha256},
        "counts": totals,
        "candidate_pair_ap": {name: average_precision(labels, scores) for name, scores in score_map.items()},
        "top_pair_recall_on_covered_divisions": {
            name: sum(row[f"{name}_positive_rank"] == 1 for row in division_rows) / max(1, len(division_rows))
            for name in score_map
        },
        "median_positive_pair_rank": {
            name: float(np.median([row[f"{name}_positive_rank"] for row in division_rows]))
            for name in score_map
        },
        "selected_parent_sets_at_best_precision_ge_0_5": {
            name: {"predicted": len(keys_selected), "true_positive": len(keys_selected & true_keys)}
            for name, keys_selected in selected.items()
        },
        "scratch_feature_selected_union": {
            "predicted": len(union), "true_positive": len(union & true_keys),
            "precision": len(union & true_keys) / max(1, len(union)),
            "recall": len(union & true_keys) / max(1, len(true_keys)),
            "intersection": len(intersection),
        },
        "positive_sister_distance_bins": geometry_bins(division_rows),
        "interpretation_limit": "Diagnostic use only; this validation set has already selected both heads.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(parent_rows[0])
    with (args.output_dir / "external_parent_diagnostics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(parent_rows)
    (args.output_dir / "diagnostic_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
