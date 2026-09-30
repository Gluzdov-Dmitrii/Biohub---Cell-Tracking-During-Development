# Primary full fold1 v2 — release and final-audit correction

Written 2026-09-28 Asia/Novosibirsk before successor implementation. The
source6bba primary fold1 v1 is sealed locally but **rejected before remote
stage** by an independent read-only audit. Preserve its plan SHA256
`b2d78b51f16b2ef38fc2ee3ddbad24bc2e9f80411b7112273767f1a50fa7869c`,
21-file manifest SHA256
`8bfda46f6755089f158a1d87abfb00e560ec8afe12b526fc4a3912793279476f`
and auditor SHA256
`32479bb6fababab765260c86438f8c6942a0b915b4b4a0ffcbda0a4d3ae19534`
unchanged as failed local evidence. V1 has no stage, lease, GPU run or outer
label read.

The audited defects are deterministic: v1 supervisor writes terminal
`complete.json` after an arbitrary JSON queue release response; the auditor
accepts empty supervisor response and a manual `RELEASED` response without
matching lease `id`; the controller reports manual release success for `{}`
and drops the raw reply in the unlaunched-release branch. The final auditor
unconditionally hashes `full_reconcile_latest.json`, which need not exist on
the normal automatic supervisor completion path. The auditor also needs an
explicit launch-versus-exit PID/start identity check; a matching finish time
alone does not bind the actual training process. Current tests wrongly accept
some malformed replies, and x138 assembler v3 pins the rejected auditor SHA.

Create a distinct primary fold1 v2 local package and unique attempt/lease.
Preserve the scientific experiment: 102 fit and 26 inner source `6bba`
movies, all 71 `44b6` outer movies excluded, 9,949/2,443 exact windows,
50 epochs, seed `20260930` before model import, no warm start, same model,
trainer, source-inner selection and quality thresholds. Recompute and seal
every new plan, bundle and source hash; never edit or stage v1.

Use the corrected fold0 v2 release protocol as the reference. A release
response is valid only when its raw `id` equals the exact lease and its
`state` is `RELEASED`. Require this for supervisor completion, manual
reconciliation and verified unlaunched absence. Save the raw reply durably
for each branch. Do not write a terminal PASS completion or return a
successful release action when the raw reply is invalid. The independent
auditor must verify the saved raw reply, matching plan/run/lease/GPU and
launch-versus-exit PID/start, clean exit/no hard timeout, dead run-owned
process/group, release-time empty GPU, live queue `RELEASED`, and source-only
training evidence. Its normal automatic-supervisor path must pass without
`full_reconcile_latest.json`; a present reconciliation may be checked and
hashed, but its absence is not failure. Keep 28 exact named audit checks
including `remote_source_metadata_matches`, each true, for downstream use.

Tests must reproduce v1 false accepts for `{}`, wrong lease `id`, wrong
state, manual missing `id`, and v1 normal-path audit `FileNotFoundError`;
show v2 rejection or successful optional-file handling as appropriate.
Include a launch/exit identity mismatch test, exact positive supervisor and
manual replies, source exclusion/window/seed checks, code compilation and
full manifest readback with no cache. A separate independent review must
pass before remote stage. The x138 reciprocal assembler must later receive
the new independently reviewed auditor SHA in a distinct version; no real
source emission while it pins v1.

This correction is local only. No SSH, queue request, GPU, target image/GEFF,
Kaggle POST or OOF score is authorized by this document. The active primary
fold0 GPU lease remains untouched.
