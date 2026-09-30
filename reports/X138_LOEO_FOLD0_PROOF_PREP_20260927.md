# x138 LOEO fold-0 outer-scoring proof — local preparation, 2026-09-27

**State:** local/read-only preparation only. No new remote code, GPU lease,
inference, target label read, Kaggle kernel push or competition POST. This note
is not a GPU launch preregistration or a promotion gate.

## Source of truth and fixed proof target

The v3 fold-0 pilot has a 19/19 independent technical audit, exit 0, an empty
denied-access log and a released lease:
`work/x138_loeo_runtime_v3/pilot_final_reconciliation.json` SHA256
`65e17c3a9ddd1ad1962587dd2615f093d37eac226d82d7e73b24aafb1edb352a`.
It trained on 56 source `44b6` movies, selected on 15 disjoint source `44b6`
movies, and excluded all 128 `6bba` movies. The checkpoint SHA256 is
`e90453d53b7e4485752222f74b816269aa23f0e9eaa8c12ac18292c23a555122`.
Its 16 updates and source-inner node recall 0.329975 are a compatibility smoke,
not a trained quality candidate.

`work/x138_loeo_fold0_proof/prepare_plan.py` pins the split, pilot receipt,
public trainer/predictor and current-organizer metric source hashes, then
chooses the outer movie with minimum SHA256 of the ID string among all 128
sealed `6bba` IDs. This fixed rule selects **`6bba_32db13fc`** without
examining image content or labels. Local-only
`work/x138_loeo_fold0_proof/plan.json` SHA256
`c2504ffccc3d1b4eb2f0ca55a88dc12af0ed0e408277c7654839d57ce400afb7`
fixes the prediction defaults: public predictor SHA256
`c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`,
math-only SDPA, detection threshold 0.99, XY-flip TTA, softmax edges above
0.5, no ILP and all frames. This is the support-pack *standalone predictor*,
not the assembled x138 inference graph.

Read-only cluster preflight `work/x138_loeo_fold0_proof/remote_readonly_preflight.json`
SHA256 `1c5ee924cef4d4c00c155c92cae5d403308647ac438d2c407e4d4dceca48ea76`
confirms that the target Zarr symlink resolves to the expected source-data
parent, has shape `[100,64,256,256]`, includes both quantile fields required
by `predict_video`, and the existing remote checkpoint still has the pinned
SHA. It did not open a GEFF label tree. Public `predict_video` calls
`open_dataset(..., require_tracks=False)` through that function's default;
`open_dataset` only loads GEFF when `require_tracks=True`. The future runner
must still present **only** the selected `.zarr` in its input view and enforce
a label-denying access audit, because source review alone is not a runtime
proof.

## Exact next execution path, pending a fresh runner and preregistration

1. Build a new immutable inference bundle and dedicated queue identity. Keep
   v1/v2 failures and the successful v3 code/run/lease untouched. Stage the
   exact support-pack predictor and pinned v3 checkpoint with hash readback.
   The target input view must contain only `6bba_32db13fc.zarr`; no target
   `.geff` link, no other embryo IDs and no `--evaluate` path.
2. On one queue-free, physically idle A100, run the pinned public standalone
   predictor for all 100 frames under math-only SDPA. Give this *proof* a
   30-minute hard runtime cap and 40-minute lease. Require exit 0, no timeout,
   zero denied target-label accesses, exactly one `6bba_32db13fc.geff`
   prediction tree, valid graph topology, a tree-content SHA and lease release.
   Any failure stays recorded under its own identity; do not silently retry.
3. Only after those receipts are sealed, let a separate CPU scorer open the
   single target GEFF label tree. Use pinned current organizer commit
   `075fc5f5a52d11077f9dc2b074644618f26939e2`, source hashes in the
   plan, the target voxel scale and `estimated_number_of_nodes` metadata.
   Report the per-movie adjusted edge, raw edge, node recall, division counts,
   graph counts and complete score. This is an execution-path proof and one
   preselected directional observation; it is not an OOF population estimate.

No executable GPU command is issued by the local plan. The fresh guarded
runner, exact stage/launch command, resource receipt and pre-execution audit
must be reviewed and communicated before any GPU job. No competition slot can
follow from this technical proof.

## Full training feasibility and provenance limit

For a separate **model-quality** experiment, the next bounded source-only
training is fold 0 with all 5,001 fit windows per epoch (not `max_iters=16`),
fixed 50 epochs, batch 8, two workers, math-only SDPA and source-inner
checkpoint selection on 1,314 windows. The pilot measured 9.2 seconds for
16 train batches and 49.1 seconds for full inner validation. A linear lower
estimate is `50 × (ceil(5001/8) × 9.2/16 + 49.1) ≈ 5.7 A100 hours` plus
dataset load, checkpoint and system overhead; budget **6–9 GPU hours** for
fold 0, with a firm per-job limit and progress receipts. Reciprocal fold 1
has 102 source fit and 26 source-inner movies, roughly 10–14 GPU hours by
movie/window scaling. Full outer inference over 128+71 movies and scoring
adds several GPU hours and requires independent graph locking before labels.
These are estimates, not measured full-epoch timings or a cost quote.

The live read-only Kaggle competition list returned **2026-09-29 23:59 UTC**
as the deadline. At 2026-09-27 13:24 UTC that leaves about **58 hours 35
minutes**. At the 13:xx queue check no request was active and both A100s
showed 0 MiB/0% use; availability is volatile. A single full fold and a
reciprocal secondary-model study could fit in the calendar if staged promptly
and resources stay free, but neither would make the *assembled x138* graph an
honest end-to-end holdout. The original secondary checkpoint fit all 199
movies; x138 primary checkpoint and V1284 head lack verified embryo split
metadata; DeepCenter trained on `44b6` and selected on `6bba` validation.
The x138 thresholds/repairs and visible train diagnostics have also been
developed on these embryo families. A standalone source-trained predictor
outer score therefore measures this component/path only. Qualifying
`PRIVATE_ROBUST` would require source-only training or verified held-out
provenance for **every** active learned component, fixed inference policy,
both embryo directions, and paired current-organizer graph evidence. No such
candidate is prepared or authorized here.
