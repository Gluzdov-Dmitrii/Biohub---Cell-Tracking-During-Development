# LOEO primary full fold 0 v1 — preregistration, 2026-09-27

**Registration state:** local plan only, before building a primary package. No SSH,
remote stage, queue request, GPU lease, training, target read, Kaggle run or POST.
This identity is `loeo-primary-full-f0-v1-20260927`, distinct from the active
secondary fold-0 job. It may be considered for launch only after that job's
lease is RELEASED and a fresh fair-queue and physically idle-GPU preflight passes.

## Evidence and hypothesis

The x138 primary checkpoint SHA256
`12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771`
and its architecture config are preserved under
`work/x138_provenance/primary_provenance/`. Its published
`ARTIFACT_MANIFEST.json` identifies a 400-epoch snapshot support pack and the
architecture, but supplies **no training invocation, movie split, seed,
learning rate, loss weights, batch size or checkpoint-selection receipt**.
The original primary's exact training recipe and embryo independence are
therefore unknown. Do not initialize from that checkpoint or describe this
experiment as a byte-identical primary reproduction.

The executable public support-pack trainer is
`work/x138_provenance/support_training/train_unet_transformer.py`, SHA256
`c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`.
Its CLI defaults are 50 epochs, LR `1e-4`, detection loss weight `1.0`,
negative-voxel weight `0.01`, 32 output channels, UNet layers `[32,64,128]`,
downsample `(1,4,4)`, window 2 and 5.0 µm pooling. Use these numeric defaults
as a fixed, transparent **primary-family refit hypothesis**. Use batch 8 and
two workers instead of CLI batch 16/eight workers because the existing sealed
A100 secondary job has verified this resource-bounded loader configuration;
this deviation is explicit, not a claim about the original primary. Set
seed `20260928`, different from the secondary's `20260927`; seed Python,
NumPy, Torch CPU and CUDA **before model construction**. Use no pretrained
weights, no partial resume, and math-only scaled-dot-product attention.

## Split, training and selection

Use the fixed nested split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`:
56 `44b6` fit movies (5,001 two-frame windows), 15 disjoint `44b6`
source-inner movies (1,314 windows), and all 128 `6bba` movies sealed as the
outer fold. Present the trainer with exactly 71 source `.zarr`/`.geff` pairs
through an isolated source view; deny target paths and foreign checkpoint
reads. The existing public trainer loads fit and inner windows, computes
padding across both source roles, evaluates the entire inner set after every
epoch, and saves `edge_predictor_best.pth` on greatest-or-equal inner
`accuracy × recall` (latest epoch on ties). Run exactly 50 complete epochs:
626 fit batches and 165 inner batches each epoch, batch 8, no `max_iters`
cap. Record every epoch, loaded ID, batch/window count, selected epoch,
checkpoint/config SHA and a finite CPU predictor load.

The fixed technical and source-inner quality gate is: exit 0 without timeout;
50 complete finite epochs; exact counts and source-only access; released lease;
selected inner accuracy `>=0.97`, recall `>=0.80`, and their product `>=0.80`.
A failure stops use of this checkpoint for outer inference. Passing the gate
only allows a separately registered full x138 inference evaluation after the
secondary and other active learned components have compatible source-only
provenance. No outer target score is part of this training attempt.

## Resources and stop conditions

Budget one A100, eight CPU, 32 GiB RAM and 8 GiB disk growth; hard child cap
32,400 seconds and lease 555 minutes. The secondary fold-0 pilot estimated
6–9 A100 hours for the same 5,001/1,314 windows and architecture; primary
stochastic training may differ. Use a fresh code directory, run directory and
lease identity. Do not overlap the current secondary Biohub lease, preempt a
foreign waiter, retry a failed attempt under the same identity, or open an
outer GEFF label. Preserve source hashes, launch intent, process identity,
release-time GPU-empty evidence and a separate independent verifier. A
transport error during later CPU checkpoint verification is inconclusive,
not an immutable training failure.

This preregistration authorizes only local package preparation and testing in
the present task. Remote stage/launch requires a later root decision. The
199 official labeled movies have been development-exposed historically, so
eventual reciprocal model-disjoint results would not be untouched OOF.
