#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp187_nested_short_track_family_20260911"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$project_root/runs/exp152_dense_native_source_selection_20260910"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run_root/results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159

"$python_bin" "$run_root/evaluate_cached_short_track_family.py" \
  --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp152/results/forward_target_low_candidate_cache" \
  --output "$run_root/results/forward.json" > "$run_root/results/forward.log" 2>&1

"$python_bin" "$run_root/evaluate_cached_short_track_family.py" \
  --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp152/results/reverse_target_low_candidate_cache" \
  --output "$run_root/results/reverse.json" > "$run_root/results/reverse.log" 2>&1

"$python_bin" "$run_root/validate_cached_short_track_control.py" \
  --forward "$run_root/results/forward.json" \
  --forward-parent "$exp152/results/forward_target_low.json" \
  --reverse "$run_root/results/reverse.json" \
  --reverse-parent "$exp152/results/reverse_target_low.json" \
  --output "$run_root/results/control_reproduction.json" \
  > "$run_root/results/control_reproduction.log" 2>&1

selector=("$python_bin" "$run_root/select_nested_pooled_arms.py"
  --forward "$run_root/results/forward.json"
  --reverse "$run_root/results/reverse.json"
  --base-arm no_filter)
for arm in no_filter min2 min3 min4 min5 min6 min6_rescue5_p90_d275_cap006; do
  selector+=(--candidate-arm "$arm")
done
"${selector[@]}" --output "$run_root/results/nested_selection.json" \
  > "$run_root/results/nested_selection.log" 2>&1

sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json \
  "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
