# V1284 capture v3 control v3 — remote wrapper readback correction

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC), before a distinct
successor implementation. Capture v3 27-file manifest SHA256
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`
is unchanged. Control v2 seven-file manifest SHA256
`befdd03f885c05fcd3e16e970f7db7214eae23787174d3f2707494bb5f496eda`
is preserved, unstaged and rejected for remote use.

Independent second review found a deterministic transport failure in control
v2 `audit_capture_runtime.py:91-103`: `remote_artifacts` includes staged
`capture_wrapper.py` in the same loop as five JSON receipts and calls
`json.loads` on its Python source. Every genuine wrapper readback raises
ValueError and becomes INCONCLUSIVE, so the independent runtime completion
needed by capture v3 can never be emitted. Existing tests inject a decoded
wrapper fixture into `assess` and miss this readback path. No remote run was
made; this is source-level and synthetic evidence.

Create a **distinct control v3 package and manifest** with the same source
split, capture v3 parent, queue/GPU/lease limits, process cleanup, access-log
and release contracts as control v2. Read back the five JSON runtime receipts
as JSON; read back `capture_wrapper.py` as raw bytes with strict base64/length/
SHA256 checks, without JSON decoding. Independently compare those exact bytes
to the sealed control v3 wrapper and the externally supplied expected control
manifest SHA. Preserve `PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2` as the
**runtime audit protocol identifier**, even though the corrected package
directory is control v3. This avoids a capture/control manifest cycle. The
auditor must record its actual control-v3 manifest hash in `runtime_audit`,
and the external audit invocation must pin that v3 hash. The handoff must
explain this naming distinction; a string alone is never proof.

Add a transport-level synthetic test using the real wrapper's Python bytes,
plus corrupt base64, length and SHA cases. Keep all control-v2 positive and
negative tests, exact manifest readback, AST and no-cache checks. A separate
independent second review must pass before stage. This correction is local
only: no SSH, stage, queue, GPU, GEFF, Kaggle or outer score.
