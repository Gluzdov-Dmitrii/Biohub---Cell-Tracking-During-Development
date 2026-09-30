#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
run="${2:?run path required}"
direction="${3:?direction required}"
expected_failure_manifest_sha="${4:?failure manifest sha required}"
code="$(cd "$(dirname "$0")" && pwd)"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
failure_manifest="$run/recovery/FAILED_STAGE_SHA256SUMS"
lock="$run/.cpu-recovery-lock"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ ! -e "$run/SHA256SUMS" && ! -e "$run/results/d4_filtered.json" ]]

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha "$expected_failure_manifest_sha" "$failure_manifest"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha 99a46daeb668c6ac17e7dbfb522f282ded9ddeeaf4c5c23b0cdb6de3850242f4 "$code/validate_exp211_d4_chunk_structure.py"
mkdir "$lock" 2>/dev/null || { echo "CPU recovery lock exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

(cd / && sha256sum -c "$failure_manifest")
case "$direction" in
  forward) minimum=8 ;;
  reverse) minimum=3 ;;
  *) echo "direction must be forward or reverse" >&2; exit 2 ;;
esac

export PYTHONHASHSEED=314159
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export PYTHONDONTWRITEBYTECODE=1
"$python_bin" "$code/evaluate_cached_short_track_family.py" \
  --repo "$run/tracking_repo" --data-dir "$root/data/honest195_missing/train" \
  --movies-json "$run/movies.json" --cache-dir "$run/results/d4_raw_candidate_cache" \
  --minimum-length 1 --minimum-length "$minimum" \
  --output "$run/results/d4_filtered.json" > "$run/results/d4_filtered.log" 2>&1
"$python_bin" "$code/validate_exp211_d4_chunk_structure.py" \
  --run-dir "$run" --direction "$direction" \
  --output "$run/results/structure_validation.json" \
  > "$run/results/structure_validation.log" 2>&1

rm -rf -- "$run/tracking_repo"
sha256sum "$code"/*.py "$code"/*.sh "$run/movies.json" "$run/launch_receipt.txt" \
  "$run/chunk.log" "$run/recovery/FAILED_STAGE_SHA256SUMS" \
  "$run"/results/*.json "$run"/results/*.log \
  "$run"/results/d4_raw_candidate_cache/*.npz > "$run/SHA256SUMS.tmp"
mv "$run/SHA256SUMS.tmp" "$run/SHA256SUMS"
printf 'PASS_EXP211_D4_CPU_RECOVERY\n'
