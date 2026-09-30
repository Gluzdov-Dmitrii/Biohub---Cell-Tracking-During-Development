# V1284 capture control v5 — one-shot queue request recovery preregistration

Written 2026-09-28 before control-v5 code. Source-v4 28-file manifest SHA256
`31d1a8c632c5cee711772e784a023bca377d4b9863a2ef9c3760a1aa54c8e55d`
and blocked control-v4 seven-file manifest SHA256
`8a555620d025665b88e0b09013fe89c37c25c190eb6b745a9fb1a52257273bb7`
remain unchanged. Source v4 retains the LF, child-import, capture-guard,
source-only and terminal empty-GPU fixes. No v4 attempt/plan was remotely
sealed or staged.

## Defect and bounded correction

Control v4 calls `scripts/launch_exp221_job.py::queue_request` before writing
any request intent. That helper sends the raw SSH queue request, then cancels
WAITING only when its JSON reply is received. An accepted request followed by
SSH timeout leaves a WAITING or RESERVED queue row with no durable local
identity; a lost cancel reply is also unreceipted. A later launch cannot
safely re-request, and an unlaunched reservation can hold an A100.

Create a distinct control-v5 package for the existing source-v4 plan
protocol, with schema/purpose `v1284_capture_v4_one_shot_control_v5` and a
new control manifest. Keep source-v4 plan identities
`loeo_v1284_capture_f<fold>_v4_<new 12-hex attempt>` and the existing
`PASS_CAPTURE_V4_RUNTIME_RELEASE_CONTROL_V4` completion protocol identifier
so the sealed source-v4 independent verifier remains compatible; the actual
control-v5 manifest hash must still be externally pinned in control config
and runtime audit. Preserve the watcher absolute-config fix, release-time
empty-GPU audit, no-GEFF guard and one-shot GPU process controls.

Before the raw queue request, write an exclusive fsynced request intent
binding the exact config SHA, source plan SHA, lease ID/token hash, project,
run path, pool and resource request. Use the raw queue request directly,
without the old helper's implicit cancel. Save its raw reply before validating
it. On SSH timeout, malformed/nonzero reply or returned WAITING, never issue
a second request. Reconcile read-only against one exact live row: require
lease ID, token, owner, project, run path, alias, pool, resources and valid
state/GPU shape. A missing, duplicate or foreign row is unresolved and
must not mutate any lease.

For WAITING, write one fsynced cancel intent before a queue cancel. For an
unlaunched RESERVED row, first recheck that the exact code/plan/source images
still match, the run path does not exist, and the assigned GPU is physically
idle; then write one fsynced release intent before `release
--verified-stopped`. Save raw mutation replies before validation. If a reply
is lost, query the live row and accept only exact CANCELLED/RELEASED terminal
state with `gpus=[]`; if still WAITING/RESERVED or it raced to another state,
fail closed. Repeated reconciliation may observe and seal a terminal state,
but must never send a duplicate cancel/release. A WAITING→RESERVED race
requires a new explicitly gated unlaunched-release decision; it cannot
reuse the cancel intent or issue a second cancel. No watcher starts without
a clean, validated RESERVED response and durable reservation receipt.

Use local mocks for normal launch/watcher, lost request reply, returned
WAITING, lost cancel reply, RESERVED unlaunched, foreign/missing rows,
WAITING→RESERVED race, busy GPU, malformed replies and repeated reconcile.
Verify exact source/control manifests, Python ASTs and no cache files.
This is local-only; no remote stage, queue request, GPU, target GEFF, scoring,
Kaggle POST, or edits to EXPERIMENTS/current state report are authorized.
Independent second review is required before any future stage or lease.
