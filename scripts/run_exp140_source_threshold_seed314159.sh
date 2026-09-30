#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp130_44b6_to_6bba_20260909"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
repo="$run_root/tracking_repo"
output_dir="$run_root/exp140_source_threshold_seed314159"
weights="$repo/weights/exp130_zebrahub_44b6_deterministic/split_0/edge_predictor_best.pth"
source_movies="$run_root/source_validation_44b6.json"
target_movies="$run_root/development_6bba.json"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
mkdir -p "$output_dir/source_grid"
cd "$repo"
test -s "$weights"

for threshold in 0.95 0.97 0.985 0.99; do
  "$python_bin" "$run_root/evaluate_registered_model.py" \
    --repo "$repo" --data-dir "$project_root/data/pilot_single_44b6" \
    --weights "$weights" --movies-json "$source_movies" \
    --movie-key source_checkpoint_validation \
    --output "$output_dir/source_grid/result_${threshold}.json" \
    --det-threshold "$threshold" --weak-probability-weight 0.1 \
    --unet-batch-size 4 --seed 314159 \
    > "$output_dir/source_grid/eval_${threshold}.log" 2>&1
done

selected_threshold=$("$python_bin" "$run_root/select_source_threshold.py" \
  --result 0.95 "$output_dir/source_grid/result_0.95.json" \
  --result 0.97 "$output_dir/source_grid/result_0.97.json" \
  --result 0.985 "$output_dir/source_grid/result_0.985.json" \
  --result 0.99 "$output_dir/source_grid/result_0.99.json" \
  --parent-threshold 0.985 --output "$output_dir/source_selection.json")
printf '%s\n' "$selected_threshold" > "$output_dir/selected_threshold.txt"

"$python_bin" "$run_root/evaluate_registered_model.py" \
  --repo "$repo" --data-dir "$project_root/data/pilot_development_6bba" \
  --weights "$weights" --movies-json "$target_movies" \
  --movie-key target_development \
  --output "$output_dir/target_registered_result.json" \
  --det-threshold "$selected_threshold" --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 314159 > "$output_dir/target_eval.log" 2>&1
