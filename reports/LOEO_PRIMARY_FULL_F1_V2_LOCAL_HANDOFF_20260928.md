# LOEO primary full fold1 v2 — corrected local handoff

Prepared 2026-09-28 Asia/Novosibirsk. **LOCAL ONLY:** no SSH, remote stage,
queue request, GPU work, target image or GEFF read, Kaggle action, or OOF score.
The fold0 lease was not touched. Independent review is still required before
any remote action.

## Pre-registration and immutable identity

- Correction preregistration:
  `reports/LOEO_PRIMARY_FULL_F1_V2_RELEASE_CORRECTION_PREREG_20260928.md`,
  SHA256 `766fec0b8f5ff7e6eafc0b04e0056ca4fb3fbb8bd6a7ad8b870acd11e491be15`.
- Local directory: `work/loeo-primary-full-f1-v2-20260928/`.
- Plan `full_plan.json` SHA256
  `4dcbd79f8e07ebec92bba37d96547ff521aa3ba7424ae12f1d7c4903725cb5c5`.
- Exact 21-file bundle manifest `full_bundle/bundle_manifest.json` SHA256
  `681ffa4a9e816177c4c11d34eb8de4613190fc39cd9fcd2509f1a57e2552ff21`.
- Fresh attempt `d0fd4e1a0cc9`; lease
  `loeo-primary-full-f1-v2-d0fd4e1a0cc9`. Planned remote code/run stems are
  `loeo_primary_full_f1_v2_d0fd4e1a0cc9` under the pinned Biohub `code/` and
  `runs/` roots. Those remote paths were not created.
- Rejected v1 was preserved unchanged: plan SHA256
  `b2d78b51f16b2ef38fc2ee3ddbad24bc2e9f80411b7112273767f1a50fa7869c`,
  21-file manifest SHA256
  `8bfda46f6755089f158a1d87abfb00e560ec8afe12b526fc4a3912793279476f`,
  auditor SHA256
  `32479bb6fababab765260c86438f8c6942a0b915b4b4a0ffcbda0a4d3ae19534`.

## Scientific and release contract

The source-only scientific experiment is unchanged: pinned split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`,
102 fit and 26 inner source `6bba` movies, all 71 `44b6` movies excluded,
9,949/2,443 exact windows, batch 8, two workers, 50 epochs, seed `20260930`
before trainer import, no warm start or maximum-iteration cap, math-only SDPA,
latest maximum inner accuracy × recall checkpoint selection, and fixed
accuracy/recall/product gate `0.97/0.80/0.80`. The source-window metadata SHA256
remains `584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`.
The training runner SHA256 remains
`2278ace9041d0c820683a639c3953b95c8453514165d9e1ab1b05708af547057`;
the wrapper SHA256 remains
`d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`.
The published primary weight is identity metadata only and is never loaded.

The corrected contract SHA256 is
`67e7ab5c021ac47a8df76f4ce4e866ea4e97035a6667253934bf66adec5f7690`;
controller SHA256
`4231228dfd5caaedc8ed0e1fefdc7f27def6f59169bf28191d04d92b1083bc8b`;
supervisor SHA256
`451209c3b7e71bde342b92bfdf8936a3c2dc20e1e3ee13831a2bf429ada74fea`;
independent final auditor SHA256
`9295030aac97b8e281d18c76d0776013a7fb4fcd4d1d4042f36477439c8dd926`.
Every release branch now saves its raw queue reply. The local controller
flushes and syncs the exclusive receipt before reporting a result. Exact
matching lease `id` plus `state=RELEASED` is required for success. The final auditor checks
that reply, release-time empty GPU, live queue state, plan/run/lease/GPU,
clean exit, dead run-owned process/group, and launch-versus-exit PID/start and
time identity. Automatic supervisor completion accepts an absent optional
`full_reconcile_latest.json`; manual release requires its immutable manual
receipt. The 28 exact v1 audit-check names, including
`remote_source_metadata_matches`, are preserved. A future real PASS requires
all 28 to be true.

## Local validation

- `python -B .../build_full_bundle.py validate-inputs`: 128 source IDs,
  71 excluded outer IDs, 13 pinned support files.
- `python -B .../test_full_local.py`: **16/16 passed**. The tests execute
  rejected v1 supervisor/controller/auditor paths in temporary directories:
  v1 falsely accepts `{}`, wrong lease ID/state, and manual missing ID;
  v1 automatic-path audit raises `FileNotFoundError` without reconciliation.
  V2 rejects those replies, preserves raw manual/unlaunched responses,
  accepts exact positive replies, and handles the optional file. PID/start
  mismatch, source split/window/seed checks, and identical 28 named check keys
  are also covered. Test source SHA256 is
  `52001947107b9ec46f6b3f9be50d8a1ed410b5c8f6fc0a1233fcc6206003cf8d`.
- Eight local Python sources compiled with `compile()`; no bytecode created.
  `full_control.read_plan()` and `verify_bundle()` reread every 21 bundled file
  and its hash, including preregistration and source metadata. The bundle had
  22 physical files including the manifest and no `.pyc` or `__pycache__`.

## Remaining gates

Root must arrange a separate independent review of this successor, including
the exact release-reply shape of the live fair queue, before considering any
remote stage. Later stage/launch needs fresh queue fairness, foreign-waiter,
existing Biohub lease, physical A100 idle, and remote byte-readback gates.
The x138 reciprocal assembler must receive the new independently reviewed
auditor SHA in a distinct version before any real source emission; it still
pins rejected v1. This handoff grants no stage, reservation, launch, outer
read, Kaggle action, or OOF claim.
