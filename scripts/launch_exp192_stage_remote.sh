#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
expected_archive_sha="${2:?expected archive SHA256 required}"
code="$root/code/exp192_honest195_confirmation_v1_20260911"
stage="$root/data/honest195_missing"
transfer="$root/data/exp192_archive_transfer"
archive="$transfer/biohub-cell-tracking-during-development.zip"
runner="$code/stage_exp192_honest195_remote.sh"
receipt="$transfer/stage_launch_receipt.txt"
lock="$transfer/.stage-launch-lock"
expected_archive_bytes=87393127165

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ "$expected_archive_sha" == "538ed8a4d7b6669fa948865f947ed43c23aba7ee006fea8826d6ddd1277dfd19" ]]
[[ "$(sha256sum "$runner" | awk '{print $1}')" == "1d39c8a3f8e34d56c25ec935759fbfc0f7b147b7a9fb4886309eb27f31615213" ]]
[[ "$(stat -c %s "$archive")" == "$expected_archive_bytes" ]]
[[ -s "$stage/honest195_missing_manifest.json" ]]
[[ $(find "$stage" -mindepth 1 -maxdepth 1 | wc -l) -eq 1 ]]
[[ ! -e "$receipt" ]]
[[ ! -e "$stage/audit.json" ]]
if pgrep -af "[s]tage_exp192_honest195_remote.sh.*$root" >/dev/null; then
  echo "EXP192 staging process already exists" >&2
  exit 24
fi
mkdir "$lock" 2>/dev/null || { echo "EXP192 staging launch lock already exists" >&2; exit 26; }

nohup bash "$runner" "$root" "$expected_archive_sha" \
  > "$transfer/stage.log" 2>&1 < /dev/null &
pid=$!
start_tick="$(awk '{print $22}' "/proc/$pid/stat")"
temporary="$receipt.tmp.$pid"
printf 'pid=%s\nstart_tick=%s\narchive_sha256=%s\narchive_bytes=%s\nrunner_sha256=%s\n' \
  "$pid" "$start_tick" "$expected_archive_sha" "$expected_archive_bytes" \
  "1d39c8a3f8e34d56c25ec935759fbfc0f7b147b7a9fb4886309eb27f31615213" \
  > "$temporary"
mv "$temporary" "$receipt"
printf '%s %s\n' "$pid" "$start_tick"
