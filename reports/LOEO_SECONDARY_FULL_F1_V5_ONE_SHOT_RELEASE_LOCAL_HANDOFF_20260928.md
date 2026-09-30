# Secondary full fold1 v5: local handoff

Local-only correction prepared 2026-09-28 under preregistration
`LOEO_SECONDARY_FULL_F1_V5_ONE_SHOT_RELEASE_PREREG_20260928.md`, SHA256
`5ee75d2e33f053170a5cc16dd0024456aa6cc95d58c98cb2e62040b0eb0769ad`.
No SSH, queue request/release/cancel, GPU use, outer data read, or Kaggle POST
was performed. V1–v4 were never staged or run. This report is a handoff for
independent second review, not approval to stage.

## Distinct immutable local package

- Directory: `work/loeo-secondary-full-f1-v5-20260928/`
- Attempt: `f99f71bed600`
- Lease ID: `loeo-secondary-full-f1-v5-f99f71bed600`
- `full_plan.json` SHA256: `bc751688641bfa0ed62d03ed1d0d4b540862612ac5c47424ef7c3042ae3a7a29`
- `full_bundle/bundle_manifest.json` SHA256: `f4ca8700b825d996cb6e2ee84366050b562778887a764de0a7c028a546021737`
- `full_control.py` SHA256: `1a1d4845106d08171a1609d91e93739c7a1b679c8969b558a0bb6024d5012622`
- `audit_completed_full.py` SHA256: `57f4ccec30cac54b13d34b45a7f804eb8b0dd17106728452805324f01384ecaf`
- `test_full_local.py` SHA256: `dc94735abed87b7e95bddf773ac18214b8cd492d15948c55995f7e4ad21ce507`

The plan retains 128 source embryos with the fixed 102 fit/26 inner split,
71 excluded outer embryos, 9,949 fit and 2,443 inner windows, 50 epochs,
and seed 20260929. The bundled trainer and quality thresholds are unchanged.
The final auditor retains the same 28 exact check names as v4.

## One-shot release correction

Both saved-reservation paths—manual release after verified process exit and
unlaunched release after verified absence—write an exclusive `open("x")`
`full_release_intent.json` before the queue release call. `_receipt` flushes
and fsyncs that intent. It binds plan and reservation hashes, exact lease ID
and token, run, allocated GPU, live queue row, process observation, physical
GPU/run-owned-process observation, and probe time. Reconcile treats an
existing intent as a read-only recovery path, so another branch cannot issue
a second release. A lost or malformed SSH reply gets a durable error receipt;
an invalid returned reply gets a raw reply receipt. Neither is credited as
release. A valid raw `id` and `RELEASED` reply still requires a fresh matching
live released row and fresh stopped process/empty GPU observation. The live
released row may have `gpus=[]`.

The inherited unreceipted request-recovery release also uses a one-shot
intent with exact token/run/GPU/recovered row, saves ambiguous response
evidence, and now requires fresh released-row and physical absence checks
before returning success. WAITING cancellation and WAITING→RESERVED race
handling remain covered by regression tests. Manual final-audit evidence is
bound to the pre-release intent and its SHA.

## Local verification

- `python -B -m unittest discover -s work/loeo-secondary-full-f1-v5-20260928 -p test_full_local.py -q`: **30 tests passed**. The saved-reservation adversarial test runs manual and unlaunched cases for timeout, wrong ID, wrong state, exact reply, wrong live row, and active GPU; each repeated reconcile makes exactly one release call.
- No-cache `compile()` succeeded for all 27 package and bundled Python files.
- Full readback verified the exact 21-file manifest set, every listed byte size and SHA256, plan/manifest hash link, plan readback and fixed scientific parameters. AST comparison verified the 28 final-audit check names equal v4.
- Sealed v4 plan, manifest, controller, and auditor hashes matched their preregistered values byte for byte after v5 implementation.

Remaining gates: independent targeted review of this v5 package, then an
explicit separate decision on remote stage/preflight. Primary fold0 remains
the sole live Biohub lease. X138 assembler pins require a separate version.
