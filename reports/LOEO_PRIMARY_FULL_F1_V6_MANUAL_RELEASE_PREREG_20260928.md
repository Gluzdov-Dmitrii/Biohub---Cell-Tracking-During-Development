# Primary full fold1 v6 — one-shot manual release after training

Written 2026-09-28 before successor implementation. The sealed local v5
corrected one-shot *unlaunched* release, but an independent parent scratch
probe found that its manual release after a stopped training process still
issues `ssh_json(release)` before any durable intent. With a valid pinned
reservation, live `RUNNING` row and safely stopped launch/exit identity,
two consecutive `reconcile()` calls after mocked lost SSH replies returned
`UNRESOLVED_RELEASE_REPLY` twice and made **two release calls**; no manual
receipt or unlaunched intent existed. Preserve v5 plan SHA256
`4f05dd6ca846c849ed0566b932e3453d0e9187a5b291de0bee07030ab3f98ac0`,
21-file manifest SHA256 `d60672f1df3b3f3aa0fe716b06b0760642b6e043cb7213cdaccfbd953df79219`,
controller SHA256 `774c0e55737fed650b3b4c4b60f4b97388d6dff302fd3c5ebaa44723c5efc157`
and auditor SHA256 `265e5d3844d29c5ad977013fa4051d83d8df5e3f7e1df10816437fd250242fa7`
unchanged as rejected local evidence. V1 through v5 remain unstaged/unrun.

Create a distinct v6 attempt, lease, plan and bundle. Before *every* manual
queue release after verified training exit, durably write an exclusive,
fsynced intent binding immutable plan SHA, exact lease ID/token, run, GPU,
saved reservation, matching launch/exit PID and start identity, fresh
dead-process/group/empty-GPU probe and time. The existing unlaunched release
intent and manual intent must both bar a second automatic release from any
branch. On lost, malformed or wrong-ID/state reply, preserve the raw
response/error as evidence and return explicitly unresolved without retry.
A valid exact `id` plus `state=RELEASED` raw reply must be saved, followed by
fresh live released row and process/GPU absence confirmation before success.
The final independent auditor must bind the new manual intent/reply and
allow only the queue's real post-release `gpus=[]` semantics. The supervisor
completion path must retain its own one-shot raw reply safeguard; ensure a
manual reconciliation cannot issue a second release after observing any
saved supervisor release attempt, even if the raw response is uncertain.

Preserve v5 source-only science and existing corrected controls: 102 fit/26
inner source `6bba` movies, all 71 outer `44b6` excluded, 9,949/2,443
windows, 50 epochs, seed `20260930`, cold start, fixed trainer/selection/gate,
exact queue reservation identity, one-shot waiting cancel, one-shot
unlaunched release and 28 named final-audit checks. Local tests must
reproduce the v5 manual double-release, show v6 release_calls=1 across
repeated reconcile after lost reply, exact valid raw/live release success,
foreign/malformed reply failure and cross-branch/supervisor prior-attempt
guards. Repeat v5 tests, no-cache compilation and all 21 bundle hashes;
independent second review before remote stage, distinct x138 pin update.

This is local only. No SSH, queue/GPU action, outer target image/GEFF,
Kaggle POST or OOF claim. The active primary fold0 lease remains untouched.
