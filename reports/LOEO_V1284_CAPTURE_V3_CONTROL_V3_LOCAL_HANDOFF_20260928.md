# V1284 capture v3 control v3 — local transport correction handoff

**State:** distinct local-only controller complete. No SSH, remote stage,
fair-queue request, lease, GPU work, `.geff` read, Kaggle action or
`EXPERIMENTS.md` edit occurred. Capture v3 remains unchanged. Control v2
manifest SHA256 `befdd03f885c05fcd3e16e970f7db7214eae23787174d3f2707494bb5f496eda`
is preserved and rejected for remote use.

The correction preregistration is
`LOEO_V1284_CAPTURE_CONTROL_V3_TRANSPORT_CORRECTION_PREREG_20260928.md`,
SHA256 `0e53f5441d2288957b107827964f12e4b46d178f13d02820d7916bd7d45300e1`.
The pinned capture v3 manifest SHA256 is
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`.
The seven-file successor is
`work/loeo-v1284-capture-v3-control-v3-20260928/`; its
`control_manifest.json` SHA256 is
`e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`.
Supply this exact external SHA to both future read-only `prepare` and
independent `audit_capture_runtime.py` invocations through
`--expected-control-manifest-sha256`.

Control v3 retains the control v2 source-only plan, same-fold checkpoint,
fair-queue, physical A100, one-shot lease, process-group cleanup, existing
zero-byte denied-access log, fresh release-time probe and raw queue reply
gates. The runtime auditor now decodes `config.json`, `launch.json`,
`exit.json`, `capture_run_status.json` and `child_runtime_identity.json` as
JSON, and decodes staged `capture_wrapper.py` only as raw Python bytes. It
checks strict base64, declared length and SHA256, then compares the complete
wrapper bytes with the locally sealed file. The externally pinned control v3
manifest binds that file and all other control source/test bytes.

The completion retains
`runtime_audit.outcome=PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2` as a
**protocol identifier** required by capture v3. It is not the control
package's version claim. `runtime_audit.control_manifest_sha256` records the
actual control v3 manifest hash, with the denied-log, intent, executed-wrapper,
five runtime artifact and live RELEASED queue-row evidence. The independent
auditor alone writes this completion; a watcher receipt does not satisfy the
capture v3 verifier.

`python -B -m unittest discover -s
work/loeo-v1284-capture-v3-control-v3-20260928 -p test_control_local.py -v`:
**17 passed**, including all 16 predecessor tests. The new transport test
uses the real Python wrapper bytes and rejects corrupt base64, length, SHA
and validly hashed altered bytes. All six Python files AST-parse; seven
manifest entries hash/read back exactly; no package cache directory exists.

Real Linux process groups, remote source-image inventory, queue responses,
GPU probes and capture throughput remain untested. A separate independent
second review must pass before remote stage. Future capture still requires
audited same-fold primary/secondary full-training receipts, a fresh v3 plan,
the fair idle A100 gate, and separate runtime plus per-frame shard audits
before any source-label processing.
