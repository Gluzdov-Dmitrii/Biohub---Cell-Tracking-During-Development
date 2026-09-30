#!/usr/bin/env bash
set -euo pipefail
root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
run="$root/runs/exp180_reciprocal_deepcenter_training_20260910"
receipt="$run/launch_receipt.txt"
if [[ -e "$receipt" ]]; then
  echo "launch receipt already exists: $receipt" >&2
  exit 23
fi
if pgrep -af '[r]un_exp180_reciprocal_deepcenter_training' >/dev/null; then
  echo "EXP180 process already exists" >&2
  exit 24
fi
CUDA_VISIBLE_DEVICES="GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba" \
  nohup bash "$run/run_exp180_reciprocal_deepcenter_training.sh" "$root" \
  > "$run/exp180.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
tmp="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\ngpu_uuid=%s\n' \
  "$pid" "$start_tick" "GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba" > "$tmp"
mv "$tmp" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
