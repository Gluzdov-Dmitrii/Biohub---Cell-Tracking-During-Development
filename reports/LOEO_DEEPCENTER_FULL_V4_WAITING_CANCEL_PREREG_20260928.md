# DeepCenter reciprocal full v4 — lost waiting reply cancellation

Written 2026-09-28 before successor implementation. Independent cross-audit
**rejected both local DeepCenter v3 packages before remote stage**. Preserve
v3 fold0 plan/training/control/auditor SHA256 values
`2acdcf24ed64cedd6a341d2b93df93881d69399d652f0209fb26eb90e4ef3d61`,
`e8cff3b24a289cd1f3197f15d98c3e23e7febb54966bf9b0d129317e201fea0c`,
`a4ea025380a8e8c4d4e83a97f61142f1291760f629e0d7d72dd952940adf0f78`,
`ee1ad9ef9dd97d8f6643f1f7d822f840643df5c20a027b1133a3e2c22b6b3ca3`;
fold1 values
`93169574cd9b62070403ef3d5bdbab47e2c357b5f3009b8f4fdd60b4825b5428`,
`704e1e7867e407581e4c66ac82f5455c8fc6f124ea055a5d607faec814e3585b`,
`d78a86d56d098d59d56ef916c548f9724f33c3dc686c7205b58ca632bafc3b82`,
`bf5438a9aecc014db6ba878c416d4d5d1184322f8bea47b57de7381130a69614`.
The v3 handoff SHA256 is
`5bae247cf4996d6c30668513bf7f138496193f57d4ac6d6249c4915b1779c134`.
V1 through v3 remain unstaged and unrun.

V3 copied `local_recovery.py` from v2. For a durable launch intent with no
reservation receipt, its exact-ID live-queue recovery treats an exact
`WAITING_RESOURCE` row as inconclusive and issues no cancellation. The
controller calls an older queue helper that cancels WAITING only when its
response is actually received. If the queue creates a waiting request and
the SSH reply is lost, no helper cancellation runs, the waiting row remains
live and the saved intent blocks a second request. The queue can later assign
a GPU to this unlaunched request. A local scratch reproduction must be kept
as evidence. `resource_queue.py` requires `cancel` for WAITING and refuses
`release` in that state.

Create distinct v4 fold0/fold1 attempts, plans, training/control bundles and
auditors. For either received WAITING reply or a lost reply followed by an
exact planned WAITING live row, validate exact ID, project, run path, owner,
token, pool/resource quantities, `gpus=[]` and no process. Durably save an
exclusive cancel intent before one exact `cancel --id/--token`. Preserve the
raw response and require exact `id` plus `state=CANCELLED`, then a fresh live
row with empty GPU/process and absent remote run before reporting cancelled.
No second request or cancel after timeout, malformed reply or ambiguous row.
If the row races to `RESERVED`, do not cancel an active allocation; requery
and use v3's safe no-run/no-process/empty-GPU verified release path. Keep
uncertain states explicitly unresolved and retain all evidence.

Preserve v3 source-frame measurement before reservation, full intent/frame/
reservation/launch lineage audit, accepted-reservation lost-reply recovery,
one-shot release, source-only split, two epochs, seed 2026, trainer and quality
gate. Fold0 remains 56 fit/15 inner source44 movies; fold1 remains 102 fit/26
inner source6 movies. No outer labels in training. Local tests must reproduce
the v3 stranded-WAITING failure, then prove exact one-shot cancel, wrong reply,
lost cancel response, WAITING→RESERVED race and valid source-lineage chain;
repeat v3 tests, all hash readback and no-cache compilation. Independent
second review before remote stage; update x138 auditor pins separately.

This correction is local only. No SSH, queue/GPU action, outer target read,
Kaggle POST or OOF claim. The active primary fold0 lease is untouched.
