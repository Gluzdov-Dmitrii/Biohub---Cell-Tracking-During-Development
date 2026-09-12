#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp209_selected_centroid_confirmation_v1_20260912"
runs="$root/runs"
run="$runs/exp209_selected_centroid_confirmation_20260912"
results="$run/results"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
data="$root/data/honest195_missing/train"
forward_repo="$runs/exp130_44b6_to_6bba_20260909/tracking_repo"
reverse_repo="$runs/exp137_6bba_to_44b6_20260909/tracking_repo"
frozen="$runs/exp192_frozen_postprocess_20260911"
exp208="$runs/exp208_source_centroid_family_20260911/results"

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ -d "$run" && -s "$run/launch_authorization.txt" ]]
[[ ! -e "$results" ]]
[[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]
[[ -d "$data" && -x "$python_bin" ]]

check_sha 36a7fa07f7d87ee0a8052a52c8fed759615cda6f095ae812cd740c06b9e9e942 "$code/evaluate_cached_intensity_centroid_family.py"
check_sha 0f812c4b4af24cf8512c59cc1cbda6323e0c17f698f46a3b5621dd011971d04b "$code/evaluate_cached_intensity_centroid_refinement.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha bbffe74bf5633a4fc0d5e52d7a09b097132f87e36d8010738ab544aefbbed2ad "$code/validate_exp209_selected_centroid_chunks_no_metrics.py"
check_sha 72c05ff7453dbefc724ded964685b8b9e33339131e05b4f214e64756c13cc1b3 "$code/merge_exp192_chunk_results.py"
check_sha aee8a897c7d502267d3ca4b130b1b9bc4b3edab9b7991faef603d7cf08cfcbe7 "$code/build_exp209_selected_centroid_confirmation.py"
check_sha a73a8bd1caf8b4bd84a6f577c6600e2c76b680bd68792b886ce028621e8312bd "$code/build_frozen_confirmation_results.py"
check_sha 0c9bdc68c6b1e80d213948262f15fed8844035f5e535a3c02db8e9134f9afcac "$code/select_nested_pooled_synthetic_gap.py"
check_sha ad716a032693e349d82edc5b17e2fa6aa66e5bb51018b916b0b6c535376082f0 "$code/analyze_nested_pooled_stability.py"
check_sha 87955accbe2c46e678858995b0ef5ba1a411146755177c01804538383073d413 "$code/chunk_index.json"
check_sha bd98ebbc70a37912a1307c1f3c7b5cc285ea4d6838e2391423694bd27023fc42 "$exp208/forward_selection.json"
check_sha ea3640b1df42c2f47e25028a23dbc7dd646c3f2be2298ffd7673a7d65a9f5526 "$exp208/reverse_selection.json"
check_sha ae03ed8fa3d28d5ecaab4afbde9996646a70d104f815c1dedfd65768bfa1b00d "$frozen/exp190_confirmation.json"
check_sha 44cf11c2085dc2e0334de100ca6a5686f72de261dcf1c1c89ade3ff290fd0431 "$frozen/exp191_confirmation.json"
check_sha 7ca2e2acbea05c380864c7c6438ec205777eaf2cf8da2f4f9ed7f5faa4d383d9 "$frozen/exp195_confirmation.json"
check_sha 21e8c846ef10ea4c1506aa239745bcf07c1e2660866906071b61932d9211c878 "$frozen/exp206_confirmation.json"

"$python_bin" - "$exp208/forward_selection.json" "$exp208/reverse_selection.json" <<'PY'
import json, sys
forward = json.load(open(sys.argv[1], encoding="utf-8"))
reverse = json.load(open(sys.argv[2], encoding="utf-8"))
assert forward["selected_arm"] == "intensity_centroid_r3_5_5"
assert forward["selected_radius_zyx_voxels"] == [3, 5, 5]
assert reverse["selected_arm"] == "intensity_centroid_r2_3_3"
assert reverse["selected_radius_zyx_voxels"] == [2, 3, 3]
PY

mkdir "$results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1

forward_inputs=()
for number in 00 01 02 03 04; do
  source_run="$runs/exp192_confirm_forward_${number}_20260911"
  output="$results/exp209_forward_${number}.json"
  "$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
    --repo "$forward_repo" --data-dir "$data" \
    --movies-json "$source_run/movies.json" --movie-key target_development \
    --cache-dir "$source_run/results/base_raw_candidate_cache" \
    --minimum-length 8 --radius 3,5,5 --output "$output" \
    > "$results/exp209_forward_${number}.log" 2>&1
  forward_inputs+=(--input "$output")
done

reverse_inputs=()
for number in 00 01 02; do
  source_run="$runs/exp192_confirm_reverse_${number}_20260911"
  output="$results/exp209_reverse_${number}.json"
  "$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
    --repo "$reverse_repo" --data-dir "$data" \
    --movies-json "$source_run/movies.json" --movie-key target_development \
    --cache-dir "$source_run/results/base_raw_candidate_cache" \
    --minimum-length 3 --radius 2,3,3 --output "$output" \
    > "$results/exp209_reverse_${number}.log" 2>&1
  reverse_inputs+=(--input "$output")
done

"$python_bin" "$code/validate_exp209_selected_centroid_chunks_no_metrics.py" \
  --chunk-index "$code/chunk_index.json" --runs-root "$runs" --result-dir "$results" \
  --output "$results/all_chunks_no_metric_gate.json" \
  > "$results/all_chunks_no_metric_gate.log" 2>&1

"$python_bin" "$code/merge_exp192_chunk_results.py" "${forward_inputs[@]}" \
  --expected-count 116 --prefix 6bba --output "$results/forward_merged.json" \
  > "$results/forward_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${reverse_inputs[@]}" \
  --expected-count 59 --prefix 44b6 --output "$results/reverse_merged.json" \
  > "$results/reverse_merged.log" 2>&1

"$python_bin" "$code/build_exp209_selected_centroid_confirmation.py" \
  --forward "$results/forward_merged.json" --reverse "$results/reverse_merged.json" \
  --exp190 "$frozen/exp190_confirmation.json" --exp191 "$frozen/exp191_confirmation.json" \
  --exp195 "$frozen/exp195_confirmation.json" --exp206 "$frozen/exp206_confirmation.json" \
  --both-output "$results/both_selected_confirmation.json" \
  --exp191-output "$results/forward_plus_exp191_confirmation.json" \
  --exp195-output "$results/forward_plus_exp195_confirmation.json" \
  > "$results/assembly.log" 2>&1

for policy in both_selected forward_plus_exp191 forward_plus_exp195; do
  "$python_bin" "$code/analyze_nested_pooled_stability.py" \
    --nested-result "$results/${policy}_confirmation.json" --draws 20000 --seed 314159 \
    --output "$results/${policy}_vs_raw_stability.json" \
    > "$results/${policy}_vs_raw_stability.log" 2>&1
  "$python_bin" "$code/analyze_nested_pooled_stability.py" \
    --nested-result "$results/${policy}_confirmation.json" \
    --reference-nested "$frozen/exp206_confirmation.json" --draws 20000 --seed 314159 \
    --output "$results/${policy}_vs_exp206_stability.json" \
    > "$results/${policy}_vs_exp206_stability.log" 2>&1
done

(
  cd "$results"
  find . -maxdepth 1 -type f ! -name SHA256SUMS ! -name SHA256SUMS.tmp -print0 | sort -z | \
    xargs -0 sha256sum > SHA256SUMS.tmp
  mv SHA256SUMS.tmp SHA256SUMS
)
echo PASS_EXP209_SELECTED_CENTROID_CONFIRMATION
