# V1284 source-v5 control-v7 terminal queue identity preregistration

Written 2026-09-28 before control-v7 code. The locally sealed but rejected
control-v6 seven-file manifest SHA256 is
`4d41d66d3ab65392c37689e72b3c767de733abad81942c0aab90f0ceeab7eced`.
The source-v5 29-file manifest SHA256 is
`3b8407413dc2837991dbf0d33b597543dcd8eac8c58e6039ea80c47164889a72`.
Both remain unchanged. No f0 v5 attempt, plan, archive, remote stage or lease
has been created. The failed f0 v4 identity remains spent.

## Defect and bounded correction

The independent review found that control-v6's
`audit_capture_runtime._raw_lease_state` accepts a live terminal row after
checking only lease ID, `RELEASED`, run path and `gpus=[]`. A row whose token,
owner, project, pool, alias or resource fields have changed can pass. It also
does not bind the queue's retained `process={pid,start}` to the exact launched
child. This is a launch/promotion blocker despite v6's sound one-shot request
and watcher release behavior.

Create a distinct control-v7 package for the unchanged sealed source-v5 plan
protocol. In the independent terminal audit, require exactly one live row and
match its full lease identity and resources to the prepared config and durable
reservation: ID, token, owner, project, run path, alias, host, pool, count,
CPU, RAM, disk, lease duration, created/allocated identity and health.
Require `RELEASED`, `gpus=[]`, a finite release timestamp, and retained
`process` metadata with positive PID and nonempty start marker exactly equal
to the verified launched child. A missing, malformed or foreign field must
fail closed. Keep the no-GEFF, source-only, process-death and GPU-empty gates.

Preserve control-v6's durable one-shot request, cancel, unlaunched release,
lost-reply reconciliation, watcher release and sibling-receipt SHA checks.
An unlaunched reconciliation row still requires `process=None`; do not
broaden that path to accept a launched terminal row. Use new control-v7
schema/purpose, prereg and parent-manifest pins. Retain the source-v5 verifier
protocol outcome literal `PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6` because
its sealed verifier requires that string; the runtime audit separately binds
the actual control-v7 manifest SHA256.

## Local tests and release gate

In addition to the inherited complete mocked suite, test the real launched
terminal row shape with retained matching process metadata. Independently
mutate token, owner, project, run path, alias, host, pool, count, CPU, RAM,
disk, lease duration, created/allocated identity, health, GPU shape, PID,
start marker and release timestamp. Each must reject. Missing/duplicate rows
must remain inconclusive. Test that source-v5's sealed verifier accepts a
valid v7 completion only with independently bound receipt hashes, and that
the unlaunched one-shot path still rejects retained process metadata.
Verify exact source/parent manifests, all control-v7 file bytes and ASTs,
and no cache files. Independent second review is required before any new
remote stage or GPU request.

This preregistration authorizes local code, tests and receipts only. No
remote stage, queue request, GPU run, target-label/outer-GEFF read, Kaggle
POST, EXPERIMENTS.md edit or current-state report edit is authorized.
