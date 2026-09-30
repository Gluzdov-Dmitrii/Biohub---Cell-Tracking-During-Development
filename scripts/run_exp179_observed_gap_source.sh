#!/usr/bin/env bash
set -euo pipefail
root="$1"
run="$root/runs/exp179_observed_gap_source_20260910"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward="$root/runs/exp130_44b6_to_6bba_20260909"
reverse="$root/runs/exp137_6bba_to_44b6_20260909"
cache="$root/runs/exp152_dense_native_source_selection_20260910/results"
mkdir -p "$run/results"

"$python_bin" "$run/evaluate_observed_gap_close.py" \
  --repo "$forward/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$forward/source_validation_44b6.json" \
  --cache-dir "$cache/forward_source_low_candidate_cache" \
  --output "$run/results/forward.json" > "$run/results/forward.log" 2>&1

"$python_bin" "$run/evaluate_observed_gap_close.py" \
  --repo "$reverse/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$root/runs/exp152_dense_native_source_selection_20260910/exp152_source_validation_6bba.json" \
  --cache-dir "$cache/reverse_source_low_candidate_cache" \
  --output "$run/results/reverse.json" > "$run/results/reverse.log" 2>&1

"$python_bin" "$run/select_observed_gap_gate.py" \
  --forward "$run/results/forward.json" --reverse "$run/results/reverse.json" \
  --output "$run/results/gate.json" > "$run/results/gate.log" 2>&1
