# LOEO primary full fold 1 v1 — preregistration, 2026-09-27 17:35 UTC

**Registration state:** local evidence review only, before implementing this
primary fold-1 package. Unique identity `loeo-primary-full-f1-v1-20260928`.
No SSH, remote stage, queue request, GPU lease, training, outer `44b6` image
or label read, Kaggle action, or `EXPERIMENTS.md` edit is part of preparation.
This is a source-only primary refit, not assembled x138 OOF or a 0.9+ claim.

## Fixed hypothesis and source identities

The published x138 primary weight SHA256
`12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
has architecture identity but lacks a training invocation, embryo split,
selection receipt, and seed. Preserve it only as provenance; **do not warm
start or resume from it or from fold 0**. The public trainer
`work/x138_provenance/support_training/train_unet_transformer.py` has verified
SHA256 `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`;
the public predictor SHA256 is
`c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`.
The 13-file support source manifest SHA256 is
`a6f57ca8232e43711253326eb20356ae625ac123ba4e5d52ee4aba87c1c07d5b`.
The published primary artifact manifest and config were independently
rehash-checked at `bc20f1f04cfb682af3b27a836ce9a57f44a2fe27508dc59039200b2a23188103`
and `e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`.
This fixed public-default recipe is a transparent primary-family refit
hypothesis, not a byte-identical reproduction of the unknown published run.

## Reciprocal split and source-only data

Use the immutable nested split
`work/x138_loeo_bootstrap/dataset_splits_nested.json`, SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.
Fold index 1 fits 102 `6bba` movies and selects on 26 disjoint `6bba`
source-inner movies. Seal all 71 `44b6` movies as outer targets. Present the
trainer with exactly 128 `6bba` `.zarr`/`.geff` pairs through a fresh isolated
source view; resolve every symlink to the approved existing source parents,
preserve ID/suffix, deny any `44b6` path, and deny external or pretrained
checkpoints. Do not open an outer image or label in this training attempt.

The read-only source metadata receipt
`work/loeo-secondary-full-f1-v1-20260928/source6_window_metadata.json`,
SHA256 `584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`,
was independently checked against the pinned split: 128 unique `6bba` IDs,
no fit/inner overlap or missing ID, 9,949 fit two-frame windows and 2,443
inner windows. Its recorded opened prefixes are only `6bba`, with
`opened_44b6_labels=false`. This is source-label metadata, not outer score.
At batch 8, exact full coverage is 1,244 fit and 306 inner batches per epoch.

## Fixed training, selection and gate

Start from random initialization. Seed Python, NumPy, Torch CPU and CUDA with
integer `20260930` **before importing the trainer or constructing the model**,
and pass the seed to the DataLoader. This differs from primary fold 0
(`20260928`) and secondary fold 1 (`20260929`). Preserve the public trainer,
predictor, architecture and augmentation files byte-for-byte. Run exactly 50
full epochs, no `max_iters` cap, no dropped last batch, and no early stop.
Use one A100, batch 8, two DataLoader workers, math-only scaled-dot-product
attention around the entire trainer call, no data parallelism, LR `1e-4`,
detection loss weight `1.0`, negative weight `0.01`, UNet layers `[32,64,128]`,
32 output channels, downsample `(1,4,4)`, two-frame windows, and 5.0 µm
pooling. Batch/workers are the declared single-A100 resource deviation from
the public CLI defaults.

The unchanged trainer selects `edge_predictor_best.pth` by greatest-or-equal
source-inner `accuracy × recall`, so exact ties select the latest epoch.
Verify 50 finite fit/inner rows, every epoch's exact windows and batches,
loaded source IDs, selected epoch and score, finite CPU load through the
public predictor, and checkpoint/config/source hashes. The fixed source-inner
quality gate is selected accuracy `>=0.97`, recall `>=0.80`, and product
`>=0.80`. A failed gate stops this checkpoint before outer inference; a pass
only permits separate full-assembly preregistration.

## Resource and safety boundary

Budget 12–17 A100 hours plus loading variance for approximately twice fold
0's fit windows; set a hard child cap of 64,800 seconds and lease of 1,110
minutes, one A100, eight CPU, 32 GiB RAM and at most 8 GiB disk growth.
Use a fresh code/run/lease identity. Before any future remote action, a root
operator must independently check the common fair queue and physical A100
idleness; defer while another project waits or another Biohub lease runs.
Do not preempt, auto-requeue, overlap training leases, or reuse an identity
after failure. Preserve source readback, launch intent, process identity,
durable release-time GPU-empty evidence, and a separate independent artifact
and lease audit. A transient transport or CPU predictor check is inconclusive
without an immutable failure receipt.

This preregistration authorizes **local package construction and tests only**.
No remote stage/launch, outer target label access, or Kaggle submission
follows from it. Historically exposed training labels limit any eventual
reciprocal result to model-disjoint development transfer evidence.
