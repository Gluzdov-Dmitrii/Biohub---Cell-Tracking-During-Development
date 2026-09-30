# Primary full fold1 v4: local correction handoff

Status: **LOCAL PACKAGE READY FOR INDEPENDENT REVIEW; NO REMOTE STAGE OR RUN**.

## Fixed predecessor and new identity

- Pre-registered correction: `LOEO_PRIMARY_FULL_F1_V4_WAITING_CANCEL_PREREG_20260928.md`, SHA256 `7caa4d0b7ff421ecd3e00898e12276ab9ef07cb10d60f059f517c42365cd33cd`.
- Rejected v3 remains sealed: plan SHA256 `68dc688662379c7f64d015e866f19c118c6c33f9cc343a5a31112354cc23c976`; 21-file manifest SHA256 `84a9774602a1d3f44cd7a8e7160f24f6be2b9518ebc9c61d051718761d355c72`; auditor SHA256 `b9913e9a211321177d28fa4a275abe70daa1d8d86d2e1783685f469345715e28`. All three were read back unchanged after the v4 build. V1 through v3 were not remotely staged or run.
- New package: `work/loeo-primary-full-f1-v4-20260928/`.
- Attempt `dc011c58fec7`; lease ID `loeo-primary-full-f1-v4-dc011c58fec7`.
- New `full_plan.json` SHA256 `a36ba2d1e6b4f256225ccb450b5353b69250566bb4af74e678d75ec0cbb4dfd6`.
- New 21-file `full_bundle/bundle_manifest.json` SHA256 `efcaabd4d3d8e90994176b93f88350ab9140c5c705c1b1d8862d37d5f1ae0097`.
- New `full_control.py` SHA256 `b0019a3a0c6cfe5dad77e7b32d212a203ac5dda73fe2a5be73319a94c45722f0`.
- New `audit_completed_full.py` SHA256 `dc5af347f05c3adf3d7b45fdfcfb4b160a6d295d0cdf16b2b43eebf2c62fec5d`.
- Local test source `test_full_local.py` SHA256 `8e1728cf54e5707840950b29e6fe152fcf53f409258b4edc30262f29f1b34b73`.

## Correction

`reconcile()` now recognizes an exact `WAITING_RESOURCE` row with all planned identity and resource fields, `gpus=[]`, and `process=None`. It checks remote run/process absence, rereads the exact queue row, and writes an exclusive fsynced `full_cancel_intent.json` before one `cancel --id <planned> --token <planned>` call. It saves the parsed and raw reply or the raw error, then rereads the live row and remote absence. It reports `CANCELLED_WAITING_VERIFIED` only for exact raw `id` plus `state=CANCELLED`, exact live `CANCELLED` row with no GPU/process, and no remote run/process. An existing intent prevents automatic recancel or rerequest. Later `ALREADY_CANCELLED` needs the original matching intent/reply and a fresh clean queue/remote readback.

If an exact waiter becomes `RESERVED`/`RUNNING` before cancel, or cancel fails because the allocation became active, reconciliation routes the new exact active row through the existing stopped-GPU/process unlaunched release checks. Ambiguous queue, cancel, raw reply, or remote state remains unresolved. A cancellation intent also bars a full-training completion audit. The 28 named audit checks remain identical to v3.

## Local evidence

- `python -B -m unittest -q test_full_local.py`: **32 tests passed**. Adversarial coverage reproduces v3's exact waiter remaining live after two reconciliations with zero cancel calls; v4 direct and lost-reply requests cancel once without training launch. Tests cover every waiting identity/resource field, wrong/missing fields, command ID/token, timeout/malformed and wrong-ID replies, unsafe remote state, raw/live cancellation readback, and both WAITING→RESERVED races, including an ACTIVE cancel error. Existing v1/v2/v3 failure and positive-path checks also pass.
- No-cache `compile()` of all eight local Python sources passed.
- `python -B build_full_bundle.py validate-inputs`: 128 source, 71 outer, 13 support files.
- Full post-build readback verified all 21 manifest entries against their bytes and SHA256, exact source copies, plan SHA, and manifest SHA. Plan science: 102 fit/26 inner source `6bba`, 71 excluded outer `44b6`, 9,949/2,443 windows, 50 epochs, seed `20260930`, no warm start and unchanged quality gates.

## Remaining gates

Independent second review must accept the v4 cancellation and race handling before any stage. Then use the explicit stage/launch/reconcile flow and remote receipts; no remote action was performed here. X138 assembler pins require a distinct later version after acceptance. This handoff does not claim an OOF result or a trained checkpoint.
