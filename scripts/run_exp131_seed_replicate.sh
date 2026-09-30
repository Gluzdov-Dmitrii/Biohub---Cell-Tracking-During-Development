#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp130_44b6_to_6bba_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
data_dir="$project_root/data/pilot_single_44b6"
splits="$run_root/trainer_44b6_source.json"
movies_json="$run_root/development_6bba.json"
output_dir="$run_root/seed271828"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=271828
mkdir -p "$output_dir"
cd "$repo"

"$python_bin" "$run_root/run_finetune_math_sdp.py" \
  --method exp131_scratch_44b6_seed271828 \
  --data-dir "$data_dir" --splits "$splits" --split 0 \
  --epochs 5 --lr 0.0001 --batch-size 2 --num-workers 0 \
  --downsample 1,4,4 --det-loss-weight 1.0 --det-neg-weight 0.01 \
  --seed 271828 --single-gpu > "$output_dir/scratch_train.log" 2>&1

"$python_bin" "$run_root/run_finetune_math_sdp.py" \
  --method exp131_zebrahub_44b6_seed271828 \
  --data-dir "$data_dir" --splits "$splits" --split 0 \
  --epochs 5 --lr 0.0001 --batch-size 2 --num-workers 0 \
  --downsample 1,4,4 --det-loss-weight 1.0 --det-neg-weight 0.01 \
  --seed 271828 --single-gpu \
  --unet-weights "$project_root/models/community_zebrahub_pretrain_20260908/unet_pretrained.pth" \
  > "$output_dir/zebrahub_train.log" 2>&1

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" --data-dir "$project_root/data/pilot_development_6bba" \
  --weights "$repo/weights/exp131_scratch_44b6_seed271828/split_0/edge_predictor_best.pth" \
  --movies-json "$movies_json" --movie-key target_development \
  --output "$output_dir/scratch_registered_result.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 271828 > "$output_dir/scratch_eval.log" 2>&1

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" --data-dir "$project_root/data/pilot_development_6bba" \
  --weights "$repo/weights/exp131_zebrahub_44b6_seed271828/split_0/edge_predictor_best.pth" \
  --movies-json "$movies_json" --movie-key target_development \
  --output "$output_dir/zebrahub_registered_result.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 271828 > "$output_dir/zebrahub_eval.log" 2>&1
