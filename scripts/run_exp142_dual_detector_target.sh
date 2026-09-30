#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp130_44b6_to_6bba_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
output_dir="$run_root/exp142_dual_detector"
primary="$repo/weights/exp131_zebrahub_44b6_seed271828/split_0/edge_predictor_best.pth"
secondary="$repo/weights/exp130_zebrahub_44b6_deterministic/split_0/edge_predictor_best.pth"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=271828
cd "$repo"
test -s "$output_dir/source_registered_result.json"

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" --data-dir "$project_root/data/pilot_development_6bba" \
  --weights "$primary" --secondary-weights "$secondary" \
  --secondary-detection-weight 0.5 --min-candidate-retention 0.9 \
  --movies-json "$run_root/development_6bba.json" --movie-key target_development \
  --output "$output_dir/target_registered_result.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 271828 > "$output_dir/target_eval.log" 2>&1
