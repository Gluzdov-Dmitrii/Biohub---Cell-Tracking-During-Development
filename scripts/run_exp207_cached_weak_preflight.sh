#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp207_d4_feature_tta8_v1_20260911"
run="$root/runs/exp207_d4_feature_tta8_20260911"
preflight="$run/preflight"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$root/runs/exp152_dense_native_source_selection_20260910/results"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ ! -e "$preflight" ]]
mkdir -p "$preflight"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

"$python_bin" "$code/evaluate_cached_fixed_weak_linker.py" \
  --repo "$forward_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp152/forward_target_low_candidate_cache" \
  --minimum-length 1 --probability-weight 0.1 \
  --output "$preflight/forward_cached_weak.json" \
  > "$preflight/forward_cached_weak.log" 2>&1
"$python_bin" "$code/validate_cached_arm_metrics_reproduction.py" \
  --reference "$exp152/forward_target_low.json" \
  --candidate "$preflight/forward_cached_weak.json" \
  --reference-arm registered_weak_hungarian \
  --candidate-arm registered_weak_p100_min1 \
  --output "$preflight/forward_reproduction.json" \
  > "$preflight/forward_reproduction.log" 2>&1

"$python_bin" "$code/evaluate_cached_fixed_weak_linker.py" \
  --repo "$reverse_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp152/reverse_target_low_candidate_cache" \
  --minimum-length 1 --probability-weight 0.1 \
  --output "$preflight/reverse_cached_weak.json" \
  > "$preflight/reverse_cached_weak.log" 2>&1
"$python_bin" "$code/validate_cached_arm_metrics_reproduction.py" \
  --reference "$exp152/reverse_target_low.json" \
  --candidate "$preflight/reverse_cached_weak.json" \
  --reference-arm registered_weak_hungarian \
  --candidate-arm registered_weak_p100_min1 \
  --output "$preflight/reverse_reproduction.json" \
  > "$preflight/reverse_reproduction.log" 2>&1

sha256sum "$preflight"/*.json "$preflight"/*.log > "$preflight/SHA256SUMS"
"$python_bin" - "$preflight/forward_reproduction.json" "$preflight/reverse_reproduction.json" <<'PY'
import json
import sys
for path in sys.argv[1:]:
    result = json.load(open(path, encoding="utf-8"))
    assert result["status"] == "PASS_EXACT_CACHED_ARM_METRIC_REPRODUCTION"
    assert result["movies"] == 12
    assert result["maximum_absolute_error"] <= 1e-12
print("PASS_EXP207_CACHED_WEAK_PREFLIGHT")
PY
