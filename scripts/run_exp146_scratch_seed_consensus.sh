#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp146_scratch_seed_consensus_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_base="$project_root/runs/exp130_44b6_to_6bba_20260909"
reverse_base="$project_root/runs/exp137_6bba_to_44b6_20260909"
forward_repo="$forward_base/tracking_repo"
reverse_repo="$reverse_base/tracking_repo"
results="$run_root/results"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=271828
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
mkdir -p "$results" "$run_root/seed314_forward_cache" "$run_root/seed314_reverse_cache"

test -s "$run_root/all12_6bba.json"
test -s "$run_root/all12_44b6.json"
test -s "$run_root/trainer_6bba_source.json"

cd "$reverse_repo"
"$python_bin" "$reverse_base/run_finetune_math_sdp.py" \
  --method exp146_scratch_6bba_seed271828 \
  --data-dir "$project_root/data/pilot_single_6bba" \
  --splits "$run_root/trainer_6bba_source.json" --split 0 \
  --epochs 5 --lr 0.0001 --batch-size 2 --num-workers 0 \
  --downsample 1,4,4 --det-loss-weight 1.0 --det-neg-weight 0.01 \
  --seed 271828 --single-gpu > "$results/reverse_seed271828_train.log" 2>&1

"$python_bin" - "$forward_base/scratch_deterministic/train.log" \
  "$forward_base/seed271828/scratch_train.log" \
  "$reverse_base/pair_seed314159/scratch_train.log" \
  "$results/reverse_seed271828_train.log" \
  "$results/source_only_topology_selection.json" <<'PY'
import json
import re
import sys
from pathlib import Path

def score(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    values = re.findall(r"Best score \(acc\*recall\): ([0-9.]+)", text)
    if len(values) != 1:
        raise SystemExit(f"expected one best score in {path}, found {values}")
    return float(values[0])

paths = list(map(Path, sys.argv[1:5]))
scores = {
    "44b6_to_6bba": {"314159": score(paths[0]), "271828": score(paths[1])},
    "6bba_to_44b6": {"314159": score(paths[2]), "271828": score(paths[3])},
}
selected = {
    fold: ("271828" if values["271828"] > values["314159"] else "314159")
    for fold, values in scores.items()
}
payload = {
    "status": "FROZEN_FROM_SOURCE_ONLY_BEFORE_TARGET_INFERENCE",
    "metric": "training-time acc*recall on two source checkpoint-selection movies",
    "scores": scores,
    "selected_topology_seed": selected,
    "tie_rule": "314159"
}
Path(sys.argv[5]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

evaluator="$reverse_base/evaluate_registered_model.py"
"$python_bin" "$evaluator" \
  --repo "$forward_repo" --data-dir "$project_root/data/pilot_single_6bba" \
  --weights "$forward_repo/weights/exp131_scratch_44b6_seed271828/split_0/edge_predictor_best.pth" \
  --movies-json "$run_root/all12_6bba.json" --movie-key target_development \
  --output "$results/forward_seed271828.json" --det-threshold 0.985 \
  --weak-probability-weight 0.1 --unet-batch-size 4 --seed 271828 \
  > "$results/forward_seed271828_eval.log" 2>&1

"$python_bin" "$evaluator" \
  --repo "$reverse_repo" --data-dir "$project_root/data/pilot_single_44b6" \
  --weights "$reverse_repo/weights/exp146_scratch_6bba_seed271828/split_0/edge_predictor_best.pth" \
  --movies-json "$run_root/all12_44b6.json" --movie-key target_development \
  --output "$results/reverse_seed271828.json" --det-threshold 0.985 \
  --weak-probability-weight 0.1 --unet-batch-size 4 --seed 271828 \
  > "$results/reverse_seed271828_eval.log" 2>&1

for cache in \
  "$forward_base/development_eval/scratch_registered_result_candidate_cache" \
  "$project_root/runs/exp144_locked_reciprocal_audit_20260910/results/forward_scratch_candidate_cache"; do
  for file in "$cache"/*.npz; do ln -sf "$file" "$run_root/seed314_forward_cache/$(basename "$file")"; done
done
for cache in \
  "$reverse_base/pair_seed314159/scratch_registered_result_candidate_cache" \
  "$project_root/runs/exp144_locked_reciprocal_audit_20260910/results/reverse_scratch_candidate_cache"; do
  for file in "$cache"/*.npz; do ln -sf "$file" "$run_root/seed314_reverse_cache/$(basename "$file")"; done
done
test "$(find "$run_root/seed314_forward_cache" -type l | wc -l)" -eq 12
test "$(find "$run_root/seed314_reverse_cache" -type l | wc -l)" -eq 12

consensus="$run_root/evaluate_coordinate_consensus.py"
"$python_bin" "$consensus" --repo "$forward_repo" \
  --data-dir "$project_root/data/pilot_single_6bba" --movies-json "$run_root/all12_6bba.json" \
  --scratch-cache "$run_root/seed314_forward_cache" \
  --zebrahub-cache "$results/forward_seed271828_candidate_cache" \
  --output "$results/forward_consensus.json" --radius-um 2.0 --alpha 0.5 \
  > "$results/forward_consensus.log" 2>&1
"$python_bin" "$consensus" --repo "$reverse_repo" \
  --data-dir "$project_root/data/pilot_single_44b6" --movies-json "$run_root/all12_44b6.json" \
  --scratch-cache "$run_root/seed314_reverse_cache" \
  --zebrahub-cache "$results/reverse_seed271828_candidate_cache" \
  --output "$results/reverse_consensus.json" --radius-um 2.0 --alpha 0.5 \
  > "$results/reverse_consensus.log" 2>&1

sha256sum "$results"/*.json "$results"/*.log > "$results/SHA256SUMS"
