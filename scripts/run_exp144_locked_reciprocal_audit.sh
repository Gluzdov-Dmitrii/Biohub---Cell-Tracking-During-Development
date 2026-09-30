#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp144_locked_reciprocal_audit_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
evaluator="$project_root/runs/exp137_6bba_to_44b6_20260909/evaluate_registered_model.py"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
forward_movies="$run_root/locked_6bba.json"
reverse_movies="$run_root/locked_44b6.json"
development_gate="$run_root/exp137_reciprocal_development_gate.json"

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
mkdir -p "$run_root/results"

"$python_bin" - "$development_gate" "$forward_movies" "$reverse_movies" <<'PY'
import json
import sys
from pathlib import Path

gate = json.loads(Path(sys.argv[1]).read_text())
if gate.get("gate_pass") is not True or gate.get("locked_audit_authority") is not True:
    raise SystemExit("EXP137 reciprocal development gate does not authorize locked audit")
for path, prefix in ((Path(sys.argv[2]), "6bba_"), (Path(sys.argv[3]), "44b6_")):
    payload = json.loads(path.read_text())
    movies = payload.get("target_locked_audit")
    if not isinstance(movies, list) or len(movies) != 8:
        raise SystemExit(f"invalid locked movie list: {path}")
    if len(set(movies)) != 8 or any(not str(movie).startswith(prefix) for movie in movies):
        raise SystemExit(f"locked movie identity drift: {path}")
PY

evaluate() {
  local repo="$1"
  local data_dir="$2"
  local weights="$3"
  local movies="$4"
  local name="$5"
  test -s "$weights"
  "$python_bin" "$evaluator" \
    --repo "$repo" --data-dir "$data_dir" --weights "$weights" \
    --movies-json "$movies" --movie-key target_locked_audit \
    --output "$run_root/results/${name}.json" \
    --det-threshold 0.985 --weak-probability-weight 0.1 \
    --unet-batch-size 4 --seed 314159 > "$run_root/results/${name}.log" 2>&1
}

evaluate "$forward_repo" "$project_root/data/pilot_single_6bba" \
  "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
  "$forward_movies" forward_scratch
evaluate "$forward_repo" "$project_root/data/pilot_single_6bba" \
  "$forward_repo/weights/exp130_zebrahub_44b6_deterministic/split_0/edge_predictor_best.pth" \
  "$forward_movies" forward_zebrahub
evaluate "$reverse_repo" "$project_root/data/pilot_single_44b6" \
  "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth" \
  "$reverse_movies" reverse_scratch
evaluate "$reverse_repo" "$project_root/data/pilot_single_44b6" \
  "$reverse_repo/weights/exp137_zebrahub_6bba_seed314159/split_1/edge_predictor_best.pth" \
  "$reverse_movies" reverse_zebrahub
