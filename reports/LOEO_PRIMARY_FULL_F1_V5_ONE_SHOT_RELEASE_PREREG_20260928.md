# Primary full fold1 v5 — durable one-shot release

Written 2026-09-28 before successor implementation. Independent read-only
review **rejected sealed local v4 before remote stage**. Preserve its plan
SHA256 `a36ba2d1e6b4f256225ccb450b5353b69250566bb4af74e678d75ec0cbb4dfd6`,
21-file manifest SHA256 `efcaabd4d3d8e90994176b93f88350ab9140c5c705c1b1d8862d37d5f1ae0097`,
controller SHA256 `b0019a3a0c6cfe5dad77e7b32d212a203ac5dda73fe2a5be73319a94c45722f0`
and auditor SHA256 `dc5af347f05c3adf3d7b45fdfcfb4b160a6d295d0cdf16b2b43eebf2c62fec5d`
unchanged. V1 through v4 have no remote stage, queue lease or training run.

V4 correctly handles exact `WAITING_RESOURCE` with one-shot cancellation,
but its unlaunched `RESERVED` release path issues the queue `release` before
durably recording an exclusive release intent. A mocked lost SSH release
reply made two consecutive `reconcile()` calls each return
`UNRESOLVED_RELEASE_REPLY` while making **two** release calls and writing no
unlaunched-release receipt. The same path is reached by an ordinary
unlaunched reservation and by a WAITING→RESERVED race. This violates the v4
one-shot release requirement; a timeout can otherwise cause repeated
mutation or obscure the true state.

Create a distinct v5 attempt, lease, plan and package. Before *every*
unlaunched queue release, durably write an exclusive, fsynced release intent
that binds immutable plan SHA, exact lease ID/token, run, GPU, reservation
receipt or recovered live row, fresh no-run/no-process/empty-GPU probe and
time. On a lost, malformed or wrong-ID/state raw release reply, preserve
response/error evidence and do not issue another automatic release on any
later reconcile. A fresh queue read may report the factual state but must
not upgrade an absent/invalid raw reply to verified release or restart the
mutation. On a valid raw reply, require exact `id` and `state=RELEASED`, save
it durably, and confirm the live released row (`gpus=[]` permitted) and empty
run/process/GPU before success. The waiting-cancel intent and unlaunched
release intent must be mutually exclusive where appropriate; a waiter that
races to RESERVED may transition to the safe release path once, never both
cancel and release repeatedly. Keep unresolved ambiguity explicit.

Preserve v4 full reservation identity, source-only science, 102 fit/26 inner
`6bba`, all 71 outer `44b6` excluded, 9,949/2,443 windows, 50 epochs, seed
`20260930`, no warm start, the same trainer/selection/gates and 28 exact final
audit names. Recompute every changed plan, bundle, controller and auditor SHA.
Local tests must reproduce the v4 double-release with an ordinary RESERVED
receipt and a WAITING→RESERVED race, show v5 one release call across repeated
reconciliations after lost reply, test a valid exact release and wrong raw
reply, and retain all v4 queue-cancel and source tests. Full no-cache compile,
manifest readback, independent second review before stage and distinct x138
pin update are required.

This correction is local only. No SSH, queue/GPU action, outer image/GEFF,
Kaggle POST or OOF claim. The current primary fold0 lease is untouched.
