#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp186_nested_pooled_synthetic_gap_sweep_20260911"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp180="$root/runs/exp180_reciprocal_deepcenter_training_20260910"
exp152="$root/runs/exp152_dense_native_source_selection_20260910/results"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
exp185="$root/runs/exp185_synthetic_gap_target_oof_continuation_20260911"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run/results/forward" "$run/results/reverse" "$run/heatmaps/forward" "$run/heatmaps/reverse"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=2026
export OMP_NUM_THREADS=8

labels=(g50_t25 g50_t10 g50_t15 g50_t20 g50_t30 g45_t20 g58_t20)
gaps=(5.0 5.0 5.0 5.0 5.0 4.5 5.8)
thresholds=(0.25 0.10 0.15 0.20 0.30 0.20 0.20)

for index in "${!labels[@]}"; do
  label="${labels[$index]}"
  gap="${gaps[$index]}"
  threshold="${thresholds[$index]}"
  "$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
    --repo "$forward_repo" --data-dir "$root/data/pilot_single_6bba" \
    --movies-json "$exp146/all12_6bba.json" --movie-key target_development \
    --cache-dir "$exp152/forward_target_low_candidate_cache" \
    --checkpoint "$exp180/output/44b6/best.pt" \
    --checkpoint-sha256 ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f \
    --gap-close-um "$gap" --deepcenter-threshold "$threshold" \
    --deepcenter-confirm-min-span-um 8.5 --synthetic-max-fraction 0.05 \
    --heatmap-cache-dir "$run/heatmaps/forward" \
    --output "$run/results/forward/$label.json" \
    > "$run/results/forward/$label.log" 2>&1

  "$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
    --repo "$reverse_repo" --data-dir "$root/data/pilot_single_44b6" \
    --movies-json "$exp146/all12_44b6.json" --movie-key target_development \
    --cache-dir "$exp152/reverse_target_low_candidate_cache" \
    --checkpoint "$exp180/output/6bba/best.pt" \
    --checkpoint-sha256 ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e \
    --gap-close-um "$gap" --deepcenter-threshold "$threshold" \
    --deepcenter-confirm-min-span-um 8.5 --synthetic-max-fraction 0.05 \
    --heatmap-cache-dir "$run/heatmaps/reverse" \
    --output "$run/results/reverse/$label.json" \
    > "$run/results/reverse/$label.log" 2>&1
done

"$python_bin" "$run/validate_exp186_baseline_reproduction.py" \
  --reference-forward "$exp185/results/forward.json" \
  --reference-reverse "$exp185/results/reverse.json" \
  --candidate-forward "$run/results/forward/g50_t25.json" \
  --candidate-reverse "$run/results/reverse/g50_t25.json" \
  > "$run/results/baseline_reproduction.log" 2>&1

selector_args=()
for label in "${labels[@]}"; do
  selector_args+=(--forward "$label=$run/results/forward/$label.json")
  selector_args+=(--reverse "$label=$run/results/reverse/$label.json")
done
"$python_bin" "$run/select_nested_pooled_synthetic_gap.py" \
  "${selector_args[@]}" --output "$run/results/nested_selection.json" \
  > "$run/results/nested_selection.log" 2>&1
