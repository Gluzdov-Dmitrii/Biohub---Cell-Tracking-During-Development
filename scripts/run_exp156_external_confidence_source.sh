#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
run_root="$project_root/runs/exp154_external_edge_fixed_coordinates_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
evaluator="$run_root/evaluate_cached_external_confidence_gate.py"
selector="$run_root/select_external_confidence_gate.py"
results="$run_root/results/exp156"
mkdir -p "$results/forward_source" "$results/reverse_source"

for floor in 0.5 0.8; do
  for bonus in 0.01 0.03; do
    key="f${floor}_b${bonus}"
    "$python_bin" "$evaluator" --repo "$forward_repo" \
      --data-dir "$project_root/data/pilot_single_44b6" \
      --cache-dir "$run_root/results/forward_source_cache" \
      --movies-json "$project_root/runs/exp130_44b6_to_6bba_20260909/source_validation_44b6.json" \
      --movie-key source_checkpoint_validation --probability-floor "$floor" \
      --bonus-weight "$bonus" --output "$results/forward_source/${key}.json" \
      > "$results/forward_source/${key}.log" 2>&1
    "$python_bin" "$evaluator" --repo "$reverse_repo" \
      --data-dir "$project_root/data/pilot_single_6bba" \
      --cache-dir "$run_root/results/reverse_source_cache" \
      --movies-json "$run_root/exp152_source_validation_6bba.json" \
      --movie-key source_checkpoint_validation --probability-floor "$floor" \
      --bonus-weight "$bonus" --output "$results/reverse_source/${key}.json" \
      > "$results/reverse_source/${key}.log" 2>&1
  done
done

forward_args=()
reverse_args=()
for floor in 0.5 0.8; do
  for bonus in 0.01 0.03; do
    key="f${floor}_b${bonus}"
    forward_args+=(--result "$results/forward_source/${key}.json")
    reverse_args+=(--result "$results/reverse_source/${key}.json")
  done
done
"$python_bin" "$selector" "${forward_args[@]}" --output "$results/forward_selection.json" \
  > "$results/forward_selection.log" 2>&1
"$python_bin" "$selector" "${reverse_args[@]}" --output "$results/reverse_selection.json" \
  > "$results/reverse_selection.log" 2>&1
sha256sum "$results"/forward_source/*.json "$results"/reverse_source/*.json \
  "$results"/forward_selection.json "$results"/reverse_selection.json > "$results/SHA256SUMS"
