#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp180_reciprocal_deepcenter_training_20260910"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
trainer="$run/train_deepcenter_explicit_split.py"
mkdir -p "$run/output/44b6" "$run/output/6bba" "$run/results"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=2026
export OMP_NUM_THREADS=8

"$python_bin" "$trainer" \
  --data-dir "$root/data/pilot_single_44b6" \
  --output-dir "$run/output/44b6" \
  --split-json "$run/trainer_44b6_source.json" \
  --epochs 2 --seed 2026 --batch-size 8 --num-workers 4 \
  --val-batches 24 --gate-eval-frames 200 --progress-interval 25 \
  > "$run/results/train_44b6.log" 2>&1

"$python_bin" "$trainer" \
  --data-dir "$root/data/pilot_single_6bba" \
  --output-dir "$run/output/6bba" \
  --split-json "$run/trainer_6bba_source.json" \
  --epochs 2 --seed 2026 --batch-size 8 --num-workers 4 \
  --val-batches 24 --gate-eval-frames 200 --progress-interval 25 \
  > "$run/results/train_6bba.log" 2>&1

"$python_bin" "$run/verify_deepcenter_training_pair.py" \
  --fold "44b6=$run/output/44b6" --fold "6bba=$run/output/6bba" \
  --output "$run/results/training_pair.json" \
  > "$run/results/verify.log" 2>&1
