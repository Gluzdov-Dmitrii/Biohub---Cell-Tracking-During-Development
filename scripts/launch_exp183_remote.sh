#!/usr/bin/env bash
set -euo pipefail
root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
run="$root/runs/exp183_synthetic_gap_target_oof_20260911"
receipt="$run/launch_receipt.txt"
lock="$run/.launch-lock"

check_sha() {
  local expected="$1"
  local path="$2"
  local actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || {
    echo "SHA mismatch for $path: expected $expected, got $actual" >&2
    exit 25
  }
}

check_sha 83a7d5ad451fab041473fb0f6e9a139b094759516bf56beeea29f20442c65c70 "$run/evaluate_synthetic_gap_deepcenter.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$run/evaluate_coordinate_consensus.py"
check_sha 3c382148606f92c1da1601fe501e2e4a8a028b0253afcf97bd7f8cd6a1588939 "$run/evaluate_observed_gap_close.py"
check_sha 6314efc742acbf67e3fce66033f1e3736a9d0f88de72ebe630b7bba12d5f7425 "$run/train_deepcenter_explicit_split.py"
check_sha 745204439720f35cb245e0cdf48efc6b70e61e572ff23b0388babe5b7916311f "$run/select_synthetic_gap_target_gate.py"
check_sha 5ad9d6c5a33c4a421b9064ddfdcf223f5a49e4bb1f62139c6b30d141db8bdfa5 "$run/run_exp183_synthetic_gap_target_oof.sh"
check_sha 0b03d66eef09208147abcd4e7d1faf68265e0645fb4804a3d65c36915e9670a7 "$run/preregistration.json"
check_sha 6e6ed3dc61b672ef271dee0aa332e675b20adb69ad5865bbc67083564e440991 "$root/runs/exp146_scratch_seed_consensus_20260910/all12_6bba.json"
check_sha d3db2a26525e4db6ac487680646e9bd7af052e5b3bd651b0a5bfac4ef5793fb7 "$root/runs/exp146_scratch_seed_consensus_20260910/all12_44b6.json"
check_sha ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/44b6/best.pt"
check_sha ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e "$root/runs/exp180_reciprocal_deepcenter_training_20260910/output/6bba/best.pt"

forward_cache="$root/runs/exp152_dense_native_source_selection_20260910/results/forward_target_low_candidate_cache"
reverse_cache="$root/runs/exp152_dense_native_source_selection_20260910/results/reverse_target_low_candidate_cache"
[[ "$(find "$forward_cache" -maxdepth 1 -type f -name '*.npz' | wc -l)" -eq 12 ]] || {
  echo "forward target cache must contain exactly 12 NPZ files" >&2
  exit 27
}
[[ "$(find "$reverse_cache" -maxdepth 1 -type f -name '*.npz' | wc -l)" -eq 12 ]] || {
  echo "reverse target cache must contain exactly 12 NPZ files" >&2
  exit 28
}

if [[ -e "$receipt" ]]; then
  echo "launch receipt already exists: $receipt" >&2
  exit 23
fi
if pgrep -af '[r]un_exp183_synthetic_gap_target_oof' >/dev/null; then
  echo "EXP183 process already exists" >&2
  exit 24
fi
mkdir "$lock" 2>/dev/null || {
  echo "EXP183 launch lock already exists" >&2
  exit 26
}
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$run/run_exp183_synthetic_gap_target_oof.sh" "$root" \
  > "$run/exp183.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
