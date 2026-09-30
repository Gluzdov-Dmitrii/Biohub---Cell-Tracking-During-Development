#!/usr/bin/env bash
set -euo pipefail

root="${1:?project root required}"
expected_root="/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development"
code="$root/code/exp192_honest195_confirmation_v1_20260911"
stage="$root/data/honest195_missing"
transfer="$root/data/exp192_archive_transfer"
runs="$root/runs"
audit="$stage/audit.json"
index="$code/chunk_index.json"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"
summary="$transfer/data_ready_receipts.json"
verification="$transfer/data_ready_finalization.json"
temporary="$summary.tmp.$$"

check_sha() {
  local expected="$1" path="$2" actual
  actual="$(sha256sum "$path" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo "SHA mismatch: $path" >&2; exit 25; }
}

[[ "$(readlink -f "$root")" == "$expected_root" ]]
check_sha 0be18408075ffc2525899814081a7186a06dfce3affde939f57ea2b15494e42e "$code/mark_exp192_runs_data_ready.py"
check_sha 9a8e531210066dcf2d18da3fc0b58272b449110f80c9b2a24df9537916afa42d "$code/verify_exp192_data_ready_receipts.py"
check_sha 87955accbe2c46e678858995b0ef5ba1a411146755177c01804538383073d413 "$index"
check_sha 4d0a16e48c76d1d6c72b06224144f71eb7e1ae17471f317ba034f6006480e9bb "$code/run_exp192_confirmation_chunk.sh"
check_sha c2acd7e59d99cb553e377c5c954905cf629055b3e11bae9e1273cc40b83e09f0 "$code/launch_exp192_chunk_remote.sh"
check_sha 30be89bf51f7e1c12be77049943ece6ff488609fe1eca03148c959f72bcd36b4 "$code/validate_exp192_chunk_structure.py"
check_sha 5d969e74f5a1f8aa095c89afc3996a0bb9f0b1c52a12aa9bde92b895e6b0ec44 "$code/evaluate_cached_fixed_local_flow.py"
check_sha 79c31e00948c8ffc3de4e2620119d8094a833ace26df7b80e0af6a01a0b5a1e7 "$code/evaluate_cached_local_flow_linker.py"
check_sha fac519e1182f31ff33182217e26ffc36c747fe2c8983cdac3e4c69440e82a7b1 "$code/evaluate_cached_coherent_motion_linker.py"
check_sha 426b4ee3c6d07a90d1848c1dcd551352eafea8c27a4cf18b05a80d047865fad2 "$code/evaluate_coordinate_consensus.py"

[[ -s "$transfer/stage_launch_receipt.txt" ]]
[[ -d "$transfer/.stage-launch-lock" ]]
[[ -s "$stage/STAGING_SHA256SUMS" ]]
[[ "$(awk 'NF {line=$0} END {print line}' "$transfer/stage.log")" == "PASS_EXP192_REMOTE_STAGE" ]]
if pgrep -af "[s]tage_exp192_honest195_remote.sh.*$root" >/dev/null; then
  echo "EXP192 staging is still running" >&2
  exit 24
fi
(cd / && sha256sum -c "$stage/STAGING_SHA256SUMS") >/dev/null

[[ ! -e "$summary" && ! -e "$verification" && ! -e "$temporary" ]]
for direction_number in forward_00 forward_01 forward_02 forward_03 forward_04 reverse_00 reverse_01 reverse_02; do
  run="$runs/exp192_confirm_${direction_number}_20260911"
  [[ ! -e "$run/data_ready.json" ]]
  [[ ! -e "$run/launch_receipt.txt" ]]
  [[ ! -e "$run/results/SHA256SUMS" ]]
done

trap 'rm -f -- "$temporary"' EXIT
"$python_bin" "$code/mark_exp192_runs_data_ready.py" \
  --audit "$audit" --chunk-index "$index" --runs-root "$runs" --code-dir "$code" \
  > "$temporary"
"$python_bin" "$code/verify_exp192_data_ready_receipts.py" \
  --summary "$temporary" --audit "$audit" --chunk-index "$index" \
  --runs-root "$runs" --code-dir "$code" --output "$verification"
mv "$temporary" "$summary"
trap - EXIT
echo "PASS_EXP192_DATA_READY $verification"
