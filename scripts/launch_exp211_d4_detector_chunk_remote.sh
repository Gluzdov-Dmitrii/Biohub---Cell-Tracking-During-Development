#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
run="${2:?run path required}"
direction="${3:?direction required}"
expected_movies_sha="${4:?movies sha required}"
expected_data_audit_sha="${5:?data audit sha required}"
code="$(cd "$(dirname "$0")" && pwd)"
receipt="$run/launch_receipt.txt"
lock="$run/.launch-lock"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha 3105f0a9805c8f84aed4e35a0d54bfc2289f60e74e2c1725b22cf1e73bf4afd2 "$code/run_exp211_d4_detector_chunk.sh"
check_sha 99a46daeb668c6ac17e7dbfb522f282ded9ddeeaf4c5c23b0cdb6de3850242f4 "$code/validate_exp211_d4_chunk_structure.py"
check_sha 642bb826e54289acee189fdcebef8abc94f25ca06b911a87b30c6664c322f6f7 "$code/exp211_predict_unet_transformer_d4_detector.py"
check_sha 36e0ce644382be779f527cf18665a816127b299229214a885eb66778989690a8 "$code/evaluate_registered_model.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha "$expected_movies_sha" "$run/movies.json"
check_sha "$expected_data_audit_sha" "$root/data/honest195_missing/audit.json"

case "$direction" in
  forward)
    check_sha dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb "$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth"
    ;;
  reverse)
    check_sha 5c0f8358389af40a646a0fe3b4e8e88fb1b1c155da12e92efa3c944eeb499366 "$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth"
    ;;
  *) echo "direction must be forward or reverse" >&2; exit 2 ;;
esac

python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
"$python_bin" -m py_compile "$code/exp211_predict_unet_transformer_d4_detector.py" \
  "$code/evaluate_registered_model.py" "$code/evaluate_cached_short_track_family.py" \
  "$code/evaluate_coordinate_consensus.py" "$code/validate_exp211_d4_chunk_structure.py"
find "$code" -type d -name __pycache__ -prune -exec rm -rf -- {} +
bash -n "$code/run_exp211_d4_detector_chunk.sh"

[[ ! -e "$receipt" && ! -e "$run/SHA256SUMS" && ! -e "$run/results" ]]
if pgrep -af "[r]un_exp211_d4_detector_chunk.sh.*$run" >/dev/null; then
  echo "EXP211 chunk process already exists" >&2; exit 24
fi
mkdir "$lock" 2>/dev/null || { echo "EXP211 chunk launch lock already exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$code/run_exp211_d4_detector_chunk.sh" "$root" "$direction" "$run" \
  > "$run/chunk.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\ndirection=%s\nmovies_sha256=%s\ndata_audit_sha256=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" "$direction" "$expected_movies_sha" \
  "$expected_data_audit_sha" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
