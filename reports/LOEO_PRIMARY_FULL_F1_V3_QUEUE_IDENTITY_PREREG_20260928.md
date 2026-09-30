# Primary full fold1 v3 — queue identity and timeout recovery

Written 2026-09-28 before successor implementation. Independent read-only
review **rejected v2 before remote stage**, despite 16/16 local tests, 21/21
bundle hashes and the same 28 named final-audit checks. Preserve v2 plan SHA256
`4dcbd79f8e07ebec92bba37d96547ff521aa3ba7424ae12f1d7c4903725cb5c5`,
manifest SHA256 `681ffa4a9e816177c4c11d34eb8de4613190fc39cd9fcd2509f1a57e2552ff21`
and final auditor SHA256 `9295030aac97b8e281d18c76d0776013a7fb4fcd4d1d4042f36477439c8dd926`
unchanged as rejected local evidence. V1 and v2 were never staged, reserved or
launched on the cluster.

Two independently demonstrated defects require a distinct v3 attempt, plan,
lease, bundle and auditor. First, `full_control.py` accepts a `RESERVED` queue
reply containing a foreign lease ID and run path; a mocked call returned
`LAUNCHED` and made two remote launch calls. Before *any* remote launch, require
the returned reservation's exact `id`, `project`, `run_path`, `token`, `owner`,
`state`, `health`, `alias`, GPU count, pool and planned resource quantities to
match the immutable plan/request. Reject a missing or mismatched field; retain
the raw response as evidence. Apply the same identity binding in the
independent completion audit, not only in the launch controller.

Second, the queue may accept a reservation before SSH times out. V2 writes no
pre-request intent, then `reconcile()` returns `NO_RESERVATION_RECEIPT` without
querying the live queue. V3 must durably write an exclusive, fsynced request
intent *before* the queue request. On timeout or malformed reply, preserve it,
query the live queue by exact planned ID and inspect the returned project,
run path and resource identity. Reconciliation must expose or safely release
any matching active lease after proving that this attempt launched no remote
run/process and its GPU is empty; a missing or ambiguous queue response must
remain an explicit unresolved state, never be treated as no reservation or
trigger a second request. Every release requires the exact raw reply
`id == lease_id` and `state == RELEASED`; preserve that reply durably. Do not
release a lease if its process identity or GPU occupancy is uncertain.

Preserve the source-only science exactly: 102 fit and 26 inner `6bba` movies,
all 71 `44b6` outer movies excluded, 9,949/2,443 windows, 50 epochs, seed
`20260930` before model import, no warm start, same model, trainer, checkpoint
selection and quality thresholds. The published primary weight remains
identity metadata only and is never loaded. Keep the v2 release and final
audit corrections, including 28 exact named checks for x138.

Local validation must reproduce both v2 failures using isolated mocks and
show v3 rejection/recovery. Test a foreign ID/run/project/token/owner, missing
fields, resource mismatch, reservation timeout with accepted live lease,
unlaunched safe release and ambiguous queue status; retain the existing
release-reply, PID/start and source-only tests. Compile code without cache and
read back every bundled hash. A separate independent review must pass before
remote stage. Later x138 assembler pin updates require a distinct version.

This is a local correction only. No SSH, queue request, GPU, outer target
image/GEFF, Kaggle POST or OOF score is authorized by this document. The
ongoing primary fold0 lease remains untouched.
