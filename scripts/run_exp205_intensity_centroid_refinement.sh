#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp205_intensity_centroid_refinement_20260911"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$project_root/runs/exp152_dense_native_source_selection_20260910"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run_root/results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

"$python_bin" "$run_root/evaluate_cached_intensity_centroid_refinement.py" \
  --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp152/results/forward_target_low_candidate_cache" \
  --minimum-length 8 --output "$run_root/results/forward.json" \
  > "$run_root/results/forward.log" 2>&1

"$python_bin" "$run_root/evaluate_cached_intensity_centroid_refinement.py" \
  --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp152/results/reverse_target_low_candidate_cache" \
  --minimum-length 3 --output "$run_root/results/reverse.json" \
  > "$run_root/results/reverse.log" 2>&1

"$python_bin" "$run_root/build_fixed_two_direction_comparison.py" \
  --forward "$run_root/results/forward.json" --reverse "$run_root/results/reverse.json" \
  --base-arm translation --candidate-arm intensity_centroid_r2_5_5 \
  --output "$run_root/results/fixed_comparison.json" \
  > "$run_root/results/fixed_comparison.log" 2>&1

"$python_bin" "$run_root/analyze_nested_pooled_stability.py" \
  --nested-result "$run_root/results/fixed_comparison.json" \
  --output "$run_root/results/stability.json" \
  > "$run_root/results/stability.log" 2>&1

sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json \
  "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
