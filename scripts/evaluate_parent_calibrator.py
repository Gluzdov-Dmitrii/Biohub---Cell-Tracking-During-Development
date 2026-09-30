"""Compare raw top-pair ranking with the trained parent MLP, external only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from train_parent_calibrated_pair import ParentPropensityHead, fixed_split, parent_dataset, select_parent_operating
from train_pretrained_feature_daughter_pair import PretrainedFeaturePairHead, load_backbone
from train_visual_daughter_pair import average_precision, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--tracking-scripts", type=Path, required=True)
    parser.add_argument("--backbone", type=Path, required=True)
    parser.add_argument("--backbone-sha256", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    if sha256(args.checkpoint) != args.checkpoint_sha256:
        raise RuntimeError("checkpoint SHA mismatch")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("Leased GPU required")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    pair_head = PretrainedFeaturePairHead().to(device)
    pair_head.load_state_dict(payload["pair_head"], strict=True)
    pair_head.eval()
    parent_head = ParentPropensityHead(payload["input_dim"]).to(device)
    parent_head.load_state_dict(payload["parent_head"], strict=True)
    parent_head.eval()
    backbone = load_backbone(
        args.tracking_scripts, args.backbone, args.backbone_sha256, device
    )
    _fit_paths, calibration_paths, evaluation_paths = fixed_split(args.data_dir)
    result = {
        "experiment": "EXP172",
        "status": "DIAGNOSTIC_COMPLETE_NO_COMPETITION_EVALUATION",
        "checkpoint_sha256": args.checkpoint_sha256,
        "splits": {},
    }
    for name, paths in (("calibration", calibration_paths), ("prospective", evaluation_paths)):
        features, labels, keys, totals, pair_ap = parent_dataset(
            pair_head, backbone, paths, device, payload["nearest_k"], args.batch_size
        )
        raw_scores = features[:, -2]
        with torch.no_grad():
            mlp_scores = torch.sigmoid(
                parent_head(torch.from_numpy(features).to(device))
            ).cpu().numpy()
        true_parents = totals["division_pairs_covered"]
        result["splits"][name] = {
            "counts": totals,
            "candidate_pair_ap": pair_ap,
            "top_pair_correct": int(labels.sum()),
            "raw_top_pair": {
                "parent_ap": average_precision(labels.astype(np.int8), raw_scores),
                "operating_point": select_parent_operating(
                    keys, labels, raw_scores, true_parents
                ),
            },
            "parent_mlp": {
                "parent_ap": average_precision(labels.astype(np.int8), mlp_scores),
                "operating_point": select_parent_operating(
                    keys, labels, mlp_scores, true_parents
                ),
            },
            "score_correlation": float(np.corrcoef(raw_scores, mlp_scores)[0, 1]),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
