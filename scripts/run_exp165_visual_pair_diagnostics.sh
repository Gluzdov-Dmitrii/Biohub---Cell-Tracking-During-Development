#!/usr/bin/env bash
set -euo pipefail

root="$1"
run="$root/runs/exp165_visual_pair_diagnostics_20260910"
repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
python="$root/envs/prepost/py3.11-stdlib-v1/bin/python"

export CUDA_VISIBLE_DEVICES="GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba"
export CUBLAS_WORKSPACE_CONFIG=":4096:8"
export PYTHONPATH="$repo/src:$repo/scripts:$run"

exec "$python" "$run/diagnose_visual_pair_errors.py" \
  --data-dir "$root/data/zebrahub_training_set" \
  --tracking-scripts "$repo/scripts" \
  --backbone "$root/models/community_zebrahub_pretrain_20260908/edge_predictor_best.pth" \
  --backbone-sha256 3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e \
  --scratch-checkpoint "$root/runs/exp159_visual_daughter_pair_20260910/output/visual_daughter_pair_final.pt" \
  --scratch-sha256 167f50a77587571bc9d01f1da645deb2a3de1e56bb8608f39d3f0ebd587427fb \
  --feature-checkpoint "$root/runs/exp160_pretrained_feature_pair_20260910/output/pretrained_feature_pair_head.pt" \
  --feature-sha256 3cdc17023606b8193cbdfb97f1035a5e8383a17763764b80c2c99ae0f1590d38 \
  --output-dir "$run/output" \
  --batch-size 512
