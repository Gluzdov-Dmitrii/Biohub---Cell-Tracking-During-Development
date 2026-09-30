# DeepCenter reciprocal v2 — ambiguous reservation recovery and fold0 frames

Written 2026-09-28 Asia/Novosibirsk before successor implementation. An
independent read-only review rejects both sealed DeepCenter full v1
controller packages before GPU launch. Preserve the fold0 training plan
SHA256 `ec3c4005a8702f9e7c6de88e81083a8020515019f3a780e57aff358a4e57d3e8`,
training manifest `18b87b58de6f1bdda9041085a764cdb0d6edafed2826ff3e891b07b5e5bf9756`,
control manifest `c405bbf4083817d193c80a3b3d11f586fb75b2ae05a5c67c7c02bb1be397ca75`;
and fold1 training plan
`f3d311bdb26944779e273c2ac03f795e10c08a27ce9f187290d6203f4648e55b`,
training manifest `a3f2d99a8ad84866f17dfbc72f1baa21981f5a0dc49ee290d449cf2d6ee09c98`,
control manifest `2176807617e05fc67b749246c654e1efa2546746f803ea6afa174de2c6597f59`
unchanged and unrun. All old local tests/manifests passed; the defects are
in resource control, not a measured model score.

Both v1 controllers write `launch_intent.json`, request a queue reservation,
then write `reservation_receipt.json` only after the request reply arrives.
The SSH helper can time out after the queue accepts a reservation. In that
state `reconcile` returns `NO_RESERVATION_RECEIPT` without consulting the
durable intent or live queue and cannot safely release or account for the
lease. The fold0 preregistration also requires actual source Zarr frame
metadata before reservation, but v1 fold0 preflight checks only 142 source
symlink identities; the frame totals are first measured postrun. Fold1
already measures exact 10,200 fit and 2,600 inner frames before reservation.

Create distinct v2 packages and unique attempts/lease IDs for both folds.
Keep the scientific experiment fixed: source44 fold0 56 fit/15 inner and
outer128 6bba; source6 fold1 102 fit/26 inner and outer71 44b6; two epochs,
seed2026, the same explicit split, public trainer/loss/augmentation, strict
minimum source-inner BCE checkpoint and fixed quality thresholds. No warm
start, source/outer mixing or post-hoc gate change. Recompute and seal new
training/control plan and bundle hashes. Do not edit or stage v1.

Before fold0 queue request, read the approved source-only Zarr shape metadata
for all 71 source movies through the guarded source view, require valid
positive time dimensions and no wrong target symlink, calculate exact fit/
inner frame and batch totals, and durably save a read-only measurement
receipt bound to the split/source-view/plan. Preflight and final verifier
must agree on this measurement. Fold1 keeps its existing pre-reservation
frame check and binds the corresponding observation.

For either fold, an intent with no reservation receipt is an **ambiguous
transaction**, not proof that no lease exists. A one-shot reconciliation must
read the durable intent and fresh queue snapshot for the exact lease ID,
project and run path; never issue the same queue request again. If the queue
shows a current reservation, verify there is no matching remote run-owned
process/group and that the allocated GPU is physically idle before releasing
with the saved token. Save the raw release reply and require exact `id` and
`state=RELEASED`. If the queue reports RUNNING, identity differs, remote
absence or GPU-idle cannot be established, or the transport result is
uncertain, preserve an explicit inconclusive receipt/state and do not release
or retry. A missing queue row immediately after timeout is likewise
inconclusive until a later authoritative recheck rules out delayed
acceptance. Normal fully launched supervisor/release and independent audit
behavior remains exact and must not regress.

Tests must simulate queue accepted plus lost reply, no reservation receipt,
matching/mismatching queue rows, delayed/missing row, live process or busy
GPU, valid safe release, wrong raw release reply, and no duplicate request.
Fold0 tests must show frame metadata is measured and bound before request;
fold1 frame checks remain. Run existing training/control tests, compile
transport scripts, rehash every sealed file and exclude caches. Separate
independent review is required before stage/launch. The x138 reciprocal
assembler must later receive any changed DeepCenter auditor SHA pins in a
distinct version; no real source emission while stale pins remain.

This correction is local only. No SSH, queue request, GPU, target image/GEFF,
Kaggle POST or OOF score is authorized by this document. The active primary
fold0 GPU lease remains untouched.
