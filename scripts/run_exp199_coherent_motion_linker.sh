#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp199_coherent_motion_linker_20260911"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$project_root/runs/exp152_dense_native_source_selection_20260910"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run_root/results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159

"$python_bin" "$run_root/evaluate_cached_coherent_motion_linker.py" \
  --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp152/results/forward_target_low_candidate_cache" \
  --minimum-length 8 --output "$run_root/results/forward.json" \
  > "$run_root/results/forward.log" 2>&1

"$python_bin" "$run_root/evaluate_cached_coherent_motion_linker.py" \
  --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp152/results/reverse_target_low_candidate_cache" \
  --minimum-length 3 --output "$run_root/results/reverse.json" \
  > "$run_root/results/reverse.log" 2>&1

selector=("$python_bin" "$run_root/select_nested_pooled_arms.py"
  --forward "$run_root/results/forward.json"
  --reverse "$run_root/results/reverse.json"
  --base-arm translation)
for arm in translation rigid_a025 rigid_a050 similarity_a025 similarity_a050; do
  selector+=(--candidate-arm "$arm")
done
"${selector[@]}" --output "$run_root/results/nested_selection.json" \
  > "$run_root/results/nested_selection.log" 2>&1

"$python_bin" "$run_root/analyze_nested_pooled_stability.py" \
  --nested-result "$run_root/results/nested_selection.json" \
  --output "$run_root/results/stability.json" \
  > "$run_root/results/stability.log" 2>&1

sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json \
  "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
