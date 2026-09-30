# Secondary full fold1 v2 — lease identity and release correction

Written 2026-09-28 Asia/Novosibirsk before successor implementation. The
sealed local-only secondary fold1 v1 is **rejected before remote stage** by an
independent read-only audit. Preserve its plan SHA256
`bd99d3ebe23a7038e6c56a2f6ea39b668966b2e9f80411b7112273767f1a50fa7869c`,
21-file manifest SHA256
`3349a7619ab47fcfa0c2a12a50c3ee276b56b6068873d979488f28b6e4298f6a`
and auditor SHA256
`df1eb40bfcc0237e7ad57c421f599d59437dc9dec08ea30c8fe5ee409f5000c8`
unchanged as failed local evidence. V1 has no stage, lease, GPU run or outer
label read.

The v1 auditor accepts saved supervisor or manual release replies with a
wrong lease `id` and `RUNNING` state, and can accept a valid manual receipt
even when a present supervisor completion is invalid. Its tests expect
incomplete replies to pass. The controller accepts a queue reservation for a
different lease/run path. The auditor does not bind launch PID/start to exit
PID/start; a mismatched pair passed an adversarial probe. Fold1 shares the
primary v1 supervisor that writes terminal completion after an arbitrary JSON
release response, and its normal automatic path risks an unconditional hash
of an absent `full_reconcile_latest.json`. These failures can be promoted by
the x138 assembler despite its exact 28-key check dictionary.

Create a distinct secondary fold1 v2 local package and unique attempt/lease.
Preserve the scientific experiment: 102 fit and 26 inner source `6bba`
movies, all 71 outer `44b6` movies excluded, 9,949/2,443 exact windows,
50 epochs, seed `20260929` before model import, no warm start, unchanged
model/trainer/augmentation, same source-inner selection and quality gates.
Recompute and seal every new plan, bundle and source hash; never edit or stage
v1.

Use the corrected secondary fold0 independent release gate and primary fold0
v2 controller as references. A reservation must bind exact lease `id`,
project, run path, GPU alias/count and current reserved state before launch.
Only a raw queue release response with exact lease `id` and `state=RELEASED`
is valid. Require and save this response for supervisor, manual and verified
unlaunched branches. Do not write terminal PASS completion or report a
successful release action for an invalid response. A present invalid
supervisor completion must fail, not be bypassed by a manual receipt.
Independently bind exact plan/run/lease/GPU, launch PID/start to exit
PID/start, clean exit/no hard timeout, dead run-owned process/group,
release-time empty GPU, live queue `RELEASED`, and source-only evidence.
Normal automatic completion must not require `full_reconcile_latest.json`;
when that file is present it may be checked and hashed. Keep all 28 exact
named audit checks, including `remote_source_metadata_matches`, for
downstream use.

Tests must reproduce v1 false acceptances for empty/wrong-ID/wrong-state
release replies, the invalid-supervisor-plus-valid-manual conflict, wrong
reservation lease/run, mismatched launch/exit PID/start and absent optional
reconciliation. Show v2 rejection or valid automatic completion as
appropriate, plus exact positive supervisor/manual replies, source/window/
seed checks, compilation and full manifest readback without cache. A separate
independent review must pass before remote stage. The x138 reciprocal
assembler must later receive this new independently reviewed auditor SHA in
a distinct version; no real source emission while it pins v1.

This correction is local only. No SSH, queue request, GPU, target image/GEFF,
Kaggle POST or OOF score is authorized by this document. The active primary
fold0 GPU lease remains untouched.
