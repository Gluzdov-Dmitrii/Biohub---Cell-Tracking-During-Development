#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
development_root="$project_root/runs/exp145_feature_tta_development_20260910"
run_root="$project_root/runs/exp145_feature_tta_locked_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
feature_repo="$development_root/tracking_repo"
evaluator="$project_root/runs/exp137_6bba_to_44b6_20260909/evaluate_registered_model.py"
gate="$run_root/exp145_feature_tta_development_gate.json"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
mkdir -p "$run_root/results"

"$python_bin" - "$gate" <<'PY'
import json
import sys
from pathlib import Path

gate = json.loads(Path(sys.argv[1]).read_text())
if gate.get("gate_pass") is not True or gate.get("locked_audit_authority") is not True:
    raise SystemExit("EXP145 development gate does not authorize locked audit")
PY

test -s "$feature_repo/scripts/predict_unet_transformer.py"
test "$(sha256sum "$feature_repo/scripts/predict_unet_transformer.py" | awk '{print $1}')" = \
  "4b6698ad7cfa8d7bc243107feb8783427ac01a2f76b77096c374e909eec3c4b1"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"

"$python_bin" "$evaluator" \
  --repo "$feature_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$forward_repo/weights/exp130_zebrahub_44b6_deterministic/split_0/edge_predictor_best.pth" \
  --movies-json "$run_root/locked_6bba.json" --movie-key target_locked_audit \
  --output "$run_root/results/forward_feature_tta.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 314159 > "$run_root/results/forward_feature_tta.log" 2>&1

"$python_bin" "$evaluator" \
  --repo "$feature_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$reverse_repo/weights/exp137_zebrahub_6bba_seed314159/split_1/edge_predictor_best.pth" \
  --movies-json "$run_root/locked_44b6.json" --movie-key target_locked_audit \
  --output "$run_root/results/reverse_feature_tta.json" \
  --det-threshold 0.985 --weak-probability-weight 0.1 \
  --unet-batch-size 4 --seed 314159 > "$run_root/results/reverse_feature_tta.log" 2>&1
