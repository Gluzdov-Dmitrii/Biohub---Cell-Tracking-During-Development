#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp184_synthetic_gap_target_oof_config_repair_20260911"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp180="$root/runs/exp180_reciprocal_deepcenter_training_20260910"
exp152="$root/runs/exp152_dense_native_source_selection_20260910/results"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
forward="$root/runs/exp130_44b6_to_6bba_20260909"
reverse="$root/runs/exp137_6bba_to_44b6_20260909"
mkdir -p "$run/results"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=2026
export OMP_NUM_THREADS=8

"$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
  --repo "$forward/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" --movie-key target_development \
  --cache-dir "$exp152/forward_target_low_candidate_cache" \
  --checkpoint "$exp180/output/44b6/best.pt" \
  --checkpoint-sha256 ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f \
  --output "$run/results/forward.json" > "$run/results/forward.log" 2>&1

"$python_bin" "$run/evaluate_synthetic_gap_deepcenter.py" \
  --repo "$reverse/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" --movie-key target_development \
  --cache-dir "$exp152/reverse_target_low_candidate_cache" \
  --checkpoint "$exp180/output/6bba/best.pt" \
  --checkpoint-sha256 ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e \
  --output "$run/results/reverse.json" > "$run/results/reverse.log" 2>&1

"$python_bin" "$run/select_synthetic_gap_target_gate.py" \
  --forward "$run/results/forward.json" --reverse "$run/results/reverse.json" \
  --output "$run/results/gate.json" > "$run/results/gate.log" 2>&1
