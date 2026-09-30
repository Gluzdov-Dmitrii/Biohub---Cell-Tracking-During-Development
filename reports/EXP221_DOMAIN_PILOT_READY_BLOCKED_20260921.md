# EXP221 paired detector-domain pilot: prepared, not launched

Status: `BLOCKED_PENDING_EXPLICIT_CLUSTER_SOURCE_TRANSFER_APPROVAL`.
Automatic approval review rejected the staging command because it transfers
private project source/experiment files to the remote cluster. No upload,
GPU lease, smoke or training occurred. Do not work around this rejection.
The parent task requested explicit approval and owns that decision.

## Frozen design

Both arms train source44b6 seed2026 from the SAME clean epoch12 model and
optimizer to epoch24 (12 additional epochs, matched updates). Fixed original
architecture, losses, source folds, reduced-window cohort, exact image cache,
upstream brightness/flip augmentations and validation. The candidate appends
temporally shared gain [0.8,1.2], gamma [0.85,1.15], exponential depth
attenuation [0,0.25] and shared spatial noise sigma [0,0.015]. Spatial labels,
padding masks and time order stay unchanged. Upstream z flips are inherited
equally; this experiment introduces no geometry transform.

Both arms fix the original unseeded per-item `np.random.default_rng()` by
seeding it from epoch-seeded global NumPy state. Candidate draws are local to
each item's generator, so subsequent control/candidate item seeds remain
matched. Checkpoint selection is best POST-intervention source validation
`accuracy * recall`: this is a proxy, **not** official graph CV. Target data
and metrics remain closed; no Kaggle submission.

EXP220 found no strong depth/time/boundary concentration. This augmentation
pilot is exploratory, not a confirmed depth-specific remedy. Do not expand
to week-long retraining from source proxy improvement alone. Need paired
target graph evidence with fixed graph parameters before promotion.

## Verification

`reports/exp221_test_results_20260921.json`: finite values, shape/dtype,
determinism, temporal sharing, input/label immutability, real upstream item
AST with stubbed cached volume reads, matched per-item RNG across four draws,
unchanged validation normalization all pass. Generated trainer/cache/launcher
Python compilation passes. The local publication copy's old flip indexing
differs from deployed code; tests use the actual read-only cluster source,
SHA `13db09817bf492f8d0f710a0a4d09776320b262060167055090a303fc6057f4e`.

Read-only live cluster status and SHA check confirmed initial checkpoint
`runs/exp214_reduced44b6_s2026_20260912/output/checkpoint_last.pth`:
`f8a43239be4136bc0d3d44ff19cfb8d69deb7b852e3abfc39f4a44c54a78a638`,
status COMPLETE_SOURCE_REFIT, epoch12, fold44b6, seed2026, no target data opened.
Generated trainer pins this SHA before loading model AND optimizer. Its
contract also pins domain module and modified exact-cache loader hashes.
Upstream trainer SHA:
`c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`.

## Authorized-continuation commands (only after transfer approval)

1. `python scripts/stage_exp221_domain_pilot.py`
2. Use `python scripts/launch_exp221_job.py --mode training --config ...`
   for the prepared `reports/exp221_{control,domain}_44b6_s2026_20260921_smoke_config.json`.
   The launcher acquires a common-queue lease and starts its existing monitor.
   Verify both smoke exits, finite benchmark losses and lease releases.
3. Launch the two matching configs without `_smoke` the same way. They can
   run concurrently on the two A100s if the live common queue allows it.
   Require first training events and start epoch12; never declare launch from
   preparation alone. No repeated unbounded invocation: stop at epoch24.

Expected pilot duration after approval: approximately 35–60 minutes training
per arm plus staging/smoke/loading; allow 1–2 hours with both A100s. Each
invocation has a 2-hour checkpoint budget and a finite epoch24 cap. New honest
paired graph inference/scoring is a separate next stage, not included in this
source-pilot ETA. Hardware contention can extend elapsed time.

Files/SHAs and configurations:
`reports/exp221_domain_pilot_prepare_20260921.json`.
Experiment-owned stage script only sends its explicit six-file allowlist,
not the entire local project or test fixtures; shared runtime stays immutable.
