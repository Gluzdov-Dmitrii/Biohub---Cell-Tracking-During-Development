#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp150_native_ilp_geometry_20260910"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run_root/results"

"$python_bin" "$run_root/evaluate_cached_native_ilp_geometry.py" \
  --repo "$forward_repo" \
  --data-dir "$project_root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp146/seed314_forward_cache" \
  --output "$run_root/results/forward.json" \
  > "$run_root/results/forward.log" 2>&1

"$python_bin" "$run_root/evaluate_cached_native_ilp_geometry.py" \
  --repo "$reverse_repo" \
  --data-dir "$project_root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp146/seed314_reverse_cache" \
  --output "$run_root/results/reverse.json" \
  > "$run_root/results/reverse.log" 2>&1

"$python_bin" "$run_root/analyze_safe_division.py" \
  --forward "$run_root/results/forward.json" \
  --reverse "$run_root/results/reverse.json" \
  --candidate-arm native_ilp_geometry \
  --experiment EXP150 \
  --output "$run_root/results/gate.json" \
  > "$run_root/results/gate.log" 2>&1

sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/* \
  > "$run_root/results/SHA256SUMS"
