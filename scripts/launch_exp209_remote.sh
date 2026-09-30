#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
code="$root/code/exp209_selected_centroid_confirmation_v1_20260912"
run="$root/runs/exp209_selected_centroid_confirmation_20260912"
runner="$code/run_exp209_selected_centroid_confirmation.sh"
runner_sha="bbe7588cb572ce070de328521ddc53cbb18fb917d3e2b10398b93c635a8d0413"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ "$(sha256sum "$runner" | awk '{print $1}')" == "$runner_sha" ]]
[[ -s "$root/data/honest195_missing/audit.json" ]]
if pgrep -af "[r]un_exp209_selected_centroid_confirmation.sh.*$root" >/dev/null; then
  echo "EXP209 process already exists" >&2
  exit 24
fi
mkdir "$run" 2>/dev/null || { echo "EXP209 run directory already exists" >&2; exit 26; }
printf 'runner_sha256=%s\nstate=AUTHORIZED_NOT_YET_STARTED\ncpu_threads=8\nram_budget_gib=16\nresource=CPU_ONLY\n' "$runner_sha" \
  > "$run/launch_authorization.txt"

CUDA_VISIBLE_DEVICES="" nohup taskset -c 0-7 bash "$runner" "$root" \
  > "$run/cpu.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
temporary="$run/launch_receipt.txt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\nrunner_sha256=%s\nresource=CPU_ONLY\ncpu_affinity=0-7\n' \
  "$pid" "$start_tick" "$runner_sha" > "$temporary"
mv "$temporary" "$run/launch_receipt.txt"
printf '%s %s\n' "$pid" "$start_tick"
