# LOEO primary full fold0 v2 — corrected local handoff

Prepared 2026-09-27 UTC. **Local package and tests complete; no remote stage or
launch has occurred.** Correction preregistration
`reports/LOEO_PRIMARY_FULL_F0_V2_CORRECTION_PREREG_20260928.md` SHA256
`0b6aaf9b90a04c07066b64fdd98456b1677bfdf1e69d723932099414032fb80a`
was saved before implementation. The rejected v1 directory is unchanged:
its old plan SHA256 is
`589fb15b6440054c9f05e8fb53c3bfee747d917eb4f69f990ef336c65647cb6b`
and old 20-file manifest SHA256 is
`ff9b0f67007057cbc1e381014144ce3afd147f41bdc8b2635304bc0b210f2990`.

## Sealed v2 identity and source contract

- Local directory: `work/loeo-primary-full-f0-v2-20260928/`.
- Exact 20-file bundle manifest:
  `work/loeo-primary-full-f0-v2-20260928/full_bundle/bundle_manifest.json`,
  SHA256 `469060e14a0f8506ee9c6d03ef5a125ef050ec02679b5a03bfa00841382096be`.
- Immutable plan: `work/loeo-primary-full-f0-v2-20260928/full_plan.json`,
  SHA256 `9a2906d18a3df5462256f1dd9faa4844f328b90be78d9ac7cd820d65cbc97e44`.
- Fresh attempt `eeb0880f73f7`, lease
  `loeo-primary-full-f0-v2-eeb0880f73f7`. Planned remote code/run stems
  are both `loeo_primary_full_f0_v2_eeb0880f73f7` under the pinned Biohub
  `code/` and `runs/` roots. These paths have not been remotely created.
- Pinned split SHA256
  `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`:
  source `44b6` fit56/inner15, 5,001/1,314 two-frame windows; all 128
  `6bba` IDs sealed. The plan fixes 50 full epochs, batch8/two workers,
  `max_iters=null`, seed `20260928` before trainer import, math-only SDPA,
  source-inner selection and the original fixed quality gate. Published
  primary weights remain identity metadata only; `unet_weights=null`.

## Corrections and checks

The remote training runner `run_full.py` SHA256
`f069cfa13e98d64023bfee3c0e44ac02c1af25a12ebf023c805ef1d525a88035`
and wrapper SHA256
`d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`
are byte-identical to rejected v1; training/split/graph policy was not
changed. The v2 contract SHA256 is
`f2e18fae521cd3d317bd81ba25604ef6ed2e82357b5c329bb3ef9122de793017`;
supervisor `5041b679c747153a7fd32b4870b65b9a22ccce811a47707879c320f798bfd561`;
local controller `1347d9eb75ec56eaff02832560b3e02429fb48a5318fc583d56f2e1cbe3f57ff`;
independent auditor `3630b86f140a8db1a73a152b1cd31760ffac0406a9f80230fbf1aa800e6c2740`.

1. Final audit now requires actual RNG seed `20260928`, matching the plan and
   contract, pre-import marker and two valid RNG digests. Synthetic 20260927
   and plan-mismatch cases fail.
2. Supervisor saves a terminal `RELEASED_AFTER_VERIFIED_EXIT` only when the
   fair-queue release reply has this exact lease `id` and `state=RELEASED`.
   Manual and unlaunched reconciliation save their raw replies but report
   `RELEASE_REPLY_UNVERIFIED` for `{}`, a non-RELEASED state or wrong lease.
   Independent audit also requires the matching saved response, current queue
   RELEASED, ordered no-process/GPU-empty release observation, run/lease/GPU
   identity and exit0. A later GPU tenant PID does not invalidate the saved
   release-time observation.
3. Final audit records `prior_reconciliation_sha256=null` when automatic
   supervisor release had no optional local reconciliation file. Manual
   release requires and hashes its immutable manual receipt separately.
   Transient artifact, process, queue or CPU predictor SSH failure remains
   inconclusive without a final audit receipt.

`python -B work/loeo-primary-full-f0-v2-20260928/test_full_local.py` passed
**15/15** local tests, including synthetic supervisor and manual false replies,
seed mismatch, automatic release without reconciliation, manual receipt hash,
later tenant and transient probe cases. Test source SHA256 is
`1f8fd0c4dceece4a2ff4757f2fbfb8761f174522a7efb626801228714a9be88a`.
`validate-inputs` found 71 source,
128 sealed outer IDs and 13 pinned support files. Final local
`full_control.read_plan()` plus `verify_bundle()` passed exact 20-file/hash
readback; no `.pyc` or `__pycache__` was present in the bundle.

## Remaining launch gate

The newest repository progress receipt still showed the secondary fold0 lease
active. Root must first independently verify its release, review this v2
correction and confirm the live queue release-reply shape carries `id` and
`state` as required. Then use fresh fair-queue, foreign-waiter, physical A100
idle and exact remote staged-byte checks before a one-shot launch. This local
handoff authorizes no SSH, stage, reservation, GPU work, target-label read,
Kaggle action or `EXPERIMENTS.md` edit. Source-inner metrics are not OOF.
