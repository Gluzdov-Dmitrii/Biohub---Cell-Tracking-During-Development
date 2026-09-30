#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp170_parent_calibrated_pair_20260910"
repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
dep="$root/runs/exp160_pretrained_feature_pair_20260910"
python="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
export CUDA_VISIBLE_DEVICES="GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba"
export CUBLAS_WORKSPACE_CONFIG=":4096:8"
export PYTHONPATH="$run:$dep:$repo/src:$repo/scripts"
exec "$python" "$run/train_parent_calibrated_pair.py" --data-dir "$root/data/zebrahub_training_set" --tracking-scripts "$repo/scripts" --backbone "$root/models/community_zebrahub_pretrain_20260908/edge_predictor_best.pth" --backbone-sha256 3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e --output-dir "$run/output" --pair-epochs 10 --parent-epochs 30 --nearest-k 4 --ordinary-parent-fraction 0.05 --batch-size 512 --pair-learning-rate 0.0003 --parent-learning-rate 0.001
