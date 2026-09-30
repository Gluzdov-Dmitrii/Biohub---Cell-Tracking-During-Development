#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
exp146="$project_root/runs/exp146_scratch_seed_consensus_20260910"
run_root="$project_root/runs/exp147_safe_division_20260910"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$project_root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$project_root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
mkdir -p "$run_root/results"
test -s "$run_root/evaluate_coordinate_consensus.py"
test -s "$run_root/compare_registered_candidate.py"

selection="$exp146/results/source_only_topology_selection.json"
test -s "$selection"
forward_seed=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_topology_seed"]["44b6_to_6bba"])' "$selection")
reverse_seed=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_topology_seed"]["6bba_to_44b6"])' "$selection")
if [[ "$forward_seed" == 314159 ]]; then forward_cache="$exp146/seed314_forward_cache"; else forward_cache="$exp146/results/forward_seed271828_candidate_cache"; fi
if [[ "$reverse_seed" == 314159 ]]; then reverse_cache="$exp146/seed314_reverse_cache"; else reverse_cache="$exp146/results/reverse_seed271828_candidate_cache"; fi

"$python_bin" "$run_root/evaluate_safe_division_repair.py" --repo "$forward_repo" \
  --data-dir "$project_root/data/pilot_single_6bba" --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$forward_cache" --output "$run_root/results/forward.json" > "$run_root/results/forward.log" 2>&1
"$python_bin" "$run_root/evaluate_safe_division_repair.py" --repo "$reverse_repo" \
  --data-dir "$project_root/data/pilot_single_44b6" --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$reverse_cache" --output "$run_root/results/reverse.json" > "$run_root/results/reverse.log" 2>&1
"$python_bin" "$run_root/analyze_safe_division.py" --forward "$run_root/results/forward.json" \
  --reverse "$run_root/results/reverse.json" --output "$run_root/results/gate.json" \
  > "$run_root/results/gate.log" 2>&1
sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/* > "$run_root/results/SHA256SUMS"
