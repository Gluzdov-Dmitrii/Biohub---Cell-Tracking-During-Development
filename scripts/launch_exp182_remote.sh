#!/usr/bin/env bash
set -euo pipefail
root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
run="$root/runs/exp182_synthetic_gap_source_packaging_repair_20260911"
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
check_sha e8c43125057aae4e6c28ef619bd8bf673f3ad3a3649941ccaa1593d8065f7c26 "$run/select_synthetic_gap_source_gate.py"
check_sha 51b48e6e1972b8422f9ccf1c109d6b1c537b0fdc5237cae71121558f4bbe9b91 "$run/run_exp182_synthetic_gap_source.sh"
check_sha 4adff38695950489a455bac69b6ddc261c48d6c9a44e51b96f7769116bd4efff "$run/preregistration.json"

if [[ -e "$receipt" ]]; then
  echo "launch receipt already exists: $receipt" >&2
  exit 23
fi
if pgrep -af '[r]un_exp182_synthetic_gap_source' >/dev/null; then
  echo "EXP182 process already exists" >&2
  exit 24
fi
mkdir "$lock" 2>/dev/null || {
  echo "EXP182 launch lock already exists" >&2
  exit 26
}
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$run/run_exp182_synthetic_gap_source.sh" "$root" \
  > "$run/exp182.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
