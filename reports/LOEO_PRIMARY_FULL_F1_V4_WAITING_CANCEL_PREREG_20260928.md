# Primary full fold1 v4 — waiting queue cancellation

Written 2026-09-28 before successor implementation. Independent review
**rejected the sealed local v3 before remote stage**. Preserve v3 plan SHA256
`68dc688662379c7f64d015e866f19c118c6c33f9cc343a5a31112354cc23c976`,
21-file manifest SHA256 `84a9774602a1d3f44cd7a8e7160f24f6be2b9518ebc9c61d051718761d355c72`
and auditor SHA256 `b9913e9a211321177d28fa4a275abe70daa1d8d86d2e1783685f469345715e28`
unchanged as rejected local evidence. V1 through v3 were not staged or run.

The fair queue can return `WAITING_RESOURCE` with `gpus=[]` and no process.
The old queue helper canceled that request, and a saved historical receipt
shows `CANCELLED`. The v3 custom request path does not cancel: an isolated
mock of an exact planned waiting row returned `REQUEST_NOT_LAUNCHED`, then
`UNRESOLVED_QUEUE_IDENTITY` on repeated reconcile, with zero cancel calls.
The durable request intent blocks a second request, but the waiting row can
remain in the queue and later acquire a GPU without a launch controller.

Create a distinct v4 attempt, lease, plan and package. For a complete queue
reply *or a lost reply discovered by exact-ID live status*, validate the
waiting row's exact project, run, owner, token, pool, resource quantities,
`state=WAITING_RESOURCE`, `gpus=[]` and no process. Save an exclusive,
fsynced cancel intent before one `cancel --id <planned> --token <planned>`.
Preserve the raw response and require exact `id` and `state=CANCELLED`, plus a
fresh matching live row with `gpus=[]`, no process and no remote run, before
reporting cancellation. A timeout, malformed reply, missing/wrong row or
uncertain remote state remains explicitly unresolved; do not send a second
request or cancel automatically. If the waiting row races to `RESERVED`, do
not cancel the active allocation: requery and use the existing verified
unlaunched RESERVED recovery with process/GPU probes and one-shot release.
No training process may launch from a waiting row.

Preserve the v3 foreign-reservation identity checks, durable request intent,
lost-reply recovery, full independent final audit, exact 28 named checks and
source-only science: 102 fit/26 inner `6bba`, 71 outer `44b6` excluded,
9,949/2,443 windows, 50 epochs, seed `20260930`, no warm start, same
model/selection/gates. Recompute and seal all changed hashes. Local tests must
reproduce the v3 stranded-waiter mock, prove exact one-shot cancel, wrong
reply/ambiguous timeout fail-closed, WAITING→RESERVED race routing and the
existing v3 adversarial checks. Full manifest readback and no-cache compile
required, followed by independent second review before stage. X138 assembler
pins must later be updated in a distinct version.

This correction is local only. No SSH, queue/GPU action, outer image/GEFF,
Kaggle POST or OOF claim. The primary fold0 lease remains untouched.
