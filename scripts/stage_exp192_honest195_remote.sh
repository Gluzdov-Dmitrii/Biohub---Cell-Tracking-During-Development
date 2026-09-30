#!/usr/bin/env bash
set -euo pipefail

root="$1"
expected_archive_sha="$2"
expected_archive_bytes=87393127165
code="$root/code/exp192_honest195_confirmation_v1_20260911"
stage="$root/data/honest195_missing"
archive="$root/data/exp192_archive_transfer/biohub-cell-tracking-during-development.zip"
python_bin="$root/envs/prepost/py3.11-stdlib-v1/bin/python"

[[ "$(readlink -f "$root")" == "/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development" ]]
[[ "$(readlink -f "$stage")" == "$root/data/honest195_missing" ]]
[[ "$(stat -c %s "$archive")" == "$expected_archive_bytes" ]]
[[ "$(sha256sum "$archive" | awk '{print $1}')" == "$expected_archive_sha" ]]

"$python_bin" "$code/validate_archive_manifest_catalog.py" \
  --archive "$archive" --manifest "$stage/honest195_missing_manifest.json" \
  --output "$stage/catalog_audit.json"
"$python_bin" "$code/extract_manifest_from_archive.py" \
  --archive "$archive" --manifest "$stage/honest195_missing_manifest.json" \
  --destination "$stage" --holdout 44b6 --output "$stage/extract_44b6.json"
"$python_bin" "$code/extract_manifest_from_archive.py" \
  --archive "$archive" --manifest "$stage/honest195_missing_manifest.json" \
  --destination "$stage" --holdout 6bba --output "$stage/extract_6bba.json"
"$python_bin" "$code/audit_honest195_stage.py" \
  --manifest "$stage/honest195_missing_manifest.json" --data-root "$stage" \
  --output "$stage/audit.json" --content-hash

sha256sum "$stage/honest195_missing_manifest.json" "$stage/catalog_audit.json" "$stage/extract_44b6.json" \
  "$stage/extract_6bba.json" "$stage/audit.json" > "$stage/STAGING_SHA256SUMS"
echo PASS_EXP192_REMOTE_STAGE
