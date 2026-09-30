# V1284 independent head audit v2 — capture v3 lineage correction

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC), before successor
implementation. The v1 head auditor manifest SHA256
`2b27bb3a3010dfdaf4cf6f37415c077b5d389ec9d0d83da6bfb70754cec537a9`
is preserved, unrun on real GEFF, and rejected for production audit. It remains
synthetically tested evidence, not a promotion gate.

Independent read-only review found two P1 defects. V1 hard-pins capture v2
`schema_version=2`, purpose, prereg and manifest, while the corrected capture
v3 emits schema 3/purpose `v1284_source_image_capture_v3` and manifest SHA256
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`;
every genuine v3 plan would fail before label read. V1 also treats an absent
`denied_access.jsonl` as clean and does not independently require the runtime
auditor outcome, raw RELEASED reply or live queue row, allowing a watcher-like
completion plus self-declared verification to pass its lineage gate. No real
head, GEFF label or remote run was involved in these findings.

Create a distinct read-only head auditor v2 package. Preserve the v1 numeric
protocol: independent 5 µm greedy source-only matching, fit-only mean/scale,
224→32→3 finite head, 80-epoch earliest-argmin history consistency, pooled and
per-movie localization replay, fixed 0.05 µm/3%/60% gate and strict tolerances.
Do not change trainer, capture v3, model, thresholds or source/outer split.

Before opening a source GEFF, require and rehash the actual capture v3 plan,
capture-v3 manifest and code pins, complete per-frame source-only shards and
same-fold primary/secondary model/audit parents. Check plan schema 3/purpose,
v3 correction prereg SHA256
`fd373ca958322bf7537d6d5ab951b7328eb6e3e05c07656979e058bb0a039d8f`,
both rejected capture-v1/v2 manifest fields, approved component/image parents,
exact source/outer IDs and source-only view. Require the **independent**
capture runtime completion, not watcher-only: exact role-specific protocol
outcome `PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2` (the string is a protocol
identifier), actual control v3 manifest SHA256
`e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`,
plan/run/lease/GPU/PID binding, ordered fresh release-time dead group and empty
GPU, raw release reply matching `id` and `state=RELEASED`, and live queue row
with that ID/run/GPU/RELEASED. Require an existing regular zero-byte remote
`denied_access.jsonl`, its empty-file SHA256 in the audit, and an exact copied
local log if one is used; absence is failure or inconclusive, never zero.
Bind `capture_verified.json` to the actual completion SHA and recheck its
source ID/frame/shard claims independently. Do not accept a PASS string or
attestation alone as provenance.

Only after those gates may the source-only GEFF loader run. Continue to hash
all source GEFF trees and refuse extra/outer aliases or unsafe links. Write
one new immutable terminal receipt only after all checks and recomputation;
missing/transport-unstable inputs remain INCONCLUSIVE without a receipt.

Synthetic tests must use a **v3-shaped plan** and independent-auditor-shaped
completion, including a positive numeric head case. Reject v2 plan, watcher
completion, absent/nonregular/nonempty denial log, wrong release reply, wrong
live row/control manifest, capture verification disconnected from completion,
parent or shard tampering, metric/epoch/gate mismatch, and any prelabel failure
must prove zero calls to the GEFF loader. Re-run v1 meaningful numeric tests,
AST, exact manifest readback and no-cache seal. Separate second review before
real use. No SSH, stage, GPU, real GEFF, outer label, Kaggle or OOF claim in
this implementation.
