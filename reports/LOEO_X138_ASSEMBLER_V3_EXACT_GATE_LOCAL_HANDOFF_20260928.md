# x138 reciprocal assembler v3 — exact gate and image identity local handoff

Date: 2026-09-28 Asia/Novosibirsk. Governing preregistration:
`reports/LOEO_X138_ASSEMBLER_V3_EXACT_GATE_CORRECTION_PREREG_20260928.md`
SHA256 `4b6338811aa44ce3a924d5448a3399f1961cd43f58fcae3034f3738886d18272`.
The rejected, unstaged v2 package was preserved unchanged at manifest SHA256
`876894ec27d5e4b9c43827787d566554a34f10882fda57281b2ba8d026c5d9a3`.

## Seal and implementation

New local package:
`work/loeo-x138-assembled-reciprocal-v3-20260928/`.
`sealed_package_manifest.json` SHA256
**`6554e44c5a8320b8bc51eb832fb8649197bc75f29f6507a0d30ace7b6c96c77f`**,
57 listed file hashes including the preregistration and 56 package files.
`assemble.py` SHA256 `a8d676ac0e7ef49035e3288fddf15e9e7b6dccea28acbee1579944ce5b2c0a9c`;
`fixture_v3.py` SHA256 `48e633cc2a0b5ba8fe36e2c05c5f6220655de346f71f9506f7a1e598aa30fa1d`;
`test_assemble.py` SHA256 `e19b414af3c6d0e4dce06c2e61a727154d7739e23fd221c634d8b915ecb566a7`.

The primary and secondary gates require exact 27 true named checks in fold0
and exact 28 in fold1. DeepCenter requires exact 16. Missing, extra and
non-true entries fail. The secondary fold0 release gate requires its exact
supervisor (8 checks) or manual (9 checks) branch, `failed_checks=[]`,
matching lease/run/GPU/exit SHA, and the saved raw RELEASED reply. A manual
branch also needs a copied release receipt with its exact byte SHA. The
V1284 nested schema and all reviewed source/manifest pins remain from v2.

Both generated runtime preflight and local `check_output` now require each
chunk alias `<ID>.zarr` to resolve to a directory with the same basename,
within the allowed image root. Existing exact alias-name inventory and
source-only chunk IDs remain. No image pixels or GEFF labels are read by
these checks.

## Verification

`python -B work/loeo-x138-assembled-reciprocal-v3-20260928/test_assemble.py -q`
passed **21 tests**. They include positive nested receipt bundles in both
folds, both release branches, exact check-set cardinalities, and a direct
read of the actual local secondary fold0 full/release receipts (SHA256
`6e0db16db9d2398e3f21be7ac9198013b2b399de5ef19f42d479702c3ac1d768`
and `157c445e51274ab9bf3c92eb5ec880980417f853308fd1e0d2a7fe475fb0238b`),
which pass the v3 exact gate. Adversarial tests first reproduce v2 acceptance
of omitted/extra true audit checks and fake release fields, then show v3
rejection. They also show that v2 accepts a 6bba chunk alias pointing to a
different 6bba movie or to a 44b6 source movie inside the allowed root,
while v3 rejects each in both generated preflight and local `check_output`.
Temporary Windows directory junctions exercised these alias cases because
this host lacks symlink creation privilege; Linux uses directory symlinks.
Synthetic assembled source for both folds compiled in memory.

Ten frozen inference/chunk/aggregate function ASTs match v2, including
`assemble_text`; the 52 plan and chunk files are byte identical. This
preserves the x138 graph policy, x162 final coordinate clamp, 50 fresh-process
chunks and all 199 sealed outer IDs. Manifest readback rehashed each entry,
confirmed the v2 parent seal, compiled all three Python files in memory and
found no bytecode cache. No production source was emitted.

## Remaining gates

Independent read-only review of this v3 package is required before source
emission. Real fold-matched source-trained primary, secondary, V1284 head and
DeepCenter checkpoints and their independently audited capture/training/release
receipts are still required for both folds. Then run 50 fresh image-only outer
processes, verify exit0 and no deadline degradation or repair fallback, lock
all prediction hashes and measure full-candidate runtime before separate
outer-label scoring. The historical public x138 0.953 leaderboard score is
not honest reciprocal OOF; no 0.9+ OOF result exists from this package.

This task used only local source and receipt files. It did not use SSH, GPU,
real target images, GEFF labels, Kaggle, or edit `EXPERIMENTS.md`.
