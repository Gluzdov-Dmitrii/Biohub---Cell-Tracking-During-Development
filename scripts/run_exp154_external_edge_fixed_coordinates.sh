#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp154_external_edge_fixed_coordinates_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_base="$project_root/runs/exp130_44b6_to_6bba_20260909"
reverse_base="$project_root/runs/exp137_6bba_to_44b6_20260909"
forward_repo="$forward_base/tracking_repo"
reverse_repo="$reverse_base/tracking_repo"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$project_root/runs/exp152_dense_native_source_selection_20260910/results"
weights="$project_root/models/community_zebrahub_pretrain_20260908/edge_predictor_best.pth"
mkdir -p "$run_root/results/forward_source_grid" "$run_root/results/reverse_source_grid"
export CUDA_VISIBLE_DEVICES=GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159

scorer="$run_root/score_fixed_coordinates_with_model.py"
guided="$run_root/evaluate_native_guided_division.py"
selector="$run_root/select_native_division_threshold.py"

"$python_bin" "$scorer" --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$weights" --fixed-cache-dir "$exp152/forward_source_low_candidate_cache" \
  --movies-json "$forward_base/source_validation_44b6.json" --movie-key source_checkpoint_validation \
  --output-cache-dir "$run_root/results/forward_source_cache" --threshold 0.02 \
  > "$run_root/results/forward_source_score.log" 2>&1
"$python_bin" "$scorer" --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$weights" --fixed-cache-dir "$exp152/reverse_source_low_candidate_cache" \
  --movies-json "$run_root/exp152_source_validation_6bba.json" --movie-key source_checkpoint_validation \
  --output-cache-dir "$run_root/results/reverse_source_cache" --threshold 0.02 \
  > "$run_root/results/reverse_source_score.log" 2>&1

for threshold in 0.5 0.2; do
  "$python_bin" "$guided" --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_44b6" \
    --movies-json "$forward_base/source_validation_44b6.json" --movie-key source_checkpoint_validation \
    --cache-dir "$run_root/results/forward_source_cache" --native-min-probability "$threshold" \
    --output "$run_root/results/forward_source_grid/result_${threshold}.json" \
    > "$run_root/results/forward_source_grid/eval_${threshold}.log" 2>&1
  "$python_bin" "$guided" --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_6bba" \
    --movies-json "$run_root/exp152_source_validation_6bba.json" --movie-key source_checkpoint_validation \
    --cache-dir "$run_root/results/reverse_source_cache" --native-min-probability "$threshold" \
    --output "$run_root/results/reverse_source_grid/result_${threshold}.json" \
    > "$run_root/results/reverse_source_grid/eval_${threshold}.log" 2>&1
done

"$python_bin" "$selector" \
  --result "0.5=$run_root/results/forward_source_grid/result_0.5.json" \
  --result "0.2=$run_root/results/forward_source_grid/result_0.2.json" \
  --output "$run_root/results/forward_selection.json" > "$run_root/results/forward_selection.log" 2>&1
"$python_bin" "$selector" \
  --result "0.5=$run_root/results/reverse_source_grid/result_0.5.json" \
  --result "0.2=$run_root/results/reverse_source_grid/result_0.2.json" \
  --output "$run_root/results/reverse_selection.json" > "$run_root/results/reverse_selection.log" 2>&1

forward_threshold=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_threshold"])' "$run_root/results/forward_selection.json")
reverse_threshold=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_threshold"])' "$run_root/results/reverse_selection.json")

"$python_bin" "$scorer" --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$weights" --fixed-cache-dir "$exp152/forward_target_low_candidate_cache" \
  --movies-json "$exp146/all12_6bba.json" --movie-key target_development \
  --output-cache-dir "$run_root/results/forward_target_cache" --threshold 0.02 \
  > "$run_root/results/forward_target_score.log" 2>&1
"$python_bin" "$scorer" --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$weights" --fixed-cache-dir "$exp152/reverse_target_low_candidate_cache" \
  --movies-json "$exp146/all12_44b6.json" --movie-key target_development \
  --output-cache-dir "$run_root/results/reverse_target_cache" --threshold 0.02 \
  > "$run_root/results/reverse_target_score.log" 2>&1

"$python_bin" "$guided" --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" --movie-key target_development \
  --cache-dir "$run_root/results/forward_target_cache" --native-min-probability "$forward_threshold" \
  --output "$run_root/results/forward.json" > "$run_root/results/forward.log" 2>&1
"$python_bin" "$guided" --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" --movie-key target_development \
  --cache-dir "$run_root/results/reverse_target_cache" --native-min-probability "$reverse_threshold" \
  --output "$run_root/results/reverse.json" > "$run_root/results/reverse.log" 2>&1

"$python_bin" "$run_root/analyze_safe_division.py" \
  --forward "$run_root/results/forward.json" --reverse "$run_root/results/reverse.json" \
  --candidate-arm registered_plus_native_guided_division --experiment EXP154 \
  --output "$run_root/results/gate.json" > "$run_root/results/gate.log" 2>&1
sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
