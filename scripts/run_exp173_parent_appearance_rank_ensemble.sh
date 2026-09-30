#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp173_parent_appearance_rank_ensemble_20260910"
repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
dep="$root/runs/exp160_pretrained_feature_pair_20260910"
parent="$root/runs/exp171_parent_calibrated_pair_20260910"
python="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
export CUDA_VISIBLE_DEVICES="GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba"
export PYTHONPATH="$run:$dep:$repo/src:$repo/scripts"
exec "$python" "$run/train_parent_appearance_rank_ensemble.py" --data-dir "$root/data/zebrahub_training_set" --tracking-scripts "$repo/scripts" --backbone "$root/models/community_zebrahub_pretrain_20260908/edge_predictor_best.pth" --backbone-sha256 3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e --checkpoint "$parent/output/parent_calibrated_pair.pt" --checkpoint-sha256 caae45fd99e5be69f670a473178474414e735d6a5905ed59e79f350112e5fb8d --output-dir "$run/output" --epochs 20 --batch-size 512
