# V1284 capture v3 and control v2 — correction preregistration

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC), before successor
implementation. The capture v2 manifest SHA256
`ef81cb60c9ebe9cbe7760dbc189d840f26b338fe101a6bb0c0d7648d742733f1`
and control v1 manifest SHA256
`c7b57925bee3a1908221344d8b57602aec86e73c6f9afa220f28634d9ee583d1`
remain preserved, unstaged and unrun. This correction keeps the same source
split, x138 feature producer, checkpoint/selection contract, zero GEFF capture
view, one-shot A100 limits, and no outer-label access.

An independent read-only review found six defects. Capture v2
`verify_capture.py::_completion_ok` accepts watcher `watch/complete.json`
without independent runtime audit or raw release-reply verification. Control
v1 treats a missing `denied_access.jsonl` as zero denials, may leave group
descendants after a timeout if the leader exits, can release using a stale
probe after a long `started` RPC, and does not independently bind all executed
control bytes. Capture v2 `plan_capture.py` hashes supplied role files before
rejecting `.geff` paths, allowing an accidental source-label read during
image-only preflight. The review is local source/synthetic evidence; no remote
capture was attempted.

## Corrected capture v3

Create a distinct package/manifest; do not edit v2. Reject any path component
ending `.geff` and any symlink-resolved component reaching a `.geff` tree for
role weight, config or audit inputs **before stat/hash/open** in planning,
validation and preflight. Permit only approved role file types/parents.
`verify_capture.py` must require a completion written by the independent
runtime/release auditor, with its role-specific `runtime_audit.outcome`, exact
plan/capture manifest, lease/GPU/run, zero-denial log existence/hash, raw
release reply `id/state=RELEASED`, release-time dead process/group/GPU-empty
evidence and a matching live RELEASED queue row. A watcher-only receipt must
fail before any shard or GEFF processing. Retain the existing full per-frame
image-only shard audit; do not change feature values or inference behavior.

## Corrected control v2

Create a distinct control package/manifest pinned to the final capture v3
manifest, with no stage/lease/remote run during implementation. Require an
existing regular zero-byte `denied_access.jsonl` and save its SHA256; missing
is inconclusive until verified absence, then a failure, never zero. On hard
timeout, terminate the whole process group, wait a bounded grace, kill any
surviving descendants even if leader exited, and verify the group dead before
release. After any `started` queue RPC, make a fresh GPU/PID/exit probe. Record
probe start/end; reject a probe older than 20 seconds at release and require
fresh observation/release ordering. Pin complete staged control bytes against
the final external control manifest SHA, including executed wrapper bytes;
the independent auditor must rehash the launch intent and wrapper and reject
any mismatch. The independent auditor alone writes the completion consumed
by capture v3; a self-declared PASS string is insufficient.

## Validation and promotion boundary

Synthetic tests must reproduce and reject all six reviewed defects, including
wrong raw release reply accepted by old capture v2, absent access log,
leader-exits/stubborn-descendant timeout, long `started` RPC stale probe,
`.geff` direct/symlink path before any read, and altered wrapper/intent.
Re-run prior positive source-only/empty-frame and release tests, AST and exact
package-manifest readback with no generated cache. An independent second
review must pass before any remote stage. Neither correction produces a
checkpoint, graph or OOF score. Real launch still requires audited same-fold
primary and secondary checkpoints, fresh fair queue, physically idle A100,
one lease at a time and exact stage readback.
