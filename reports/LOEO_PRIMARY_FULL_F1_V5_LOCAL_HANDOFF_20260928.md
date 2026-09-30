# Primary full fold1 v5: local one-shot release handoff

Status: **LOCAL PACKAGE READY FOR INDEPENDENT REVIEW; NO REMOTE STAGE, QUEUE LEASE OR RUN**.

## Immutable identities

- Pre-registration `LOEO_PRIMARY_FULL_F1_V5_ONE_SHOT_RELEASE_PREREG_20260928.md` SHA256 `f9c55d8b1a4c740b05453126abc7c6b2d50191cd502f0b80e53cd2b61764860b`.
- Rejected v4 remains sealed and was read back unchanged: plan SHA256 `a36ba2d1e6b4f256225ccb450b5353b69250566bb4af74e678d75ec0cbb4dfd6`; 21-file manifest SHA256 `efcaabd4d3d8e90994176b93f88350ab9140c5c705c1b1d8862d37d5f1ae0097`; controller SHA256 `b0019a3a0c6cfe5dad77e7b32d212a203ac5dda73fe2a5be73319a94c45722f0`; auditor SHA256 `dc5af347f05c3adf3d7b45fdfcfb4b160a6d295d0cdf16b2b43eebf2c62fec5d`. V1 through v4 were not remotely staged or run.
- New local package: `work/loeo-primary-full-f1-v5-20260928/`, attempt `0d6cdbb84b54`, lease ID `loeo-primary-full-f1-v5-0d6cdbb84b54`.
- `full_plan.json` SHA256 `4f05dd6ca846c849ed0566b932e3453d0e9187a5b291de0bee07030ab3f98ac0`.
- 21-file `full_bundle/bundle_manifest.json` SHA256 `d60672f1df3b3f3aa0fe716b06b0760642b6e043cb7213cdaccfbd953df79219`.
- `full_control.py` SHA256 `774c0e55737fed650b3b4c4b60f4b97388d6dff302fd3c5ebaa44723c5efc157`.
- `audit_completed_full.py` SHA256 `265e5d3844d29c5ad977013fa4051d83d8df5e3f7e1df10816437fd250242fa7`.
- `test_full_local.py` SHA256 `6097a8236fb3c60c226d1c0df5e05e6e3439a565dd5be3bb79cfb513ccd1cda5`.

## Correction

Every unlaunched `RESERVED` or `RUNNING` release now writes an exclusive, fsynced `full_unlaunched_release_intent.json` **before** the queue mutation. The intent binds the immutable plan SHA, exact lease ID/token/run/GPU, exact active queue row, pinned reservation receipt or recovered row SHA, fresh empty GPU/process and absent run probe, time, and any prior waiting-cancel intent SHA. A confirmed cancel reply blocks release; a WAITING→RESERVED race may proceed through one safe release.

`_queue_release` preserves the parsed and raw stdout/stderr, including timeout and malformed-response evidence. A later reconcile seeing an active row and an existing release intent never sends another release. Exact raw `id` and `state=RELEASED`, a fresh full-identity live `RELEASED` row (`gpus=[]` allowed), and a fresh empty GPU/process/absent run probe are all required before reporting unlaunched release success. Lost, wrong or malformed replies remain unresolved even if the queue reports `RELEASED`. A release intent bars a full-training completion audit. The 28 named final checks and all v4 waiting-cancel guards remain in place.

## Local validation

- `python -B -m unittest -q test_full_local.py`: **38 tests passed**. A v4 reproducer proves two release calls after two lost-reply reconciliations for both ordinary `RESERVED` and WAITING→RESERVED; v5 makes one release call and retains the intent across both reconciliations, including an ACTIVE cancel race. Exact positive raw/live readback, wrong ID/state, physical-state rejection, intent/receipt binding, timeout and malformed reply, and all v4 cancel/source tests passed.
- No-cache `compile()` passed for all eight local Python sources.
- `python -B build_full_bundle.py validate-inputs`: 128 source, 71 outer, 13 support files.
- Post-build full byte/SHA readback passed for all 21 manifest entries, exact local source copies, plan SHA and manifest SHA. Science remains 102 fit/26 inner source `6bba`, 71 excluded outer `44b6`, 9,949/2,443 windows, 50 epochs, seed `20260930`, no warm start and unchanged quality gates.

## Remaining gates

Independent second review must accept v5 before any remote stage. The x138 assembler requires a distinct later pin update. No SSH, queue/GPU action, outer image/GEFF, Kaggle POST or OOF result occurred in this correction.
