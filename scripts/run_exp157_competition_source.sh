#!/usr/bin/env bash
set -euo pipefail

root="$1"
run="$root/runs/exp157_division_positive_recalibration_20260910"
forward="$root/runs/exp130_44b6_to_6bba_20260909"
reverse="$root/runs/exp137_6bba_to_44b6_20260909"
exp152="$root/runs/exp152_dense_native_source_selection_20260910/results"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
weights="$run/output/zebrahub_pretrain/edge_predictor_best.pth"
mkdir -p "$run/competition_source"
export CUDA_VISIBLE_DEVICES=GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159

"$python_bin" "$run/score_fixed_coordinates_with_model.py" \
  --repo "$forward/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
  --weights "$weights" --fixed-cache-dir "$exp152/forward_source_low_candidate_cache" \
  --movies-json "$forward/source_validation_44b6.json" --movie-key source_checkpoint_validation \
  --output-cache-dir "$run/competition_source/forward_cache" --threshold 0.02 \
  > "$run/competition_source/forward_score.log" 2>&1

"$python_bin" "$run/score_fixed_coordinates_with_model.py" \
  --repo "$reverse/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
  --weights "$weights" --fixed-cache-dir "$exp152/reverse_source_low_candidate_cache" \
  --movies-json "$root/runs/exp154_external_edge_fixed_coordinates_20260910/exp152_source_validation_6bba.json" \
  --movie-key source_checkpoint_validation \
  --output-cache-dir "$run/competition_source/reverse_cache" --threshold 0.02 \
  > "$run/competition_source/reverse_score.log" 2>&1

"$python_bin" "$run/evaluate_native_guided_division.py" \
  --repo "$forward/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$forward/source_validation_44b6.json" --movie-key source_checkpoint_validation \
  --cache-dir "$run/competition_source/forward_cache" --native-min-probability 0.5 \
  --output "$run/competition_source/forward.json" > "$run/competition_source/forward.log" 2>&1

"$python_bin" "$run/evaluate_native_guided_division.py" \
  --repo "$reverse/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$root/runs/exp154_external_edge_fixed_coordinates_20260910/exp152_source_validation_6bba.json" \
  --movie-key source_checkpoint_validation --cache-dir "$run/competition_source/reverse_cache" \
  --native-min-probability 0.5 --output "$run/competition_source/reverse.json" \
  > "$run/competition_source/reverse.log" 2>&1

sha256sum "$run/competition_source"/*.json "$run/competition_source"/*.log \
  > "$run/competition_source/SHA256SUMS"
