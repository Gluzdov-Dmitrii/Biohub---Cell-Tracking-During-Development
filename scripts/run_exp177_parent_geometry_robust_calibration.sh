#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp177_parent_geometry_robust_calibration_20260910"
repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
dep="$root/runs/exp160_pretrained_feature_pair_20260910"
pair="$root/runs/exp171_parent_calibrated_pair_20260910/output/parent_calibrated_pair.pt"
geometry="$root/runs/exp175_parent_geometry_rank_ensemble_20260910/output/parent_geometry.pt"
python="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
data="$root/data/zebrahub_training_set"
backbone="$root/models/community_zebrahub_pretrain_20260908/edge_predictor_best.pth"
export CUDA_VISIBLE_DEVICES="GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONPATH="$run:$dep:$repo/src:$repo/scripts"
args=(
  --data-dir "$data"
  --tracking-scripts "$repo/scripts"
  --backbone "$backbone"
  --backbone-sha256 3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e
  --pair-checkpoint "$pair"
  --pair-checkpoint-sha256 caae45fd99e5be69f670a473178474414e735d6a5905ed59e79f350112e5fb8d
  --geometry-checkpoint "$geometry"
  --geometry-checkpoint-sha256 52cd08b05f66dd9b59ac4f371c06d4e410909fc1ab5a068a6e63c93897a02dac
  --output "$run/output/calibration.json"
  --batch-size 512
)
exec "$python" "$run/calibrate_parent_geometry_robust.py" "${args[@]}"



