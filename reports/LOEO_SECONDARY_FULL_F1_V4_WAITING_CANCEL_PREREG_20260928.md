# Secondary full fold1 v4 — waiting queue cancellation

Written 2026-09-28 before successor implementation. An independent review
initially passed the sealed secondary fold1 v3, then **retracted that PASS**
after a targeted cross-audit found a deterministic `WAITING_RESOURCE` queue
lifecycle defect. Preserve v3 plan SHA256
`9c1061c4d9e524aa572181834711c5414c07d7ff16f6aecd7af99ccfd8dc28d0`,
21-file manifest SHA256 `07a957514e58047f81ec623a42437b39e25b899707238873b03a5c2eac063113`
and auditor SHA256 `52285517ac376e0183d13d61190de5d12c9d606a19664b93749741e421c2fcb9`
unchanged as rejected local evidence. V1 through v3 were never staged/run.

An exact planned waiting row can be created before the queue SSH reply is
lost. V3 `launch()` then invokes unreceipted reconciliation, but its
reservation matcher rejects `WAITING_RESOURCE` and returns
`UNRESOLVED_QUEUE_IDENTITY` without canceling. A scratch mock recorded zero
cancel calls, while the durable request intent blocks retry. Queue source
shows that only `cancel` closes a waiting row; `release` refuses it. The old
helper canceled a waiting reply only when that reply arrived, so it cannot
resolve the lost-response case. A waiting row may persist and later allocate.

Create a distinct v4 attempt, lease, plan and package. For a complete
waiting reply or an exact waiting row found by live status after a lost
reply, check exact ID, project, run, owner, token, pool/resources,
`state=WAITING_RESOURCE`, `gpus=[]` and no process. Durably write exclusive
cancel intent before one exact `cancel --id/--token`. Save the raw reply and
require matching `id` plus `state=CANCELLED`, then a fresh matching live
cancelled row with empty GPU/process and absent remote run before claiming
safe cancellation. No automatic duplicate request or cancel after an
ambiguous response. If the row changes to `RESERVED` before cancel, requery
and use the v3 safe unlaunched RESERVED release path with remote run/process/
GPU probes; never cancel an active lease. Missing/wrong/ambiguous rows stay
unresolved, never successful.

Preserve v3 corrected post-release `gpus=[]` semantics, reservation and
release identity binding, one-shot release, PID/start checks, 28 exact final
audit names and source-only science: 102 fit/26 inner `6bba`, 71 outer
`44b6` excluded, 9,949/2,443 windows, 50 epochs, seed `20260929`, no warm
start, unchanged trainer and gates. Local tests must reproduce the v3 lost
waiting reply and show exact cancellation, raw response validation,
WAITING→RESERVED race and ambiguity handling. Repeat v3 tests, full hash
readback and no-cache compilation. Independent review before any stage; x138
assembler pins updated separately after that review.

This correction is local only: no SSH, queue/GPU action, target image/GEFF,
Kaggle POST or OOF claim. The current primary fold0 lease stays untouched.
