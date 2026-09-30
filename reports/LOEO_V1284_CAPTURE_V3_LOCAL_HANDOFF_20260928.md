# V1284 source-image capture v3 — local correction handoff

**State:** local code and synthetic verification only. No real checkpoint,
source image, source/target GEFF, SSH, stage, queue, lease, GPU, head refit,
graph score, or Kaggle action was used.

The correction was preregistered in
`reports/LOEO_V1284_CAPTURE_CONTROL_V3_CORRECTION_PREREG_20260928.md`,
SHA256 `fd373ca958322bf7537d6d5ab951b7328eb6e3e05c07656979e058bb0a039d8f`.
The rejected v2 package remains unchanged, manifest SHA256
`ef81cb60c9ebe9cbe7760dbc189d840f26b338fe101a6bb0c0d7648d742733f1`.

## Sealed package and capture boundary

The distinct v3 package is `work/loeo-v1284-source-capture-v3-20260928/`.
Its exact 27-file `package_manifest.json` SHA256 is
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`.
The five executable capture cells are byte-identical to v2, SHA256
`eabb04f72c57bc33bec4f266d14bc15e6be77e9df451b3b30f5b9fafb45d4e2b`.
The public support copy and generated predictor are also unchanged. Thus the
two-movie/empty-frame feature capture and capture-only post-`predict_video`
graph skip remain the same. Only `README.md`, `capture_contract.py`,
`capture_guard.py`, `plan_capture.py`, `verify_capture.py`, and focused tests
changed relative to v2.

V3 plans use a new `loeo_v1284_capture_f{fold}_v3_{attempt}` identity and
schema/purpose version 3. Planning requires explicit
`--approved-component-parent` root(s) in addition to approved image parents.
All six primary/secondary role paths are preflighted before the CLI hashes
any role file. Each direct and symlink-resolved path component is checked for
`.geff` before role stat/hash/open. Weight paths must be `.pth`; config and
independent audit receipts must be `.json`, within approved component roots.
The planner stores canonical resolved paths, and validation repeats this
preflight before reading model or audit files. Published input paths remain
forbidden.

`verify_capture.py` now rejects watcher `watch/complete.json` and any
completion lacking `runtime_audit.outcome =
PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2`. It requires the exact v3
capture manifest and plan SHA, valid control manifest/intent/wrapper hashes,
top-level lease/GPU/run/launch/exit identity, a raw release reply with matching
lease `id` and `state=RELEASED`, release-time dead identity/group and empty
GPU PIDs, a fresh ordered probe/release within 20 seconds, and a matching live
RELEASED queue row for the exact run and GPU. The denial log must exist as a
regular zero-byte file with the empty-file SHA. Its hash, plus the five local
run metadata file hashes, must match the independent auditor's report before
any source-view/frame/shard scan. The earlier full per-frame shard and
image-only view checks remain.

## Validation and remaining gates

`python -B -m unittest discover -s
work/loeo-v1284-source-capture-v3-20260928 -p test_capture_local.py -v`:
**9 passed**. Regressions cover `.geff` direct and symlinked role paths with
the hash function trapped, the old watcher-only bypass before shard reads,
wrong raw release reply and queue row, missing denial log, altered runtime
file, malformed/missing shards, and the prior two-movie one-empty-frame
capture integration. All 21 Python files AST-parse, the manifest inventory
and all 27 file hashes read back exactly, and no generated cache is present.

Control v2 must pin the v3 manifest above and emit the completion schema
required by this verifier. A separate second review is required before any
remote stage. Real use still requires independently audited, quality-passing
same-fold primary and secondary checkpoints, explicit narrow component
parents, an approved source image view, a fresh fair queue/idle A100 check,
one bounded lease, exact stage readback, and the independent control/shard
audits. No assembled OOF or 0.9+ claim follows from this local seal.
