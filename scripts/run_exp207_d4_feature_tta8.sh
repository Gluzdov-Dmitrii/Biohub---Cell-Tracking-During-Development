#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp207_d4_feature_tta8_v1_20260911"
run="$root/runs/exp207_d4_feature_tta8_20260911"
gpu="$run/gpu"
results="$gpu/results"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
exp190="$root/runs/exp190_extended_short_track_lengths_20260911/results"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ ! -e "$gpu" ]]
[[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha 642bb826e54289acee189fdcebef8abc94f25ca06b911a87b30c6664c322f6f7 "$code/predict_unet_transformer_d4_optional_feature_tta.py"
check_sha 36e0ce644382be779f527cf18665a816127b299229214a885eb66778989690a8 "$code/evaluate_registered_model.py"
check_sha 397ecd3e9d3e14799ab1c57291b531e702882d50615f6e67f3d4d3b5658ae349 "$code/evaluate_cached_fixed_weak_linker.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha 4d1a5bb10c4fd46ce3615ed0b196aecfab21cbf8f0fe6a67d41cd3627bbbbd9f "$code/build_fixed_separate_two_direction_comparison.py"
check_sha 9eb638bf66b965c0c8c3774d9183dba02ae9de801d04a9370bd3c372a186d143 "$code/validate_exp207_d4_controls.py"
check_sha 4dcb57c1ab526be37b8b0e81cfefefc9a03a1a74c1881724f353476da17f49c3 "$code/validate_cached_arm_metrics_reproduction.py"
check_sha 0c9bdc68c6b1e80d213948262f15fed8844035f5e535a3c02db8e9134f9afcac "$code/select_nested_pooled_synthetic_gap.py"
check_sha ad716a032693e349d82edc5b17e2fa6aa66e5bb51018b916b0b6c535376082f0 "$code/analyze_nested_pooled_stability.py"
check_sha dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb \
  "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth"
check_sha 5c0f8358389af40a646a0fe3b4e8e88fb1b1c155da12e92efa3c944eeb499366 \
  "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth"

"$python_bin" - "$run/preflight/forward_reproduction.json" "$run/preflight/reverse_reproduction.json" <<'PY'
import json
import sys
for path in sys.argv[1:]:
    result = json.load(open(path, encoding="utf-8"))
    assert result["status"] == "PASS_EXACT_CACHED_ARM_METRIC_REPRODUCTION"
    assert result["movies"] == 12
    assert result["maximum_absolute_error"] <= 1e-12
PY

mkdir -p "$results" "$gpu/tracking_repo"
cp -a "$forward_repo/src" "$gpu/tracking_repo/"
cp -a "$forward_repo/scripts" "$gpu/tracking_repo/"
find "$gpu/tracking_repo" -type d -name __pycache__ -prune -exec rm -rf -- {} +
cp "$code/predict_unet_transformer_d4_optional_feature_tta.py" \
  "$gpu/tracking_repo/scripts/predict_unet_transformer.py"
check_sha 642bb826e54289acee189fdcebef8abc94f25ca06b911a87b30c6664c322f6f7 \
  "$gpu/tracking_repo/scripts/predict_unet_transformer.py"
"$python_bin" - "$gpu/tracking_repo/scripts/predict_unet_transformer.py" <<'PY'
import sys
compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec")
PY

export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1

run_inference() {
  local label="$1" feature="$2" direction="$3" repo="$4" data="$5" weights="$6" movies="$7"
  [[ "$label" == "off" && "$feature" == "0" || "$label" == "on" && "$feature" == "1" ]]
  BIOHUB_EDGE_FEATURE_TTA="$feature" "$python_bin" "$code/evaluate_registered_model.py" \
    --repo "$gpu/tracking_repo" --data-dir "$data" --weights "$weights" \
    --movies-json "$movies" --output "$results/${label}_${direction}_raw.json" \
    --det-threshold 0.985 --edge-threshold 0.02 --weak-probability-weight 0.1 \
    --unet-batch-size 4 --seed 314159 \
    > "$results/${label}_${direction}_raw.log" 2>&1
}

run_inference off 0 forward "$forward_repo" "$root/data/pilot_single_6bba" \
  "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
  "$exp146/all12_6bba.json"
run_inference on 1 forward "$forward_repo" "$root/data/pilot_single_6bba" \
  "$forward_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth" \
  "$exp146/all12_6bba.json"
run_inference off 0 reverse "$reverse_repo" "$root/data/pilot_single_44b6" \
  "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth" \
  "$exp146/all12_44b6.json"
run_inference on 1 reverse "$reverse_repo" "$root/data/pilot_single_44b6" \
  "$reverse_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth" \
  "$exp146/all12_44b6.json"

for feature in off on; do
  "$python_bin" "$code/evaluate_cached_short_track_family.py" \
    --repo "$gpu/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
    --movies-json "$exp146/all12_6bba.json" \
    --cache-dir "$results/${feature}_forward_raw_candidate_cache" \
    --minimum-length 8 --output "$results/${feature}_forward_registered.json" \
    > "$results/${feature}_forward_registered.log" 2>&1
  "$python_bin" "$code/evaluate_cached_fixed_weak_linker.py" \
    --repo "$gpu/tracking_repo" --data-dir "$root/data/pilot_single_6bba" \
    --movies-json "$exp146/all12_6bba.json" \
    --cache-dir "$results/${feature}_forward_raw_candidate_cache" \
    --minimum-length 8 --probability-weight 0.1 \
    --output "$results/${feature}_forward_weak.json" \
    > "$results/${feature}_forward_weak.log" 2>&1
  "$python_bin" "$code/evaluate_cached_short_track_family.py" \
    --repo "$gpu/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
    --movies-json "$exp146/all12_44b6.json" \
    --cache-dir "$results/${feature}_reverse_raw_candidate_cache" \
    --minimum-length 3 --output "$results/${feature}_reverse_registered.json" \
    > "$results/${feature}_reverse_registered.log" 2>&1
  "$python_bin" "$code/evaluate_cached_fixed_weak_linker.py" \
    --repo "$gpu/tracking_repo" --data-dir "$root/data/pilot_single_44b6" \
    --movies-json "$exp146/all12_44b6.json" \
    --cache-dir "$results/${feature}_reverse_raw_candidate_cache" \
    --minimum-length 3 --probability-weight 0.1 \
    --output "$results/${feature}_reverse_weak.json" \
    > "$results/${feature}_reverse_weak.log" 2>&1
done

"$python_bin" "$code/validate_exp207_d4_controls.py" \
  --forward-movies "$exp146/all12_6bba.json" --reverse-movies "$exp146/all12_44b6.json" \
  --forward-off-raw "$results/off_forward_raw.json" --forward-on-raw "$results/on_forward_raw.json" \
  --reverse-off-raw "$results/off_reverse_raw.json" --reverse-on-raw "$results/on_reverse_raw.json" \
  --forward-off-filtered "$results/off_forward_registered.json" \
  --forward-on-filtered "$results/on_forward_registered.json" \
  --reverse-off-filtered "$results/off_reverse_registered.json" \
  --reverse-on-filtered "$results/on_reverse_registered.json" \
  --forward-off-cache "$results/off_forward_raw_candidate_cache" \
  --forward-on-cache "$results/on_forward_raw_candidate_cache" \
  --reverse-off-cache "$results/off_reverse_raw_candidate_cache" \
  --reverse-on-cache "$results/on_reverse_raw_candidate_cache" \
  --output "$results/feature_controls.json" > "$results/feature_controls.log" 2>&1

"$python_bin" "$code/build_fixed_separate_two_direction_comparison.py" \
  --base-forward "$results/off_forward_weak.json" --candidate-forward "$results/on_forward_weak.json" \
  --base-reverse "$results/off_reverse_weak.json" --candidate-reverse "$results/on_reverse_weak.json" \
  --base-arm registered_weak_p100_min8 --candidate-arm registered_weak_p100_min8 \
  --base-reverse-arm registered_weak_p100_min3 \
  --candidate-reverse-arm registered_weak_p100_min3 \
  --output "$results/feature_comparison.json" > "$results/feature_comparison.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$results/feature_comparison.json" --draws 20000 --seed 314159 \
  --output "$results/feature_stability.json" > "$results/feature_stability.log" 2>&1

"$python_bin" "$code/build_fixed_separate_two_direction_comparison.py" \
  --base-forward "$exp190/forward.json" --candidate-forward "$results/off_forward_registered.json" \
  --base-reverse "$exp190/reverse.json" --candidate-reverse "$results/off_reverse_registered.json" \
  --base-arm min8 --candidate-arm min8 --base-reverse-arm min3 --candidate-reverse-arm min3 \
  --output "$results/detector_comparison.json" > "$results/detector_comparison.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$results/detector_comparison.json" --draws 20000 --seed 314159 \
  --output "$results/detector_stability.json" > "$results/detector_stability.log" 2>&1

find "$code" "$gpu" -type f ! -name SHA256SUMS -print0 | sort -z | \
  xargs -0 sha256sum > "$results/SHA256SUMS.tmp"
mv "$results/SHA256SUMS.tmp" "$results/SHA256SUMS"
echo PASS_EXP207_D4_FEATURE_TTA8_RUN
