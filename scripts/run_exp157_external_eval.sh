#!/usr/bin/env bash
set -euo pipefail

root="$1"
run="$root/runs/exp157_division_positive_recalibration_20260910"
repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
export CUDA_VISIBLE_DEVICES=GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba
export PYTHONPATH="$repo/src:$repo/scripts"
"$root/envs/prepost/py3.11-stdlib-v1/bin/python" "$run/evaluate_zebrahub_division_head.py" \
  --tracking-scripts "$repo/scripts" --data-dir "$root/data/zebrahub_training_set" \
  --checkpoint "$run/output/zebrahub_pretrain/edge_predictor_best.pth" \
  --output "$run/external_division_result.json"
