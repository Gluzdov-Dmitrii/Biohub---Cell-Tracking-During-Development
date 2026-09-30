#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp208_source_centroid_family_v1_20260911"
run="$root/runs/exp208_source_centroid_family_20260911"
results="$run/results"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
forward_base="$root/runs/exp130_44b6_to_6bba_20260909"
reverse_base="$root/runs/exp137_6bba_to_44b6_20260909"
forward_repo="$forward_base/tracking_repo"
reverse_repo="$reverse_base/tracking_repo"
exp146="$root/runs/exp146_scratch_seed_consensus_20260910"
exp152="$root/runs/exp152_dense_native_source_selection_20260910"
stage_audit="$root/data/honest195_missing/audit.json"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ -d "$run" ]]
[[ -s "$run/launch_authorization.txt" ]]
[[ ! -e "$results" ]]
[[ -s "$stage_audit" ]]
[[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha 36a7fa07f7d87ee0a8052a52c8fed759615cda6f095ae812cd740c06b9e9e942 "$code/evaluate_cached_intensity_centroid_family.py"
check_sha f04c0e6d15f5d32053e783b9e606d29189369e69a374191d798945672c1ff191 "$code/select_source_centroid_radius.py"
check_sha 0f812c4b4af24cf8512c59cc1cbda6323e0c17f698f46a3b5621dd011971d04b "$code/evaluate_cached_intensity_centroid_refinement.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 4d1a5bb10c4fd46ce3615ed0b196aecfab21cbf8f0fe6a67d41cd3627bbbbd9f "$code/build_fixed_separate_two_direction_comparison.py"
check_sha ad716a032693e349d82edc5b17e2fa6aa66e5bb51018b916b0b6c535376082f0 "$code/analyze_nested_pooled_stability.py"
check_sha 44044f26d08e12527bc4e75ddce1fc06ec072413182f4ab6a4f3517cacc58ac8 "$forward_base/source_validation_44b6.json"
check_sha e82cf1e2add8e7a0356e1d1b4ff6c4b9c56194be897192557d568c52ed956e27 "$exp152/exp152_source_validation_6bba.json"
check_sha 6e6ed3dc61b672ef271dee0aa332e675b20adb69ad5865bbc67083564e440991 "$exp146/all12_6bba.json"
check_sha d3db2a26525e4db6ac487680646e9bd7af052e5b3bd651b0a5bfac4ef5793fb7 "$exp146/all12_44b6.json"

"$python_bin" - "$stage_audit" <<'PY'
import json, sys
result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["status"] == "PASS_EXP192_DATA_AUDIT"
assert result["movies"] == 175
assert result["files"] == 21525
assert result["bytes"] == 75045173746
assert len(result["content_sha256_by_movie"]) == 175
PY

[[ $(find "$exp152/results/forward_source_low_candidate_cache" -maxdepth 1 -type f -name '*.npz' | wc -l) -eq 2 ]]
[[ $(find "$exp152/results/reverse_source_low_candidate_cache" -maxdepth 1 -type f -name '*.npz' | wc -l) -eq 2 ]]
[[ $(find "$exp152/results/forward_target_low_candidate_cache" -maxdepth 1 -type f -name '*.npz' | wc -l) -eq 12 ]]
[[ $(find "$exp152/results/reverse_target_low_candidate_cache" -maxdepth 1 -type f -name '*.npz' | wc -l) -eq 12 ]]

mkdir -p "$results"
export CUDA_VISIBLE_DEVICES=""
export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1

radii=("1,3,3" "1,5,5" "2,3,3" "2,5,5" "2,7,7" "3,5,5")
radius_args=()
arm_args=(--arm-order translation)
for radius in "${radii[@]}"; do
  radius_args+=(--radius "$radius")
  arm_args+=(--arm-order "intensity_centroid_r${radius//,/_}")
done

"$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
  --repo "$forward_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$forward_base/source_validation_44b6.json" \
  --movie-key source_checkpoint_validation \
  --cache-dir "$exp152/results/forward_source_low_candidate_cache" \
  --minimum-length 8 "${radius_args[@]}" --output "$results/forward_source.json" \
  > "$results/forward_source.log" 2>&1
"$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
  --repo "$reverse_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$exp152/exp152_source_validation_6bba.json" \
  --movie-key source_checkpoint_validation \
  --cache-dir "$exp152/results/reverse_source_low_candidate_cache" \
  --minimum-length 3 "${radius_args[@]}" --output "$results/reverse_source.json" \
  > "$results/reverse_source.log" 2>&1

"$python_bin" "$code/select_source_centroid_radius.py" \
  --source-result "$results/forward_source.json" "${arm_args[@]}" \
  --output "$results/forward_selection.json" > "$results/forward_selection.log" 2>&1
"$python_bin" "$code/select_source_centroid_radius.py" \
  --source-result "$results/reverse_source.json" "${arm_args[@]}" \
  --output "$results/reverse_selection.json" > "$results/reverse_selection.log" 2>&1

forward_arm=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_arm"])' "$results/forward_selection.json")
reverse_arm=$("$python_bin" -c 'import json,sys; print(json.load(open(sys.argv[1]))["selected_arm"])' "$results/reverse_selection.json")
forward_radius=$("$python_bin" -c 'import json,sys; x=json.load(open(sys.argv[1]))["selected_radius_zyx_voxels"]; print("" if x is None else ",".join(map(str,x)))' "$results/forward_selection.json")
reverse_radius=$("$python_bin" -c 'import json,sys; x=json.load(open(sys.argv[1]))["selected_radius_zyx_voxels"]; print("" if x is None else ",".join(map(str,x)))' "$results/reverse_selection.json")
forward_target_args=()
reverse_target_args=()
[[ -z "$forward_radius" ]] || forward_target_args=(--radius "$forward_radius")
[[ -z "$reverse_radius" ]] || reverse_target_args=(--radius "$reverse_radius")

"$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
  --repo "$forward_repo" --data-dir "$root/data/pilot_single_6bba" \
  --movies-json "$exp146/all12_6bba.json" \
  --cache-dir "$exp152/results/forward_target_low_candidate_cache" \
  --minimum-length 8 "${forward_target_args[@]}" --output "$results/forward_target.json" \
  > "$results/forward_target.log" 2>&1
"$python_bin" "$code/evaluate_cached_intensity_centroid_family.py" \
  --repo "$reverse_repo" --data-dir "$root/data/pilot_single_44b6" \
  --movies-json "$exp146/all12_44b6.json" \
  --cache-dir "$exp152/results/reverse_target_low_candidate_cache" \
  --minimum-length 3 "${reverse_target_args[@]}" --output "$results/reverse_target.json" \
  > "$results/reverse_target.log" 2>&1

"$python_bin" - "$results/forward_target.json" "$forward_arm" "$results/reverse_target.json" "$reverse_arm" <<'PY'
import json, sys
for path, arm, expected_movies in ((sys.argv[1], sys.argv[2], 12), (sys.argv[3], sys.argv[4], 12)):
    result = json.load(open(path, encoding="utf-8"))
    assert result["status"] == "PASS_FIXED_INTENSITY_CENTROID_FAMILY"
    expected = {"translation"} if arm == "translation" else {"translation", arm}
    assert set(result["per_movie_by_arm"]) == expected
    assert all(len(rows) == expected_movies for rows in result["per_movie_by_arm"].values())
    base = {row["dataset"]: row for row in result["per_movie_by_arm"]["translation"]}
    selected = {row["dataset"]: row for row in result["per_movie_by_arm"][arm]}
    assert set(base) == set(selected)
    assert all(base[name]["num_pred_nodes"] == selected[name]["num_pred_nodes"] for name in base)
PY

"$python_bin" "$code/build_fixed_separate_two_direction_comparison.py" \
  --base-forward "$results/forward_target.json" --candidate-forward "$results/forward_target.json" \
  --base-reverse "$results/reverse_target.json" --candidate-reverse "$results/reverse_target.json" \
  --base-arm translation --candidate-arm "$forward_arm" \
  --base-reverse-arm translation --candidate-reverse-arm "$reverse_arm" \
  --output "$results/target_comparison.json" > "$results/target_comparison.log" 2>&1
"$python_bin" "$code/analyze_nested_pooled_stability.py" \
  --nested-result "$results/target_comparison.json" --draws 20000 --seed 314159 \
  --output "$results/target_stability.json" > "$results/target_stability.log" 2>&1

find "$code" "$run" -type f ! -name SHA256SUMS -print0 | sort -z | \
  xargs -0 sha256sum > "$results/SHA256SUMS.tmp"
mv "$results/SHA256SUMS.tmp" "$results/SHA256SUMS"
echo PASS_EXP208_SOURCE_CENTROID_FAMILY
