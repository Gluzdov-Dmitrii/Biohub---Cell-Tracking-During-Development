#!/usr/bin/env bash
set -euo pipefail

root="$1"
direction="$2"
run="$3"
code="$(cd "$(dirname "$0")" && pwd)"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
data="$root/data/honest195_missing/train"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run/results"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

if [[ "$direction" == "forward" ]]; then
  repo="$forward_repo"
  weights="$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth"
  flow_neighbours=32
  flow_alpha=0.50
  flow_minimum_length=8
  "$python_bin" "$code/evaluate_registered_model.py" \
    --repo "$repo" --data-dir "$data" --weights "$weights" \
    --movies-json "$run/movies.json" --movie-key target_development \
    --output "$run/results/base_raw.json" --det-threshold 0.985 \
    --edge-threshold 0.02 --weak-probability-weight 0.1 --unet-batch-size 4 --seed 314159 \
    > "$run/results/base_raw.log" 2>&1
  "$python_bin" "$code/evaluate_cached_short_track_family.py" \
    --repo "$repo" --data-dir "$data" --movies-json "$run/movies.json" \
    --cache-dir "$run/results/base_raw_candidate_cache" \
    --minimum-length 1 --minimum-length 8 \
    --output "$run/results/base_filtered.json" > "$run/results/base_filtered.log" 2>&1
elif [[ "$direction" == "reverse" ]]; then
  repo="$reverse_repo"
  weights="$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth"
  flow_neighbours=16
  flow_alpha=0.25
  flow_minimum_length=3
  deepcenter="$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/6bba/best.pt"
  mkdir -p "$run/heatmaps" "$run/arm_cache/gap"
  "$python_bin" "$code/evaluate_registered_model.py" \
    --repo "$repo" --data-dir "$data" --weights "$weights" \
    --movies-json "$run/movies.json" --movie-key target_development \
    --output "$run/results/base_raw.json" --det-threshold 0.985 \
    --edge-threshold 0.02 --weak-probability-weight 0.1 --unet-batch-size 4 --seed 314159 \
    > "$run/results/base_raw.log" 2>&1
  "$python_bin" "$code/evaluate_cached_short_track_family.py" \
    --repo "$repo" --data-dir "$data" --movies-json "$run/movies.json" \
    --cache-dir "$run/results/base_raw_candidate_cache" \
    --minimum-length 1 --minimum-length 3 \
    --output "$run/results/base_filtered.json" > "$run/results/base_filtered.log" 2>&1
  "$python_bin" "$code/evaluate_synthetic_gap_deepcenter.py" \
    --repo "$repo" --data-dir "$data" --movies-json "$run/movies.json" \
    --movie-key target_development --cache-dir "$run/results/base_raw_candidate_cache" \
    --checkpoint "$deepcenter" \
    --checkpoint-sha256 ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e \
    --gap-close-um 4.5 --deepcenter-threshold 0.20 \
    --deepcenter-confirm-min-span-um 8.5 --synthetic-max-fraction 0.05 \
    --heatmap-cache-dir "$run/heatmaps" --arm-cache-dir "$run/arm_cache/gap" \
    --output "$run/results/gap.json" > "$run/results/gap.log" 2>&1
  "$python_bin" "$code/evaluate_cached_selected_edge_short_tracks.py" \
    --repo "$repo" --data-dir "$data" --movies-json "$run/movies.json" \
    --cache-dir "$run/arm_cache/gap" --minimum-length 1 --minimum-length 6 \
    --output "$run/results/gap_filtered.json" > "$run/results/gap_filtered.log" 2>&1
  "$python_bin" "$code/validate_cached_arm_reproduction.py" \
    --cached-result "$run/results/gap_filtered.json" --source-result "$run/results/gap.json" \
    --source-arm synthetic_gap_deepcenter --output "$run/results/gap_cache_reproduction.json" \
    > "$run/results/gap_cache_reproduction.log" 2>&1
else
  echo "direction must be forward or reverse" >&2
  exit 2
fi

"$python_bin" "$code/evaluate_cached_fixed_local_flow.py" \
  --repo "$repo" --data-dir "$data" --movies-json "$run/movies.json" \
  --cache-dir "$run/results/base_raw_candidate_cache" \
  --minimum-length "$flow_minimum_length" --neighbours "$flow_neighbours" \
  --alpha "$flow_alpha" --output "$run/results/local_flow.json" \
  > "$run/results/local_flow.log" 2>&1

"$python_bin" "$code/validate_exp192_chunk_structure.py" \
  --run-dir "$run" --direction "$direction" \
  --output "$run/results/structure_validation.json" \
  > "$run/results/structure_validation.log" 2>&1

sha256sum "$code"/*.py "$code"/*.sh "$run"/*.json "$run"/results/*.json "$run"/results/*.log \
  > "$run/results/SHA256SUMS"
