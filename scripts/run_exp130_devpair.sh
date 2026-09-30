#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp130_44b6_to_6bba_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
data_dir="$project_root/data/pilot_development_6bba"
movies_json="$run_root/development_6bba.json"
output_dir="$run_root/development_eval"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
mkdir -p "$output_dir"

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" \
  --data-dir "$data_dir" \
  --weights "$repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
  --movies-json "$movies_json" \
  --movie-key target_development \
  --output "$output_dir/scratch_registered_result.json" \
  --det-threshold 0.985 \
  --weak-probability-weight 0.1 \
  --unet-batch-size 4 \
  --seed 314159

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" \
  --data-dir "$data_dir" \
  --weights "$repo/weights/exp130_zebrahub_44b6_deterministic/split_0/edge_predictor_best.pth" \
  --movies-json "$movies_json" \
  --movie-key target_development \
  --output "$output_dir/zebrahub_registered_result.json" \
  --det-threshold 0.985 \
  --weak-probability-weight 0.1 \
  --unet-batch-size 4 \
  --seed 314159
