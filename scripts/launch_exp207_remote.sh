#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp207_d4_feature_tta8_v1_20260911"
run="$root/runs/exp207_d4_feature_tta8_20260911"
receipt="$run/gpu_launch_receipt.txt"
lock="$run/.gpu-launch-lock"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ -n "${CUDA_VISIBLE_DEVICES:-}" ]]
[[ "$(sha256sum "$code/run_exp207_d4_feature_tta8.sh" | awk '{print $1}')" == \
  "384ed4551c4455ff42deccf28098cd9906eb29367bb658b2bf4750a55cc567b9" ]]
[[ -s "$run/preflight/forward_reproduction.json" ]]
[[ -s "$run/preflight/reverse_reproduction.json" ]]

if [[ -e "$receipt" || -e "$run/gpu/results/SHA256SUMS" ]]; then
  echo "EXP207 launch/output receipt already exists" >&2
  exit 23
fi
if pgrep -af "[r]un_exp207_d4_feature_tta8.sh.*$root" >/dev/null; then
  echo "EXP207 process already exists" >&2
  exit 24
fi
mkdir "$lock" 2>/dev/null || { echo "EXP207 launch lock already exists" >&2; exit 26; }
trap 'rmdir "$lock" 2>/dev/null || true' EXIT

CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" \
  nohup bash "$code/run_exp207_d4_feature_tta8.sh" "$root" \
  > "$run/gpu.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
temporary="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' \
  "$pid" "$start_tick" "$CUDA_VISIBLE_DEVICES" > "$temporary"
mv "$temporary" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
