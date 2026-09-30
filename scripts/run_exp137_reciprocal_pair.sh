#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp137_6bba_to_44b6_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
data_dir="$project_root/data/pilot_single_6bba"
splits="$run_root/trainer_6bba_source.json"
movies_json="$run_root/development_44b6.json"
output_dir="$run_root/pair_seed314159"
initializer="$project_root/models/community_zebrahub_pretrain_20260908/unet_pretrained.pth"
base_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
mkdir -p "$run_root" "$output_dir"
if [[ ! -d "$repo/src" ]]; then
  mkdir -p "$repo"
  rsync -a --exclude 'weights/' "$base_repo/" "$repo/"
  mkdir -p "$repo/weights"
fi
test -s "$initializer"
test -s "$splits"
test -s "$movies_json"
cd "$repo"

"$python_bin" "$run_root/run_finetune_math_sdp.py" \
  --method exp137_scratch_6bba_seed314159 \
  --data-dir "$data_dir" --splits "$splits" --split 1 \
  --epochs 5 --lr 0.0001 --batch-size 2 --num-workers 0 \
  --downsample 1,4,4 --det-loss-weight 1.0 --det-neg-weight 0.01 \
  --seed 314159 --single-gpu > "$output_dir/scratch_train.log" 2>&1

"$python_bin" "$run_root/run_finetune_math_sdp.py" \
  --method exp137_zebrahub_6bba_seed314159 \
  --data-dir "$data_dir" --splits "$splits" --split 1 \
  --epochs 5 --lr 0.0001 --batch-size 2 --num-workers 0 \
  --downsample 1,4,4 --det-loss-weight 1.0 --det-neg-weight 0.01 \
  --seed 314159 --single-gpu --unet-weights "$initializer" \
  > "$output_dir/zebrahub_train.log" 2>&1

for arm in scratch zebrahub; do
  if [[ "$arm" == scratch ]]; then method=exp137_scratch_6bba_seed314159; else method=exp137_zebrahub_6bba_seed314159; fi
  "$python_bin" "$run_root/evaluate_registered_model.py" \
    --repo "$repo" --data-dir "$project_root/data/pilot_single_44b6" \
    --weights "$repo/weights/$method/split_1/edge_predictor_best.pth" \
    --movies-json "$movies_json" --movie-key target_development \
    --output "$output_dir/${arm}_registered_result.json" \
    --det-threshold 0.985 --weak-probability-weight 0.1 \
    --unet-batch-size 4 --seed 314159 > "$output_dir/${arm}_eval.log" 2>&1
done
