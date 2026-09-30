# Secondary full fold1 v5 — one-shot ordinary release

Written 2026-09-28 before successor implementation. An independent targeted
cross-audit **retracted the local v4 static PASS before remote stage**.
Preserve sealed v4 plan SHA256
`5c275b92e5619b017d8143cc41052fe9f4eb9093f61b917b409e68a8a7b3892b`,
21-file manifest SHA256 `7a2aacb0348a59fd5a68341efe333b25db2831b9b888728791df352a5bbf1869`,
controller SHA256 `773d3fadf333d2f42745ffde6d680ed5ba69327fd04a1db7666e1826b87bcf83`
and auditor SHA256 `52285517ac376e0183d13d61190de5d12c9d606a19664b93749741e421c2fcb9`
unchanged as rejected local evidence. V1 through v4 were never staged/run.

V4's unreceipted WAITING→RESERVED recovery writes a durable release intent,
but ordinary `reconcile()` after a saved reservation has no one-shot guard
in its manual and unlaunched release branches. Both issue the queue release
before any exclusive intent. If the SSH reply is lost, the next reconcile
can issue release again. Isolated mocks must reproduce both ordinary paths
and count release calls. The previous 30 local tests and static PASS omitted
this lost-response scenario.

Create a distinct v5 attempt, lease, plan and bundle. Before *every* local
queue `release` call, including manual after verified exit and unlaunched
recovery, durably write an exclusive fsynced release intent binding immutable
plan SHA, exact lease ID/token, run, allocated GPU, reservation or recovered
row, fresh process/GPU absence probe and time. A lost, malformed, missing or
wrong-ID/state raw release reply must be saved as evidence and remain
unresolved; no later reconcile may issue a second automatic release. A valid
raw reply requires exact `id` and `state=RELEASED` and a fresh live released
row plus empty GPU/run-owned process before success. It is permissible for
the live released row to have `gpus=[]`, as the queue clears allocation.
An already durable release intent without a verified raw reply must not be
bypassed by a different release branch. WAITING cancel and release intents
must not enable duplicate mutation. The guarded WAITING→RESERVED path stays
correct and is covered by regression tests.

Preserve v4 waiting cancellation, reservation identity, PID/start and
release-row semantics, all 28 exact final-audit names and source-only science:
102 fit/26 inner `6bba`, all 71 outer `44b6` excluded, 9,949/2,443 windows,
50 epochs, seed `20260929`, no warm start, unchanged trainer/selection/gates.
Local adversarial tests must reproduce v4 double release in manual and
unlaunched paths, then show one release across repeated reconcile after lost
reply, exact valid reply success, wrong reply failure, and preserve v4
WAITING/race tests. Recompute new plan/lease/attempt/bundle hashes, full
manifest readback and no-cache compilation, followed by independent second
review before remote stage. X138 assembler pins require a separate version.

This correction is local only: no SSH, queue/GPU action, outer target read,
Kaggle POST or OOF claim. Primary fold0 remains the sole live Biohub lease.
