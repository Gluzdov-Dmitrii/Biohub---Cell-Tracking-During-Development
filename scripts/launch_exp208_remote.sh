#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp208_source_centroid_family_v1_20260911"
run="$root/runs/exp208_source_centroid_family_20260911"
runner="$code/run_exp208_source_centroid_family.sh"
runner_sha="ce78e9e942cb41dd0cfee9dafce677baca865cb8120f0c65f334f224b87380de"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ "$(sha256sum "$runner" | awk '{print $1}')" == "$runner_sha" ]]
[[ -s "$root/data/honest195_missing/audit.json" ]]
if pgrep -af "[r]un_exp208_source_centroid_family.sh.*$root" >/dev/null; then
  echo "EXP208 process already exists" >&2
  exit 24
fi
mkdir "$run" 2>/dev/null || { echo "EXP208 run directory already exists" >&2; exit 26; }
printf 'runner_sha256=%s\nstate=AUTHORIZED_NOT_YET_STARTED\n' "$runner_sha" \
  > "$run/launch_authorization.txt"

CUDA_VISIBLE_DEVICES="" nohup bash "$runner" "$root" \
  > "$run/cpu.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
temporary="$run/launch_receipt.txt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\nrunner_sha256=%s\nresource=CPU_ONLY\n' \
  "$pid" "$start_tick" "$runner_sha" > "$temporary"
mv "$temporary" "$run/launch_receipt.txt"
printf '%s %s\n' "$pid" "$start_tick"
