#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp152_dense_native_source_selection_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_base="$project_root/runs/exp130_44b6_to_6bba_20260909"
reverse_base="$project_root/runs/exp137_6bba_to_44b6_20260909"
forward_repo="$forward_base/tracking_repo"
reverse_repo="$reverse_base/tracking_repo"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
mkdir -p "$run_root/results/forward_source_grid" "$run_root/results/reverse_source_grid"
export CUDA_VISIBLE_DEVICES=0
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159

evaluator="$run_root/evaluate_registered_model.py"
guided="$run_root/evaluate_native_guided_division.py"

if [[ ! -s "$run_root/results/forward_source_low.json" ]] || \
   [[ $(find "$run_root/results/forward_source_low_candidate_cache" -maxdepth 1 -name '*.npz' 2>/dev/null | wc -l) -ne 2 ]]; then
  "$python_bin" "$evaluator" --repo "$forward_repo" \
    --data-dir "$project_root/data/pilot_single_44b6" \
    --weights "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
    --movies-json "$forward_base/source_validation_44b6.json" --movie-key source_checkpoint_validation \
    --output "$run_root/results/forward_source_low.json" --det-threshold 0.985 \
    --edge-threshold 0.02 --weak-probability-weight 0.1 --unet-batch-size 4 --seed 314159 \
    > "$run_root/results/forward_source_low.log" 2>&1
fi

"$python_bin" "$evaluator" --repo "$reverse_repo" \
  --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth" \
  --movies-json "$run_root/exp152_source_validation_6bba.json" --movie-key source_checkpoint_validation \
  --output "$run_root/results/reverse_source_low.json" --det-threshold 0.985 \
  --edge-threshold 0.02 --weak-probability-weight 0.1 --unet-batch-size 4 --seed 314159 \
  > "$run_root/results/reverse_source_low.log" 2>&1

for threshold in 0.5 0.2 0.1 0.05 0.02; do
  "$python_bin" "$guided" --repo "$forward_repo" \
    --data-dir "$project_root/data/pilot_single_44b6" \
    --movies-json "$forward_base/source_validation_44b6.json" --movie-key source_checkpoint_validation \
    --cache-dir "$run_root/results/forward_source_low_candidate_cache" \
    --native-min-probability "$threshold" \
    --output "$run_root/results/forward_source_grid/result_${threshold}.json" \
    > "$run_root/results/forward_source_grid/eval_${threshold}.log" 2>&1
  "$python_bin" "$guided" --repo "$reverse_repo" \
    --data-dir "$project_root/data/pilot_single_6bba" \
    --movies-json "$run_root/exp152_source_validation_6bba.json" --movie-key source_checkpoint_validation  \
    --cache-dir "$run_root/results/reverse_source_low_candidate_cache" \
    --native-min-probability "$threshold" \
    --output "$run_root/results/reverse_source_grid/result_${threshold}.json" \
    > "$run_root/results/reverse_source_grid/eval_${threshold}.log" 2>&1
done

selector="$run_root/select_native_division_threshold.py"
"$python_bin" "$selector" \
  --result "0.5=$run_root/results/forward_source_grid/result_0.5.json" \
  --result "0.2=$run_root/results/forward_source_grid/result_0.2.json" \
  --result "0.1=$run_root/results/forward_source_grid/result_0.1.json" \
  --result "0.05=$run_root/results/forward_source_grid/result_0.05.json" \
  --result "0.02=$run_root/results/forward_source_grid/result_0.02.json" \
  --output "$run_root/results/forward_selection.json" > "$run_root/results/forward_selection.log" 2>&1
"$python_bin" "$selector" \
  --result "0.5=$run_root/results/reverse_source_grid/result_0.5.json" \
  --result "0.2=$run_root/results/reverse_source_grid/result_0.2.json" \
  --result "0.1=$run_root/results/reverse_source_grid/result_0.1.json" \
  --result "0.05=$run_root/results/reverse_source_grid/result_0.05.json" \
  --result "0.02=$run_root/results/reverse_source_grid/result_0.02.json" \
  --output "$run_root/results/reverse_selection.json" > "$run_root/results/reverse_selection.log" 2>&1

forward_threshold=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_threshold"])' "$run_root/results/forward_selection.json")
reverse_threshold=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_threshold"])' "$run_root/results/reverse_selection.json")

"$python_bin" "$evaluator" --repo "$forward_repo" \
  --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
  --movies-json "$exp146/all12_6bba.json" --output "$run_root/results/forward_target_low.json" \
  --det-threshold 0.985 --edge-threshold 0.02 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 314159 > "$run_root/results/forward_target_low.log" 2>&1
"$python_bin" "$evaluator" --repo "$reverse_repo" \
  --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth" \
  --movies-json "$exp146/all12_44b6.json" --output "$run_root/results/reverse_target_low.json" \
  --det-threshold 0.985 --edge-threshold 0.02 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 314159 > "$run_root/results/reverse_target_low.log" 2>&1

"$python_bin" "$guided" --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" --cache-dir "$run_root/results/forward_target_low_candidate_cache" \
  --native-min-probability "$forward_threshold" --output "$run_root/results/forward.json" \
  > "$run_root/results/forward.log" 2>&1
"$python_bin" "$guided" --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" --cache-dir "$run_root/results/reverse_target_low_candidate_cache" \
  --native-min-probability "$reverse_threshold" --output "$run_root/results/reverse.json" \
  > "$run_root/results/reverse.log" 2>&1

"$python_bin" "$run_root/analyze_safe_division.py" \
  --forward "$run_root/results/forward.json" --reverse "$run_root/results/reverse.json" \
  --candidate-arm registered_plus_native_guided_division --experiment EXP152 \
  --output "$run_root/results/gate.json" > "$run_root/results/gate.log" 2>&1
sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
