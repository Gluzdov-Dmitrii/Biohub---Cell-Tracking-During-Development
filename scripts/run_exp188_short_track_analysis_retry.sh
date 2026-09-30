#!/usr/bin/env bash
set -euo pipefail

project_root="$1"
exp187="$project_root/runs/exp187_nested_short_track_family_20260911"
run_root="$project_root/runs/exp188_short_track_analysis_retry_20260911"
python_bin="$project_root/envs/prepost/py3.11-stdlib-v1/bin/python"
exp152="$project_root/runs/exp152_dense_native_source_selection_20260910"
mkdir -p "$run_root/results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159

printf '%s  %s\n' \
  'd68b656ad6c5f595a025e51c879b744d3f4cd150b3bc928ce8c7a8e3532ca45e' \
  "$exp187/results/forward.json" \
  'b401d688bd4234171010c62b49a41756ba4bb9d28ade66e008e73147b239fa43' \
  "$exp187/results/reverse.json" | sha256sum -c -

"$python_bin" "$run_root/validate_cached_short_track_control.py" \
  --forward "$exp187/results/forward.json" \
  --forward-parent "$exp152/results/forward_target_low.json" \
  --reverse "$exp187/results/reverse.json" \
  --reverse-parent "$exp152/results/reverse_target_low.json" \
  --output "$run_root/results/control_reproduction.json" \
  > "$run_root/results/control_reproduction.log" 2>&1

selector=("$python_bin" "$run_root/select_nested_pooled_arms.py"
  --forward "$exp187/results/forward.json"
  --reverse "$exp187/results/reverse.json"
  --base-arm no_filter)
for arm in no_filter min2 min3 min4 min5 min6 min6_rescue5_p90_d275_cap006; do
  selector+=(--candidate-arm "$arm")
done
"${selector[@]}" --output "$run_root/results/nested_selection.json" \
  > "$run_root/results/nested_selection.log" 2>&1

sha256sum "$run_root"/*.py "$run_root"/*.sh "$run_root"/results/*.json \
  "$run_root"/results/*.log > "$run_root/results/SHA256SUMS"
