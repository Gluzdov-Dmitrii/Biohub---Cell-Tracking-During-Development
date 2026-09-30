#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp130_44b6_to_6bba_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
output_dir="$run_root/exp141_unet_soup"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=271828
cd "$repo"
test -s "$output_dir/unet_soup.pth"

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$output_dir/unet_soup.pth" \
  --movies-json "$run_root/source_validation_44b6.json" \
  --movie-key source_checkpoint_validation \
  --output "$output_dir/source_registered_result.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 271828 > "$output_dir/source_eval.log" 2>&1
