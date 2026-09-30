# LOEO primary full fold 1 v1 — sealed local handoff, 2026-09-27 UTC

**State:** local package and tests complete. No SSH, remote stage, queue
request, A100 lease, GPU training, outer `44b6` image or label read, Kaggle
action, or `EXPERIMENTS.md` edit occurred. Future stage/launch requires a
separate root decision and fresh fair-queue/physical-idle checks.

## Fixed experiment and source evidence

Preregistration was saved before implementation at
`reports/LOEO_PRIMARY_FULL_F1_V1_PREREG_20260928.md`, SHA256
`f644475d7f0fe0e4e3873caf434f9af8aad6a7927734661ef7753827e2f82a14`.
Fold 1 of the pinned split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`
has 102 `6bba` fit, 26 disjoint `6bba` source-inner and 71 sealed outer
`44b6` movies. The independently rehashed source-only metadata receipt SHA256
`584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`
matches all 128 source IDs and gives 9,949 fit / 2,443 inner windows,
1,244 / 306 batches at batch 8. No target labels were opened during this
preparation. The trainer and predictor in the sealed bundle retain the public
SHA256s `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`
and `c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`.

The published x138 primary weight lacks a split or invocation receipt. Its
SHA256 `12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
is pinned as provenance **only**, never loaded or used as a warm start.
Published primary manifest/config SHA256s are
`bc20f1f04cfb682af3b27a836ce9a57f44a2fe27508dc59039200b2a23188103`
and `e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`.

## Sealed package

- Local directory: `work/loeo-primary-full-f1-v1-20260928/`.
- Immutable plan: `full_plan.json`, SHA256
  `b2d78b51f16b2ef38fc2ee3ddbad24bc2e9f80411b7112273767f1a50fa7869c`.
- Exact 21-file bundle: `full_bundle/bundle_manifest.json`, SHA256
  `8bfda46f6755089f158a1d87abfb00e560ec8afe12b526fc4a3912793279476f`.
- Unique attempt `dd06287e66ca`, lease
  `loeo-primary-full-f1-v1-dd06287e66ca`, planned remote code/run paths
  `code/loeo_primary_full_f1_v1_dd06287e66ca` and
  `runs/loeo_primary_full_f1_v1_dd06287e66ca` beneath the pinned Biohub
  project root. These paths were **not** created here.
- Training: random initialization, seed `20260930` before public trainer
  import/model construction, 50 full epochs, public numeric defaults,
  batch 8/two workers, math-only SDPA, one A100, no data parallelism or
  `max_iters`, and latest maximum source-inner accuracy × recall selection.
  Fixed selected inner gate: accuracy `>=0.97`, recall `>=0.80`, product
  `>=0.80`.
- Resources: one A100, eight CPU, 32 GiB RAM, 8 GiB disk growth;
  64,800-second hard child cap and 1,110-minute lease. Source-only symlink
  view, pathname/socket audit, launch intent, fair-queue control, bounded
  wrapper, release-time GPU-empty observation and separate completion audit
  follow the fold-0 hazard corrections. The completion audit treats a
  transient transport/CPU predictor failure as inconclusive, not a final
  training failure.

Key local source SHA256s: `full_contract.py`
`4b96f2f505305a97f17c4c08348acd772d4a05abbf6be42b7bce8a0970233e1e`,
`run_full.py` `2278ace9041d0c820683a639c3953b95c8453514165d9e1ab1b05708af547057`,
`full_control.py` `e5ce2a3c0bfa9b18496ad5a227150fcb6bce08b941ebfbb65ca769d676876f8c`,
`audit_completed_full.py` `32479bb6fababab765260c86438f8c6942a0b915b4b4a0ffcbda0a4d3ae19534`.
The wrapper/supervisor bytes remain identical to the sealed secondary fold-1
control sources; the primary role, provenance pins and seed differ.

## Local validation and next gate

`python -B .../build_full_bundle.py validate-inputs` passed with 13 public
support files, 128 source and 71 outer IDs. `python -B .../test_full_local.py`
passed **11/11** focused tests. All nine local Python sources AST-parse.
`full_control.read_plan()` and `verify_bundle()` passed exact plan, 21-file
set, file hashes, source metadata, trainer/predictor identities, prereg
copy and role/seed assertions; there are no `.pyc` files in the seal.
Tests and final seal verification were local-only and did not call SSH.

Before any later remote stage/launch, root must refresh the secondary
fold-0 lease state (last `EXPERIMENTS.md` receipt had it RUNNING), the common
fair queue and physically idle A100s, then independently review the fixed
identity and remote path/source readback. Do not stage or reserve while a
different project waits or another Biohub lease is active. After a completed
run, require the independent artifact/lease audit and fixed source-inner
gate before any outer inference. This component alone supplies no assembled
x138 OOF or evidence of a 0.9+ score.
