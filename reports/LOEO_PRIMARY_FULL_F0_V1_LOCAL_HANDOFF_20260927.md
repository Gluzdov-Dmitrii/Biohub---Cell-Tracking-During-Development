# LOEO primary full fold 0 v1 — sealed local handoff, 2026-09-27

**State:** local preparation and validation complete. No SSH, remote stage,
queue request, GPU lease, source/target data access, Kaggle run or competition
POST was performed. The active secondary fold-0 A100 lease must release before
this package is considered for a new reservation.

## Fixed hypothesis and evidence limit

Preregistration: `reports/LOEO_PRIMARY_FULL_F0_V1_PREREG_20260927.md`,
SHA256 `814ce78243c9b4210bde80167e69a70ab55ca51cc0a50ee20d05a2e916529df4`.
The published x138 primary artifact has architecture/weight identity, but no
training invocation or embryo split. Its manifest SHA256 is
`bc20f1f04cfb682af3b27a836ce9a57f44a2fe27508dc59039200b2a23188103`;
its weight SHA256 is `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`.
That weight is provenance metadata only and is **not** a warm start. This
package fixes the public trainer's numeric defaults for LR `1e-4`, detection
loss `1.0`, negative loss `0.01`, 50 epochs and architecture; batch 8/two
workers are the explicit single-A100 resource deviation from CLI defaults.
Its seed `20260928` is distinct from secondary fold-0 seed `20260927`.

## Sealed package

- Local directory: `work/loeo-primary-full-f0-v1-20260927/`.
- Immutable plan: `full_plan.json`, SHA256
  `589fb15b6440054c9f05e8fb53c3bfee747d917eb4f69f990ef336c65647cb6b`.
- Exact 20-file bundle: `full_bundle/bundle_manifest.json`, SHA256
  `ff9b0f67007057cbc1e381014144ce3afd147f41bdc8b2635304bc0b210f2990`.
- Unique attempt `eabbee582c77`; lease
  `loeo-primary-full-f0-v1-eabbee582c77`. Planned code and run are
  `code/loeo_primary_full_f0_v1_eabbee582c77` and
  `runs/loeo_primary_full_f0_v1_eabbee582c77` under the pinned Biohub remote
  project root. Neither path has been created by this preparation.
- Same nested split as the secondary fold-0 package: 56 source fit movies /
  5,001 windows and 15 disjoint source-inner movies / 1,314 windows. All 128
  `6bba` IDs are excluded from the 71-pair training view. Expected full epoch
  coverage is 626 fit and 165 inner batches. No outer image or label is used.
- The public support-pack trainer/predictor remain byte-identical to the
  secondary sealed source. The remote runner is role-isolated, seeds Python,
  NumPy and Torch before constructing the model, enforces math-only SDPA and
  source-only pathname/loader guards, records each epoch and chooses the
  latest maximum inner accuracy × recall. Output must be CPU-loadable and
  finite. Fixed quality gate: selected inner accuracy at least `0.97`, recall
  at least `0.80`, product at least `0.80`.
- The stage/launch controller checks exact plan and bundle bytes, fresh
  code/run/lease identity, common queue, foreign waiters and physical A100
  idleness. Supervisor persists the GPU-empty release-time observation before
  lease release. The separate completion verifier treats transport/CPU probe
  errors as inconclusive without writing an immutable failure receipt.

## Local validation and next gate

`python -B work/loeo-primary-full-f0-v1-20260927/test_full_local.py` passed
10 tests. `validate-inputs` found all 13 pinned public support files and the
71/128 source/outer catalog. Nine local Python files AST-parse. A local
`full_control.read_plan()` reread and verified the exact 20 bundle files,
plan hash, preregistration and source identities; no SSH path was invoked.

After root review and **after secondary lease release**, the intended order
is a fresh `full_control.py --preflight`, `stage`, and `launch`, then finite
observation/reconciliation and `audit_completed_full.py`. Stage or launch is
not authorized by this handoff. A completed primary checkpoint alone is not
assembled-x138 OOF, does not establish a 0.9 score, and does not authorize
target-label read or competition submission.
