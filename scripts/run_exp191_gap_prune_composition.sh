#!/usr/bin/env bash
set -euo pipefail

root="$1"
run="$root/runs/exp191_gap_prune_composition_20260911"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$root/runs/exp152_dense_native_source_selection_20260910"
exp186="$root/runs/exp186_nested_pooled_synthetic_gap_sweep_20260911"
exp190="$root/runs/exp190_extended_short_track_lengths_20260911"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run/results" "$run/heatmaps/forward" "$run/heatmaps/reverse" \
  "$run/arm_cache/forward_g50_t30" "$run/arm_cache/reverse_g45_t20" \
  "$run/arm_cache/reverse_g50_t30"
export CUDA_VISIBLE_DEVICES=0
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159

"$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
  --repo "$forward_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" --movie-key target_development \
  --cache-dir "$exp152/results/forward_target_low_candidate_cache" \
  --checkpoint "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/44b6/best.pt" \
  --checkpoint-sha256 ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f \
  --gap-close-um 5.0 --deepcenter-threshold 0.30 \
  --deepcenter-confirm-min-span-um 8.5 --synthetic-max-fraction 0.05 \
  --heatmap-cache-dir "$run/heatmaps/forward" \
  --arm-cache-dir "$run/arm_cache/forward_g50_t30" \
  --output "$run/results/forward_g50_t30.json" > "$run/results/forward_g50_t30.log" 2>&1

for spec in g45_t20:4.5:0.20 g50_t30:5.0:0.30; do
  IFS=: read -r label gap threshold <<< "$spec"
  "$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
    --repo "$reverse_repo" --data-dir "$root/data/pilot_single_44b6" \
    --movies-json "$exp146/all12_44b6.json" --movie-key target_development \
    --cache-dir "$exp152/results/reverse_target_low_candidate_cache" \
    --checkpoint "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/6bba/best.pt" \
    --checkpoint-sha256 ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e \
    --gap-close-um "$gap" --deepcenter-threshold "$threshold" \
    --deepcenter-confirm-min-span-um 8.5 --synthetic-max-fraction 0.05 \
    --heatmap-cache-dir "$run/heatmaps/reverse" \
    --arm-cache-dir "$run/arm_cache/reverse_$label" \
    --output "$run/results/reverse_$label.json" > "$run/results/reverse_$label.log" 2>&1
done

length_args=()
for length in 1 2 3 6 8 10 12; do length_args+=(--minimum-length "$length"); done
for spec in forward_g50_t30:forward reverse_g45_t20:reverse reverse_g50_t30:reverse; do
  IFS=: read -r label direction <<< "$spec"
  if [[ "$direction" == forward ]]; then
    repo="$forward_repo"; data="$root/data/pilot_single_6bba"; movies="$exp146/all12_6bba.json"
  else
    repo="$reverse_repo"; data="$root/data/pilot_single_44b6"; movies="$exp146/all12_44b6.json"
  fi
  "$python_bin" "$run/evaluate_cached_selected_edge_short_tracks.py" \
    --repo "$repo" --data-dir "$data" --movies-json "$movies" \
    --cache-dir "$run/arm_cache/$label" "${length_args[@]}" \
    --output "$run/results/${label}_filtered.json" > "$run/results/${label}_filtered.log" 2>&1
done

"$python_bin" "$run/validate_cached_arm_reproduction.py" \
  --cached-result "$run/results/forward_g50_t30_filtered.json" \
  --source-result "$run/results/forward_g50_t30.json" --source-arm synthetic_gap_deepcenter \
  --output "$run/results/forward_cache_reproduction.json" > "$run/results/forward_cache_reproduction.log" 2>&1
"$python_bin" "$run/validate_cached_arm_reproduction.py" \
  --cached-result "$run/results/reverse_g45_t20_filtered.json" \
  --source-result "$run/results/reverse_g45_t20.json" --source-arm synthetic_gap_deepcenter \
  --output "$run/results/reverse_g45_cache_reproduction.json" > "$run/results/reverse_g45_cache_reproduction.log" 2>&1
"$python_bin" "$run/validate_cached_arm_reproduction.py" \
  --cached-result "$run/results/reverse_g50_t30_filtered.json" \
  --source-result "$run/results/reverse_g50_t30.json" --source-arm synthetic_gap_deepcenter \
  --output "$run/results/reverse_g50_cache_reproduction.json" > "$run/results/reverse_g50_cache_reproduction.log" 2>&1

"$python_bin" "$run/merge_prefixed_oof_arms.py" \
  --source "base=$exp190/results/forward.json" \
  --source "gap_primary=$run/results/forward_g50_t30_filtered.json" \
  --source "gap50=$run/results/forward_g50_t30_filtered.json" \
  --output "$run/results/forward_merged.json"
"$python_bin" "$run/merge_prefixed_oof_arms.py" \
  --source "base=$exp190/results/reverse.json" \
  --source "gap_primary=$run/results/reverse_g45_t20_filtered.json" \
  --source "gap50=$run/results/reverse_g50_t30_filtered.json" \
  --output "$run/results/reverse_merged.json"

selector=("$python_bin" "$run/select_nested_pooled_arms.py"
  --forward "$run/results/forward_merged.json" --reverse "$run/results/reverse_merged.json"
  --base-arm base_no_filter)
for prefix in base gap_primary gap50; do
  for suffix in no_filter min2 min3 min6 min8 min10 min12; do
    selector+=(--candidate-arm "${prefix}_${suffix}")
  done
done
"${selector[@]}" --output "$run/results/nested_selection.json" \
  > "$run/results/nested_selection.log" 2>&1

sha256sum "$run"/*.py "$run"/*.sh "$run"/results/*.json "$run"/results/*.log \
  > "$run/results/SHA256SUMS"
