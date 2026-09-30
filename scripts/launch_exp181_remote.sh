#!/usr/bin/env bash
set -euo pipefail
root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
run="$root/runs/exp181_synthetic_gap_source_20260911"
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
check_sha e8c43125057aae4e6c28ef619bd8bf673f3ad3a3649941ccaa1593d8065f7c26 "$run/select_synthetic_gap_source_gate.py"
check_sha 2844c785bb5780b1308abade7d4f2bcd9f9607df8bb5a065e75e0f16518007a5 "$run/run_exp181_synthetic_gap_source.sh"
check_sha 93487ce5752a8afe74245937ec7befa78950412f745db63a84b3d497809ce7b5 "$run/preregistration.json"

if [[ -e "$receipt" ]]; then
  echo "launch receipt already exists: $receipt" >&2
  exit 23
fi
if pgrep -af '[r]un_exp181_synthetic_gap_source' >/dev/null; then
  echo "EXP181 process already exists" >&2
  exit 24
fi
mkdir "$lock" 2>/dev/null || {
  echo "EXP181 launch lock already exists" >&2
  exit 26
}
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:?GPU lease must set CUDA_VISIBLE_DEVICES}" \
  nohup bash "$run/run_exp181_synthetic_gap_source.sh" "$root" \
  > "$run/exp181.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
