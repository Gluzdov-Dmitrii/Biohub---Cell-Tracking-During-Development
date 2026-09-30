# V1284 source-image capture v1 — local handoff, 2026-09-28

**State:** local code and synthetic validation complete. No real fold-specific
capture plan, checkpoint read, GEFF label read, cluster stage, lease, GPU run,
head train, graph score, Kaggle action, or submission occurred.

## Pinned source and deltas

- Executed x138 notebook: `work/loeo-v1284-source-capture-v1-20260928/pinned_x138.ipynb`, SHA256 `044fe7f2524caf218f60e10c8b744d7955bf46825983b488cd982c2acb980941`.
- Its 12 executed code cells reconstruct `work/x138_original/source.py` byte-for-byte, SHA256 `eace83c4e4ec8f967aa03edf516acdbb3eb35bbcfaf02fbef93465fa26680775`. The prereg's written hash omitted one `c` in the `...35bbcfaf...` segment; the actual source and copied source both hash to the 64-digit value here. There is no executed-cell/source delta.
- Capture cells 0–1 are unchanged. Cells 2–4 are the only changed cells; cell 4 patches the public detector in its original order and stops after the predictor. Generated patched predictor SHA256: `e777b9f5e79c40c2f40a29d23ebdeaf1945a5eb33c5bf6b02645d90adf19aed0`. Generated head-free V1284 module SHA256: `db22bcf2cd7d54dda021302c281b224ef517508e53f2aaa7c75fd47b6fe11e8a`.
- `capture_cells.json` SHA256 `7561fe39f04f966721c6f8eb02514caded724b9b57fcb599b36f613283504e6e`; `capture_cells_manifest.json` SHA256 `50c40bb26a3d1661571755e33d5fbf3c47b97e2f6135ae8c0730505b5b8dbb2e`.
- Full 27-file `package_manifest.json` SHA256 `15bb00405aa8caec4090a7cb45291f02787207d8970d8b047b13bf48b543b38e`; no `__pycache__` exists inside the package. Its entries pin the copied split SHA256 `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1` and 13-file public support manifest SHA256 `a6f57ca8232e43711253326eb20356ae625ac123ba4e5d52ee4aba87c1c07d5b`.

## Local contract

`plan_capture.py` accepts only separately verified, same-fold full-training
quality audit receipts with exact source IDs, role, split, released lease,
checkpoint/config hashes and required independent checks. Fold 0 is 56 fit +
15 inner source `44b6` movies with 128 outer `6bba` IDs sealed. Fold 1 is 102
fit + 26 inner source `6bba` movies with 71 outer `44b6` IDs sealed. Plan and
work identities are unique; existing identities are rejected.

`run_capture.py` executes only cells 0–4 against an isolated source `.zarr`
view and copied audited model assets. The child audit hook denies GEFF,
opposite-prefix, published-input, direct data-root, and unapproved checkpoint
access; records loaded model/config hashes; and forbids `V1284_HEAD`.
Capture writes first-seen unshifted detector coordinates and primary 224-value
UNet features as one exclusive shard per frame, including empty `(0,4)`
integer coordinates and `(0,224)` float32 features. The detector fusion
weight is 0.80; the original first-seen and graph-policy path is pinned by
the patched predictor hash. No graph policy is executed beyond cell 4.

`verify_capture.py` requires a separately recorded release-time empty GPU
observation, exit zero, dead run process/group, released queue state, intact
model/source identities, zero denied accesses, Zarr-derived frame counts,
and exactly one valid shard per expected source `(stem,t)` with no extras.
Successful verification writes exclusive `frame_counts.json`,
`runtime_identity.json`, and hashed `capture_verified.json` for the separate
`head_refit.py seal` step. No label read is part of this verifier.

## Validation

`python -B -m unittest discover -s work/loeo-v1284-source-capture-v1-20260928 -p test_capture_local.py -v` — **7 passed**. Mock integration executes cells 0–3 with fold-1 synthetic audited model assets, and cell 4 on the pinned support predictor with a mocked subprocess. Tests cover empty/nonempty and duplicate shards, head rejection, first-seen source order, forbidden access, role/audit mismatch, missing/extra/malformed shards, release timing, and package inventory tampering. All eight package `.py` files and five capture cells AST-parse; package, split, support, source, and generated-code hashes were independently read back. No CUDA inference was run.

## Next runtime gates

Real primary and secondary quality-passing audited checkpoints for the same
fold are required before creating each plan. A controller still must supply
fair-queue eligibility, physical-idle A100 check, source/checkpoint readback,
one bounded launch, and durable release receipt; none is included or claimed
here. The later Linux environment needs the x138 predictor dependencies,
including `IPython` for an unused executed-cell import. Windows denied source
symlink creation (`WinError 1314`), so source-view symlink creation and actual
Zarr frame-count reads remain runtime checks. Do not proceed to source GEFF
label matching until the independent capture verifier passes. The separate
head refit, opposite-embryo images-only outer run, serialization choice, and
graph scoring remain future steps under the preregistration.
