#!/usr/bin/env bash
set -euo pipefail

root="$1"
run="$2"
direction="$3"
expected_movies_sha="$4"
expected_data_audit_sha="$5"
code="$(cd "$(dirname "$0")" && pwd)"
receipt="$run/launch_receipt.txt"
lock="$run/.launch-lock"

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

check_sha 4d0a16e48c76d1d6c72b06224144f71eb7e1ae17471f317ba034f6006480e9bb "$code/run_exp192_confirmation_chunk.sh"
check_sha 30be89bf51f7e1c12be77049943ece6ff488609fe1eca03148c959f72bcd36b4 "$code/validate_exp192_chunk_structure.py"
check_sha 36e0ce644382be779f527cf18665a816127b299229214a885eb66778989690a8 "$code/evaluate_registered_model.py"
check_sha a9156bbbe9f57239eedb45908f018b4f3c31b9d6d811ea788c4f7e454c5bbba3 "$code/evaluate_cached_short_track_family.py"
check_sha 9a93702994f84e3510329419cdfec8b3f63eb949e1e0c0623f7fad570466dfc9 "$code/evaluate_synthetic_gap_deepcenter.py"
check_sha d411f0c937f12928e6019993b7ea5c42d2594356ea820ec3b9c06fd9cd3c190e "$code/evaluate_cached_selected_edge_short_tracks.py"
check_sha 3ca9fc363f98b95f37c4c5d4bcea7eaba351e04cf723685c41d8dc1520be0278 "$code/validate_cached_arm_reproduction.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"
check_sha 5d969e74f5a1f8aa095c89afc3996a0bb9f0b1c52a12aa9bde92b895e6b0ec44 "$code/evaluate_cached_fixed_local_flow.py"
check_sha 79c31e00948c8ffc3de4e2620119d8094a833ace26df7b80e0af6a01a0b5a1e7 "$code/evaluate_cached_local_flow_linker.py"
check_sha fac519e1182f31ff33182217e26ffc36c747fe2c8983cdac3e4c69440e82a7b1 "$code/evaluate_cached_coherent_motion_linker.py"
check_sha 3c382148606f92c1da1601fe501e2e4a8a028b0253afcf97bd7f8cd6a1588939 "$code/evaluate_observed_gap_close.py"
check_sha 6314efc742acbf67e3fce66033f1e3736a9d0f88de72ebe630b7bba12d5f7425 "$code/train_deepcenter_explicit_split.py"
check_sha "$expected_movies_sha" "$run/movies.json"
check_sha "$expected_data_audit_sha" "$root/data/honest195_missing/audit.json"

case "$direction" in
  forward)
    check_sha dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb \
      "$root/runs/exp130_44b6_to_6bba_20260909/tracking_repo/weights/exp130_scratch_44b6_deterministic/split_0/edge_predictor_best.pth"
    ;;
  reverse)
    check_sha 5c0f8358389af40a646a0fe3b4e8e88fb1b1c155da12e92efa3c944eeb499366 \
      "$root/runs/exp137_6bba_to_44b6_20260909/tracking_repo/weights/exp137_scratch_6bba_seed314159/split_1/edge_predictor_best.pth"
    check_sha ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e \
      "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/6bba/best.pt"
    ;;
  *) echo "direction must be forward or reverse" >&2; exit 2 ;;
esac

python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
"$python_bin" "$code/evaluate_registered_model.py" --help >/dev/null
"$python_bin" "$code/evaluate_cached_short_track_family.py" --help >/dev/null
"$python_bin" "$code/evaluate_cached_fixed_local_flow.py" --help >/dev/null
if [[ "$direction" == reverse ]]; then
  "$python_bin" "$code/evaluate_synthetic_gap_deepcenter.py" --help >/dev/null
  "$python_bin" "$code/evaluate_cached_selected_edge_short_tracks.py" --help >/dev/null
fi
bash -n "$code/run_exp192_confirmation_chunk.sh"

if [[ -e "$receipt" || -e "$run/results/SHA256SUMS" ]]; then
  echo "EXP192 chunk launch/output receipt already exists" >&2; exit 23
fi
if pgrep -af "[r]un_exp192_confirmation_chunk.sh.*$run" >/dev/null; then
  echo "EXP192 chunk process already exists" >&2; exit 24
fi
mkdir "$lock" 2>/dev/null || { echo "EXP192 chunk launch lock already exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$code/run_exp192_confirmation_chunk.sh" "$root" "$direction" "$run" \
  > "$run/chunk.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\ndirection=%s\nmovies_sha256=%s\ndata_audit_sha256=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" "$direction" "$expected_movies_sha" \
  "$expected_data_audit_sha" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
