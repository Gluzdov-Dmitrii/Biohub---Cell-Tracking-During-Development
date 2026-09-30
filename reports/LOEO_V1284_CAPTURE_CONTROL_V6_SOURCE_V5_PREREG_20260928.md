# V1284 source-v5 capture control-v6 preregistration — 2026-09-28

Written before control-v6 code. This is a distinct local-only successor to
sealed control-v5 (`9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`)
and the failed f0 source-v4 attempt `loeo_v1284_capture_f0_v4_ba382850b115`.
The failed identity, run, queue receipt and source-v4/control-v5 seals remain
immutable. Source-v5 is being separately corrected and must be sealed before
control-v6's exact source constants and manifest can be pinned.

## Reason and scope

The v4 predictor crashed on its first source movie because the retention
guard log opened `/kaggle/working/retention_guard_single.jsonl`, a Kaggle-only
directory absent on the cluster. A later detector-coordinate manifest used
the same unavailable directory. Source-v5 will redirect both label-free
diagnostic outputs to its exact run-local directory. The control-v5 contract
pins source-v4's manifest, capture cells, predictor, plan schema and purpose,
identity and lease format, and completion outcome. A distinct control-v6
successor is necessary to admit only sealed source-v5 plans.

Copy control-v5's seven-file control design into a new control-v6 package.
Change only versioned source lineage and matching completion/audit pins,
plus tests required to prove that lineage. Keep the one-shot queue request
intent and raw reply receipts, exact live-row reconciliation, one-shot
cancel/release intent and lost-reply behavior, arbitrary-cwd watcher config,
process/GPU release gates, and sibling-receipt hash bindings unchanged.
Never make a second queue request, cancel or release on ambiguous transport.
Do not weaken the source-only image and no-GEFF boundaries.

Pin the final source-v5 package manifest SHA, capture cells SHA, generated
predictor SHA and V1284 module SHA from its independently read-back seal.
Pin source-v5's actual plan schema, purpose and fresh identity/lease format;
reject the failed v4 identity and all v4 plans. Pin the exact source-v5
completion outcome and verifier contract rather than fabricating a compatible
string. Use a new control-v6 schema/purpose/manifest. Preserve plan SHA and
model/config SHA checks throughout prepare, launch, watcher and runtime audit.

Before implementation, the coordinated new verifier/runtime outcome was
fixed as `PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6`. Source-v5 and
control-v6 must use that literal consistently and reject old outcome strings.

## Local release gates

Before sealing, run the complete mocked control branch suite for normal
launch/watcher, lost or malformed request/cancel/release replies, returned
WAITING, RESERVED unlaunched recovery, foreign/missing rows, GPU/process busy,
repeated reconciliation, and terminal `RELEASED` with `gpus=[]` and retained
process metadata. Add positive source-v5 plan/completion lineage tests and
negative source-v4, mismatched hash, stale identity and malformed source-v5
fixtures. Verify all package manifest bytes, Python ASTs, source-v5 verifier
compatibility, exact immutable receipt hashes and no cache files. Require an
independent second review before any future remote stage or queue lease.

This task authorizes local code and test preparation only. No remote stage,
queue request, GPU run, target-label or outer-GEFF read, Kaggle POST,
EXPERIMENTS.md edit or current-state report edit is authorized.
