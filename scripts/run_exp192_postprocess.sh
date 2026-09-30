#!/usr/bin/env bash
set -euo pipefail

root="$1"
code="$root/code/exp192_honest195_confirmation_v1_20260911"
runs="$root/runs"
final="$runs/exp192_frozen_postprocess_20260911"
temporary="$runs/.exp192_frozen_postprocess_20260911.tmp"
lock="$runs/.exp192_frozen_postprocess_20260911.lock"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_repo="$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo"
data="$root/data/honest195_missing/train"

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ ! -e "$final" && ! -e "$temporary" ]]
mkdir "$lock" 2>/dev/null || { echo "postprocess lock exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

check_sha 426c1e5f3b8fba6469cef86aeaf145d49b971a8002d1fe8d85abb70f0c33ab6f "$code/validate_exp192_all_chunks_no_metrics.py"
check_sha 72c05ff7453dbefc724ded964685b8b9e33339131e05b4f214e64756c13cc1b3 "$code/merge_exp192_chunk_results.py"
check_sha a73a8bd1caf8b4bd84a6f577c6600e2c76b680bd68792b886ce028621e8312bd "$code/build_frozen_confirmation_results.py"
check_sha e69892948038ce54f0f9cb056ec720407bfa25e4fc22c859ec4147263b4fc572 "$code/build_exp195_confirmation_result.py"
check_sha 5733d126648b914b557b479badb846cc34df07a9e280e2d78b7f71220b569f04 "$code/build_exp201_confirmation_result.py"
check_sha a0d2ecb4e8b436b2f1e86f9e8c9c8ca2e6f3347c15f9f89783eb793d1aab5d36 "$code/build_exp202_composed_confirmation_result.py"
check_sha ad716a032693e349d82edc5b17e2fa6aa66e5bb51018b916b0b6c535376082f0 "$code/analyze_nested_pooled_stability.py"
check_sha 3e15e296c26c21c5659502ee03ff6fe5d48d0324bd742a8d1a55ee161e2d234e "$code/select_exp194_nested_inference_gate.py"
check_sha 0c9bdc68c6b1e80d213948262f15fed8844035f5e535a3c02db8e9134f9afcac "$code/select_nested_pooled_synthetic_gap.py"
check_sha 23c9d3553df6239d643be0261beba4bf8338fa123c6ea15a06bfbfdb1d57e439 "$code/deployable_policy.json"
check_sha 0f812c4b4af24cf8512c59cc1cbda6323e0c17f698f46a3b5621dd011971d04b "$code/evaluate_cached_intensity_centroid_refinement.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha 64da6a739fd442feb87f4fbd025ef08e66b7ff6aabfc3d3394ead2df6602e31d "$code/validate_exp206_centroid_chunks_no_metrics.py"
check_sha dc111add2d5db2cf3853afb70cd4dc6a4cb201e5e77a50d51b0643a4e73e1322 "$code/build_exp206_centroid_composed_confirmation_result.py"

mkdir "$temporary"
"$python_bin" "$code/validate_exp192_all_chunks_no_metrics.py" \
  --chunk-index "$code/chunk_index.json" --runs-root "$runs" \
  --output "$temporary/all_chunks_no_metric_gate.json" \
  > "$temporary/all_chunks_no_metric_gate.log" 2>&1

forward_centroid=()
for number in 00 01 02 03 04; do
  chunk_run="$runs/exp192_confirm_forward_${number}_20260911"
  centroid_result="$temporary/exp206_forward_${number}.json"
  "$python_bin" "$code/evaluate_cached_intensity_centroid_refinement.py" \
    --repo "$forward_repo" --data-dir "$data" \
    --movies-json "$chunk_run/movies.json" \
    --cache-dir "$chunk_run/results/base_raw_candidate_cache" \
    --minimum-length 8 --output "$centroid_result" \
    > "$temporary/exp206_forward_${number}.log" 2>&1
  forward_centroid+=(--input "$centroid_result")
done
"$python_bin" "$code/validate_exp206_centroid_chunks_no_metrics.py" \
  --chunk-index "$code/chunk_index.json" --runs-root "$runs" \
  --result-dir "$temporary" --output "$temporary/exp206_all_forward_no_metric_gate.json" \
  > "$temporary/exp206_all_forward_no_metric_gate.log" 2>&1

forward_base=()
forward_flow=()
for number in 00 01 02 03 04; do
  run="$runs/exp192_confirm_forward_${number}_20260911/results"
  forward_base+=(--input "$run/base_filtered.json")
  forward_flow+=(--input "$run/local_flow.json")
done
reverse_base=()
reverse_flow=()
reverse_gap=()
reverse_gap_filtered=()
for number in 00 01 02; do
  run="$runs/exp192_confirm_reverse_${number}_20260911/results"
  reverse_base+=(--input "$run/base_filtered.json")
  reverse_flow+=(--input "$run/local_flow.json")
  reverse_gap+=(--reverse-gap-chunk "$run/gap.json")
  reverse_gap_filtered+=(--input "$run/gap_filtered.json")
done

"$python_bin" "$code/merge_exp192_chunk_results.py" "${forward_base[@]}" \
  --expected-count 116 --prefix 6bba --output "$temporary/forward_base_merged.json" \
  > "$temporary/forward_base_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${reverse_base[@]}" \
  --expected-count 59 --prefix 44b6 --output "$temporary/reverse_base_merged.json" \
  > "$temporary/reverse_base_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${forward_flow[@]}" \
  --expected-count 116 --prefix 6bba --output "$temporary/forward_flow_merged.json" \
  > "$temporary/forward_flow_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${reverse_flow[@]}" \
  --expected-count 59 --prefix 44b6 --output "$temporary/reverse_flow_merged.json" \
  > "$temporary/reverse_flow_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${reverse_gap_filtered[@]}" \
  --expected-count 59 --prefix 44b6 --output "$temporary/reverse_gap_filtered_merged.json" \
  > "$temporary/reverse_gap_filtered_merged.log" 2>&1
"$python_bin" "$code/merge_exp192_chunk_results.py" "${forward_centroid[@]}" \
  --expected-count 116 --prefix 6bba --output "$temporary/forward_centroid_merged.json" \
  > "$temporary/forward_centroid_merged.log" 2>&1

"$python_bin" "$code/build_frozen_confirmation_results.py" \
  --forward-base "$temporary/forward_base_merged.json" \
  --reverse-base "$temporary/reverse_base_merged.json" \
  --reverse-gap "$temporary/reverse_gap_filtered_merged.json" \
  --exp190-output "$temporary/exp190_confirmation.json" \
  --exp191-output "$temporary/exp191_confirmation.json" \
  > "$temporary/exp190_exp191_confirmation.log" 2>&1

reverse_base_chunks=()
reverse_gap_filtered_chunks=()
for number in 00 01 02; do
  run="$runs/exp192_confirm_reverse_${number}_20260911/results"
  reverse_base_chunks+=(--reverse-base-chunk "$run/base_filtered.json")
  reverse_gap_filtered_chunks+=(--reverse-gap-filtered-chunk "$run/gap_filtered.json")
done
"$python_bin" "$code/build_exp195_confirmation_result.py" \
  --forward-base "$temporary/forward_base_merged.json" \
  "${reverse_base_chunks[@]}" "${reverse_gap[@]}" "${reverse_gap_filtered_chunks[@]}" \
  --policy "$code/deployable_policy.json" \
  --output "$temporary/exp195_confirmation.json" \
  > "$temporary/exp195_confirmation.log" 2>&1
"$python_bin" "$code/build_exp201_confirmation_result.py" \
  --forward "$temporary/forward_flow_merged.json" \
  --reverse "$temporary/reverse_flow_merged.json" \
  --output "$temporary/exp201_confirmation.json" \
  > "$temporary/exp201_confirmation.log" 2>&1
"$python_bin" "$code/build_exp202_composed_confirmation_result.py" \
  --forward-flow "$temporary/forward_flow_merged.json" \
  --forward-base "$temporary/forward_base_merged.json" \
  "${reverse_base_chunks[@]}" "${reverse_gap[@]}" "${reverse_gap_filtered_chunks[@]}" \
  --policy "$code/deployable_policy.json" \
  --output "$temporary/exp202_confirmation.json" \
  > "$temporary/exp202_confirmation.log" 2>&1
"$python_bin" "$code/build_exp206_centroid_composed_confirmation_result.py" \
  --forward-centroid "$temporary/forward_centroid_merged.json" \
  --forward-base "$temporary/forward_base_merged.json" \
  "${reverse_base_chunks[@]}" "${reverse_gap[@]}" "${reverse_gap_filtered_chunks[@]}" \
  --policy "$code/deployable_policy.json" \
  --output "$temporary/exp206_confirmation.json" \
  > "$temporary/exp206_confirmation.log" 2>&1

"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp190_confirmation.json" \
  --output "$temporary/exp190_stability.json" > "$temporary/exp190_stability.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp191_confirmation.json" \
  --reference-nested "$temporary/exp190_confirmation.json" \
  --output "$temporary/exp191_vs_exp190_stability.json" > "$temporary/exp191_vs_exp190_stability.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp195_confirmation.json" \
  --reference-nested "$temporary/exp190_confirmation.json" \
  --output "$temporary/exp195_vs_exp190_stability.json" > "$temporary/exp195_vs_exp190_stability.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp201_confirmation.json" \
  --output "$temporary/exp201_stability.json" > "$temporary/exp201_stability.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp202_confirmation.json" \
  --reference-nested "$temporary/exp195_confirmation.json" \
  --output "$temporary/exp202_vs_exp195_stability.json" > "$temporary/exp202_vs_exp195_stability.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$temporary/exp206_confirmation.json" \
  --reference-nested "$temporary/exp195_confirmation.json" \
  --output "$temporary/exp206_vs_exp195_stability.json" > "$temporary/exp206_vs_exp195_stability.log" 2>&1

sha256sum "$temporary"/*.json "$temporary"/*.log > "$temporary/SHA256SUMS"
mv "$temporary" "$final"
echo "PASS_EXP192_FROZEN_POSTPROCESS $final"
