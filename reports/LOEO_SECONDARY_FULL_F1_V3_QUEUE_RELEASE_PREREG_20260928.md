# Secondary full fold1 v3 — released queue semantics and ambiguous request

Written 2026-09-28 before successor implementation. Independent read-only
review **rejected local v2 before remote stage**. Preserve its plan SHA256
`4b2c375f55e0260e55dc900c056c78a39dd4ad57c4e875d12affac0dd887c570`,
21-file manifest SHA256 `13b244ae4728de83c04c8d8eec13d82f32e2bf433c3e375a64d18eb6de81f871`
and final auditor SHA256 `a88f9b26ebca546c367f2784865d415722a84583b36a983ccc0914ee09cd4816`
unchanged as rejected local evidence. V1 and v2 have no remote stage, lease,
GPU run, or outer target read.

The v2 final auditor demands `gpus == [runtime_gpu]` on the *current*
`RELEASED` queue row. Actual saved secondary fold0 release evidence in
`work/loeo-secondary-full-f0-v1-20260927/full_final_reconciliation.json`
has the matching lease ID, project, run path, alias, count and
`state=RELEASED`, but `gpus=[]`: the queue clears allocation on release. The
v2 test fixture invented a `RELEASED` row that retained the GPU. A valid
completed fold1 run would therefore fail `lease_released`. The v3 auditor
must bind the allocated GPU from the pinned `RESERVED` receipt and saved
release-time empty-GPU observation, then verify stable ID/project/run/owner/
pool/count/resources and `state=RELEASED` on the current row while accepting
the queue's cleared `gpus=[]`. Reject a current released row with an unrelated
nonempty allocation or missing stable identity. Add an adversarial test using
the real fold0 response shape and a test for mismatched current identity.

The v2 controller also writes its first local receipt *after* requesting a
queue lease. An accepted request whose SSH reply times out can leave an
active lease with no local receipt, and `reconcile()` reports
`NO_RESERVATION_RECEIPT` without querying the queue. Create a durable,
exclusive, fsynced request intent before the queue call. On timeout or
malformed reply, use that intent to query the live queue and identify the
exact planned lease. Reconcile or safely release an active matching lease
only after proving that this attempt launched no remote run/process and its
GPU is empty. Preserve ambiguous states as unresolved evidence and forbid a
duplicate request. Any release success requires a saved raw reply with
matching lease ID and `state=RELEASED`; no release if process/GPU identity is
uncertain. Test the accepted-before-timeout case and an ambiguous queue view.

Preserve the corrected v2 reservation identity, release-response and
PID/start safeguards, all 28 exact named final-audit checks, and the science:
102 fit and 26 inner `6bba` movies, all 71 `44b6` outer movies excluded,
9,949/2,443 windows, 50 epochs, seed `20260929` before model import, no
warm start, unchanged model/trainer/selection/gates. Recompute and seal new
attempt, lease, plan and 21-file bundle; leave both rejected predecessors
untouched. The v2 preregistration contains a typo in the historical v1 plan
SHA; the actual v1 plan SHA256 is
`bd99d3ebe23a7038e6c56a2f6ea39b668966b2e5cfedd47bd1b2525ff378ba06`.

Use local adversarial mocks, source-only checks, no-cache compilation and
full manifest readback. An independent second review must pass before stage.
Update x138 assembler pins in a distinct version after that review. This
correction is local only: no SSH, queue request, GPU, target image/GEFF,
Kaggle POST or OOF claim. Do not disturb the active primary fold0 lease.
