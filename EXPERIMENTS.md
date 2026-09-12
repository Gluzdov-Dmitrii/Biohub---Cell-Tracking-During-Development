# 2026-09-09 private-first continuation — reliable local OOF and publication notebook

The primary objective is post-close private performance, not short-term public
LB rank. Every new notebook header must state that model selection is based on
embryo-level LOEO/OOF stability, worst-fold behaviour and same-sign paired
deltas; public LB is only a hidden-runtime and gross-regression check. The user
authorizes up to five Kaggle submissions, but the standing portfolio remains
non-interchangeable: slots 1-2 are `GOLD_PUBLIC`, slots 3-5 are
`PRIVATE_ROBUST`. This authorization does not waive per-candidate gates or
permit a correlated sweep. RTX6000 jobs remain one-at-a-time under the common
atomic lease.

## EXP129 — RTX6000 frozen-OOF baseline reproduction (no submission)

Hypothesis: before changing the model, the external RTX6000 environment and
downloaded labels must reproduce the frozen EXP009/EXP011 embryo-disjoint
baseline on available untouched `44b6` movies. The checkpoint was trained only
on `6bba`; threshold `0.985` and registered-Hungarian policy were frozen by
EXP011 before its untouched audit. The available remote pilot contains exactly
the first four EXP011 audit movies plus four checkpoint-selection movies. EXP129
evaluates only the four audit movies, skips unavailable confirmation movies,
compares the already frozen linker arms on identical detections, and exports
candidate caches for later CPU-only ensemble/linker work. It performs no
threshold selection and has no LB submission authority.

Integrity preflight found the remote EXP009 checkpoint was truncated to
5,865,472 bytes with SHA
`2c4110b9b4c96a30b525f3cc7e4f5cb4f50318a60ae6ca0f875b44c92017ae98`.
The corrupt file was atomically replaced from the verified local artifact;
the required contract identity is 8,357,783 bytes and SHA
`eebb8eaa9fe0ca02a9957ac97ab51d84ee8f162fb17a175a04a66d9ef9134382`.
The reciprocal EXP010 remote checkpoint already matches its contract SHA
`0e0543250ec241aeebcd225947ff9a209ad8e897a069c81553a001415fabccad`.
EXP129 source is `scripts/external_oof_44b6.py`; the run must use math SDPA on
one Quadro RTX6000, preserve per-movie sufficient statistics/cache SHA values,
and release the lease on completion. Promotion gate is reproduction quality
only: compare the four-movie aggregate and per-movie values with the immutable
full EXP011 audit; any contract, data-count, graph or metric anomaly stops the
model-development lane.

### EXP129 result

The one-GPU RTX6000 run completed under the common atomic lease, used forced
math SDPA, and released the lease immediately afterward. The result artifact
is `outputs/research/exp129_oof_repro_44b6_20260909/loeo_44b6_model_comparison_result.json`,
921,400 bytes, SHA-256
`e778940d79a9ffb84efb5151b731553f496c2073798482a7e2c733b70d6bae1f`.
Registered Hungarian scored `0.8255500924`; the frozen 10% learned tie-break
scored `0.8333342882`, delta `+0.0077841958`, with identical node recall
`0.9617421024`. Probability-heavy registered linking (`0.5127817247`), public
ILP (`0.5353571201`) and support ILP (`0.6191316085`) were rejected. All four
registered per-movie rows exactly reproduce immutable EXP011 and all weak-arm
rows exactly reproduce EXP050, so the repaired checkpoint, remote data and
RTX6000 implementation pass the reproduction gate.

This pilot has no division events and substantially overstates the weak-arm
effect: its `+0.0077842` delta is about 10.6 times the full 63-movie 44b6
audit delta `+0.0007339`. It is therefore useful as an environment and
data-integrity validation but is not sufficient evidence for private-model
selection. The durable receipt is `reports/exp129_oof_repro_20260909.json`;
no Kaggle slot was consumed.

## EXP130 — corrected compute-matched initialization test (pre-registered; no submission)

Parent is the independently trained EXP026 Zebrahub checkpoint, but the exact
fine-tune initializer is its 74-key UNet-only extraction, 6,013,480 bytes, SHA
`0aa004c64252e86e115249a75974be93023c859f632e758f4f87294f18bd6037`.
Remote receipt SHA is
`25fea0212593e0a0e2633c664c0bbdc89d2efe437c4c04c6061b4d4999f91701`.
The prior EXP027 log was rechecked and does show `0 missing, 0 unexpected`, so
its public `0.616` result remains a valid negative result; a temporary concern
about namespace mismatch was disproved by the exact remote artifact receipt.

Hypothesis: under a truly compute-matched, reciprocal embryo-domain protocol,
the Zebrahub UNet initialization improves target-embryo development score over
scratch in both directions. Each arm uses seed `314159`, five full epochs,
batch size `2`, four workers, downsample `(1,4,4)`, learning rate `1e-4`, the
same architecture and identical linker policy. For each direction, the first
10 lexicographic source-embryo movies train the model and the final two source
movies select its checkpoint. No target-embryo movie participates in fitting
or checkpoint selection. The first four target movies form a development
stress test; the final eight remain locked until the model, detector threshold
and linker policy are frozen. The split/audit builder is
`scripts/build_official24_private_splits.py`, SHA
`ea37ed9c152f2fa78e433f25114324fe3bf572c92ba77a19a633f20f3cddad6e`.

The reproducible trainer source is the support-pack trainer with explicit
Python/NumPy/Torch/CUDA seeding, worker-derived augmentation RNG, deterministic
algorithm warnings and fail-closed pretrained-key validation; SHA is
`07b3c369114d34418d067fd80d4a436760563338cf491c54109fb109ccb3eebf`.
It accepts either the verified 74-key UNet extraction or a full checkpoint by
extracting only the `unet.` namespace; any missing or unexpected key aborts.
Only one RTX6000 process may run at a time under the common atomic lease.

Gate to open the locked audit: Zebrahub-minus-scratch must be nonnegative on
both reciprocal four-movie development folds and positive pooled, without a
catastrophic source-validation reversal. Final private-robust promotion then
requires same-sign reciprocal deltas on the two locked eight-movie audits,
positive pooled sufficient-statistic score, acceptable worst-fold and
per-movie stability, and no node-recall/division regression. With only two
embryo domains, movie bootstrap is conditional finite-sample uncertainty, not
a population confidence interval for unseen embryos. EXP130 has no direct LB
submission authority; any later notebook candidate needs its own clean
Internet-off runtime audit and guarded receipt.

### EXP130 pre-run environment correction

The first queue-managed scratch attempt stopped before training because the
project-local `TMPDIR` plus Python multiprocessing listener suffix exceeded
Linux's AF_UNIX path limit. Parent PID `125502` and its four orphaned
DataLoader workers were explicitly stopped, RTX6000 returned to 5 MiB / 0%,
and queue request `biohub-exp130-scratch44b6-20260909` was released only after
the complete process tree was verified absent. No checkpoint or model score
was produced. The retry and every compute-matched arm use `num_workers=0`,
which removes multiprocessing sockets while keeping temporary files in the
registered project root. This correction was frozen before any EXP130 model
result; all other configuration and promotion gates are unchanged.

The `num_workers=0` retry then reached the first CUDA batches but emitted
CuBLAS reproducibility warnings before completing epoch 0 because
`CUBLAS_WORKSPACE_CONFIG` was unset. It was stopped before any checkpoint or
selection score, PID `126000` was verified absent, GPU returned to 5 MiB / 0%,
and queue request `biohub-exp130-scratch44b6-nw0-20260909` was released. The
final retry freezes `CUBLAS_WORKSPACE_CONFIG=:4096:8` for scratch and every
initialized arm. This second pre-result correction closes the deterministic
seed contract without changing model/data/hyperparameters.

Runtime validation subsequently showed a remaining PyTorch limitation shared
by both compute-matched arms: `upsample_trilinear3d_backward` and
`max_pool3d_with_indices_backward_cuda` do not have deterministic CUDA
implementations. Seed, data order, one GPU UUID and CuBLAS workspace are fixed,
but bitwise training reproducibility cannot be claimed. The paired comparison
may reject a clear effect; any small promotion-sized delta requires a repeat
seed/run before the locked audit or publication claim.

### EXP130 first-seed result and development decision

Both five-epoch arms completed on the same queue-managed Quadro RTX6000 and
released their leases after PID/GPU checks. Scratch selected source-validation
score `0.8628` and checkpoint SHA
`dc06a79401671b2acc7ad36e8db19316f51d11676ba46508c356839df682fdbb`;
Zebrahub initialization selected `0.8399` and checkpoint SHA
`2ec65d049fcb23634060923047607699bf1c64183b523b9c102cbc1b3e44a346`.
Both checkpoints are 8,357,362 bytes. The initialized arm loaded the exact
74-key payload with `0 missing, 0 unexpected`; neither log contains a runtime
error, and each contains only the two predeclared non-bitwise-deterministic
CUDA backward warnings.

On the four target-development `6bba` movies, with the frozen `0.985`
detector threshold and registered Hungarian linker, scratch scored
`0.6275335233` and Zebrahub initialization scored `0.6294409207`, delta
`+0.0019073975`. Per-movie adjusted-edge deltas are `+0.0018234094`,
`-0.0069007802`, `-0.0205726371`, and `+0.0464131323`: two positive and two
negative. Node recall improves `0.9631207004 -> 0.9713970448`, but the score
effect is too small and heterogeneous to open the locked audit. The already
frozen weak learned tie-break scores `0.6272461253 -> 0.6300393815`; it remains
descriptive because it is not uniformly better than registered linking.
No Kaggle slot is authorized or consumed by this result.

## EXP131 — repeat-seed stability check (pre-registered; no submission)

Because EXP130's effect is small relative to its per-movie dispersion and the
known CUDA nondeterminism, repeat the exact scratch-versus-Zebrahub pair with
seed `271828`. Data, 10/2 source split, five epochs, architecture, optimizer,
batch size, worker count, detector threshold, registered linker and hardware
remain unchanged. Run both arms and their four-movie evaluation sequentially
inside one queue allocation. The repeat supports this direction only if the
registered Zebrahub-minus-scratch delta is nonnegative for seed `271828` and
the two-seed pooled direction remains positive; otherwise reject Zebrahub
initialization before reciprocal training. Do not inspect the eight locked
target movies and do not use an LB submission. The weak-linker arm is a frozen
secondary diagnostic and cannot rescue a negative registered result.

EXP131's first allocation completed the seed-`271828` scratch arm (selected
source-validation score `0.8233`) and then stopped before initialized model
construction: the launcher changed working directory to `tracking_repo` but
retained the initializer path relative to the prior run root. The resulting
`FileNotFoundError` occurred before `torch.load`, so there is no partial
Zebrahub checkpoint or score. PID `128754` and GPU use were verified absent
before release. The continuation uses the exact existing scratch checkpoint,
an absolute initializer path whose SHA is checked, and runs only the missing
initialized arm plus both frozen development evaluations. This operational
path correction changes no data, seed, model or gate.

### EXP131 result

The continuation loaded the exact initializer (`0 missing, 0 unexpected`),
completed without runtime errors and released the RTX6000 lease after process
and GPU checks. Seed `271828` scratch selected source-validation `0.8233`,
checkpoint SHA `50934d7c292bc97a1e07a95c2a5c6458cdb9c6e11ffb08e566ecb88f4d372326`,
and target-development score `0.6295225359`. Zebrahub initialization selected
source-validation `0.8460`, checkpoint SHA
`19cc6d0523cf3323210ecc81218368e1e6244dba5a9d2f5e68bb503f12efb69f`,
and target score `0.6711156817`: delta `+0.0415931459`. Its four paired
movie deltas are all positive: `+0.0524692724`, `+0.0366939120`,
`+0.0231403642`, `+0.0580232799`; node recall also improves
`0.9485082112 -> 0.9657465453`.

The initialization direction is therefore positive in both seeds
(`+0.0019073975`, `+0.0415931459`) and passes the seed-stability requirement
for this one embryo direction. The large effect-size variation remains an
important uncertainty signal. Locked `6bba` audit stays closed because the
reciprocal `6bba -> 44b6` development fold is still required by the original
gate. No Kaggle submission is authorized or consumed.

## EXP132 — fixed detector-consensus ensemble (pre-registered; no submission)

Reuse the already exported EXP130 development candidate caches; perform no
new neural inference and do not read locked movies. Transfer the verified open
coordinate-consensus mechanism from H057/EXP014: within each frame, mutual
nearest-match scratch and Zebrahub detections at `<2 µm`, move matched base
detections halfway (`alpha=0.5`), retain unmatched base detections and preserve
the base model's registered-Hungarian edge topology exactly. Evaluate two
predeclared topology bases (scratch and Zebrahub) because the coordinate sets
are not identical. This is one symmetric mechanism comparison, not a weight
sweep. Promote only if an ensemble exceeds the better single-model pooled
score and is nonnegative against that parent on every development movie;
otherwise reject before reciprocal/locked evaluation. Candidate-cache/result
hashes and exact match counts must be preserved. No Kaggle submission authority.

### EXP132 result

The CPU-only cache evaluation passed source/hash/runtime checks. Scratch-base
consensus scored `0.6293397177`; Zebrahub-base consensus scored
`0.6315026679`, which is `+0.0020617472` above its stronger single-model
parent. However, its paired per-movie deltas versus that parent are
`+0.0111780529`, `+0.0039022649`, `+0.0030978883`, and `-0.0132477957`.
The predeclared all-movie nonnegative gate therefore fails. Match coverage is
78.81–87.21% of base detections; mean disagreement is 0.260–0.340 µm and p95
is 1.625 µm. Preserve the mechanism and result SHA
`7838dbd9887c1402aa26cf7f927b22ddf180a13d32f67eeffb40e569bb3a4739`
as useful evidence, but do not open locked audit or submit it.

The identical fixed mechanism was then applied descriptively to EXP131's
second-seed caches. Zebrahub-base consensus scored `0.6746626389` versus its
parent `0.6711156817`, pooled delta `+0.0035469572`, but per-movie deltas were
`+0.0131786624`, `-0.0025545371`, `+0.0058620730`, and `-0.0038360601`.
Thus pooled direction repeats across seeds while per-movie stability again
fails (this time on two movies). Result SHA is
`8de68211d9880ac8be6df3767c5290f257c4957fed26a973edbe477bbed52b49`;
the reject decision is strengthened, not reversed.

## EXP133 — private Kaggle data pack for reciprocal OOF (pre-registered)

The official per-file competition API downloader is live and resumable but is
being throttled after roughly six files per five minutes. Six of twelve `6bba`
movies are already complete and exact-size checked. To finish the reciprocal
fold without spending many hours on transport overhead, run one private,
Internet-off, CPU Kaggle notebook with the competition source attached. It may
only archive the six still-missing movie pairs (`3abfe10a`, `784a78c9`,
`7b5d3b2c`, `7d3058ae`, `aeee7805`, `cff5865f`) into deterministic 512 MiB
parts and emit a source/part manifest with SHA-256. It must not compute metrics,
inspect tracks, train a model or create a submission. After download,
reconstruct and verify the full tar SHA, extract only under the local project,
validate every file against the frozen official manifest, then transfer under
the registered remote Kaggle project root. The slow downloader is stopped only
after the private kernel is accepted; all partial progress remains reusable.

The local private packer source and metadata passed JSON/Python validation,
but no Kaggle version was created: the execution environment rejected the
kernel push because exporting competition payloads requires a separate,
explicit risk acknowledgement for the data and destination. This control is
not bypassed. The official resumable per-file downloader remains active; no
competition data was uploaded, no Kaggle compute was started and no submission
quota was consumed by EXP133.

## EXP134 — source-selected dual-seed coordinate consensus (pre-registered)

Combine only the two completed Zebrahub-initialized seed models. Select seed
`271828` as topology base solely because its source-embryo checkpoint score is
`0.8460` versus `0.8399` for seed `314159`; target score is not a selection
input. Preserve its registered-Hungarian links exactly. Mutual-nearest match
same-frame detections from the other seed at `<2 µm` and average matched
coordinates with fixed `alpha=0.5`; retain unmatched base nodes. This adapts
the verified dual-seed/coordinate-consensus idea from open EXP004/005/014 but
uses our independently trained checkpoints and honest target-development
evaluation. Promote only if pooled score exceeds the selected base and every
movie delta is nonnegative. No locked data or Kaggle submission authority.

### EXP134 result

The selected-base ensemble scored `0.6764188959` versus seed-`271828` parent
`0.6711156817`, pooled delta `+0.0053032142`. Per-movie deltas are
`-0.0006438457`, `+0.0007673569`, `+0.0124721166`, and `+0.0095747539`.
Although three movies and pooled score improve, the first movie is negative,
so the exact predeclared gate fails. Preserve result SHA
`b386f3c5c0bf194882c8ca0d785688cde9d99642167180aef0719edcb7b5679c`
as evidence that dual-seed coordinate consensus is promising but not yet
private-robust; do not open locked audit or submit.

## EXP135 — lower-LR pretraining retention (pre-registered; no submission)

Both Zebrahub-initialized seeds select an early source checkpoint and then lose
source recall, suggesting that `1e-4` may forget external detector features too
quickly. Starting from the same verified 74-key initializer and seed `271828`,
change only learning rate from `1e-4` to `5e-5`; retain the exact 10/2 source
split, five epochs, batch size 2, architecture, losses, deterministic controls,
source-only checkpoint selection, detector threshold `0.985` and registered
linker. Compare against EXP131 seed-`271828` initialized parent on the same four
development movies. Promotion requires positive pooled score, no negative
movie delta, and no node-recall regression. Locked audit and Kaggle submission
remain unauthorized regardless of this one-direction result.

### EXP135 result

The run completed cleanly and released the RTX6000 lease. Source-only
checkpoint selection peaked at `0.7351`; checkpoint SHA is
`a79ed6877b2d9a63ec395cbabcfe10151b59ed14764678155adb1a59e1649e79`.
Target-development registered score improves from the seed-`271828` parent
`0.6711156817` to `0.6908211466`, delta `+0.0197054648`, with four positive
movie deltas: `+0.0710209661`, `+0.0015889342`, `+0.0074690803`, and
`+0.0020160494`. However, mean node recall falls from `0.9657465453` to
`0.9558069956` (`-0.0099395497`). The predeclared no-recall-regression gate
therefore fails. This is useful evidence that slower fine-tuning trades recall
for adjusted-edge precision under domain shift, but it is not promoted to
locked audit or Kaggle submission.

## EXP136 — full Zebrahub model transfer (pre-registered; no submission)

Read-only compatibility audit shows that the independent EXP026 full checkpoint
and the competition model have exactly the same 136 state keys and tensor
shapes (`136/136`, zero shape mismatch). Test whether transferring the temporal
transformer/detection head together with the U-Net improves association beyond
EXP131's U-Net-only initialization. Use seed `271828`, LR `1e-4`, five epochs
and every other EXP131 data/training/evaluation setting unchanged. The new
trainer option `--model-weights` is mutually exclusive with `--unet-weights`,
unwraps an optional `model` container and fails on any missing/unexpected key.
Its source SHA is
`38f8f73b9619944da8edc88e807798c876925a53c912047cf6037c57f347fe2c`;
the exact prior trainer is preserved remotely at SHA
`07b3c369114d34418d067fd80d4a436760563338cf491c54109fb109ccb3eebf`.
Promotion requires positive pooled score versus the seed-`271828` U-Net-only
parent, no negative movie delta, no node-recall regression and a clean strict
`136/136` load. Locked audit and Kaggle submission remain unauthorized.

### EXP136 result

The strict full checkpoint load passed (`0 missing, 0 unexpected`), training
completed, and the RTX6000 lease was released after process/GPU checks. Source
selection peaked at `0.8557`; checkpoint SHA is
`e46d3083e333661173b6b70b47836a68b3f552295821f972e4da2f75ec33a751`.
Target score is `0.5994288696`, delta `-0.0716868122` versus the U-Net-only
parent. Three of four movie deltas are strongly negative (`-0.1210788538`,
`+0.0278898852`, `-0.0797191322`, `-0.1312344131`). Node recall rises by
`+0.0112585466`, but predicted-node excess reaches 28.1–47.2% on three movies,
and the official count adjustment exposes the resulting precision failure.
Reject full-model transfer: independent visual U-Net features transfer, while
the synthetic temporal/edge head does not. No locked or Kaggle action follows.

## EXP137 — reciprocal 6bba-to-44b6 pair (pre-registered; waiting data)

Complete EXP130's missing reciprocal direction with the already supported
comparison only: scratch versus the verified 74-key Zebrahub U-Net initializer,
seed `314159`, LR `1e-4`, five epochs and otherwise identical trainer/evaluator
settings. Source `6bba` uses its first 10 lexicographic movies for gradients
and final two for source-only checkpoint selection. Target development is the
first four `44b6` movies; its final eight remain the locked evaluation subset.
The exact source and target lists are frozen before the remaining transport
completes. Both arms run sequentially in one RTX6000 allocation. Gate is
Zebrahub-minus-scratch nonnegative in this direction and positive when pooled
with EXP130/131, without node-recall regression; a small result requires seed
replication. This is reciprocal cross-fit OOF: each scored movie is predicted
by a model excluding its embryo, but with only two embryos it is not an
independent estimate for a third unseen embryo. No LB authority.

### EXP137 data-stage update 1

The official single-worker downloader now has six complete `6bba` movies and
is progressing through the seventh with server-directed HTTP-429 backoff. Two
newly complete movies (`13f19531`, `20852818`) were checked against the live
manifest for every component count and total byte size, packed locally, split
into eight transport parts and copied to `nsu-quadro`. Every part SHA and the
reassembled 735,989,760-byte tar SHA matched; the latter is
`72af006f252f37513ee583cb4ded7946d96cf7f8b8a1a19f53a9211dc8060178`.
Extraction added exactly `102/21` files for each movie to the registered remote
`data/pilot_single_6bba` root. Receipt:
`reports/exp137_data_stage_batch1_20260909.json`.

After verification, the exact local and remote transport tar/part files and
the newly generated trainer `.pyc` were deleted. Extracted official data,
frozen split files and evidence remain. EXP137 is still `waiting data`: do not
allocate RTX6000 or open the target locked audit until all 12 `6bba` movies pass
the full official manifest audit. No Kaggle kernel or submission was created.

### EXP137 data-stage update 2

The downloader completed `6bba_3abfe10a` and moved on to `784a78c9`. The
completed movie matched the live manifest exactly: 102 Zarr files totaling
539,403,678 bytes and 21 GEFF files totaling 13,841 bytes. Its six transport
parts and reassembled 539,682,304-byte tar matched locally and remotely; tar
SHA is `2e7b5771e40d8716fc8a1e6e6299d10869908d7ff591c6f7b483c3842f2eb414`.
Remote extraction produced exactly 102/21 files. Receipt:
`reports/exp137_data_stage_batch2_20260909.json`.

This movie is in the frozen locked subset for the 44b6-to-6bba direction, so no
label or score was read; it is staged solely as future source data for the
reciprocal 6bba-to-44b6 fold. All local and remote batch2 transport files were
deleted after verification. No Kaggle action occurred.

## EXP138 — discriminative U-Net learning rate (pre-registered; no submission)

Hypothesis: EXP136 shows that the independently pretrained synthetic temporal
head transfers poorly, while EXP130/131 show that its 74-key visual U-Net
initialization transfers positively. End-to-end fine-tuning at one learning
rate may nevertheless overwrite useful visual features faster than the random
competition-specific edge head learns. Test a discriminative optimizer with
the U-Net at `1e-5` and all non-U-Net parameters at `1e-4` (`unet_lr_scale=0.1`).
Use the stronger source-selected seed `271828`, five epochs and every other
EXP131 training, checkpoint-selection, target-development and registered-linker
setting unchanged. Compare only with the exact EXP131 seed-`271828` U-Net-only
parent (`0.6711156817` on the four untouched `6bba` development movies).

Promotion requires positive pooled score, no negative per-movie delta and no
node-recall regression versus EXP131. The implementation must log both learning
rates and keep the default scale at `1.0` behaviourally equivalent to the prior
trainer. This is one mechanism-led candidate, not a learning-rate sweep. No
locked audit, Kaggle kernel or submission is authorized by this experiment.

### EXP138 result

The single RTX6000 run completed under queue lease
`biohub-exp138-discriminative-lr-20260909`; the logged optimizer rates were
U-Net `1e-5` and non-U-Net `1e-4`. Source-only selection retained epoch 0 at
`0.8295`; later epochs lost source recall. On the same four frozen `6bba`
development movies the candidate scored `0.4871232494` versus the EXP131 parent
at `0.6711156817` (delta `-0.1839924324`). Every movie regressed
(`-0.149983`, `-0.348515`, `-0.028442`, `-0.179469`) and pooled node recall
fell from `0.9657465` to `0.7015841` (delta `-0.2641624`).

Reject: reducing only the U-Net rate prevents sufficient detector-domain
adaptation; useful pretrained visual structure does not imply that the detector
can be nearly frozen during this short competition fine-tune. PID exit and an
idle 5-MiB/0% GPU were verified before the lease was released. Receipt:
`reports/exp138_discriminative_lr_20260909.json`. No locked audit, Kaggle kernel
or submission follows. The rejected local/remote checkpoint and config, empty
launcher log and generated `.pyc` files were removed after their hashes were
captured; result JSON and train/eval logs remain as evidence.

## EXP139 — source-only detector-threshold calibration (pre-registered; no submission)

Hypothesis: the fixed runtime threshold `0.985` came from an upstream public
pipeline rather than this embryo-disjoint fine-tune. Calibrating only on the two
source-embryo checkpoint-validation movies may improve detector transfer without
using target labels. Freeze the EXP131 seed-`271828` checkpoint and registered
linker; evaluate the predeclared thresholds `[0.95, 0.97, 0.985, 0.99]` on
source validation `44b6_e35b117d` and `44b6_f28707c6`. Select maximum pooled
source score, breaking an exact tie by smallest distance to parent `0.985`,
then by higher threshold. Evaluate the selected threshold exactly once on the
same four frozen `6bba` development movies.

This is one source-calibration hypothesis, not four target hypotheses. Promotion
requires the selected threshold to beat the parent target pooled score, have no
negative per-movie target delta and no pooled node-recall regression. Report the
entire source grid, including the parent threshold. No locked audit, Kaggle
kernel or submission is authorized.

## EXP140 — independent-seed source-threshold replication (pre-registered; no submission)

EXP139 has a small positive pooled/recall effect but fails the all-movie gate,
so replicate the source-only calibration with the independent EXP130 seed
`314159` checkpoint. Keep the exact source-validation movies, threshold grid
`[0.95, 0.97, 0.985, 0.99]`, registered linker, selection objective and
tie-break from EXP139. Select without `6bba` access, then run exactly one target
development evaluation. Compare with the seed-`314159` U-Net parent at threshold
`0.985` (`0.6294409207`).

This tests stability of the calibration mechanism, not a new target sweep.
Promotion requires positive pooled target delta, no negative target movie delta
and no node-recall regression in this seed, followed by reciprocal-fold evidence
before any locked audit. No Kaggle action is authorized.

### EXP140 result

The independent seed selected the opposite grid end: source scores were
`0.581646` (`0.95`), `0.601060` (`0.97`), `0.597236` (`0.985`) and `0.604541`
(`0.99`), so `0.99` was frozen before target inference. Target registered score
then fell from `0.6294409207` to `0.6277910965` (`-0.0016498242`), pooled node
recall fell by `-0.0025747951`, and three of four movies regressed. The source
selector is therefore seed-unstable (`0.95` for seed 271828, `0.99` for seed
314159) and fails replication.

Reject threshold calibration as a private-ready global rule. Preserve it as a
clear warning that two source-validation movies are insufficient to calibrate
a seed-specific detector threshold. PID/GPU shutdown was verified and the
RTX6000 lease released. Receipt:
`reports/exp140_source_threshold_seed314159_20260909.json`. No locked/Kaggle
action occurred.

## EXP141 — aligned two-seed U-Net weight soup (pre-registered; no submission)

Hypothesis: both competition fine-tunes started from the exact same Zebrahub
U-Net initializer, so corresponding visual tensors remain aligned. Averaging
their U-Net weights may reduce seed variance without the runtime/memory cost of
a two-model detector. Build one checkpoint with fixed `alpha=0.5`: copy every
non-U-Net tensor exactly from the source-training-selected seed `271828` parent,
and average matching floating `unet.*` tensors with seed `314159`; retain the
primary value for any non-floating U-Net buffers. Fail on any key/shape/dtype
mismatch and record all input/output hashes.

At parent threshold `0.985` and the unchanged registered linker, first compare
the soup against seed `271828` on the two source-validation movies. Proceed to
one target-development pass only if source pooled score is nonnegative versus
that parent. Target promotion requires positive pooled score, no negative movie
delta and no node-recall regression versus seed `271828`. No alpha sweep, locked
audit, Kaggle kernel or submission is authorized.

### EXP141 result

The CPU builder passed all compatibility checks: both inputs had 136 matching
keys/shapes/dtypes; 64 floating U-Net tensors were averaged, 10 non-floating
U-Net buffers and all 62 tracking-head tensors came from seed `271828`. Soup
checkpoint SHA was
`406fba7e74e2d1c3d76a059c0aa16f1bf8b9184398cbafbd7dfe3f51b6a33dcb`.
At threshold `0.985` it produced no matched source-validation nodes and score
`0.0` versus the parent source score `0.552416`, so the predeclared source gate
stopped the experiment before any target evaluation.

Reject naive weight-space averaging. A shared initializer does not guarantee
linear compatibility after independent fine-tuning; use prediction- or
coordinate-level ensembles instead. The RTX6000 lease was released after
PID/GPU checks. The soup checkpoint, empty caches and empty launcher log were
deleted after hashes were recorded; source result/log/build receipt remain.
Receipt: `reports/exp141_unet_weight_soup_20260909.json`. No target, locked or
Kaggle action occurred.

## EXP142 — guarded dual-seed detector-logit fusion (pre-registered; no submission)

Adapt one verified open-notebook mechanism from the archived qrz1201/tangai1
families: fuse detector predictions before peak extraction, while retaining a
single primary tracking head and dynamic runtime inference. Use seed `271828`
as primary because it won the original source-training checkpoint selector and
seed `314159` as the detector donor. Average detector logits with fixed donor
weight `0.5`; for each frame fall back to primary detections if the fused count
is below 90% of the primary count. Keep primary U-Net features for edge scoring,
threshold `0.985`, registered linker and every other evaluation setting fixed.

This is prediction-level fusion, not weight averaging. First evaluate the two
source-validation movies and compare with the exact seed-`271828` primary at
the same threshold. Proceed to one target-development pass only if source pooled
score is nonnegative; target promotion requires positive pooled score, no
negative movie delta and no node-recall regression. Record per-frame retention
telemetry and both checkpoint hashes. No fusion-weight/guard sweep, locked audit,
Kaggle kernel or submission is authorized.

### EXP142 result

The fixed fusion passed its pre-registered pooled-only source gate: registered
source score rose from `0.5524158065` to `0.6162304931` and node recall rose by
`+0.0703703704`. The response was already heterogeneous, with movie deltas
`+0.102256` and `-0.073862`, but the source gate did not require both signs to be
positive, so the single target-development pass proceeded without retuning.

On the four frozen `6bba` movies, the registered weak-linker score fell from
`0.6715071138` to `0.6436492579` (`-0.0278578559`). Three movies regressed
(`-0.043363`, `-0.011921`, `-0.091761`) and one improved (`+0.014811`). Pooled
node recall increased by `+0.0037821084`, showing that added detections did not
translate into reliable edges. Telemetry confirms the failure mechanism: over
400 target frames, primary proposals totalled 87,502, fused proposals 90,398,
and the one-sided 90% retention fallback activated only once. It protected
against proposal loss but not proposal excess.

Reject for private selection. Do not tune the guard or fusion weight on these
target movies; a future ensemble must use a source-selected symmetric or
precision-aware guard and then pass reciprocal embryo evidence. PID exit and an
idle RTX6000 (5 MiB, 0%) were verified before queue lease
`biohub-exp142-dual-detector-target-20260909` was released. Empty launcher logs
and generated local/remote `.pyc` files were removed; verified result JSON,
evaluation logs and candidate caches remain as evidence. Receipt:
`reports/exp142_dual_detector_fusion_20260909.json`. No locked audit, Kaggle
kernel or submission followed.

## EXP143 — seven-movie reciprocal pipeline pilot (pre-registered; no submission)

Purpose: use the seven complete, official-manifest-size-verified `6bba` movies
to validate the reverse `6bba → 44b6` training/evaluation dataflow while the
remaining official files download. This is an infrastructure and directional
pilot, not a sixth model hypothesis and not final reciprocal evidence.

Freeze seed `314159`, five epochs, LR `1e-4`, batch size 2, deterministic CUDA,
registered linker, threshold `0.985` and weak tie-break `0.1`. Train on
`05b6850b, 05db0fb1, 062c8d37, 07477033, 13f19531`; checkpoint-select only on
`20852818, 3abfe10a`; evaluate scratch and U-Net-only Zebrahub initialization
once on the four already-frozen `44b6` development movies. The two arms are
compute matched. Do not inspect or open any locked-audit movie.

Interpretation gate: report source checkpoint-selection history, exact hashes,
target score/recall, per-movie deltas and pipeline failures. A positive result
is only directional because five source-training movies are incomplete domain
coverage; a negative result may reject the initialization mechanism early. In
neither case may EXP143 open a locked audit, authorize a Kaggle kernel or spend
a submission slot. Full EXP137 on the pre-registered 10+2 split remains
mandatory after all 12 `6bba` movies pass the strengthened integrity audit.

### Data/metric reliability hardening during EXP143

The official-24 audit supersedes its earlier recorded source hash with SHA
`9246570ba2c69dbaf93993665bb7e67aae52e0b9a314648a0ac7f8a300aab384`.
It now rejects duplicate/out-of-scope/traversal manifest paths, parses every
Zarr metadata JSON as a v3 array/group, and can compute per-movie SHA-256 tree
digests over names, sizes and bytes. These hashes prove identity across our
copies; the Kaggle manifest itself exposes no independent content hashes.

The paired candidate comparator now has SHA
`325d98c71041ad7a6803adeb6f0b60eb32a6e102741d1f25ca825ae1e6941c48`.
It fail-closes unless stored summaries exactly agree (`1e-12`) with scores,
recall and counts recomputed from per-movie sufficient statistics. Five focused
unit tests cover deterministic content hashing, manifest traversal rejection,
official weighted aggregation, tampered summaries and invalid counts; all pass.

### EXP143 result

The seven-movie reverse pipeline completed cleanly. Source-only checkpoint
selection chose epoch 4 for both arms: scratch validation recall `0.8831`,
Zebrahub-initialized `0.9007`. On the four frozen `44b6` development movies,
registered score improved from `0.7851112547` to `0.8025893908`
(`+0.0174781361`) and mean node recall improved by `+0.0548925500`.
Per-movie score deltas were `-0.007270`, `+0.061228`, `-0.029909`, and
`+0.042033` (2 positive / 2 negative). Registered and weak-linker summaries
were identical in this pilot and passed exact recomputation from TP/FP/FN.

This supports the *direction* of U-Net initialization in the reverse embryo
fold, but fails the strict all-movie gate and uses only five source-training
movies. It cannot replace EXP137's full 10+2 reciprocal run, open locked data,
or authorize a submission. The PID exited, RTX6000 returned to 5 MiB/0%, and
the lease was released. After checkpoint hashes were captured, the 17-MiB
copied repo (including supersedable pilot checkpoints) and empty launcher log
were removed; results, logs and candidate caches remain. Receipt:
`reports/exp143_reciprocal_7movie_pilot_20260909.json`.

### EXP137 full-data pre-run correction

The strengthened split builder emits both directions in one trainer JSON:
index 0 is `44b6 → 6bba`, index 1 is `6bba → 44b6`. Final preflight caught
that the waiting EXP137 launcher still requested index 0. No EXP137 process,
checkpoint or score existed. Before launch, the script was corrected to train
and read weights from `split_1`, stage an isolated repo copy without inherited
weights, and enforce the same eight-thread limits used by the pilot. This is a
dataflow correction required to execute the already pre-registered direction;
it changes no model, seed, hyperparameter, target subset or promotion gate.

### EXP139 result

The source-only grid selected threshold `0.95`: source registered scores were
`0.557421` (`0.95`), `0.546436` (`0.97`), `0.552416` (`0.985`) and `0.537077`
(`0.99`). Selection occurred before the target pass and used no `6bba` metric.
On target development, `0.95` improved registered pooled score from
`0.6711156817` to `0.6768015581` (`+0.0056858763`) and pooled node recall by
`+0.0085994726`. Per-movie deltas were `-0.005583`, `+0.023031`, `-0.000325`
and `+0.001396`.

Reject strict promotion because two movies regress. Retain source-only detector
calibration as a promising, reusable mechanism that needs independent-seed and
reciprocal-fold support; do not open locked audit. The RTX6000 PID exited, the
GPU returned to 5 MiB/0%, and the queue lease was released. Receipt:
`reports/exp139_source_threshold_20260909.json`. No Kaggle slot was used.

# 2026-09-08 W1 continuation — EXP027 GOLD_PUBLIC slot 1 pre-POST receipt

This candidate is the first `GOLD_PUBLIC` slot of the current continuation
block. It is not a `PRIVATE_ROBUST` claim: reciprocal `6bba` data remain
unavailable after repeated official API HTTP 429 responses, so the
Zebrahub-trained transfer has only a single-embryo pilot diagnostic and is
promoted here solely through the public-track full-inference gate.

Hypothesis: initializing the support-pack TemporalUNet3D edge predictor from
an independently pretrained Zebrahub synthetic tracking task, then fine-tuning
on the complete downloaded `44b6` pilot, may improve the public frontier while
preserving a valid dynamic code-competition path. Parent/source: the audited
`exp092_finetuned_d4` runtime-inference notebook and its support/relinking
pipeline; the new model artifact is not a replay of any public
`submission.csv`. Independent pretraining receipt:
`outputs/research/zebrahub_pretrain_20260908/exp026_receipt.json`; full-5-epoch
pilot fine-tune receipt:
`outputs/research/pilot_finetune_44b6_20260908/exp027_full5_receipt.json`.

The submitted source is
`kaggle_notebooks/exp027_zebrahub_gold_public/zebrahub_gold_public.ipynb`,
Kaggle kernel
`dmitriigluzdov/biohub-exp027-zebrahub-gold-public` v3, source SHA-256
`60a2ac8bd577ab2f8fe86123455042311c50dc1c04f1c1262081df2d9671d071`.
Kaggle is Internet-off with GPU enabled and the competition source attached;
the private model dataset is
`dmitriigluzdov/biohub-exp027-zebrahub-finetuned-44b6-v1`, containing the
8,357,362-byte checkpoint SHA-256
`082d3882ad183892b3bb7541ecbb1383670eef5ba474d110afb58ffef7f77583`.
Runtime dataflow discovers the mounted competition `test/*.zarr` datasets,
loads the model, performs inference and graph postprocessing, and writes one
root `submission.csv`; it does not read a frozen public submission artifact.

The clean v3 runtime completed with 4 prediction graphs. Downloaded output
`outputs/research/exp027_kernel_v3_audit/submission.csv` passed the local
schema/finite-value/dataset-ID/endpoint/degree audit: SHA-256
`f520090009de1064761eaa1576ae50eb532f2af600c68f96f2873e4403aebb46`,
9,969,725 bytes, 192,399 rows, 97,951 nodes, 94,448 edges, 336 division
sources, four dynamic dataset IDs (`44b6_0113de3b`, `44b6_0b24845f`,
`6bba_05b6850b`, `6bba_05db0fb1`), max in-degree 1 and max out-degree 2.
Promotion gate: submit exactly once through
`scripts/submit_code_file_once.py`; after POST query the full API object and
record ref/status/error/score/bytes/URL/quota. Do not present this as honest
private OOF evidence and do not spend a further slot unless a separate
candidate passes its own track gate.

### EXP027 POST correction and result

The first helper attempt intentionally stopped before POST because Kaggle
canonicalized markdown sources and compacted JSON. The builder now reproduces
that exact canonical representation; the corrected local and remote v3/v4
source SHA is `67ac3428724e0e57a76ede0219adf9737a5d2ec0a45d49acb06bbd67ea8ed52e`.
The next helper attempt then stopped before POST because an optional cover-cell
reference to `pilkwang/pilkwang-public-dataset-for-notebooks-figures` was not
attached; v4 added that explicit attachment and reran successfully. No quota
was consumed by either stopped attempt.

After v4 passed the same full output audit, the candidate was submitted once
through `scripts/submit_code_file_once.py` as ref `56095320`. The immediate
full API object at `2026-09-08T09:17:24.027000Z` is
`SubmissionStatus.PENDING` with `public_score=null`, `private_score=null`,
`error_description=null`, `total_bytes=0`, file `submission.csv`, and URL
`/code/dmitriigluzdov/biohub-exp027-zebrahub-gold-public?scriptVersionId=348179069`.
Quota is now `1/5` used today, `4` available, `79` total, not limited by total.
The output/result receipt is `reports/submission_exp027_20260908.json`.

### EXP027 live score update — 2026-09-09

The previously pending ref `56095320` is now `SubmissionStatus.COMPLETE` in the
live API with public score **`0.616`**, `private_score=null`,
`error_description=null`, and `total_bytes=176655593`. The URL still matches
the submitted kernel v4 and script version ID `348179069`. This is a valid
account LB result, but it is a substantial regression versus the current
public frontier around `0.94`; the independent Zebrahub initialization plus
the 44b6-only fine-tune is therefore rejected as a score-improving direction.
No private score or private-robustness claim is made. The published checkpoint
dataset remains API status `ready`; the final GPU check found Quadro RTX 6000
at 5 MiB / 0% utilization with dispatch lock absent.

# 2026-09-07 W1 D3 pre-registration: S11-S15

D2 is closed with EXP127 recorded as a terminal zero-byte runtime failure:
Kaggle reports that the coordinate-frontier notebook exceeded the allowed
runtime. This is an anomaly, not a score, and the exact source/output receipt
is preserved below in the 2026-09-06 section. The failure diagnosis is that
the candidate performs a second full detector inference over the four runtime
movies; the clean run reached about 3,449 seconds before Kaggle packaging,
which is not a safe submission runtime for a hidden dataset of variable size.

The next W1 block is D3 with the non-interchangeable portfolio policy: S11 and
S12 are `GOLD_PUBLIC`, while S13 through S15 are `PRIVATE_ROBUST`. Live
preflight at `2026-09-07` shows `0/5` submission slots used and `5` available.
No D3 POST is authorized by this pre-registration until its candidate passes
the clean Internet-off runtime, source identity, dynamic test-dataflow,
schema/finite-value, dataset-ID and graph audits.

S11 is `UNUSED`: the existing high-confidence edge-consensus diagnostic was
rejected by its physical-motion veto and no new full-inference source is
available. S12 is `UNUSED`: the distinct harmonic/edge sources already have
account submissions, so reproducing them would be a duplicate rather than a
new arm. S13 is `BLOCKED`: cached Kalman/velocity OOF has not produced the
required reciprocal embryo-level reversal, and the already submitted EMA
velocity source is not a new OOF-backed candidate. S14 is pre-registered as
the only currently eligible build: a full runtime-inference source with a
fixed 10% learned ambiguity tie-break, using the positive H050 reciprocal
OOF mechanism. Its Kaggle GPU clean run has now completed successfully on a
T4; no quota has been spent before the guarded POST. S15 is `UNUSED`:
the reciprocal OOF reversal gate is absent and the prior corrected min-cost-
flow submission scored `0.884`.

## D3-S14 — EXP128 PRIVATE_ROBUST — weak learned tie-break

Local candidate source: `kaggle_notebooks/exp128_d3_s14_weak_tiebreak/weak_learned_tiebreak.ipynb`, SHA-256
`e5927961866dce793930cc91bb27f676861c662c7aec1074b46d41bbf7dba1af`.
Parent is the clean `arnav170/biohub-940e` full-inference source, not a
frozen public CSV. The source dynamically discovers the competition
`test/*.zarr`, performs detector/edge inference and graph postprocessing, and
changes only the motion-relink ambiguity policy to a 7 µm physical gate with
zero velocity term and a fixed learned bonus `0.1`. The mechanism is the
production analogue of H050's fixed 10% learned tie-break, whose reciprocal
untouched-fold deltas are `+0.000734` and `+0.000771`; those are mechanism
evidence, not a promised leaderboard gain.

The intended kernel is
`dmitriigluzdov/biohub-exp128-d3-s14-weak-learned-tiebreak` v1 with Internet
off, the competition source and the same explicit support datasets as its
parent. The clean T4 run completed successfully; the normalized remote source
SHA is `c7025c80d182b215f3ba05388e3881c65b2e3fa66ed2232d1733403ec93c3635`.
The root output audit is PASS: `submission.csv` SHA
`419b7bcf976664673ba5454ddbb6046b78bd13a27485437b89f2145f773a2eac`,
12,093,821 bytes, 232,381 rows, 118,534 nodes, 113,847 edges and 148
division sources across four dynamic runtime dataset IDs; max in-degree is 1
and max out-degree is 2. The first two pushes were rejected for title/id slug
mismatch and the corrected push was then rejected with Kaggle 403 while
another GPU kernel was running. An alternate `NvidiaTeslaP100` push was also
rejected with HTTP 403; the successful T4 push is the clean run used here.
The candidate was submitted once through the guarded helper as ref `56071282`.
The immediate full API object at `2026-09-07T06:59:36.993000Z` is
`SubmissionStatus.PENDING` with `public_score=null`, `private_score=null`,
`error_description=null` and `total_bytes=0`. The URL is
`/code/dmitriigluzdov/biohub-exp128-d3-s14-weak-learned-tiebreak?scriptVersionId=347884817`,
matching the pre-registered kernel v1. Quota changed to `1/5` used today,
`4` available, `78` total, not limited by total. This is a permitted
nonterminal state and not a score.

Pre-registration receipt: `reports/submission_batch_20260907.json`.

### EXP128 POST update

EXP128 was sent once through `scripts/submit_code_file_once.py` as ref
`56071282`. The guarded helper accepted the exact normalized source SHA and
the completed Internet-off T4 kernel. The immediate API post-check is
`SubmissionStatus.PENDING` with no error, no public/private score and zero
nonterminal bytes; the exact v1 URL contains script version ID `347884817`.
The daily quota is `1/5` used, `4` available, `78` total, and not limited by
the total. No score or private-robust promotion claim is made while pending.

# 2026-09-06 W1 D2 pre-registration: EXP124-126; S06-S07 UNUSED

The next W1 block is pre-registered with the non-interchangeable portfolio
policy: D2-S01 and D2-S02 are `GOLD_PUBLIC`, while D2-S03 through D2-S05 are
`PRIVATE_ROBUST`. S06/S07 are not reassigned to the private track. S06 is
blocked by Kaggle's live maximum of two concurrent GPU sessions, and S07
depends on a qualifying S06 result; both remain `UNUSED` unless the required
gate is later satisfied in a separately authorized block.

Live preflight at `2026-09-06T02:52:20.8005221Z`: quota is `0/5` used today,
`5` available, `73` total, and not limited by the total. Big Cells is rank 108
at `0.942`; the downloaded leaderboard has 3,167 teams, with landmarks rank
1 `0.970`, rank 16 `0.949`, rank 155 `0.941` and rank 311 `0.940`.

The three selected candidates are one count-calibration diagnostic (EXP124),
one temporal-plus-appearance agreement candidate (EXP125), and one capped
short-track/dim-cell rescue candidate (EXP126). They are not presented as
honest OOF evidence. Each must pass the guarded helper, current kernel/source
identity validation, clean Internet-off runtime inference over dynamic
competition test data, schema/finite-value/graph audits, and the full API
post-check. Stop on the first API anomaly, terminal empty score, error, zero
bytes, version mismatch or quota anomaly.

## EXP124 — D2-S03 PRIVATE_ROBUST — count calibration

Hypothesis: the current `aagneye/biohub-v25-det-090` operating point may
provide a useful count-calibration diagnostic against the higher-threshold
detector family. Parent is the D1 public frontier (`0.942`) and the prior
detector family, not a claim of independent mechanism quality. The source is
kernel `aagneye/biohub-v25-det-090`, v1, script ID `346930642`, source SHA
`51680ac5061f4ae696e5e3261f08bd2713e9c7d3773f5e34805c7b2644868667`, at
`outputs/research/frontier_20260904/aag_v25/biohub-v25-det-090.ipynb`.
The expected output is one root `submission.csv`, SHA
`2af45e16f4336a777e19f54cc6084d5903ebc6c1125aa52a9807bf06f58f3dc1`, with
244,095 rows, 124,282 nodes, 119,813 edges and 324 division sources across
four runtime datasets. Its runtime dataflow discovers `test/*.zarr`, runs
dual-seed detector inference at the `.90` calibration threshold, then
association and graph postprocessing; it does not replay a frozen public
submission. Local graph audit is PASS. Promotion requires a valid hidden
rerun and stable/no-meaningful-regression evidence; the result must not be
called OOF evidence or used to justify a sweep.

## EXP125 — D2-S04 PRIVATE_ROBUST — temporal + appearance agreement

Hypothesis: the current dual-seed temporal/appearance agreement gate may be a
stable private hedge with a different error mechanism from the detector and
gap-rescue arms. Parent is the D1 portfolio/frontier (`0.942`). The source is
kernel `flexonafft/biohub-agreement-gated-dual-seed-fusion`, v20, script ID
`347436742`, source SHA
`2337f0af854e0dee3f3b5701141934d70eb683844a7d629d12edf2fdd61f832a`, at
`outputs/research/frontier_20260906/s09_source/biohub-agreement-gated-dual-seed-fusion-v20.ipynb`.
The expected output is one root `submission.csv`, SHA
`a00f5ee9941576c5092876f93f58835ee36694768bb142a5db2e2a0b8ef9b755`, with
234,161 rows, 119,178 nodes, 114,983 edges and 150 division sources across
four runtime datasets. Its runtime dataflow discovers runtime
`test/*.zarr`, performs temporal and dual-seed/appearance agreement with
harmonic association and graph postprocessing, and does not read a frozen
public `submission.csv`. Local graph audit is PASS; its physical-edge overlap
is `0.943625` against the earlier agreement version and `0.957779` against
EXP123, so it is a distinct version but not independent of that family.
Promotion requires a valid hidden rerun and stability/mechanism-diversity
review; public title or local proxy is not private evidence.

## EXP126 — D2-S05 PRIVATE_ROBUST — capped dim-cell rescue

Hypothesis: the bounded short-track/gap-2 rescue in
`qrz1201/biohub-ablation-gap5-only` can recover dim or briefly missed cells
without an uncontrolled graph expansion. Parent is EXP123's fixed harmonic
control and the D1 private portfolio (`0.942`). The source is kernel
`qrz1201/biohub-ablation-gap5-only`, v1, script ID `347362347`, source SHA
`5782115d808b52f0f00e33ac841d773b8940dcc53a0e2a73e892a39eb7a103f3`, at
`outputs/research/frontier_20260905/sources/qrz1201__biohub-ablation-gap5-only__1/biohub-ablation-gap5-only.ipynb`.
The expected output is one root `submission.csv`, SHA
`d6eaa617c02ebe03ce1c7cbcb14f2348001f4bcc9fee46dc3a8147f0fa414f4b`, with
234,433 rows, 119,329 nodes, 115,104 edges and 151 division sources across
four runtime datasets. Its runtime dataflow dynamically discovers
`test/*.zarr`, applies detector threshold `.965`, gap-close `5.0`, and capped
adaptive short-track rescue with explicit length, mean-probability, distance
and node-count limits, followed by graph postprocessing. It does not replay a
frozen public artifact. Local graph audit is PASS. The output is close to
EXP123 in core edges (`0.995838` physical-edge overlap) but materially changes
rescue/division behavior; promotion therefore requires hidden validity and
private stability, not a public-LB delta.

Pre-registration receipt: `reports/submission_batch_20260906.json`.

### EXP124 POST update

EXP124 was sent once through `scripts/submit_code_file_once.py` as ref
`56045303`. The immediate full API object at
`2026-09-06T02:54:23.900000Z` is `SubmissionStatus.PENDING` with
`public_score=null`, `private_score=null`, `error_description=null` and
`total_bytes=0`. The URL is
`/code/aagneye/biohub-v25-det-090?scriptVersionId=346930642`, matching the
pre-registered v1 exactly. Quota changed to `1/5` used today, `4` available,
`74` total, not limited by total. This is a permitted nonterminal state and
not a score; the batch remains eligible for independent candidates.

### EXP125 POST update

EXP125 was sent once through `scripts/submit_code_file_once.py` as ref
`56045327`. The immediate full API object at
`2026-09-06T02:56:18.067000Z` is `SubmissionStatus.PENDING` with
`public_score=null`, `private_score=null`, `error_description=null` and
`total_bytes=0`. The URL is
`/code/flexonafft/biohub-agreement-gated-dual-seed-fusion?scriptVersionId=347436742`,
matching the pre-registered v20 exactly. Quota is now `2/5` used today, `3`
available, `75` total, not limited by total. This is a permitted nonterminal
state and not a score.

### EXP126 POST update and D2 close

EXP126 was sent once through `scripts/submit_code_file_once.py` as ref
`56045360`. The immediate full API object at
`2026-09-06T02:58:18.913000Z` is `SubmissionStatus.PENDING` with
`public_score=null`, `private_score=null`, `error_description=null` and
`total_bytes=0`. The URL is
`/code/qrz1201/biohub-ablation-gap5-only?scriptVersionId=347362347`, matching
the pre-registered v1 exactly. Quota is now `3/5` used today, `2` available,
`76` total, not limited by total. This is a permitted nonterminal state and
not a score.

D2 closes with EXP124/125/126 submitted in their pre-registered
`PRIVATE_ROBUST` slots. D2-S01/S06 and D2-S02/S07 remain `UNUSED` because the
coordinate-frontier clean push was blocked by Kaggle's concurrent GPU-session
limit and S07 required a qualifying S06 result. The two remaining slots were
not borrowed across tracks. All three submissions remain pending; no public
score or private-selection claim is made until terminal, error-free scoring.

### Correction: EXP124-126 terminal results

The preceding D2 close was an accurate snapshot before scoring and before the
GPU session became available again. A subsequent live API read found EXP124
`COMPLETE` at `0.911` with `208969475` bytes, EXP125 `COMPLETE` at `0.940`
with `204302276` bytes, and EXP126 `COMPLETE` at `0.940` with `204643508`
bytes. All three have null `error_description`; these are public scores only,
not private evidence. The account frontier remains `0.942`.

### 2026-09-06 D2 GOLD_PUBLIC continuation: EXP127-128

The user authorized filling the two remaining D2 slots. The earlier GPU
blocker has cleared, so the slots may be filled only within their original
`GOLD_PUBLIC` track. EXP127 is pre-registered as D2-S01: the clean Kaggle
candidate `dmitriigluzdov/biohub-exp061-coordinate-frontier-submission` v1,
source SHA
`5e7c1614422b685600d6c1023a8237d8318131a3ad15316c17c7eacc6d987a72`, local
prepared output SHA `ee54117f5af261d0942bc4304a6f37952880b47e861eb6bf890d4ff7ad2ef078`.
The clean Kaggle runtime output SHA is
`9d3d9c8786d71787b43b7ddc386fc638dab8a2c99daec97542299d521cef5266`, with
239,626 rows, 122,032 nodes, 117,594 edges and 67 division sources
across four runtime datasets. Its source dynamically discovers runtime
competition `test/*.zarr` and performs full inference plus coordinate-only
consensus alpha `.25`; it does not replay a public submission. The local
audit is PASS. Promotion requires a clean hidden-compatible rerun and a
public score above the `0.942` frontier or credible gold-boundary evidence.

EXP128 is conditionally pre-registered as D2-S02: the alpha `.50` candidate
`dmitriigluzdov/biohub-exp060-coordinate-frontier-submission` v1, source SHA
`bd4f391c90df96cd7ebacae477e18b033c072e81fa510cc4d0a3f1090bb76ec4`, output
SHA `5fb789eafc49aa62a1777608c4b1dcebf5e2b3121bb0ba24751569fcf5cbbb99`,
with the same audited graph counts. It may be submitted only if EXP127 first
completes above `0.942` without an anomaly; otherwise D2-S02 remains UNUSED.
Receipt: `reports/submission_batch_20260906.json`.

### EXP127 POST update

The clean S06 runtime source was normalized by Kaggle on push: the remote blob
SHA is `7809016a93be280bebdb5865e5e4ccfff57a0c30ed142bfb4e0fb258abf71d0e`
and all 15 cell sources match the local candidate. EXP127 was then sent once
through `scripts/submit_code_file_once.py` as ref `56053651`, URL
`/code/dmitriigluzdov/biohub-exp061-coordinate-frontier-submission?scriptVersionId=347679332`.
The immediate full API object at `2026-09-06T11:09:16.437000Z` is
`SubmissionStatus.PENDING` with `public_score=null`, `private_score=null`,
`error_description=null` and `total_bytes=0`. Quota changed to `4/5` used,
`1` available, `77` total, not limited by total. The kernel itself is
`COMPLETE`; this is a permitted nonterminal submission state and not a score.
The first helper attempt with the local notebook SHA stopped before POST on
the Kaggle notebook-normalization mismatch and consumed no quota. The exact
remote blob was then downloaded, its 15 cell sources were confirmed equal to
the local candidate, and the helper accepted the remote SHA.

# 2026-09-05 W1 D1 S04 replacement: EXP123

The user authorized a same-track replacement for the unused `D1-S04` slot after
the X56 attribution gate failed. This does not alter the original map or move a
GOLD_PUBLIC slot. EXP123 is `PRIVATE_ROBUST` and is pre-registered before POST
as `D1-S04-ALT`.

Live preflight at `2026-09-05T09:20:17.977548Z`: qrz1201's
`biohub-ablation-dc025-only` is current v1, `COMPLETE`, Internet off, attached
to the competition and all three explicit support datasets; remote source SHA
matches `c0e7d8f63fd72b74545d52ce114e63a2fa34260fb37d40acc94c35c192788d05`.
The account quota is `4/5` used, one available, `72` total, not limited by the
total. EXP119/120/121/122 are all still `PENDING` with no error or score and
zero nonterminal bytes.

EXP123 uses the audited runtime-inference source
`qrz1201/biohub-ablation-dc025-only` v1, script ID `347362385`, and output SHA
`e4f356737800678c9504e58465cc4e8f926fcad7e316d26fe4cdd404e6321f55`.
The output audit is PASS: 234,373 rows, 119,315 nodes, 115,058 edges, 92
division sources, four runtime dataset IDs, contiguous IDs, endpoint closure,
adjacent-frame edges, max indegree 1 and max outdegree 2. The source discovers
runtime `test/*.zarr`, performs dual-seed detector and fixed harmonic
association/ILP/gap/division inference, and does not read a frozen public
`submission.csv`. Local four-movie proxy is `0.9414` and is recorded only as a
non-honest diagnostic, not OOF evidence.

Hypothesis: the lower-complexity fixed harmonic association control with
gap-close `5.8` provides a mechanism-diverse private hedge against adaptive
association, detector-threshold and grouped-confidence arms. Its edge overlap
is `0.916837` physical at 2 um to EXP119, `0.997682` to EXP120, `0.945520` to
EXP121 and `0.905698` to EXP122. This is credible structural diversity but not
error decorrelation. Promotion requires a valid hidden rerun and a final
mechanism-diversity review; the title/proxy does not certify private quality.
Pre-registration receipt: `reports/submission_batch_20260905.json`.

### EXP123 POST update and D1 close

EXP123 was sent exactly once through `scripts/submit_code_file_once.py` as ref
`56029401`. The immediate full API object at
`2026-09-05T09:21:47.729592Z` is `SubmissionStatus.PENDING` with
`public_score=null`, `private_score=null`, `error_description=null` and
`total_bytes=0`. The URL is
`/code/qrz1201/biohub-ablation-dc025-only?scriptVersionId=347362385`, matching
the pre-registered v1 exactly. Quota changed from `4/5` used and `72` total to
`5/5` used and `73` total; no quota anomaly occurred. This is a permitted
nonterminal state and not a score.

The final five-slot D1 portfolio is now complete: EXP119/120/121/122 and
EXP123 are submitted; the original X56 D1-S04 entry remains historically
`UNUSED`, while EXP123 is its same-track user-authorized replacement. No
leaderboard or score claim is made until the PENDING submission reaches a
terminal, error-free result with a non-empty score. Full replacement receipt:
`reports/submission_batch_20260905.json`.

Final live audit at `2026-09-05T09:23:24.023053Z` found all five current-day
refs (`56028571`, `56028590`, `56028627`, `56028644`, `56029401`) still
`PENDING`, with null public/private scores, null errors and zero nonterminal
bytes. The leaderboard has 3,121 teams; Big Cells is rank 205 at `0.940`.
Landmarks are rank 1 `0.970`, rank 16 `0.948`, rank 155 `0.941` and rank 311
`0.939`. The final quota is exhausted at `5/5` used, `0` available and `73`
total. No score delta can be reported while the submissions remain pending.

## Hypotheses and experiment log

This file is the competition source of truth. Update it before launching an experiment and after every CV/LB result.

## 2026-09-05 W1 D1 pre-registration: EXP119-122; S04 UNUSED

Live API preflight at `2026-09-05T08:35:55.056487Z`: the account is `Big Cells`,
rank `201`, account best `0.940`, with 3,120 leaderboard teams. Scores at ranks
1/16/155/311 are `0.970/0.948/0.941/0.939`; the current limit is `0/5` used,
five available, 68 total, not limited by total and frozen. The 2026-09-04
results were independently confirmed from full API objects before this batch:
EXP113 `0.940`, EXP114 `0.940`, EXP115 `0.935`, EXP117 `0.912`, EXP116 terminal
`ERROR` with exact Kaggle system-error text and zero bytes, and the authorized
one-time retry EXP118 `0.931`.

W1 D1 is pre-registered with the non-interchangeable two-plus-three portfolio
in `reports/submission_batch_20260905.json`. EXP119 is `GOLD_PUBLIC-1`, the
fresh confidence-adaptive association arm; EXP120 is `GOLD_PUBLIC-2`, the
analytica 0.941 attributed arm; EXP121 is `PRIVATE_ROBUST-1`, X54's single
detector-threshold factor; and EXP122 is `PRIVATE_ROBUST-3`, clean grouped
confidence dominance with division-source invariance. All four sources are
current v1, COMPLETE, Internet off, competition attached, explicit dataset
attachments nonblank, and remote source SHA matches the audited local blob.
Their exact runtime outputs pass the full four-dataset schema/topology audit:

| Slot | Experiment | Source / output SHA | Output audit | Gate |
|---|---|---|---|---|
| D1-S01 GOLD_PUBLIC | EXP119 | `ab727284…35db8` / `14ab1da…7823d` | 241,134 rows; 122,704 nodes; 118,430 edges; 158 divisions; degrees 1/2 | POST |
| D1-S02 GOLD_PUBLIC | EXP120 | `24253cae…25389` / `bf66c879…a52bd` | 234,288 rows; 119,279 nodes; 115,009 edges; 94 divisions; degrees 1/2 | POST |
| D1-S03 PRIVATE_ROBUST | EXP121 | `9c7d220a…e72ff` / `6359d60d…080bd` | 231,999 rows; 118,079 nodes; 113,920 edges; 152 divisions; degrees 1/2 | POST |
| D1-S04 PRIVATE_ROBUST | — | `925a4693…aaa10` / `7b228c4e…38ddb` | audit PASS; 118,037 nodes; 113,821 edges; 86 divisions | UNUSED: attribution gate absent |
| D1-S05 PRIVATE_ROBUST | EXP122 | `a399a983…79922` / `61b7705f…20234` | 233,785 rows; 119,193 nodes; 114,592 edges; 73 divisions; degrees 1/2 | POST |

No honest exact-model OOF is claimed for any public-weight arm. EXP122's
private gate is mechanism diversity only: exact edge Jaccard to the EXP113
0.940 artifact is `0.837276`, but physical 2 um edge Jaccard is `0.904598`,
so this is modest diversity evidence rather than measured error decorrelation.
The selected source/output SHA values are absent from prior receipts. The
guard suite is `14 passed`; helper `py_compile` and `git diff --check` pass.
Each candidate dynamically discovers runtime `test/*.zarr`, performs inference,
emits one root `submission.csv`, and never reads a frozen public submission.

POST state is intentionally blank until each guarded helper call is followed
by a full live API object read. Continue on PENDING only; stop on any error,
terminal empty score, zero-byte terminal state, URL/version mismatch or quota
anomaly. This section is pre-registration evidence and is not a score claim.

### W1 D1 POST update 1

EXP119 was sent once through `scripts/submit_code_file_once.py` as ref
`56028571`. The immediate full API object is `SubmissionStatus.PENDING`, with
`public_score=null`, `private_score=null`, `error_description=null`,
`total_bytes=0`, and URL
`/code/rishabhr0y/941-biohub-fresh-adaptive-assoc?scriptVersionId=347093919`.
This is a permitted nonterminal state, not a score. Quota changed from `0/5`
used (`68` total) to `1/5` used (`69` total). The exact script-version gate
passed; the next independent candidate is EXP120.

### W1 D1 POST update 2

EXP120 was sent once through `scripts/submit_code_file_once.py` as ref
`56028590`. The immediate full API object is `SubmissionStatus.PENDING`, with
`public_score=null`, `private_score=null`, `error_description=null`,
`total_bytes=0`, and URL
`/code/analyticaobscura/biohub-lb-941?scriptVersionId=347182184`.
This is a permitted nonterminal state, not a score. Quota changed from `1/5`
used (`69` total) to `2/5` used (`70` total). The exact script-version gate
passed; the next independent candidate is EXP121.

### W1 D1 POST update 3

EXP121 was sent once through `scripts/submit_code_file_once.py` as ref
`56028627`. The immediate full API object is `SubmissionStatus.PENDING`, with
`public_score=null`, `private_score=null`, `error_description=null`,
`total_bytes=0`, and URL
`/code/anvithpothula/biohub-x54?scriptVersionId=347284486`.
This is a permitted nonterminal state, not private evidence. Quota changed from
`2/5` used (`70` total) to `3/5` used (`71` total). The exact script-version
gate passed; the next independent candidate is EXP122.

### W1 D1 POST update 4 and batch close

EXP122 was sent once through `scripts/submit_code_file_once.py` as ref
`56028644`. The immediate full API object is `SubmissionStatus.PENDING`, with
`public_score=null`, `private_score=null`, `error_description=null`,
`total_bytes=0`, and URL
`/code/rishabhr0y/biohub-adaptive-grouped-confidence-dominance-v2?scriptVersionId=347347742`.
This is a permitted nonterminal state, not private evidence. Quota changed from
`3/5` used (`71` total) to `4/5` used (`72` total). The exact script-version
gate passed. W1 D1 is closed with refs `56028571`, `56028590`, `56028627` and
`56028644`, all independently posted and immediately API-confirmed PENDING;
D1-S04 remains `UNUSED` because its required attribution gate was not met.
The one remaining quota slot is deliberately preserved.

Final live read at `2026-09-05T08:43:50.073258Z` confirms all four new refs are
still PENDING with no `error_description`, no public/private score and
`total_bytes=0`; URLs retain the four exact registered scriptVersionIds. The
final quota is `4/5` used, one available, `72` total, not limited by total.
The leaderboard remains 3,120 teams and `Big Cells` remains rank `201` at
`0.940`; after the batch the rank-1/16/155/311 scores are
`0.970/0.948/0.941/0.939`. No post-batch score delta can be reported yet.

## 2026-09-04 EXP112 incident close and EXP113-117 five-slot pre-registration

The September 3 batch is now terminal. EXP108-111 completed without errors at
`0.938 / 0.939 / 0.939 / 0.934`; the account frontier is `0.939`. EXP112
completed with an empty score, zero bytes, and the Kaggle hidden-rerun error
that the notebook hit an unhandled error. Exact source/metadata inspection
identified the concrete fault: the notebook requires
`pawanmali/biohub-learned-division-head-v1`, but the current kernel metadata
contains a blank dataset entry and does not attach that dataset. Its successful
public artifact was therefore not proof of a hidden-compatible rerun. The
dataset is also inaccessible to this account (`403`), so EXP112 is failed
evidence and is not retried.

The sole submission helper now fails closed before POST when the requested
ordinal is not the live current version, the remote source blob SHA differs
from the audited local file, the competition source is absent, a dataset
attachment is blank, or an explicit `/kaggle/input/datasets/owner/slug`
reference is not attached. The updated suite is `11 passed`; `py_compile` and
`git diff --check` pass.

Live September 4 quota is `0/5` used, five available, 63 total. Every selected
kernel is the exact live current blob, COMPLETE, Internet off, with competition
data and all explicit datasets attached. Each performs inference from the
runtime competition `test/*.zarr`, produces one root `submission.csv`, and
passes schema/types, finite-value, four-dataset, contiguous-ID, graph and SHA
audits. Today's non-interchangeable portfolio is pre-registered as follows:

1. EXP113 / `GOLD_PUBLIC-1`: Nusrati `0.940` v3, script ID `346951079`,
   source SHA `75a1f4cc...8dd9a`, output SHA `4e02ba49...64e93`. Audit PASS:
   234,517 rows / 119,365 nodes / 115,152 edges / 148 divisions. Exact
   four-embryo proxy is `0.9414`. Hypothesis: the attributed `0.940` safe-
   division configuration improves the `0.939` account frontier. Parent is
   EXP109/110. Gate: compare the exact account score with `0.939` and the
   approximate public-gold boundary; title attribution alone is not evidence.
2. EXP114 / `GOLD_PUBLIC-2`: Arnav `biohub-940e` v1, script ID `347140166`,
   source SHA `38458024...ce2c9`, output SHA `5b745a79...db5c`. Audit PASS:
   234,555 / 119,387 / 115,168 / 147. Exact four-embryo proxy is `0.9411`.
   Physical edge Jaccard versus EXP113 is `0.974487` at 2 um, so this is not a
   duplicate output. Hypothesis: its detector/association retune improves the
   public frontier while preserving the strong proxy. Parent is EXP113's
   family. Gate: require a valid hidden rerun and compare against `0.939`.
3. EXP115 / `PRIVATE_ROBUST-1`: Tomako conservative v1, script ID `347115869`,
   source SHA `455c8f0c...294d`, output SHA `a1be07f9...3d94`. Audit PASS:
   233,611 / 118,907 / 114,704 / 227. Exact four-embryo proxy is `0.9368`;
   physical edge/division Jaccard versus EXP110 is `0.988424 / 0.504274`.
   Hypothesis: the conservative harmonic association and intermediate division
   topology provide a lower-variance hedge against the public-tuned geometry
   arm. Gate: private retention is based on holdout and topology, not a tiny
   public delta.
4. EXP116 / `PRIVATE_ROBUST-2`: Notoverk wide-division/track-rescue v3, script
   ID `345877408`, source SHA `eb01b88a...f0a30`, output SHA
   `e7ee404d...e4905`. Audit PASS: 237,611 / 120,847 / 116,764 / 320. Exact
   four-embryo proxy is `0.9325`; physical edge/division Jaccard versus EXP110
   is `0.861254 / 0.211957`. Hypothesis: wide division plus gap-2 and guarded
   short-track rescue is a materially different recall hedge for private
   embryos. Gate: retain only for mechanism diversity after a valid hidden run;
   do not rank it above stronger holdout arms from the public score alone.
5. EXP117 / `PRIVATE_ROBUST-3`: Aagneye detector threshold `0.9375` v1, script
   ID `346917633`, source SHA `338f68a3...be71`, output SHA
   `d45640b8...f9cb`. Audit PASS: 241,793 / 123,098 / 118,695 / 312. No honest
   OOF score is claimed. Its stability evidence is the adjacent `0.90` run:
   physical edge/division Jaccard `0.947258 / 0.781513`; its diversity versus
   EXP110 is `0.822099 / 0.060680`. Hypothesis: select one representative from
   the sensitivity bracket as a high-recall detector hedge. Gate: submit only
   this representative, not the correlated threshold sweep, and retain for the
   private portfolio only if the hidden run is valid.

Rejected before POST: Rishabh SDEC12, QRZ dualwide, Ale 0.940 repro and Arnav
0.940 are exact output/source duplicates of EXP113; Luffy and Rishabh div45
duplicate prior account outputs; Aagneye v23 has stale receipts and a
non-contiguous actual CSV; Aagneye v25 is a correlated adjacent threshold;
Tomako's self-declared `candidate_unverified` promotion receipt is superseded
only by the independently inspected exact four-embryo validator, not by its
title; Pawan learned-division/recovery candidates have missing or blank
attachments; Heon is a training smoke run without a submission candidate.
Per-POST gate: inspect the full API object and URL script ID; continue on
PENDING, but stop on the first current-day error, terminal empty score, quota
anomaly, or version mismatch. Canonical receipt:
`reports/submission_batch_20260904.json`.

Post-submit receipt: all five candidates were sent exactly once through the
guarded helper without waiting for earlier PENDING jobs to score. Immediate
full API objects contain `total_bytes=0` and omit status, score and error fields,
which is recorded as PENDING rather than as success. Each URL matches the exact
pre-registered script ID:

- EXP113 ref `56004160`, script ID `346951079`;
- EXP114 ref `56004172`, script ID `347140166`;
- EXP115 ref `56004182`, script ID `347115869`;
- EXP116 ref `56004187`, script ID `345877408`;
- EXP117 ref `56004193`, script ID `346917633`.

Quota is `5/5` used, zero available, 68 total. No immediate API error,
duplicate POST, source-version mismatch or quota anomaly was observed. Later
scores and any terminal failure must be copied from the full live API objects;
PENDING is not a scored result.

### EXP116 system failure and EXP118 exact retry

EXP116 / ref `56004187` became terminal `ERROR` with zero bytes, no score, and
Kaggle's exact infrastructure message: `A system error. Please try
resubmitting to resolve the error and contact Kaggle Support if it persists.`
The failed attempt was refunded: live state returned to `4/5` used, one
available, 67 total. This is not the notebook-unhandled-error class seen in
EXP112.

Read-only revalidation found no candidate drift or exposed code fault. Kernel
`notoverkil/biohub-base-0937` remains COMPLETE at exact v3/script ID
`345877408`, Internet off; remote source SHA remains
`eb01b88a...f0a30`; every explicit dataset is attached. The same downloaded
output SHA `e7ee404d...e4905` again passes the full audit at 237,611 rows / four
datasets / 120,847 nodes / 116,764 edges / max degrees `1/2`.

The user's explicit instruction to check and resubmit the one failed solution
authorizes a one-time, ref-scoped exception for this Kaggle infrastructure
error only. EXP118 reuses PRIVATE_ROBUST slot 2 and the exact EXP116
kernel/version/source/output hypothesis; it is not a sixth portfolio
candidate. Description: `EXP118 RETRY EXP116 PRIVATE_ROBUST system error`.
The helper exception accepts only ref `56004187` when status is ERROR, score is
empty, bytes are zero, and the error string exactly matches Kaggle's retryable
system error. Any other current-day failure still blocks. Gate: submit exactly
once, inspect the full API object immediately, and stop if the error repeats.

EXP118 post-submit receipt: sent exactly once through the ref-scoped guarded
path as ref `56008261`. The immediate full API object omits status, score and
error fields, has `total_bytes=0`, and resolves to the exact expected URL
script ID `345877408`; this is PENDING, not success. Quota is `5/5` used, zero
available, 68 total. EXP116 remains preserved as failed evidence. Do not issue
another retry if EXP118 returns the same system error without new user
direction and a fresh diagnosis.

## 2026-09-03 EXP108-112 five-slot pre-registration

The September 2 batch closed cleanly: EXP103-107 are COMPLETE without errors
at `0.935 / 0.936 / 0.933 / 0.933 / 0.931`. EXP104 raises the account frontier
to `0.936`. Live quota is `0/5` used with five available and 58 total. The
current public leaderboard's approximate tenth-place gold boundary is `0.949`.

All selected sources are the exact live current Kaggle blobs and ordinal
versions, COMPLETE with Internet off and competition data attached. Every
source dynamically reads runtime `test/*.zarr` and performs model inference;
none consumes a frozen public submission. Downloaded root `submission.csv`
files pass exact schema/types, finite-value, four-dataset, graph-invariant and
SHA audits. Guard tests are `7 passed`.

Today's pre-registered portfolio:

1. EXP108 / `GOLD_PUBLIC-1`: Nusrati `0.938` v1, script ID `346859144`,
   source SHA `ea9de93c...d60e2a`, output SHA `650be35e...534587`. Audit PASS:
   234,371 rows / 119,339 nodes / 115,032 edges / 47 divisions. This tests the
   attributed `0.938` low-division profile against account `0.936`.
2. EXP109 / `GOLD_PUBLIC-2`: Ali V19B safe-div-parent-9um v1, script ID
   `346872771`, source SHA `376bbffa...4bfa5`, output SHA
   `0696a283...57baa2`. Audit PASS: 234,515 / 119,365 / 115,150 / 146.
   Exact four-embryo proxy is `0.9414`; test the reported `0.939` arm.
3. EXP110 / `PRIVATE_ROBUST-1`: Ali V19C sister-distance-14um v1, script ID
   `346873612`, source SHA `363139b1...08fd9`, output SHA
   `b4d8319b...943feb`. Audit PASS: 234,482 / 119,358 / 115,124 / 125.
   Exact four-embryo proxy is `0.9414`; physical edge/division Jaccard versus
   private C41 is `0.965822 / 0.339744`, supporting division complementarity.
4. EXP111 / `PRIVATE_ROBUST-2`: Sushanth EMA-velocity relinker v2, script ID
   `346413832`, source SHA `4b575f3b...89463e`, output SHA
   `628199ec...47ba64`. Audit PASS: 234,197 / 119,145 / 115,052 / 288.
   Exact four-embryo proxy is `0.9365`; physical edge Jaccard to EXP104 is
   `0.945672`, a material motion/linking change.
5. EXP112 / `PRIVATE_ROBUST-3`: Pawan learned division head v2, script ID
   `346880985`, source SHA `00476246...217ef`, output SHA
   `0aaea0c5...7a52f5`. Audit PASS: 237,254 / 122,560 / 114,694 / 20.
   The exact log reports a no-test-overlap 19-well score `0.9338` (not
   independently rerun here); physical edge Jaccard to EXP104 is `0.502774`,
   providing a genuinely different learned image-crop division mechanism.

Rejected before POST: Tomako is source-identical to EXP103; Ali V19A is
output-identical to EXP108; V19D union is output-identical to EXP109; V19D-wide
and V19E have exact holdout proxies `0.9210/0.9201` with zero division Jaccard;
Flex v11 is too close to EXP104 (`0.999670` physical edge Jaccard); Sushanth
rescue-localCV is ERROR with no output. Per-POST gate remains full API and URL
script-ID inspection, continuing on PENDING but stopping on the first error,
terminal empty score, or version mismatch. Canonical receipt:
`reports/submission_batch_20260903.json`.

Post-submit receipt: all five candidates were sent exactly once through the
guarded helper. Immediate full API objects are PENDING with empty
`error_description`, empty scores, `total_bytes=0`, and exact URL script IDs:

- EXP108 ref `55973111`, script ID `346859144`;
- EXP109 ref `55973125`, script ID `346872771`;
- EXP110 ref `55973135`, script ID `346873612`;
- EXP111 ref `55973141`, script ID `346413832`;
- EXP112 ref `55973147`, script ID `346880985`.

Quota is `5/5` used, zero available, 63 total. No immediate error, terminal
empty score, duplicate POST, or source-version mismatch was observed. PENDING
is permitted; later scores must be read from full live API objects.

## 2026-09-02 EXP103-107 five-slot pre-registration

Live Kaggle state before mutation is `0/5` used, five available, 53 total;
the latest submission EXP102 is COMPLETE `0.934` with no error. The exact
current remote source blob, ordinal version, public page script-version ID and
downloaded output were checked for every candidate. All five kernels completed
with Internet off and competition data attached. Each dynamically discovers
runtime `test/*.zarr`, performs inference, asserts runtime/output dataset-ID
equality, and emits one root `submission.csv`. The guarded source audit passes
for all five and its test suite is `7 passed`.

Today's non-interchangeable portfolio is pre-registered as follows:

1. EXP103 / `GOLD_PUBLIC-1`: Cloud current v1 exact reproduction, script ID
   `346554587`, source SHA `1c169787...bfe177`, output SHA
   `f9d42e27...279c4`. Audit PASS at 234,871 rows / 119,517 nodes / 115,354
   edges / 219 divisions. Honest four-embryo proxy is `0.9379`. Its attributed
   `0.948` title is a hypothesis, not account evidence; compare the exact score
   against the account's `0.934` and approximate public-gold `0.949` boundary.
2. EXP104 / `GOLD_PUBLIC-2`: Nusrati current v10 frontier, script ID
   `346568302`, source SHA `4b86c247...7036883`, output SHA
   `665e54ac...870812`. Audit PASS at 234,691 rows / 119,426 nodes / 115,265
   edges / 215 divisions. Honest four-embryo proxy is `0.9376`; test whether its
   conservative low-division topology improves the scored anchor.
3. EXP105 / `PRIVATE_ROBUST-1`: C41 retrained temporal detector v1, script ID
   `346606370`, source SHA `85562b51...171301`, output SHA
   `9320b28c...dfa64a`. Audit PASS at 234,096 rows / 119,097 nodes / 114,999
   edges / 293 divisions. Four-embryo proxy `0.9399`; physical edge Jaccard to
   EXP098 is `0.971354`, confirming a material detector-coordinate mechanism.
4. EXP106 / `PRIVATE_ROBUST-2`: C42 PU appearance detector v1, script ID
   `346611908`, source SHA `1b93b6e0...f86cd8`, output SHA
   `fe09f4d7...62be4e`. Audit PASS at 234,562 rows / 119,337 nodes / 115,225
   edges / 291 divisions. Four-embryo proxy `0.9373`; this is the conservative
   independently learned appearance-recovery hedge, not a public-delta claim.
5. EXP107 / `PRIVATE_ROBUST-3`: Flex agreement-gated dual-seed v7, script ID
   `346599770`, source SHA `2a5a7ee3...2d2c3d`, output SHA
   `72317188...a2de27`. Audit PASS at 236,140 rows / 120,127 nodes / 116,013
   edges / 316 divisions. Four-embryo proxy `0.9358`; physical edge Jaccard to
   EXP098 is `0.936197`, providing the portfolio's strongest mechanism-diverse
   seed-ensemble hedge.

C43 is explicitly rejected from today's private allocation: it is nearly
identical to C41 (physical edge Jaccard `0.999235`, division Jaccard `1.0`).
Per-POST gate: inspect full API fields and URL script ID; continue on PENDING,
but stop on the first error, terminal empty score, or exact-version mismatch.
Canonical receipt: `reports/submission_batch_20260902.json`.

Post-submit batch receipt: all five candidates were sent exactly once through
the guarded helper. Their immediate full API objects are PENDING with empty
`error_description`, empty scores, `total_bytes=0`, and exact URL script IDs:

- EXP103 ref `55952817`, script ID `346554587`;
- EXP104 ref `55952820`, script ID `346568302`;
- EXP105 ref `55952831`, script ID `346606370`;
- EXP106 ref `55952836`, script ID `346611908`;
- EXP107 ref `55952843`, script ID `346599770`.

Quota is now `5/5` used, zero available, 58 total. No immediate error,
terminal empty score, duplicate POST, or source-version mismatch was observed.
PENDING is permitted by the user-authorized batching policy; do not infer a
score until later full API objects become terminal.

## 2026-09-02 five-result close and 2/3 medal portfolio

Live Kaggle API closes the September 1 batch without errors:

- EXP098 / `55931493`: COMPLETE `0.934`, `204,778,810` bytes;
- EXP099 / `55940151`: COMPLETE `0.933`, `204,498,940` bytes;
- EXP100 / `55941347`: COMPLETE `0.933`, `205,345,991` bytes;
- EXP101 / `55941357`: COMPLETE `0.931`, `204,290,758` bytes;
- EXP102 / `55941369`: COMPLETE `0.934`, `204,778,810` bytes.

EXP102's successful score does not erase its recorded source-version mismatch:
its submitted URL used script ID `346407867`, while the audited current page
source was `346424066`. Treat its LB result as valid account evidence but not
as proof that the audited current source produced it.

The account frontier is a stable `0.934`, which the user identifies as the
bronze zone. Five new daily slots are available. From now on the quota is a
non-interchangeable portfolio:

- `GOLD_PUBLIC-1` and `GOLD_PUBLIC-2`: actively search for the current public
  gold-medal boundary. Allowed work includes improving or repairing open
  solutions, exact version-audited reproduction of stronger notebooks,
  controlled retuning, and justified ensembles. Public LB is a direct search
  signal for this track, but hidden-compatible runtime inference remains
  mandatory.
- `PRIVATE_ROBUST-1`, `PRIVATE_ROBUST-2`, and `PRIVATE_ROBUST-3`: search for a
  strong private-leaderboard portfolio after competition close. Promotion
  requires honest embryo-level holdout/OOF evidence, stability/sensitivity
  checks, or a credible mechanism-diversity rationale. Tiny public deltas,
  titles, and correlated copies are insufficient.

Every pre-submit receipt must name its track and slot. Unused slots may not be
borrowed between tracks just to exhaust quota. Safety stop conditions override
the allocation. Historical experiment queues below are evidence, not today's
instructions.

## 2026-09-01 EXP100-102 independently audited remaining batch

Live state before mutation: EXP098 is COMPLETE `0.934`; EXP099 / `55940151`
is PENDING with no recorded error; quota is `2/5` used and three slots remain.
Under the user-authorized batching policy, a PENDING candidate does not block
another independently pre-registered and audited candidate. The batch must
still stop immediately on any recorded error or terminal empty score.

Three candidates are pre-registered, in this order:

1. EXP100 C37 temporal-dim rescue. Hypothesis: temporally conditioned rescue
   improves difficult dim-cell recall without changing the frozen association
   family. Parent/comparator: EXP098 C35 `0.934` and pending EXP099 C36.
   Kernel `tangai1/biohub-c37-temporal-dim-rescue-20260831`, version `1`, live
   script version ID `346355373`, COMPLETE, Internet off. Source SHA
   `7648f4a30b5c9740ac58f38538d471a7973b2bd6bd649f34d771ec2a9719d7ab`;
   output SHA `d4ae966f734c8b2135b6f121f97e406c6bbaa092ba96d3833b4e08879848d544`.
   Audit PASS: 235,642 rows / 119,882 nodes / 115,760 edges / 295 divisions /
   four runtime datasets / degrees `1/2`.
2. EXP101 C39 learned marginal verifier. Hypothesis: the frozen learned
   structural verifier improves marginal detections through a mechanism
   distinct from temporal-dim rescue. Parent/comparator: EXP098 C35 `0.934`.
   Kernel `tangai1/biohub-c39-marginal-verifier-20260901`, version `1`, live
   script version ID `346435959`, COMPLETE, Internet off. Source SHA
   `7710e80e0bd7be4005466c5a169f3cb352dd105ece443e949d6c0c530b169ac0`;
   output SHA `84c554cf7479b3e7d98cf2172bef0340516cc6f88645e6eab8c297e0e29a3842`.
   Audit PASS: 234,364 rows / 119,239 nodes / 115,125 edges / 295 divisions /
   four runtime datasets / degrees `1/2`.
3. EXP102 attributed `0.935` reproduction. Hypothesis: its materially lower
   division count improves precision relative to EXP098 while retaining nearly
   the same edge set; source title/rank is attribution, not account evidence.
   Parent/comparator: EXP098 C35 `0.934`. Kernel
   `leolin05/biohub-0-935-reproduction-audit-and-validation`, version `1`, live
   script version ID `346424066`, COMPLETE, Internet off. Source SHA
   `d514fce0896dd766f4258039ed07be68666fddf368db1adeacd2d8e67b7c0a9c`;
   output SHA `f9d42e27f6b2cbeba1ea8f433087fba45be7742b41b38d271c4109339e9279c4`.
   Audit PASS: 234,871 rows / 119,517 nodes / 115,354 edges / 219 divisions /
   four runtime datasets / degrees `1/2`; division Jaccard to C35 `0.644231`.

All three sources dynamically read competition `test/*.zarr`, perform runtime
inference, and include a runtime/output dataset-ID equality audit; none reads a
frozen public submission. Guard suite: `7 passed`. Expected output for each is
one root `submission.csv`. Per-POST gate: inspect ref, status, score, error,
bytes, URL and quota; continue on PENDING or a valid scored completion, but stop
the batch on the first error or terminal empty score. C38 is omitted as a more
correlated joint child; C40 is rejected as a near-duplicate of C39.

Canonical receipt: `reports/submission_batch_20260901_remaining.json`.

EXP100 post-submit receipt: submitted once as ref `55941347`; full API object
is `PENDING`, with no error, no score, `total_bytes=0`, URL script version
`346355373`, and quota `3/5` used / two available. No anomaly is recorded, so
the PENDING-compatible batch policy permits EXP101.

EXP101 post-submit receipt: submitted once as ref `55941357`; full API object
is `PENDING`, with no error, no score, `total_bytes=0`, URL script version
`346435959`, and quota `4/5` used / one available. No anomaly is recorded, so
the PENDING-compatible batch policy permits EXP102.

EXP102 post-submit receipt and immediate correction: submitted once as ref
`55941369`; full API object is `PENDING`, with no error, no score,
`total_bytes=0`, and quota `5/5` used. The submission URL resolves ordinal
version `1` to script version ID `346407867`, not the pre-registered current
page ID `346424066`. Therefore the pre-registered local source SHA and output
audit do **not** establish exact identity of the historical source actually
submitted. Historical pull returned HTTP 403, so this cannot presently be
reconciled. This is a source-version anomaly: preserve the receipt, make no
claim of exact-source verification for EXP102, and stop the batch. EXP099-101
remain PENDING without recorded errors at this snapshot.

## 2026-09-01 submission batching policy correction

User authorization removes the serial wait-for-score rule. A PENDING earlier
submission no longer blocks another independently pre-registered,
hidden-compatible and fully audited candidate, and a child is not required to
wait for a scored parent. The guarded helper still rejects
frozen-public-output wrappers, duplicate descriptions, exhausted quota and any
earlier same-day submission with a recorded API error. Full API fields must
still be inspected and recorded after every POST. This is a protocol change;
it does not retroactively validate failed EXP094–097 or authorize correlated
sweeps without hypotheses.

## 2026-09-01 EXP098 result and EXP099 adaptive-detection probe

EXP098 / ref `55931493` is COMPLETE with public score `0.934`, no error, and
`204,778,810` scored bytes. This beats its scored EXP093 parent (`0.933`) and
passes the pre-registered promotion gate. Live quota before the next mutation
is `1/5` used, four available.

EXP099 is the sole newly authorized candidate:

- hypothesis: C36's pre-registered adaptive secondary detection fusion improves
  the scored C35/EXP098 `0.934` parent while association and division settings
  remain frozen;
- parent: EXP098 / `55931493`, COMPLETE `0.934`, no error;
- kernel: `tangai1/biohub-c36-adaptive-detection-20260831`, version `1`, live
  script version ID `346353192`, COMPLETE, Internet off, T4 GPU, competition
  source attached;
- source: `outputs/research/frontier_20260901/c36/biohub-c36-adaptive-detection-20260831.ipynb`,
  exact SHA-256 `4f1c02ad5a034c93542ce47b7dd5194b640a88a14c566ea68b1e5ba68afd73b7`;
- hidden dataflow: hard-bound runtime competition `test/*.zarr` discovery,
  detector/association inference, and strict equality between runtime and
  output dataset IDs; no frozen public submission input;
- expected output: one root `submission.csv`; downloaded artifact SHA-256
  `00d75136ebd551885279267863935eb668fd0fffae274bfab2f8c0e1cdaebcb4`;
- audit: 233,759 rows / 118,927 nodes / 114,832 edges / 287 divisions / four
  datasets / max degrees `1/2`, status PASS; guard suite `7 passed`;
- diversity versus EXP098: physical node/edge/division Jaccard at `2 µm`
  `0.972789 / 0.966522 / 0.832808`;
- promotion gate: submit EXP099 once, query its full API object, and stop until
  it is COMPLETE, error-free, non-empty, and scored. Do not submit C37 or C38
  merely because three daily slots remain.

Post-submit receipt: EXP099 was sent once through the guarded path as ref
`55940151`. Its full account object is `PENDING`, with no error, no score,
`total_bytes=0`, and URL script version `346353192`; quota is now `2/5` used
with three slots available. Queue gate is `WAIT`: C37, C38, and any fourth
candidate remain unauthorized until EXP099 is terminal and scored.

Read-only descendant preparation while EXP099 runs:

- C37 temporal-dim rescue: kernel COMPLETE; script version ID `346355373`;
  source SHA `7648f4a30b5c9740ac58f38538d471a7973b2bd6bd649f34d771ec2a9719d7ab`;
  output SHA `d4ae966f734c8b2135b6f121f97e406c6bbaa092ba96d3833b4e08879848d544`;
  audit PASS at 235,642 rows / 119,882 nodes / 115,760 edges / 295 divisions /
  degrees `1/2`; physical node/edge/division Jaccard versus C36 at `2 µm` is
  `0.963631 / 0.955844 / 0.796296`;
- C38 joint child: kernel COMPLETE; script version ID `346348268`; source SHA
  `3f833f85ecff95275e92980a342c54032d3e9e4c6485df8d7e288cab5e76d8af`;
  output SHA `88fef9c151ae9f5f95f51851d63a68e209d8caa5120133984f9761d97298f909`;
  audit PASS at 234,058 rows / 119,078 nodes / 114,980 edges / 293 divisions /
  degrees `1/2`; physical node/edge/division Jaccard versus C36 at `2 µm` is
  `0.984897 / 0.981138 / 0.901639`.

These receipts are preparation only. C37 requires EXP099's terminal scored
promotion result; C38 requires scored evidence from its parent mechanisms.

Fresh read-only frontier audit found two later Tangai candidates and one
independently attributed reproduction:

- C39 learned marginal verifier: COMPLETE, script version ID `346435959`,
  source SHA `7710e80e0bd7be4005466c5a169f3cb352dd105ece443e949d6c0c530b169ac0`,
  output SHA `84c554cf7479b3e7d98cf2172bef0340516cc6f88645e6eab8c297e0e29a3842`,
  audit PASS at 234,364 rows / 119,239 nodes / 115,125 edges / 295 divisions /
  degrees `1/2`;
- C40 temporal student: COMPLETE, script version ID `346446706`, source SHA
  `64c16e244d17e09e3b09e508d899fc846778f500407e6a462992d962627d5b13`,
  output SHA `81d4371ab84d58836192c526a5ac5052fccc98a14aafe25a2d2366c3ae917eec`,
  audit PASS at 234,443 rows / 119,279 nodes / 115,164 edges / 294 divisions.
  Reject C40 as a separate LB probe because its physical edge Jaccard to C39
  is `0.998585`;
- Leolin attributed `0.935` reproduction: COMPLETE, script version ID
  `346424066`, source SHA
  `d514fce0896dd766f4258039ed07be68666fddf368db1adeacd2d8e67b7c0a9c`,
  output SHA `f9d42e27f6b2cbeba1ea8f433087fba45be7742b41b38d271c4109339e9279c4`,
  audit PASS at 234,871 rows / 119,517 nodes / 115,354 edges / 219 divisions /
  degrees `1/2`. Versus C35 its physical node/edge/division Jaccard is
  `0.994272 / 0.992275 / 0.644231`, so its division policy is materially
  different despite near-identical edges.

C39 and the attributed reproduction are possible later choices, not
pre-authorized submissions. Their source dataflow and exact versions must be
rechecked after all earlier serial gates resolve.

## 2026-09-01 EXP098 clean C35 fallback-detection probe

Live account state before mutation: EXP093 / `55907915` is COMPLETE `0.933`,
with no error and `204,403,440` scored bytes. EXP094–097 remain invalid and
provide no evidence. The new UTC day has `0/5` used and five available slots.

EXP098 is pre-registered as the first and only immediately authorized probe:

- hypothesis: Tangai C35's corrected full-inference fallback/provenance path and
  `0.15` bidirectional weight improve the scored C33 `0.933` anchor without a
  hidden-test wrapper or metric hack;
- parent: EXP093 exact C33 anchor, account score `0.933`;
- kernel: `tangai1/biohub-c35-fallback-detection-cleanroom-20260831`, version
  `1`, COMPLETE, Internet off, T4 GPU, runtime competition source mounted;
- source: `outputs/research/frontier_20260901/c35/biohub-c35-fallback-detection-cleanroom-20260831.ipynb`,
  exact SHA-256 `678cfbae3c03cddb53621326f09f8b65d1fb5d4149ce2dd08a2e92487b229878`;
- hidden dataflow: dynamically enumerate competition `test/*.zarr`, perform
  detector/association inference for every runtime movie, and assert exact
  equality between runtime and output dataset IDs; no parent `submission.csv`
  artifact is read;
- expected output: one root `submission.csv`; downloaded public artifact SHA
  `5c2b16467f9aac1519df392364abcf755ac6be5e3426a3bc089487cb1c77af6c`;
- audit: 234,507 rows / 119,309 nodes / 115,198 edges / 294 divisions / four
  datasets / max degrees `1/2`, schema, finite values, endpoints and time-step
  checks PASS; full repository suite `28 passed`;
- diversity versus EXP093: physical node/edge/division Jaccard
  `0.973898 / 0.968318 / 0.794479` at `2 µm`;
- promotion gate: submit once, then stop until the full account object is
  terminal, error-free, non-empty and scored. Promote the C36/C37 descendants
  only after EXP098's score is observed; do not fill quota if it loses.

Canonical pre-submit receipt: `reports/submission_batch_20260901.json`.

Post-submit receipt: EXP098 was sent once through the guarded path as ref
`55931493`. The full account object remains `PENDING`, with no error, no score,
`total_bytes=0`, and URL script version `346223185`; daily quota is `1/5` used
and four slots remain. Promotion gate is `WAIT`: no EXP099 or descendant may be
submitted until EXP098 is terminal, error-free, and has a non-empty account
score. A reboot or lost chat context does not waive this gate.

C36 was prepared read-only while waiting, but is not authorized for POST. The
current Kaggle kernel is COMPLETE with Internet off and the competition source
attached. Pulled source SHA-256 is
`4f1c02ad5a034c93542ce47b7dd5194b640a88a14c566ea68b1e5ba68afd73b7`;
downloaded `submission.csv` SHA-256 is
`00d75136ebd551885279267863935eb668fd0fffae274bfab2f8c0e1cdaebcb4`.
The artifact audit passes with 233,759 rows, four datasets, 118,927 nodes,
114,832 edges, 287 divisions, and max degrees `1/2`; guard tests are `7 passed`.
Versus C35, physical node/edge/division Jaccard at `2 µm` is
`0.972789 / 0.966522 / 0.832808`. Its exact Kaggle script version and parent
promotion gate must still be revalidated after EXP098 scores and before POST.

## 2026-08-31 incident correction and fail-closed recovery

The earlier section below incorrectly treated EXP094–097 as completed outputs
whose scores had not populated. Live full Kaggle API objects prove all four
failed: refs `55908273`, `55908462`, `55908629`, and `55908683` have
`status=COMPLETE`, `public_score=null`, `total_bytes=0`, and the error
`submission file with incorrect format`.

Root cause is hidden incompatibility, not CSV syntax on the public run. The
EXP094–097 wrapper reads frozen public parent `submission.csv` artifacts by SHA
and never reads the runtime competition test set. Its local/public four-dataset
schema, topology, and hash checks were real but insufficient: hidden rerun
still produced public dataset IDs. After the first failure, the agent did not
inspect `error_description` and sent three more variants; it also failed to
wait for the still-PENDING EXP093 anchor. EXP094–097 are invalid, have no LB
evidence, and must not be resubmitted in this form.

The current recovery state and mandatory submission protocol are frozen in
`reports/RECOVERY_20260831.md` and `AGENTS.md`. Submission is now serial and
fail-closed: dynamic hidden-test inference, exact source SHA, scored-parent gate,
and full post-submit API inspection are required before another slot can be
spent.

## 2026-08-31 verified 0.933 anchor and own coordinate ensemble batch

August 30 results are complete: EXP088 EMA `0.926`, EXP089 controlled EMA-0.5
`0.924`, EXP090 edge-threshold-0.40 `0.928`, EXP091 division-heavy `0.926`,
and EXP092 fine-tuned-linker/D4 `0.900`. The only architecture-diverse arm was
also the weakest; diversity without quality is not a final-submission hedge.

Current-version cards and exact outputs were checked rather than trusting
titles. Tangai C33 v1 is a genuine **`0.933`** full-inference result. Evgen's
current v22 is `0.930`; its page's best `0.933` belongs to historical v20.
Flex agreement-gated v1 is `0.929`. C33 has physical edge overlap `0.857571`
to EXP083 and `0.961146` to Evgen v22. Anhad's new output is effectively a C33
duplicate (`0.999392` physical edge overlap), and Reyhan is also near-duplicate
(`0.976986`), so neither received a slot.

Five code submissions are registered:

- EXP093 / `55907915`: exact audited Tangai C33 v1 anchor; source score `0.933`.
- EXP094 / `55908273`: **our** coordinate-only C33/C29 ensemble, mutual-nearest
  gate `2 µm`, `alpha=0.25`; 112,531/119,132 nodes matched, mean applied shift
  `0.0534 µm`.
- EXP095 / `55908462`: same frozen matches with `alpha=0.50`; mean applied shift
  `0.1067 µm`.
- EXP096 / `55908629`: **our** C33/C30 `alpha=0.25` coordinate ensemble;
  115,436 matches, mean applied shift `0.0212 µm`.
- EXP097 / `55908683`: **our** C33/Comb2 `alpha=0.25` coordinate ensemble;
  113,618 matches, mean applied shift `0.1427 µm`. Comb2 supplies the most
  structurally different localization donor in this batch.

All four own arms preserve the exact C33 node IDs, timepoints, 115,046 edges
and 291 divisions. Kaggle CPU versions 3–6 each emitted one root
`submission.csv`; downloaded outputs reproduce the pre-registered Linux SHA
and pass four-movie schema, endpoint and degree `1/2` audits. A multi-output
V2 also reproduced all four artifacts, but Kaggle code submission accepts only
the root filename. A direct file POST and the multi-output POST were rejected
with HTTP 400 and consumed no quota. Final quota: five used, zero remaining,
48 lifetime submissions. Scores were not yet populated at freeze time.

Rejected before LB: unanimous C33 edge replacements proposed four changes.
Three made both edge length and constant-velocity residual substantially worse;
the fourth shortened neither criterion jointly. The edge arm was not submitted.
Exact honest OOF remains unavailable for EXP093–097; coordinate-only LB deltas
measure localization changes on the four public movies, not private stability.
Canonical receipt: `reports/submission_batch_20260831.json`.

## 2026-08-30 final-selection diagnostic batch

August 29 results are complete: EXP083 Stephen **0.931**, EXP084 SDW85
`0.929`, EXP085 Evgen v15 `0.928`, EXP086 Anvith `0.928`, and our EXP087
SDW90 `0.926`. The controlled `0.85 -> 0.90` detector-weight step therefore
worsened the displayed LB by `0.003`; the useful detector-mixture region ended
before `0.90`. EXP087's leaky train-movie proxy predicted the wrong direction
and is not OOF.

The next five slots are allocated by mechanism rather than notebook title:

- EXP088 / `55882197`: full four-frame averaged-motion EMA, PENDING.
- EXP089 / `55882683`: our controlled EMA interpolation `1.0 -> 0.5`, PENDING.
  No other executable setting changes. Artifact audit: 122,219 nodes / 117,945
  edges / 269 divisions, SHA `563861dc...609be`; physical edge overlap to
  EMA-1.0 is `0.981219`.
- EXP090 / `55882198`: edge-candidate threshold `0.48 -> 0.40`, PENDING.
  Physical edge overlap to EXP083 is `0.939815`, so this is a sensitivity test.
- EXP091 / `55882203`: division-heavy full-inference graph, PENDING; 384
  predicted divisions and physical division overlap `0.490486` to EXP083.
- EXP092 / `55882642`: offline reproduction of public fine-tuned linker weights
  plus D4 TTA, PENDING. Its 4-movie artifact is byte-identical to the reviewed
  public output (SHA `740f7c83...3ca6`), and has physical edge overlap `0.744633`
  to EXP083. It is the batch's only serious structural hedge. The original
  source version had Internet enabled and was not submitted; our exact
  executable reproduction ran with Internet disabled.

Rejected before LB: Aagneye Detector3D completed with only 44 nodes from one of
four movies; Grafael harmonic and Notoverkil base are exact duplicates of
EXP084 and EXP083; Akihiro is a near-duplicate of EXP088 (`0.972646` physical
edge Jaccard). All three registered artifacts pass four-movie schema, endpoint
closure and maximum-degree checks. Exact honest OOF remains unavailable.
Final-selection policy is frozen in `reports/FINAL_SELECTION_20260830.md`.
All five submissions are registered exactly once and PENDING. Daily quota:
five used / zero available; lifetime account submissions: 43.

## 2026-08-29 clean frontier, correlation audit and five authorized submissions

Yesterday's account results are complete: EXP078 SDW70 **0.928**, EXP079 Flex v22 **0.928**, EXP080 SDW75 **0.928**, EXP081 VEL10 **0.926**, EXP082 MTL8 **0.923**. The three equal `0.928` scores do not constitute three independent private-stability checks, and the leaderboard's three-decimal display can hide small raw-score differences. On the four public test movies SDW70 versus SDW75 has physical-node/edge Jaccard `0.970384/0.963701`; SDW70 versus Flex v22 is `0.861317/0.829558`. All use the same public dual-seed TemporalUNet, DeepCenter and harmonic-association lineage. The evidence is consistent with a broad detector-mixture plateau near `0.70–0.75`, plus a different checkpoint/division-veto route in Flex, rather than three separate breakthroughs.

The current clean public frontier is Stephen v1 at an actual displayed **0.931**. Its title is not used as evidence: the version card and full source were inspected. The notebook performs full inference, does not branch on hidden test identity, and contains no public-CSV wrapper or metric-hack nodes. It changes division geometry, reverse weight and detector mixture but remains correlated with Flex v22: physical-node/edge Jaccard `0.925603/0.910946`. SDW85's title says `0.938`, but its actual version score is **0.929**.

Five new experiments were frozen before submission in `reports/submission_batch_20260829.json`:

- EXP083: Stephen clean frontier v1, author `0.931`, submission `55858606`, PENDING.
- EXP084: SDW85 v1, actual author `0.929`, submission `55858609`, PENDING.
- EXP085: Evgen v15, author `0.928`, submission `55858612`, PENDING.
- EXP086: Anvith v1, author `0.928`, submission `55858614`, PENDING.
- EXP087: our controlled SDW90 continuation, submission `55859147`, PENDING. The reviewed SDW85 architecture, weights and postprocessing are unchanged; exactly one environment value moves secondary detection-logit weight `0.85→0.90`. Kaggle v1 completed, and its output passed audit at 119,722 nodes / 115,437 edges / 251 divisions, SHA `e2bdb2c4…6ab5`. Physical node/edge Jaccard versus SDW85 is `0.973106/0.967084`, confirming this is a boundary probe rather than a diverse model.

EXP083–086 are explicitly source-attributed public reproductions, not neural models trained by us. EXP087 is our controlled parameter fork of the attributed public pipeline, not a newly trained architecture. Exact honest OOF remains null for all five because the public checkpoints were trained using all labelled competition movies. EXP087's built-in four-train-movie proxy is `0.9294` (`0.9183` adjusted edge Jaccard, `0.1111` division Jaccard), but is explicitly leaky and not OOF. The graph-overlap audit measures prediction correlation, not error correlation and not private score. Twenty-one local tests pass. Kaggle rewrote notebook metadata and appended empty cells for EXP087, but a fail-closed audit proves all ten nonempty executable cells remain exact and ordered, with one unique `0.90` anchor. A nonfatal nbconvert schema warning after v1 output was fixed in the local builder. Every submitted artifact passed four-dataset schema, endpoint-closure and degree `1/2` checks. Daily quota: five used / zero available; total account submissions 38.

## 2026-08-28 results and five authorized submissions

Confirmed account scores: EXP073 SDW60 / `55808574` **0.927**, EXP074 Anhad v21 / `55808576` **0.927**, EXP075 Evgen v11 / `55808638` **0.927**, EXP076 SEC25 / `55808636` **0.923**. Best is now **0.927**. These remain public-source reproductions; exact submitted-model OOF is unavailable.

EXP077 completed all four full movies on CPU in `1218.073 s` (20.30 minutes), no failures. Local-flow minus weak-registration is exactly `0.0` on both embryos and pooled. Pooled registered/weak/local-flow/ILP scores: `0.624991 / 0.624970 / 0.624970 / 0.613500`. Local-flow does alter graphs, but not the annotated metric counts on these four movies. No GT divisions occur in this pilot, so it provides no division-recall evidence. No own-method promotion follows; it establishes CPU feasibility only. These abbreviated no-TTA weights must not be assigned as CV scores to the 0.927 public models.

Five candidates are frozen before submission in `reports/submission_batch_20260828.json`, with raw source notebooks archived in git under `research/frozen_sources_20260828/`. All five complete public outputs pass schema/topology checks, have distinct hashes, and have source/metadata versions checked before and after output download. Author score is taken from the version card, not the title. Eighteen local tests pass, including version/source-drift and five-submission guards.

- H066 / EXP078: SDW70 v1 (`rishabhr0y/biohub-934-sdw70`), secondary detection weight 0.70. Author **0.928**, not 0.934. Main frontier probe.
- H067 / EXP079: Flex v22 (`flexonafft/biohub-harmonic-fusion`), best epoch-2 DeepCenter checkpoint with safe-division veto on the inherited gap3/6.5um family. Author **0.928**. Do not infer effective bidirectional inference merely from an added environment flag.
- H068 / EXP080: SDW75 v1 (`arnav170/biohub-sdw75`), detector-mixture extrapolation to 0.75. No author score displayed; exploratory.
- H069 / EXP081: VEL10 v1 (`arnav170/biohub-vel10`), full constant-velocity extrapolation instead of half-velocity on the 0.475 detector mixture. No author score displayed; exploratory.
- H070 / EXP082: MTL8 v1 (`arnav170/biohub-mtl8`), minimum component length 8 instead of 6, preserving division components. Author **0.923**. Lower-priority sensitivity control, not a justified record or private-stability claim.

All five are attributed public reproductions, not new neural models trained by us. Our newly implemented local-flow candidate remains separate and unsubmitted. GPU training quota is still exhausted until 2026-08-29 00:00 UTC; no GPU training or paid compute is launched. Anhad v22 is excluded as code-identical to submitted v21; Evgen v13 (0.923/private source), Black Cat B (0.884), and the boundary-rescue lane without a verified frontier result are not selected.

Submission status: all five registered once and API-confirmed PENDING: EXP078 `55836059`, EXP079 `55836064`, EXP080 `55836067`, EXP081 `55836071`, EXP082 `55836074`. Account scores are not yet available. Daily quota is now 5 used / 0 available, total account submissions 33. An initial SSL failure occurred during read-only preflight; the account list was checked before retrying, so no submission request was blindly repeated. User authorization: next five submissions.

## 2026-08-27 CPU / own-method follow-up

Attribution: EXP073–076 are public-source reproductions, not our newly trained models. Our own EXP039 secondary checkpoint, EXP054 registered relinking and EXP055 intensity composition scored `0.906`, `0.905`, `0.893`; they have not surpassed the public-derived frontier. EXP009/010 are our reciprocal training runs of the public architecture, not a new architecture.

H065 / EXP077 is pre-registered before launch: CPU-only, four **full** movies (first two per embryo from the already frozen 24-movie hash-selected pilot), no flip TTA, one independently trained checkpoint per holdout. All four arms share detections/candidates: registered Hungarian, 10% learned tie-break, **our new leave-self-out robust local deformation field + tie-break**, and a public-style ILP control. Local motion uses unambiguous mutual anchors; each cell excludes its own anchor; uncertain neighborhoods revert to global registration. No new training, no LB submission and no GPU allocation.

The run is capped at six hours / 90 minutes per movie, with per-movie caches and scores. It is a speed and large-regression pilot, not complete OOF or evidence for a `0.001` private improvement. Training excludes evaluated movies and their embryo, but checkpoint/calibration used other movies of that embryo. These audit movies were also scored in previous experiments. Therefore call this a **movie-held-out paired audit**, not an untouched embryo-independent final test. No-TTA changes the pipeline; existing thresholds remain frozen, not retuned on these four movies.

Implementation: `kaggle_notebooks/exp077_cpu_local_flow/cpu_local_flow.py`; ten synthetic/control-parity tests pass. Status: Kaggle v1 RUNNING, model/cfg/selection hashes verified; runtime and metric pending. API confirms GPU disabled and exact remote/local code SHA `5b79389f998de936d39d98c1aba49057372010ffaa1b7bc5db31658dbff5a36a`. Kaggle created slug `dmitriigluzdov/biohub-exp077-cpu-held-out-local-flow-pilot` from the title; local metadata now uses that actual slug. All arm graphs are frozen before labels are read; official aggregation and per-embryo deltas are saved. See `reports/CPU_LOCAL_FLOW_PILOT.md` for scope and continuation.

First v1 result: `44b6_415c0a3a.zarr` completes all four arms and official scoring in `356.032 s` on CPU (`289.963 s` neural inference), exit 0. Registered `0.677837`, weak `0.669063`, local flow `0.669063`, ILP `0.718948`; own-method paired delta `0.0`. No divisions in this movie. CPU feasibility is demonstrated; an own-method gain is **not** demonstrated. Second embryo inference has started; complete fold/pilot metrics remain pending. First-movie evidence is saved in `reports/cpu_pilot_launch_20260827.json`.

## 2026-08-27 update (supersedes older pending/version interpretations)

Completed August 26 results: EXP068R `0.884`; EXP069R `0.926`; EXP070 `0.926`; EXP071 `0.923`; EXP072 `0.918`. Confirmed best remains `0.926`.

The user authorized four further exploratory LB tests. These are source-attributed public full-inference notebooks, not newly trained proprietary architectures:

- EXP073 / `55808574`: `arnav170/biohub-sdw60` v1, secondary detection fusion weight 0.60 with harmonic association. Author's version score `0.927`; account score pending. Artifact SHA `1237f162efe3d6f535d2ab73dcc3e8bd03e623826bbb2e7fc2d3ec6286fb15c3`; 121,815 nodes / 117,548 edges / 267 divisions; full structural audit PASS. New detection mixture rather than another radius sweep.
- EXP074 / `55808576`: `anhadmahajan06/biohub-track-your-cells-development` v21, harmonic association plus guarded division recovery. Author's version score `0.927`; account score pending. SHA `188e0e7995a59ba9eb2ece6b623b0f7afe1cb3d7c00523461dce2826fbe6efe8`; 122,156 / 117,923 / 305; full structural audit PASS. Its graph differs materially from EXP073 (physical edge overlap 0.877430).
- EXP075 / `55808638`: `evgendvorkin/biohub-0-927-lb` v11, explicitly the historical `0.927` version, not v12/EXP065 (`0.924`). Account score pending. Historical page and rendered code inspected; immutable source/artifact download was unavailable, so no local SHA or complete artifact audit is claimed for v11. This is a separately documented version-correction LB probe.
- EXP076 / `55808636`: `arnav170/biohub-sec25` v1, secondary edge-logit weight 0.25; author score `0.923`; account pending. SHA `59b204c02027d4347f79cd11a3773c0980d8a1368e9bab592748a8291fa132cb`; 122,378 / 118,093 / 267; full structural audit PASS. Lower-priority exploratory arm, not an evidence-backed promise to exceed 0.926.

Frozen metadata and exceptions are in `reports/submission_batch_20260827.json`. No new exact OOF scores were generated and no new training was launched. Every new experiment's honest-OOF field remains null.

Provenance correction: installed Kaggle CLI `kernels_output()` parses but never sends the version suffix. The purported v11 download with SHA `33c179b0...` was actually latest v12 and is not a v11 artifact. Similarly, latest Flex v17 is byte-identical to Ahmet v1, but that alone does not prove the submitted Flex v11 was byte-identical. Retain version-specific submission IDs as authoritative and retract unsupported immutable-artifact claims in earlier entries.

The old EXP065 title mismatch is **not** evidence of runtime/private instability: the UI explicitly shows v12 public score 0.924 and best v11 score 0.927. No generic portability conclusion follows from that example.

Validation shortlist: EXP066 (`0.926`), EXP071 (`0.923`, edge overlap 0.873648 to EXP066), EXP008 (`0.917`, edge overlap 0.545528). These are graph-diverse, not proven error-uncorrelated. Reconsider EXP073/074 once their account results exist. The 24-movie pilot and exact-model limitations are recorded in `reports/OOF_MODEL_COMPARISON.md`; previous 40–70 GPU-hour claims are not a measured budget for exact-model reproduction.

## Decision gates

- Primary CV: leave-one-embryo-out (LOEO); report each embryo/movie and pooled official metric.
- Promotion: positive paired delta on honest held-out embryos, no schema/scoring failures, acceptable runtime, and a plausible mechanism.
- Public LB is supporting evidence, not the promotion gate.
- A run with metric exploitation, hidden-test branching, train/test cache leakage, or unofficial node matching is rejected.

## Active hypotheses

| ID | Hypothesis | Controlled change | Evidence to collect | Status |
|---|---|---|---|---|
| H-001 | Learned temporal features materially outperform pure nearest-neighbor association. | EXP-003 vs EXP-001, with each pipeline otherwise intact. | LB score, node/edge counts, runtime. | directionally supported on LB (`0.143→0.908`), but detector and repair also change, so this is not a controlled causal estimate |
| H-002 | Calibrating detection count near `estimated_number_of_nodes` improves adjusted edge Jaccard without hurting raw edge Jaccard. | Threshold sweep within one fixed model/linker. | raw/adjusted edge Jaccard, node ratio, paired movie deltas. | queued |
| H-003 | Independent-seed logit blending reduces detection/association variance and beats downstream-only repairs. | EXP-004 vs EXP-003. | honest LOEO delta and LB delta. | public LB supports `+0.004` (`0.908→0.912`), but both public-weight pipelines remain below the harmonic `0.920–0.923` family; honest LOEO confirmation still required |
| H-004 | Association errors, especially wrong-partner choices after sudden motion, dominate missed detections. | Error decomposition on held-out movies. | wrong partner / missing link / missed endpoint counts. | queued |
| H-005 | Global graph constraints help only when candidate probabilities contain ambiguity not already resolved by assignment. | ILP on/off with identical detections and candidate graph. | paired official score, changed-edge audit. | queued |
| H-006 | Conservative division prediction is preferable because division prevalence and metric weight are low. | divisions off vs high-confidence-only. | division TP/FP/FN and total score delta. | queued |
| H-007 | Gap repair helps only in detection-recall-limited regimes and otherwise adds false structure. | gap repair off/on with independent image evidence. | recovered GT edges, added FP, node penalty. | queued |
| H-008 | Embryo-held-out CV is directionally reliable while crop-random CV is optimistically leaked. | LOEO vs random-crop split. | CV gap and rank correlation to LB variants. | queued |
| H-009 | Consensus pseudo-labels from diverse open trackers can replace missing dense edge supervision. | Cellpose/DoG detections + Ultrack/Trackastra/rule-based short-track agreement. | precision of consensus edges on sparse GT and LOEO gain. | queued |
| H-010 | A temporal affinity/motion field handles abrupt displacement better than centroid-distance extrapolation. | Predict local displacement/center-of-motion from adjacent 3D frames. | wrong-partner reduction, especially for correct targets 5–7 µm away. | queued |
| H-011 | Reverse-time edge evidence becomes useful when combined with dual-seed features before assignment. | Harmonic forward/reverse fusion at weight 0.30 on the fixed dual-seed pipeline. | EXP-005 vs EXP-004 LB and changed-edge/node audit. | artifact complete; LB pending |
| H-012 | Wider division geometry can add true branches safely when mutual-NN, future divergence, and DeepCenter vetoes all agree. | EXP-006 vs EXP-005; only division thresholds/guarded geometry differ materially. | division counts, graph diff and LB delta; source run is associated with `0.923`. | account LB `0.919`; source-attributed `0.923` is not portable evidence |
| H-013 | D4 TTA helps association when all views score the same physical detections, avoiding node-set misalignment. | Average node-transformer edge logits across eight inverse-aligned XY views; keep detection threshold, assignment and repair fixed. | Changed-edge audit, runtime multiplier, LOEO/LB delta against the calibrated graph. | artifact complete; LB not measured |
| H-014 | A three-model detector ensemble with preprocessing diversity provides a useful independent graph arm even if its standalone linker is weaker. | Bright, top-hat-v1 and top-hat-v2 3D U-Nets with flip TTA; appearance-aware physical Hungarian and conservative graph repair. | Artifact audit, exact-coordinate diversity vs EXP-006/007, source/LB evidence, pseudo-label agreement precision. | artifact complete; candidate teacher |
| H-015 | Training the exact public `0.923` architecture with embryo-separated folds gives directionally reliable model-selection evidence and exposes public-weight leakage. | Two reciprocal folds: train on one embryo; use 4 held-out movies for checkpoint/threshold/policy tuning, 4 separate movies for frozen-policy confirmation, and preserve all remaining held-out movies for audit-only inference. | Per-fold official metric on never-loaded audit movies, confirmation-to-audit gap, detector recall, edge/division TP-FP-FN and fold variance. | EXP-009/010 staged training |
| H-016 | Robust framewise global-shift compensation reduces wrong-partner errors on abrupt embryo/camera motion without requiring a heavier learned model. | Estimate the median inlier displacement between adjacent detection clouds, compensate that shift, then solve one-to-one Hungarian within a `7 µm` residual gate. | Calibration selection frequency, held-out edge TP/FP/FN, wrong-partner reduction and per-movie gains on high-shift clips. | pre-registered in EXP-011/012 |
| H-017 | Combining transformer edge probability with registered physical residual is more robust than either signal alone on ambiguous close cells. | Hungarian score `0.7 × learned_probability + 0.3 × exp(-registered_residual/3)`; require a learned candidate, `<7 µm` residual and combined score `>=0.55`. | Calibration selection frequency and reciprocal untouched-audit delta against greedy, ILP and motion-only Hungarian. | pre-registered; runtime smoke PASS |
| H-018 | Independent detector agreement can improve localization without risking the strong graph topology. | Keep every EXP-006 node ID, time and edge unchanged; for mutual-nearest EXP-006/008 detections within `2 µm`, use a fixed convex coordinate blend. | Artifact invariants, matched fraction, displacement distribution and LB delta for the pre-registered `alpha=0.5` candidate. | EXP-014 artifact PASS; strongest paired differential `+0.005209`; next-slot candidate |
| H-019 | Unanimous alternative associations from diverse trackers can correct wrong partners in the strongest graph at very high precision. | Map clean tracker nodes mutually to EXP-006 within `2 µm`; replace a one-to-one EXP-006 edge only when complete mapped outgoing sets contain the same single different target. | Number of unanimous alternatives, degree/schema invariants and independent physical-motion veto. | rejected: three-tracker consensus fails the motion veto |
| H-020 | Additional low-LR epochs from the complete honest model state improve association without the reset implicit in the support script's UNet-only preload path. | Resume all `UNetNodeTransformer` parameters from SHA-verified EXP-009/010 checkpoints; restart AdamW at `5e-5`, preserve the exact split contract, and add a compute-matched 5/10 epochs. | Parent-vs-resume checkpoint calibration and untouched-audit score; launch only if v3 audit suggests underfitting. | EXP-016/017 prepared, not launched |
| H-021 | Independent localization consensus and unanimous association consensus provide additive low-risk corrections because they affect disjoint parts of the prediction. | Apply EXP-014's fixed coordinate blend to EXP-015's one-edge consensus topology; keep every node ID/time and all other edges fixed. | Exact composition audit plus independent motion plausibility of every edge change. | rejected: EXP-015 edge fails physical veto; keep EXP-014 only |
| H-022 | A small raw-intensity center-of-mass correction can undo quantization/localization error without disturbing the strong lineage topology. | Around each EXP-006 node use a `5×11×11` crop, subtract its 20th percentile, accept COM shifts `<=1.5 µm`, and apply fixed `alpha=0.35`; keep graph topology fixed. | Artifact displacement distribution and LB delta after EXP-014; fail closed on exact EXP-006 SHA. | EXP-019 artifact PASS; paired differential `+0.001163`; second next-day candidate |
| H-023 | Independent detector consensus and raw-intensity refinement contain complementary localization signal when their displacement directions agree. | Identity-aligned coordinate blend `0.6×EXP-014 + 0.4×EXP-019`; node identity and EXP-006 topology fixed. | Direction agreement, exact topology audit and LB only after both parent effects are measured. | EXP-022 artifact PASS; paired differential `+0.001990`; gated behind both parents |
| H-024 | Requiring directional agreement between independent localization corrections isolates a higher-precision coordinate subset than blending every node. | Relative to EXP-006, require both EXP-014/019 displacements and cosine `>=0.5`; on eligible nodes use the fixed `0.6/0.4` blend, otherwise retain EXP-006. | Eligible fraction, topology audit and LB only after parent effects are measured. | EXP-023 artifact PASS; paired differential `+0.000775`; gated behind parents |
| H-025 | Fully labelled physical simulations can improve the division/association representation when used only for pretraining and then recalibrated on real embryos. | Full-model synthetic pretrain on fixed 32³ crops, followed by compute-matched real-data fine-tuning; compare against the same real-only initialization/epochs on both frozen LOEO folds. | Reciprocal untouched-audit delta, especially division TP/FP/FN; real detection recall and edge score must not regress. | EXP-024 pretrain prepared; real-data promotion test not yet launched |
| H-026 | Dense, real Zebrahub light-sheet tracks provide a higher-fidelity detector/association pretraining source than synthetic images. | Pretrain the exact architecture on physically resampled Zebrahub crops, then use the same compute-matched real fine-tune and reciprocal LOEO controls as H-025. | Real untouched-audit delta against random initialization and synthetic pretraining; per-component error decomposition and timelapse-held-out external diagnostics. | source authorized/audited; bounded extractor and pretrainer prepared, promotion still gated on reciprocal LOEO |
| H-027 | The DeepCenter safe-division veto at `0.12` rejects some real but borderline daughter detections. | Keep EXP-006 byte-for-byte except lower `DEEPCENTER_SAFE_DIV_THRESHOLD` from `0.12` to `0.08`. | Exact output graph diff, changed/accepted division counts, attributable LB evidence and later reciprocal LOEO division TP/FP/FN. | rejected: the relaxed veto swaps 73/455 division parents and loses the only reused-label division TP; proxy `0.9235→0.9131` |
| H-028 | A nearby dual-seed/boundary-rescue graph and the diverse EXP-008 detector may agree on a high-precision subset of EXP-006 association corrections. | Mutually map each tracker to EXP-006 within `2 µm`; replace an edge only when both complete mapped outgoing sets unanimously select the same alternative. | Proposal count, exact topology delta and physical motion residuals. | rejected: zero unanimous alternatives |
| H-029 | Two lower-scoring but detector-diverse clean trackers can identify rare EXP-006 wrong-partner edges by unanimous mapped association. | Use explicit-`0.916` Hira ensemble plus exact-`0.917` EXP-008 as voters; retain EXP-006 nodes and replace only conflict-free unanimous alternatives. | Exact edge diff, distance and constant-velocity residual for every change. | rejected: all three accepted alternatives fail the physical veto |
| H-030 | Directional agreement between two detector-diverse localization errors isolates a higher-precision coordinate correction than either donor alone. | Mutually map EXP-008 and explicit-`0.916` Hira nodes to EXP-006 within `2 µm`; require both nonzero displacements and cosine `>=0.5`, then move halfway toward their mean coordinate. | Eligible fraction, direction strength, displacement bounds, exact topology audit and LB only after parent localization evidence. | EXP-031 artifact PASS; weak paired `+0.000339` with one TP lost; low priority |
| H-031 | A clean frame-retention/harmonic variant and detector-diverse EXP-008 can unanimously expose rare EXP-006 association errors. | Mutually map both trackers within `2 µm`; require complete outgoing sets and the same one-to-one alternative target. | Proposal count, exact graph delta and physical residual for every accepted change. | rejected: zero unanimous alternative proposals |
| H-032 | Directional localization agreement between a nearby retention-guard tracker and detector-diverse EXP-008 identifies stable subvoxel corrections. | Keep EXP-006 topology/identity; mutually map Raunak and EXP-008 within `2 µm`, require two nonzero shifts and cosine `>=0.5`, then move `0.5` toward their mean. | Eligible fraction, shift distribution, exact topology audit; LB only after EXP-014/019 evidence. | EXP-033 local artifact PASS; ultra-conservative and gated behind localization parents |
| H-033 | A calibrated reused-label metric can reject harmful coordinate-only candidates before spending LB slots, even though it cannot promote them. | Score EXP-006/014/019/022/023/031 with identical matching and topology-aware division code on the four visible labelled movies; require EXP-006 to reproduce its logged proxy first. | Base calibration, per-movie/delta table, matched-node and edge TP/FP/FN changes. | rejected before deltas: logged `0.9235` uses four different held-out train movies, not the visible-output stems |
| H-034 | Within the four same-stem visible/train overlaps, a frozen paired coordinate differential can reject candidates that worsen node assignment even though its absolute score is non-honest. | Freeze the EXP-006 v2 control before exposing candidate summaries (`adjusted/proxy=0.8870825255`, division `0`), then score EXP-014/019/022/023/031 identically. | Exact base replay, paired matched-node and edge TP/FP/FN deltas; never use positive deltas for promotion. | complete: all deltas non-negative; reject none, preserve EXP-014→019→conditional-022 queue |
| H-035 | A detector-diverse tracker and a nearby clean harmonic tracker can expose a missing second daughter when both independently agree on the same division and EXP-006 already contains one daughter. | Map EXP-008 and Raunak mutually to EXP-006 within `2 µm`; add only an unparented second-daughter edge when both complete outgoing sets are the same two targets, the existing EXP-006 child is one of them, both edges are `<=7 µm`, their displacement cosine is `<=0`, and both daughters continue in EXP-006. | Exact one-edge/topology audit, physical geometry, reject-only visible-overlap division TP/FP/FN, and later honest LOEO mechanism evidence; a positive reused-label delta cannot promote. | inconclusive: frozen overlap metric is exactly unchanged; hold without submission or promotion |
| H-036 | A five-branch extension of the detector-diverse EXP-008 family can expose high-precision association errors when it agrees with its cleaner two/three-branch parent against EXP-006. | Mutually map exact EXP-008 and newly completed Arnav ENS5 to EXP-006 within `2 µm`; accept only complete unanimous one-to-one alternatives with conflict-free targets. | Proposal count, exact graph audit, edge length and constant-velocity residual for every accepted replacement. | rejected post-hoc: five accepted replacements all worsen physical residuals; shared detector backbone makes the vote correlated |
| H-037 | A separately trained public secondary checkpoint can provide a compatible and genuinely different third learned seed for later low-margin consensus. | Before any inference, compare exact checkpoint SHA, state-dict keys/shapes and tensor equality against the frozen public split-0 architecture in a CPU-only Kaggle audit. | Complete key/shape compatibility, parameter counts, finite tensors, exact SHA provenance and evidence that weights are not a duplicate; no score/promotion claim. | rejected: the attachable SHA is exactly EXP-006's existing secondary checkpoint, not a third seed |
| H-038 | The completed `own_seed_v1` checkpoint from the cancelled Harshini run is architecture-compatible and genuinely new relative to both EXP-006 learned seeds. | Stage the exact public output privately with attribution, then compare its complete tensor state against frozen primary SHA `12f688…` and secondary SHA `9bac2…` before any inference. | Exact source SHA/bytes, complete key/shape/dtype compatibility, finite tensors, and parameter distance to both existing seeds; no score/promotion claim. | supported as checkpoint fact: exact architecture and distinct from both seeds; no performance claim |
| H-039 | Replacing only EXP-006's highly correlated secondary checkpoint with the independently trained `own_seed_v1` state improves low-margin detection/association consensus without changing the strong topology recipe. | Exact EXP-006 notebook fork: retain primary, secondary detection/edge weights, harmonic forward/reverse fusion, thresholds, ILP, gaps, divisions and DeepCenter; change only secondary artifact SHA/slug. | Fail-closed runtime integrity, full artifact audit, exact graph diversity/physical diagnostics, reject-only visible-overlap differential and LB only after current parent queue. | rejected: frozen overlap differential `-0.003185`; no LB slot |
| H-040 | A high-residual subset of EXP-006's wide safe divisions are ordinary continuations rather than true branches. | Mutually map frozen EXP-005 and detector-diverse EXP-008 to EXP-006 within `2 µm`; prune only when both donors have complete outgoing sets equal to the same singleton EXP-006 daughter, the rejected daughter has constant-velocity residual `>=4 µm`, and its residual is `>=2 µm` worse than the retained daughter. | Exact SHA/node/topology audit, proposal count and physical residuals for every prune; reused-label overlap is reject-only and honest LOEO division TP/FP/FN is required before any promotion. | pre-registered before running the fixed rule |
| H-041 | The extreme tail of H040 supplies a higher-precision division-prune arm if the broad `4/2 µm` gate is too aggressive. | Keep the exact H040 voters/mapping/singleton contract, but require rejected-daughter constant-velocity residual `>=7 µm` and a `>=4 µm` residual margin; freeze this nested arm before reading EXP040's reused-label result. | Exact subset relationship to EXP040, graph audit, change count and honest reciprocal LOEO division TP/FP/FN; same-stem labels remain reject-only. | pre-registered while EXP034 v6 was still RUNNING |
| H-045 | Independent coordinate localization and high-precision division pruning are additive because they change disjoint submission fields. | Compose exact EXP014 node rows with exact EXP040 edge rows; require node ID/time identity and preserve each parent serialization semantically. | Full graph audit and reject-only overlap; submit only if EXP014 LB is `>=0.919` and the `4/2 µm` physical mechanism is non-negative on both untouched LOEO folds. | pre-registered before artifact construction and before either promotion gate is known |
| H-047 | The strict physical tail is a safer topology complement to independent coordinate localization if the broad division-prune arm is too aggressive. | Compose exact EXP014 node rows with exact EXP041 edge rows; this differs from H045 only by using the frozen nested `7/4 µm` arm (55 rather than 160 prunes). | Full graph audit and reject-only overlap; submit only if EXP014 LB is `>=0.919` and the strict mechanism is separately non-negative in score, adjusted-edge Jaccard and division TP on both untouched LOEO folds. | pre-registered before any untouched result; artifact/full audit PASS, both gates remain closed |
| H-049 | Prefix-wise cross-embryo production inference can generalize better than public all-movie checkpoints whose local validation is leaked. | For every `44b6` test movie use only the EXP009 checkpoint trained on `6bba`; for every `6bba` movie use only EXP010 trained on `44b6`. Take each fold's threshold and linker policy mechanically from its frozen EXP011/012 selection receipt; do not tune on visible/reused labels. | Reciprocal confirmation/audit gap, pooled untouched official metric, exact checkpoint/split/policy receipt and full test artifact audit. Build test inference only after both audit receipts complete; one supporting LB slot is allowed only if each untouched score is `>=0.55`, node recall is `>=0.85`, and its confirmation-to-audit drop is no worse than `−0.10`. | Original route pre-registered before confirmation/audit; numeric no-collapse gate frozen after EXP011 confirmation and only 7/63 individual audit rows were visible, before its aggregate and before any EXP012 selection/confirmation/audit value. |
| H-050 | Learned association probability is useful as a weak ambiguity tie-breaker but harmful as a hard candidate requirement under cross-embryo shift. | Starting from registered Hungarian, keep every residual `<7 µm` candidate; score `0.9 × exp(-registered_residual/3) + 0.1 × learned_probability`, with missing learned probability equal to zero and the unmatched dummy set from the same motion gate. Use each fold's already-selected threshold and compare only against pure registered motion. | Pre-register before confirmation/audit disclosure; paired score/adjusted-edge/TP-FP-FN on both confirmation and untouched folds, no threshold or weight reselection. Promote only if non-negative on each untouched fold and positive pooled. | supported: untouched fold deltas `+0.000734/+0.000771`, pooled `+0.000767`; preserve for a later production linker |
| H-052 | The strong EXP-006 detector/node set benefits from replacing its learned/ILP topology with the robust registered-motion linker selected under embryo separation. | Preserve every EXP-006 node ID, time and coordinate byte-semantically; discard only its edges and relink each adjacent frame with the exact median-inlier shift, `<7 µm` residual gate and one-to-one Hungarian policy used by EXP011/012. No threshold, coordinate, node-count, gap or division repair is added. | Exact node-provenance/topology audit and reject-only visible-overlap diagnostic. Promotion requires EXP050/051 to show registered motion non-negative versus their paired greedy base on each untouched fold and positive when pooled; the official score must absorb any loss of division TP. | promoted: registered−greedy score `+0.164190/+0.129587` on untouched folds and `+0.134782` pooled |
| H-053 | Detector-consensus coordinates and registered-motion topology are additive because they modify disjoint fields on the exact same node identities. | Compose all EXP014 node rows with all EXP052 edge rows; require exact `(dataset,node_id,t)` identity and preserve each parent's rows semantically. | Full graph/provenance audit plus reject-only visible-overlap diagnostic. Submit only if EXP014 public LB is `>=0.919` and H052 passes its two-fold registered-vs-greedy gate. | preserved by strongest reject-only delta `+0.010675`; still waiting both honest gates |
| H-054 | The positive H052 topology mechanism can be made valid for the code competition by applying it inside the full EXP006 inference notebook rather than wrapping a public CSV. | Exact EXP006 inference and node postprocessing remain intact. After final node coordinates are rounded exactly as for submission, discard only edges and rebuild adjacent-frame links with H052's median-inlier global shift, `<7 µm` residual gate and one-to-one Hungarian assignment. | Fail-closed source patch receipt, hidden-data-dynamic input discovery, full graph audit, and exact semantic agreement with EXP052 on the public test. Submission requires the reciprocal H052 untouched-fold gate and a complete Kaggle rerun. | pre-registered before notebook construction or execution; designed specifically for hidden code-competition reruns |
| H-055 | The conservative raw-intensity coordinate correction from EXP019 is additive with H052 because it changes only node coordinates after the registered topology has been frozen. | Run exact EXP054 through registered linking on the final EXP006 integer nodes, then apply EXP019's `5×11×11`, 20th-percentile-subtracted center of mass with raw shift `<=1.5 µm` and `alpha=0.35`; preserve every node identity and registered edge. | Exact semantic agreement with EXP019 node coordinates and EXP052 edge topology on public test, full graph audit, hidden-dynamic raw-frame reads and the H052 reciprocal gate. | implementation and H052 gates PASS; hold behind clean EXP054 LB control |
| H-056 | Detector-diverse localization from EXP008 is additive with the robust registered topology and should be safer than tuning a new public-LB threshold. | Run the exact EXP054 full inference and exact EXP008 3×UNet/flip-TTA inference on every dynamically mounted movie. Mutual-nearest match detections within `2 µm`, move EXP054 nodes halfway toward EXP008, and preserve every registered edge. | Hidden-dynamic dual-inference receipt, exact public semantic agreement with EXP053, full graph audit, and H052's reciprocal embryo-disjoint topology gate. | pre-registered before production notebook execution; strongest frozen coordinate/topology proxy `+0.010675` |
| H-057 | Independent detector-consensus localization can improve the current `0.919` frontier without sacrificing EXP006's much stronger learned/ILP topology and safe divisions. | Run exact EXP006 and EXP008 inference dynamically, mutual-nearest match within `2 µm`, and move EXP006 nodes by frozen `alpha=0.50`; preserve every EXP006 edge byte-semantically. | Exact public semantic agreement with EXP014, full graph audit, hidden-data dual inference, and LB because no honest localization labels exist. | promoted to production after EXP054/055 showed topology and intensity changes are harmful; strongest remaining controlled coordinate-only candidate |
| H-058 | A conservative half-dose of detector consensus may retain localization signal while reducing the risk that the lower-scoring donor moves correct EXP006 nodes. | Use the exact H057 matches and topology but `alpha=0.25`; emit from the same inference run so parent predictions and matching are identical. | Full graph/identity audit and paired LB against H057/EXP006; no threshold or match-set change. | pre-registered before EXP057 execution and any LB result |
| H-059 | H052's ordinary-link gain may coexist with EXP006's valuable division decisions if registered links are used only outside original division sources. | Start with H057 coordinates; registered-link ordinary nodes, restore every exact EXP006 division-source edge, and remove registered target conflicts to keep max indegree 1/outdegree 2. | Full graph audit, exact division-edge preservation, public topology receipt and LB; reject if any conflict or division loss occurs. | pre-registered before EXP057 execution and any LB result; diversified third candidate |
| H-060 | Independent detector-consensus localization can improve the actual `0.920` leader while preserving its conservative harmonic topology and divisions. | Run exact EXP005 and EXP008 inference dynamically; mutual-nearest match within `2 µm`, move EXP005 nodes by `alpha=0.50`, and preserve every EXP005 edge. | Exact public artifact/full graph audit, hidden-dynamic dual inference and LB; compare only against EXP005 because no honest localization CV exists. | public artifact PASS; production built before LB, GPU launch quota-blocked |
| H-061 | A quarter-dose detector correction is a safer private-shift hedge when EXP008 disagrees with an already-correct EXP005 localization. | Use the exact H060 matches and EXP005 topology but `alpha=0.25`; emit in the same inference run. | Exact identity/topology audit and paired LB against H060/EXP005; no match-set or threshold change. | public artifact PASS; production built before LB, GPU launch quota-blocked |
| H-063 | Linker rankings should be measured on identical embryo-disjoint detections rather than inferred from unrelated public pipelines. | Reuse each frozen LOEO checkpoint/threshold once per untouched movie; compare registered, weak learned tie-break, learned-heavy registered, two ILP settings and three greedy/physical arms on the exact same candidates. | Per-movie/fold/pooled official metric, paired bootstrap and sign agreement across both embryos; persist candidates before scoring for CPU-only follow-ups. | reciprocal sources built and compile PASS; GPU launch quota-blocked |
| H-064 | Once embryo-disjoint candidate caches exist, physical Kalman/constant-velocity, particle-filter and min-cost-flow linkers can be compared honestly without another neural inference pass. | Consume only EXP063/064 frozen candidate caches; pre-register every linker/gate before opening its score and evaluate all 183 untouched movies. | Paired per-movie deltas, embryo-wise signs, bootstrap interval, division TP/FP/FN and runtime. | queued behind EXP063/064 cache export; designed for CPU |

## Runs

| Experiment | Date | Parent/source | Method / one controlled purpose | CV | Public LB | Runtime | State | Decision / notes |
|---|---|---|---|---:|---:|---:|---|---|
| EXP-001 | 2026-08-22 | `inversion/cell-tracking-getting-started-w-nearest-neighbor` | CPU sanity: percentile detection + Hungarian nearest-neighbor links. | — | **0.143**, submission `55686043` | — | complete v1 | Valid end-to-end floor; 7,067 nodes, 4,629 edges, 11,696 visible rows. |
| EXP-002 | 2026-08-22 | `isakatsuyoshi/biohub-rule-based-baseline` | Classical multi-scale blob detector + physical-distance Hungarian + 1-frame gap closure. | — | **0.826**, submission `55686045` | — | complete v1 | `+0.683` over NN floor, but `-0.095` below current rank-100; valuable as an orthogonal pseudo-label teacher. |
| EXP-003 | 2026-08-22 | `yusuketogashi/clean-approach-lightweight-local-cv-no-hack` | Clean single-seed TemporalUNet3D + node transformer + ILP + conservative repair. | mixed/in-sample diagnostics only; not promotion-grade | **0.908**, submission `55686657` | ~35 min visible run + fixed-8 CV | complete v1; hold | 120,246 nodes, 115,957 edges, 236,203 rows; schema/dataset/id guards valid; public weights trained on all labelled movies. It establishes the clean learned floor but is `-0.015` below EXP-006's attributable source score. |
| EXP-004 | 2026-08-22 | `pilkwang/biohub-cell-tracking-two-seeds-logit-blend` | Dual-seed aligned logit blend + transformer + ILP + DeepCenter-confirmed gaps. | public weights; not promotion-grade | **0.912**, submission `55686487` | ~24 min visible run | complete v1; hold | 119,039 nodes, 114,863 edges, 233,902 rows; schema valid. It is `-0.011` below the attributable clean EXP-006 source and `-0.005` below EXP-008; retain only as diversity evidence. EXP-003 is still pending, so this does not isolate the independent-seed effect. |
| EXP-005 | 2026-08-22 | `yunusgmsoy/lb-0-920-biohub-cell-tracking-v17` | Dual-seed pipeline plus harmonic forward/reverse association, DeepCenter gap/division veto and strict guards. | public validator uses labelled movies; not promotion-grade | **0.920**, submission `55719392` | ~37 min | complete v1/full audit; current public leader | 122,032 nodes, 117,594 edges, 67 divisions; audit PASS. SHA-256 exactly matches the source `0.920` artifact: `9507eccb…6425`. Submitted at `2026-08-23 16:08:04 UTC`. The exact weights used all labelled movies, so this score has no honest embryo-disjoint OOF and is a strong clean public control rather than proof of private robustness. |
| EXP-006 | 2026-08-22 | `yunusgmsoy/kimi-notebook-v17` | EXP-005 harmonic core with safe-division radii `12/15/10 µm`, mutual-NN, divergence and DeepCenter veto. | public validator uses labelled movies; not promotion-grade | **0.919**, submission `55687578`; source-attributed historical run `0.923` | ~40 min | complete v1; current baseline | 122,266 nodes, 118,156 edges, 455 divisions; audit PASS. Exact `BIOHUB_*` env diff is only three division radii; submitted SHA-256 matches source artifact `5c852379…1f4d`, yet the account receives `0.919`, so the external `0.923` attribution is not portable score evidence. Versus EXP-005, the reused-label proxy moves `0.9152→0.9235` because division Jaccard rises `0.0→0.1` despite adjusted-edge `0.9152→0.9135`; this proxy materially overstates transfer. |
| EXP-007 | 2026-08-22 | `ericwang03/biohub-daily-probe-lane-5` | Single TemporalUNet3D with D4 detection TTA and equal-weight eight-view shared-node association-logit TTA; calibrated motion and conservative divisions fixed. | public weights; no honest held-out score | **0.900**, submission `55732491` | — | complete v1/full audit; reject | 130,132 node rows, 125,569 edges, 427 divisions, audit PASS. Our private run exactly reproduces the source: SHA-256 `740f7c83…3ca6`, node/edge/division Jaccard all `1.0`. The `-0.020` delta to EXP005 rejects expensive association-logit D4 TTA as a standalone direction. |
| EXP-008 | 2026-08-22 | `navazshfathi/best-score` | Three 3D U-Nets with bright/top-hat preprocessing diversity, flip-quartet TTA, appearance-aware Hungarian, line-fit smoothing, safe divisions and snap-only gaps. | public weights; no honest held-out score | **0.917**, submission `55732259`; exact source attributed **0.917** | — | complete v1/full audit; retain as detector-diverse hedge | 126,419 nodes, 121,191 edges, 352 divisions, audit PASS. Multiple sources reproduce SHA-256 `d7ba9e6a…f2bb`; the account score exactly confirms the independent `0.917` attribution. It remains useful for detector diversity and coordinate consensus, but is `-0.003` below EXP005 standalone. |
| EXP-009 | 2026-08-22 | support-pack `train_unet_transformer.py` | Exact TemporalUNet3D + node-transformer training, hold out embryo `44b6`; deterministic 8-movie calibration subset and frozen remainder for audit only. | LOEO contract frozen before training | not a test submission | 7h10m, dual T4 | v1 OOM; v2 cancelled as runtime-infeasible; v3 complete PASS | Seed `314159`; training contains only `6bba_*`. V3 confirms 128 train / 4 checkpoint / 8 calibration / 63 untouched audit movies, 1,549 batches/epoch, T4×2 and 2,076,706 parameters. Checkpoint score/recall improved `0.8511/0.8519 → 0.8990/0.8993` at epoch 2 and later epochs did not beat it (`0.8971/0.8959/0.8771` recall). The saved 8,357,783-byte checkpoint SHA is `eebb8eaa…4382`; this is checkpoint-selection evidence only. EXP011 v4 audit is running. |
| EXP-010 | 2026-08-22 | support-pack `train_unet_transformer.py` | Reciprocal exact architecture fold, hold out embryo `6bba`; otherwise identical to EXP-009. | LOEO contract frozen before training | not a test submission | 8h38m, dual T4 | v1 OOM; v2 cancelled as runtime-infeasible; v3 complete PASS | Seed `314159`; 71 train / 4 checkpoint / 8 calibration / 120 audit, 790 batches/epoch, T4×2, 2,076,706 parameters. Checkpoint score/recall progressed `0.8519/0.8531 → 0.8770/0.8786 → 0.9192/0.9199` over epochs 1–3; epochs 4–10 never beat it and final recall is `0.9000`. The saved 8,357,783-byte epoch-3 checkpoint SHA is `0e054325…cad`; contract SHA is `66de0e85…6ed`. The 120 audit movies remained untouched and EXP012 v1 launched only after both SHAs/splits passed. |
| EXP-011 | 2026-08-22 | EXP-009 checkpoint | Holdout-`44b6` nested official-metric audit: tune five detection thresholds × five pre-registered linkers on the four checkpoint movies, persist the pair, confirm it without reselection on the other four calibration movies, then evaluate 63 untouched audit movies once. | strict held-out audit contract | not a test submission | T4; 87 movie-passes | v4 COMPLETE; untouched audit PASS | V4 froze `det_threshold=0.985` plus registered motion Hungarian at `0.732233`; frozen confirmation was `0.674835`. On all 63 untouched movies the official score is **`0.744130`**, edge Jaccard `0.758797`, node recall `0.972594`, with `0/0/25` division TP/FP/FN. The confirmation→audit gap is `+0.069295`; all provenance/split contracts pass. Because the selected graph has no divisions, both physical-prune arms are exact no-ops here and supply no H040 donor-consensus promotion evidence. |
| EXP-012 | 2026-08-22 | EXP-010 checkpoint | Reciprocal nested audit: identical 4-movie tuning + 4-movie frozen confirmation, followed by one pass over 120 untouched `6bba` audit movies. | strict held-out audit contract | not a test submission | T4; 144 movie-passes | v1 COMPLETE; untouched audit PASS, H049 drop gate fails | The complete 25-cell calibration froze `det_threshold=0.99` plus registered motion Hungarian at `0.687306`; frozen confirmation was `0.721963`. On all 120 untouched movies the score is **`0.595767`**, edge Jaccard `0.606323`, node recall `0.943095`, divisions `0/0/117`. This clears H049's absolute score/recall floors but confirmation→audit is `−0.126196`, below its predeclared `−0.10` limit; cross-embryo production therefore fails closed. As in EXP011, physical-prune arms are no-ops on the division-free selected graph. |
| EXP-013 | 2026-08-22 | support-pack runtime | CPU-only environment smoke test for the exact graph policies and GEFF save/reload path used by EXP-011/012. | synthetic graph; no model/data score | not a test submission | <1 min CPU | complete v2 | PASS: with motion-inconsistent alternatives at probability `0.95` and true shifted links at `0.70`, hybrid Hungarian recovered `(0→3, 1→4, 2→5)` and GEFF round-trip succeeded. Receipt SHA-256 `a6abec1f…5074`. |
| EXP-014 | 2026-08-22 | EXP-006 topology + EXP-008 coordinates | Coordinate-only ensemble: mutual-nearest same-frame detections within `2 µm`, fixed `alpha=0.5` convex blend; no node, time or edge changes. | public weights; topology inherited from clean `0.923` source | invalid as current code-competition wrapper | 11 s local; ~5 min Kaggle CPU | artifact PASS; hidden rerun invalid | 93,630/122,266 nodes matched (`76.58%`); mean detector disagreement `0.999 µm`, p95 `1.773 µm`, so the base graph moves only `0.499/0.887 µm` at mean/p95. Kaggle output and independent audit PASS: 122,266 nodes, 118,156 edges, four datasets, max degrees 1/2. Canonical Kaggle/local SHA-256 is exactly `c970d943…4de0`. Submission `55703183` completed without a score because the wrapper emits a public-test artifact during the hidden rerun; it is now hard-blocked until implemented inside full inference. |
| EXP-015 | 2026-08-22 | EXP-006 + mapped EXP-007/008 edges | Edge-only unanimous correction: replace a base one-to-one edge only when both independent trackers have complete mapped outgoing sets and agree on the same different target. | public weights; high-precision consensus diagnostic | do not submit | 13 s local | rejected after artifact PASS | The sole accepted change (`21133→21434` to `21133→21435`) is also supported by General V4, but physical evidence strongly favors the base: raw/CV residual `3.28/0.41 µm` versus `6.56/4.69 µm`. This exposes crowded-frame node-mapping aliasing despite three tracker votes. SHA-256 `4c1ee557…4278`. |
| EXP-016 | prepared 2026-08-22 | canonical EXP-009 v3 checkpoint | Full-state staged continuation for holdout `44b6`: +5 epochs at LR `5e-5`; same 128/4/8/63 split contract. | LOEO; audit remains untouched | not a test submission | projected like EXP-009 | prepared, gated on v3 audit | Fail-closed parent epoch/seed/split/bytes/SHA checks. Patches the audited support source at an exact anchor and requires zero missing/unexpected keys before training; optimizer is deliberately restarted. |
| EXP-017 | prepared 2026-08-22 | canonical EXP-010 v3 checkpoint | Reciprocal full-state continuation for holdout `6bba`: +10 epochs at LR `5e-5`; same 71/4/8/120 contract. | LOEO; audit remains untouched | not a test submission | projected like EXP-010 | prepared, gated on v3 audit | Identical provenance and full-model-load contract; compute-matched to EXP-016. Not launched until reciprocal v3 evidence justifies the GPU cost. |
| EXP-018 | 2026-08-22 | EXP-015 topology + EXP-008 coordinates | Exact composition of the fixed `alpha=0.5`, `2 µm` coordinate ensemble and the single unanimous edge correction. | public weights; topology inherited from EXP-015 | do not submit; EXP-014 dominates | 11 s build + 26 s audit | rejected after artifact PASS | Schema/topology PASS, but its only difference from EXP-014 is the physically implausible EXP-015 edge. SHA-256 `b772ef3e…9853`. |
| EXP-019 | 2026-08-22 | exact EXP-006 artifact + raw test volumes | CPU-only gated intensity-COM coordinate refinement; no node, time or edge changes. | public weights; mechanism independently used by EXP-008 | invalid as current code-competition wrapper | 9.2 min CPU + 27 s local audit | artifact PASS; hidden rerun invalid | Kaggle and independent audit PASS: 122,266 nodes, 118,156 identical edges, 118,563 coordinates changed. Accepted-shift mean/p95/max `0.272/0.462/0.525 µm`; 3,703 raw shifts over the `1.5 µm` gate rejected. SHA-256 `7487ecb7…96c6`. Submission `55703198` completed without a score after an unhandled hidden-rerun error; this public-artifact wrapper is hard-blocked pending a full-inference implementation. |
| EXP-020 | 2026-08-22 | EXP-006 + EXP-008/General-V4 edges | Pairwise unanimous alternatives from the diverse EXP-008 detector and clean General V4 tracker. | public weights; diagnostic only | do not submit | 13 s build + 26 s parallel audit | rejected after artifact PASS | 3 proposals, 2 accepted, 1 target conflict. Besides the failed EXP-015 edge, `28843→29158` lacks EXP-007 support and is physically worse than base: raw/CV residual `3.35/4.96 µm` versus `1.68/0.00 µm`. SHA-256 `607768ef…bf28`. |
| EXP-021 | 2026-08-22 | EXP-006 + EXP-007/General-V4 edges | Pairwise unanimous alternatives from the shared-backbone D4 and General-V4 trackers. | public weights; correlated diagnostic | do not submit | 15 s build + 26 s parallel audit | rejected after artifact PASS | 27 proposals, 10 accepted, 17 target conflicts. Only `21133→21435` also has EXP-008 support, and that edge fails the physical veto; all correlated-pair changes are rejected. SHA-256 `f9c21016…d7d6`. |
| EXP-022 | 2026-08-22 | EXP-014 detector coordinates + EXP-019 intensity coordinates | Fixed identity-aligned `0.6/0.4` coordinate blend; exact EXP-006 topology. | public weights; parents have no honest localization CV | submit only if both parents are non-negative on LB | local 6 s build + 26 s audit; Kaggle CPU v1 complete | Kaggle artifact complete; gated | Among 91,869 nodes changed by both parents, direction cosine median is `0.650`; 80.6% agree in halfspace and only 7.7% strongly oppose. The fail-closed Kaggle wrapper verified exact parent SHAs and reproduced coordinate fingerprint `7989529a…00e53`; downloaded output independently passes 122,266-node / 118,156-edge topology audit, SHA-256 `91e24e75…fb6a`. |
| EXP-023 | 2026-08-22 | EXP-006 base + EXP-014/019 coordinates | Direction-gated `0.6/0.4` blend only where both corrections exist and cosine is at least `0.5`; otherwise keep base coordinates. | public weights; label-free visible-test agreement | submit only after parent LB evidence | local 11 s build + 25 s audit; Kaggle CPU v1 complete | Kaggle artifact complete; gated | Exactly 55,338/122,266 nodes are eligible (`45.26%`). The Kaggle wrapper verifies all three parent SHAs, 91,869 jointly changed nodes, eligibility count and fingerprint `370f7525…0457`; downloaded output independently passes exact EXP-006 topology audit, SHA-256 `8bff01ab…de3`. |
| EXP-024 | prepared 2026-08-22 | CC0 `josefreitasalvesneto/biohub-synthetic-dataset` + exact public architecture | Full-model pretraining on 512 synthetic six-frame movies, 64 synthetic validation movies, fixed 32³ crops and all five adjacent transitions; eight epochs. | synthetic-only selection is not promotion evidence | not a test submission | projected <2h T4×2 | prepared; gated behind current LOEO jobs | Source manifest verifies 1,539 static volumes, 2,174 sequences, 4,056,226 nodes and 165,267 divisions. Audit found pooled 64³ images paired with native-grid y/x (sample max `243.17`); the fail-closed adapter divides y/x by four before cropping. Division prior is inflated (`4.07%` vs about `0.26%` real), so checkpoint must be fine-tuned and judged only by reciprocal untouched real audit. |
| EXP-025 | 2026-08-22 | authorized public `ZSNS001_tail` OME-Zarr + tracks | CPU/internet extraction of 256 train and 64 time-disjoint validation two-frame crops, exact physical resampling to `64³ @ 1.625 µm`, with every annotated cell in each crop and continuation/division edges. | external train times `10–629`; external checkpoint times `650–789`; 21-frame gap | not a test submission | ~13 min CPU/network; 113.4 MB shards | complete v2 | Full local receipt audit verifies 320/320 shard SHA-256 values with no missing/bad files: 326,490/92,209 train/valid nodes, 160,373/45,321 edges and 1,636/393 division edges. Shards span 71–2,885 nodes and 35–1,425 edges; min/max-density structure, volume dtype/shape, coordinate bounds and edge indices PASS. The exact 486,953,955-byte source table SHA is `8a30b8c9…a660`, and the raw table was deleted. |
| EXP-026 | prepared 2026-08-22 | exact EXP-025 shards + public TemporalUNet3D/node-transformer | Twelve-epoch real-domain pretraining on the exact public architecture; external late-time score selects a checkpoint only. | inherits time-disjoint external split; not real promotion evidence | not a test submission | projected <4h T4 | source/runtime validation PASS; training gated on LOEO | Verifies every EXP-025 shard SHA before loading, keeps all crop annotations to avoid false negatives, uses isotropic detector volumes and the public `(1,4,4)` edge-coordinate scale. Batch is conservatively fixed at 2 because the densest frame contains 1,449 cells. The actual Kaggle runtime constructed all 256/64 windows through the exact source in EXP-027. Promotion requires compute-matched competition fine-tuning and positive deltas on both untouched reciprocal LOEO audits. |
| EXP-027 | 2026-08-22 | immutable EXP-026 source at git `95f704d` + exact EXP-025/support inputs | CPU-only runtime smoke of EXP026 through all 320 SHA checks and `FrameWindowData` construction; exits before DataLoader/model/training. | validation only; no score | not a test submission | 47 s core validation | complete v1 | PASS in Kaggle's actual runtime. Source SHA `060d1b8a…12eb`; receipt SHA `56f0cdca…8743`; 256/64 windows, max 1,449 nodes/frame, and all node/edge/division aggregates reproduce EXP-025 exactly. This clears source/runtime construction risk without consuming GPU quota. |
| EXP-028 | 2026-08-22 | refreshed `yunusgmsoy/kimi-notebook-v17` vs exact EXP-006 source | External controlled safe-division-veto ablation: lower only the default DeepCenter safe-division score threshold `0.12 → 0.08`. | reused-label diagnostic only: adjusted edge `0.9131`, division `TP/FP/FN=0/5/5`, proxy `0.9131` vs EXP-006 `0.9235` | **0.919**, submission `55732720` | ~50 min public run | complete/full audit; reject threshold change | Full audit PASS: 122,208 nodes / 118,113 edges / 455 divisions, SHA-256 `a15e99ba…c9f4`. Although source changes only one threshold, selection/pruning cascades into 93 removed and 35 added node IDs, 461 coordinate changes among common nodes, 143 removed and 100 added edges, and 73 removed plus 73 added division parents (382 retained). Physical `2 µm` node/edge Jaccard remains `0.997222/0.995869`; the account score is `-0.001` to EXP005 and agrees directionally with the negative reused-label proxy, so the relaxed veto is rejected. |
| EXP-029 | 2026-08-22 | EXP-006 base + `backtracking/biohub-medal-v1` + EXP-008 | Edge-only unanimous alternatives from a very-near dual-seed/boundary-rescue tracker and the diverse three-U-Net tracker. | label-free visible-test consensus only | do not submit | 13 s build + full audit | rejected no-op | Medal V1 is a distinct clean artifact (122,921 nodes / 118,426 edges / 321 divisions, SHA `130fbee1…27d1`) but is highly correlated with EXP-006 at physical `2 µm` (`0.965096/0.955579` node/edge Jaccard) and is sorted below exact-`0.917` EXP-008. After mapping 120,415 Medal and 93,630 EXP-008 nodes, the two trackers produced zero unanimous alternative edges. The parsed output is exactly EXP-006 topology; no candidate or submission is promoted. |
| EXP-030 | 2026-08-22 | EXP-006 base + `hiranorm/new-lb-0-916-infer-ensemble-lf-exp002` + EXP-008 | Edge-only unanimous alternatives from two explicit lower-scoring detector-diverse ensembles. | label-free visible-test consensus only | do not submit | 13 s build + full audit | rejected after physical audit | The Hira artifact has 116,166 nodes / 111,762 edges / 80 divisions and explicit `0.916` attribution (SHA `b1e741c8…b0cc`); it has only six boundary coordinates equal to `-1`, no negative time/hubs, but fails our strict in-volume raw-artifact gate. Mapping 96,314 Hira and 93,630 EXP-008 nodes yielded five proposals, three conflict-free replacements. Every alternative is physically worse than EXP-006: edge/CV residuals move `1.862/0.813→3.565/4.596`, `1.675/0.000→3.350/4.959`, and `1.862/1.675→3.833/4.241 µm`. This is repeated evidence that crowded-frame mapping consensus needs an independent motion veto. |
| EXP-031 | 2026-08-22 | EXP-006 coordinates/topology + EXP-008/Hira detector coordinates | Two-donor direction-gated coordinate consensus: for mutually mapped, nonzero donor shifts with cosine `>=0.5`, move `0.5` toward their mean; otherwise keep EXP-006 exactly. | label-free visible-test localization agreement | submit only after non-negative EXP-014/019 evidence | 10.8 s build + CPU wrapper | Kaggle artifact complete; gated | 82,517 nodes have both mutual mappings, 78,933 have two nonzero shifts and 50,909 are eligible; eligible cosine mean is `0.806`. Applied physical shift mean/p95/max is `0.491/0.836/0.995 µm`, with zero out-of-volume proposals. The fail-closed Kaggle wrapper locates all parents by SHA and exactly reproduces the local smoke: 122,266 nodes / 118,156 edges, unchanged topology/identity, full audit PASS, canonical SHA `fcdc9a0a…fa93d`, serialized coordinate fingerprint `26f3847e…173b0`. The older local default-CSV SHA `aa64ba08…3360` and in-memory fingerprint are retained only as pre-wrapper provenance. |
| EXP-032 | 2026-08-22 | EXP-006 base + `raunakdey07/biohub-harmonic-fusion-dual-seed-pipeline` + EXP-008 | Edge-only unanimous alternatives from a nearby retention-guard/harmonic graph and the diverse three-U-Net graph. | label-free visible-test consensus only | do not submit | 13 s build | rejected as no-op | Raunak is clean and distinct (122,083 nodes / 117,803 edges / 307 divisions, SHA `3e98739f…a1e0`) but physically close to EXP-006 at `2 µm` (`0.975815/0.966866` node/edge Jaccard). Mapping 120,678 Raunak and 93,630 EXP-008 nodes finds zero unanimous alternative proposals, so the output is topology-identical to EXP-006 and receives no slot. |
| EXP-033 | 2026-08-22 | EXP-006 coordinates/topology + EXP-008/Raunak detector coordinates | Fixed two-donor direction-gated coordinate consensus using the exact EXP-031 gate/cosine/alpha contract. | label-free visible-test localization agreement | do not submit before parent localization evidence | 11 s build + full audit | local artifact complete; gated | Only intended change from EXP-031 is donor B: clean Raunak replaces raw Hira. Of 93,160 common mutual mappings, only 1,407 have two nonzero donor shifts and 628 pass cosine `>=0.5`; shift mean/p95/max is `0.566/0.860/0.956 µm`, zero out-of-volume. Exact topology/identity audit PASS at 122,266 nodes / 118,156 edges, SHA `139c2912…3a5d`. Independent EXP-019 changes 597/628 of these nodes and agrees at cosine `>=0.5` on 321; this is supporting precision evidence, not a promotion gate. |
| EXP-034 | 2026-08-22 | frozen EXP-006/014/019/022/023/031/035/040/041/045/047 Kaggle artifacts + competition train GEFF | CPU-only reused-label coordinate/topology diagnostic with SHA-located inputs, 7 µm physical Hungarian matching, node-count adjustment and topology-aware division matching. | four visible/test same-stem labelled overlaps; explicitly non-honest/reused | diagnostic only; never submit | ~8 min CPU/version | v1–v4 infrastructure/calibration aborts; v3/v5–v9 complete PASS | Frozen EXP006 replays exactly at `0.8870825255`. Broad/strict prune parents give `+0.002329/+0.000775`; their coordinate compositions EXP045/047 give `+0.007562/+0.005992`. EXP045 changes edge `TP/FP/FN 2029/164/98→2032/148/95`; EXP047 reaches the same `2032/95` TP/FN with FP `152`. V9 summary SHA `9c44f9a6…a3b1`, receipt SHA `ab1657ae…1e39`. Both compositions are preserved, broad stronger on reused labels, but positive evidence never promotes. |
| EXP-035 | 2026-08-22 | exact EXP-006 topology + EXP-008/Raunak division consensus | Add a second daughter only under the frozen H-035 completeness, orphan, `7 µm`, divergent-motion and daughter-continuation guards; preserve every node and all existing edges. | label-free consensus plus reject-only same-stem visible overlap; not honest CV | do not submit without later honest division evidence | 14 s build + 31 s audit; ~4 min Kaggle CPU | Kaggle v2 complete PASS; hold | The label-free scan found exactly one conflict-free proposal: dataset `6bba_05db0fb1`, parent `65628`, existing child `66324`, proposed orphan child `66302`. EXP-008 and Raunak agree exactly; Medal-V1 and Anhad independently reproduce the same pair. Edge lengths are `0.575/5.585 µm`, daughter separation `5.984 µm`, and displacement cosine `-0.669`. Full audit PASS at 122,266 nodes / 118,157 edges / 456 divisions, every base row preserved. The downloaded Kaggle graph at SHA `7376bd3c…74bd4` is semantically exact to local SHA `db19d213…f953`. Frozen overlap scoring returns an exact zero differential because the sparse labelled matching does not observe this event; therefore no reject signal but also no evidence to spend a slot. |
| EXP-036 | 2026-08-22 | exact EXP-006 base + EXP-008/Arnav ENS5 edges | Post-hoc unanimous edge diagnostic using the same complete-source/conflict-free contract as EXP-015/020. | label-free visible-test consensus; no score | do not submit | 15 s local | rejected after physical audit | ENS5 itself is clean and full-audit PASS (128,584 nodes / 123,287 edges / 339 divisions, SHA `77e06053…430a9`) but shares the EXP-008 detector family (`2 µm` node/edge overlap `0.796416/0.762308`) and has no attributable LB. The pair proposed 20 alternatives, five conflict-free. Every accepted edge increases both length and constant-velocity residual: respectively `1.862/0.812→3.565/4.596`, `3.350/3.375→4.375/4.614`, `1.675/0.000→3.350/4.959`, `2.438/1.724→3.833/5.585`, and `1.862/0.812→2.471/2.633 µm`. Output SHA `2d0b5c1b…e84`; reject without wrapper or slot. |
| EXP-037 | 2026-08-22 | stable last-COMPLETE `luffyh04/harshini-1` kernel input + frozen support-pack split-0 checkpoint | CPU-only checkpoint provenance/compatibility audit before considering the accessible public secondary model as a third seed. | architecture diagnostic only; no validation or LB claim | not a submission | <1 min CPU | v1 provenance abort; v2 complete PASS; rejected as already used | The current cancelled Harshini output downloaded through the CLI contains an 8,357,783-byte `own_seed_v1` checkpoint at SHA `b1507f69…a7b7`, but Kaggle correctly resolves notebook inputs to the last COMPLETE version instead. V1 stopped before loading tensors and enumerated the attachable artifact; v2 proves it has the exact 136 keys/shapes and 2,077,996 parameters of the primary architecture, zero non-finite tensors, zero equal keys, global cosine `0.9999999958`, and relative L2 difference `0.01061`. Crucially, SHA `9bac2fa0…305f` is byte-for-byte the secondary checkpoint already pinned and loaded by EXP-006, so this is provenance confirmation rather than a new third seed. Receipt SHA `c11115ed…0ff6`; no inference or slot. |
| EXP-038 | 2026-08-22 | cancelled-run `luffyh04/harshini-1` `own_seed_v1` output + exact EXP-006 primary/secondary weights | Private staging plus CPU-only three-checkpoint provenance/compatibility audit. | architecture diagnostic only; no validation or LB claim | not a submission | <1 min CPU | v1 compatibility PASS; v2 duplicate-mount abort; v3 complete PASS | The staged source is exactly 8,357,783 bytes, SHA `b1507f69…a7b7`, with original attribution/no relicensing. V1 locates all three exact SHAs and returns `PASS_NEW_COMPATIBLE_CHECKPOINT`: 136/136 keys, 2,077,996 parameters, zero shape/dtype/nonfinite failures and zero equal keys against either seed. Relative L2 is `0.99320/0.99327` to primary/secondary (global cosine `0.9999878` for both), proving a genuinely different compatible state but not better predictions. V1 receipt SHA `049d88d6…0de6`. Dataset v3 adds a fail-closed manifest and loader-compatible weight tree. Kaggle auto-expanded `weights.zip`, so v2 correctly exposed three byte-identical mounts and aborted before the loader check. V3 selects the canonical manifest path and passes the actual expanded-directory loader contract without relaxing SHA/config validation; receipt SHA `bb9b5386…f9c4`. |
| EXP-039 | 2026-08-23 | exact EXP-006 notebook + EXP-038 `own_seed_v1` checkpoint | Controlled full-test inference replacing only secondary SHA `9bac2…` with `b1507…`; every numeric/model/postprocess setting remains frozen. | runtime label-free; visible overlap is reject-only | **0.906**, submission `55732718` | ~40 min T4 | Kaggle v1/full graph audit PASS; reject checkpoint | The fail-closed run verifies primary/secondary/DeepCenter SHAs and no ground-truth access. Candidate SHA `73370617…eb12` contains 120,259 nodes / 116,088 edges / 447 divisions, degrees `1/2`. The large `-0.014` LB delta confirms the negative EXP034 reject-only sign and rules out this checkpoint as a production ensemble seed. |
| EXP-040 | 2026-08-22 | exact EXP-006 base + frozen EXP-005/008 division votes | Edge-removal-only division prune under the pre-registered H040 unanimous-singleton and constant-velocity rule. | label-free physical consensus; same-stem truth is reject-only | do not submit before honest LOEO evidence | 7 s local | artifact/topology + reject-only truth PASS; hold for LOEO | Exact input SHAs are pinned. Both donors map `121,695/93,630` nodes and agree on 208 base divisions as the same singleton continuation; 197 have a predecessor and the frozen `4/2 µm` physical gate prunes 160. Candidate keeps all 122,266 nodes/coordinates and removes only those 160 edges: `118,156→117,996`, divisions `455→295`, max degrees `1/2`, SHA `9f0b0711…a5e3`. Removed branches have median CV residual `6.320 µm` versus `2.011 µm` retained. EXP034 v6 exactly recalibrates EXP006 and gives a positive reject-only delta `+0.002329`: edge `TP/FP/FN 2029/164/98→2029/158/98`, division `0/12/3→0/9/3`. Summary SHA `673dfdd2…a9e`, receipt SHA `e8eec2d7…e23d`; reused labels preserve rather than promote H040. |
| EXP-041 | 2026-08-22 | exact EXP-040 rule with nested `7/4 µm` physical thresholds | Strict high-precision subset of the same frozen two-tracker division prune. | label-free physical consensus; frozen before EXP040 truth result | do not submit before honest LOEO evidence | 7 s local | artifact/topology + reject-only truth PASS; hold for LOEO | The exact same 208 unanimous-singleton proposals and 197 predecessor-qualified sources yield 55 prunes, a strict subset of all 160 EXP040 changes. Nodes/coordinates remain exact, edges `118,156→118,101`, divisions `455→400`, max degrees `1/2`, SHA `21a42ffa…e114`. EXP034 v7 exactly recalibrates EXP006 and gives `+0.000775`: edge `TP/FP/FN 2029/164/98→2029/162/98`, division `0/12/3→0/11/3`. Summary SHA `a696e635…7f33`, receipt SHA `42371b97…35cb`. The broad EXP040 arm catches three visible false divisions versus one here, but reused labels can only preserve both until paired untouched evidence. |
| EXP-043 | 2026-08-23 | exact EXP-011/012 physical-prune graph reconstruction contract | CPU-only synthetic `tracksdata`/GEFF runtime smoke for nested `4/2` and `7/4 µm` arms. | synthetic graph; no model/data score | not a test submission | <1 min CPU | complete v1 PASS; launch prerequisite | Two frozen forks have rejected-child CV residuals `6/8 µm`. Broad prunes both and strict only the `8 µm` fork, preserving all eight nodes and yielding `6→4/5` edges exactly; both GEFF save/reloads pass and strict removals are a proper subset. The normalized function AST is identical in EXP011, EXP012 and EXP043. Receipt SHA `944f24b5…eb71`; the LOEO launcher now refuses source/receipt drift before pushing either audit. |
| EXP-044 | 2026-08-23 | immutable Kaggle-staged EXP-040/041 artifacts | CPU-only wrapper that revalidates both candidate SHAs, build/topology receipts, schema, node/edge/division counts, endpoint closure and degree limits, then exposes distinctly named byte-identical files. | artifact audit only; no validation or promotion | never auto-submit from wrapper receipt | 9 s CPU | v1 unbounded locator; v2 complete PASS | V1 spent time walking the attached competition tree and was superseded; v2 uses canonical dataset paths and passes in 9 s. Outputs reproduce exact SHAs `9f0b0711…a5e3` / `21a42ffa…e114`, receipt SHA `c07665ef…9607`. The submission helper now recognizes both but hard-blocks `-Submit` while `SubmissionReady=false`; immutable artifact validation alone cannot authorize a slot. |
| EXP-045 | 2026-08-23 | exact EXP-014 nodes + exact EXP-040 edges | Disjoint coordinate/division composition under H045. | both parents use public weights; promotion gates still closed | submit only if EXP014 LB and both untouched physical folds pass | 7 s local | composition/full graph + reject-only truth PASS; hold | Input SHAs are pinned. The artifact contains all 122,266 node rows from EXP014 and all 117,996 edge rows from EXP040: 93,630 moved coordinates, 295 divisions, max degrees `1/2`, output SHA `4d93515e…9f88`. EXP034 v8 gives reject-only delta `+0.007562` with `+3 TP/-16 FP/-3 FN`; this preserves H045 but cannot open either promotion gate. |
| EXP-046 | 2026-08-23 | immutable Kaggle-staged EXP-045 artifact | CPU-only fail-closed wrapper that revalidates the exact composition SHA, both parent SHAs, row-provenance receipt, schema, counts, endpoint closure and degree limits before exposing `exp045_submission.csv`. | artifact audit only; no validation or promotion | never auto-submit from wrapper receipt | 9 s CPU | Kaggle v1 complete PASS | Kaggle reproduces SHA `4d93515e…9f88` at 122,266 nodes / 117,996 edges / 295 divisions and max degrees `1/2`; receipt SHA `7aad3d38…60ff`. The wrapper hard-codes `submission_allowed_by_this_receipt=false`, so immutable packaging cannot open either H045 promotion gate. |
| EXP-047 | 2026-08-23 | exact EXP-014 nodes + exact EXP-041 edges | Strict nested disjoint coordinate/division composition under H047. | both parents use public weights; promotion gates still closed | submit only if EXP014 LB and both strict untouched physical folds pass | 7 s build + full audit | composition/full graph + reject-only truth PASS; hold | Exact EXP014 nodes plus EXP041 edges yield 122,266 nodes / 118,101 edges / 400 divisions, max degrees `1/2`, SHA `5dd662d8…63f2`. EXP034 v9 gives `+0.005991844`, edge `TP/FP/FN 2032/152/95`, division `0/11/3`; positive but below broad EXP045. This rejects neither arm and opens no promotion gate. |
| EXP-048 | 2026-08-23 | immutable Kaggle-staged EXP-047 artifact | CPU-only fail-closed wrapper revalidating exact composition/parent SHAs, row provenance, schema, graph counts, endpoint closure and degree limits before exposing `exp047_submission.csv`. | artifact audit only; no validation or promotion | never auto-submit from wrapper receipt | 9 s CPU | Kaggle v1 complete PASS | Kaggle reproduces SHA `5dd662d8…63f2` at 122,266 nodes / 118,101 edges / 400 divisions and max degrees `1/2`; receipt SHA `8b878f9c…66c7`. The submit helper recognizes EXP047 but hard-blocks `-Submit` while its two scientific gates remain closed. |
| EXP-049 | 2026-08-23 | reciprocal EXP-009/010 checkpoints + frozen EXP-011/012 receipts | Fail-closed H049 production inference, prefix-routing each test movie to the model trained exclusively on the other embryo. | production only after both strict untouched audits | one supporting LB slot only if both numeric gates pass | — | killed by predeclared gate; no submission | EXP011 passes score/recall/drop (`0.744130/0.972594/+0.069295`), while EXP012 passes absolute score/recall (`0.595767/0.943095`) but its confirmation→audit drop is `−0.126196`, below the frozen `−0.10` floor. The automatically launched notebook also encountered an early offline dependency-version import error, but repairing it cannot change the already-failed scientific gate; EXP049 is not relaunched and spends no slot. |
| EXP-050 | 2026-08-23 | EXP-009 checkpoint + frozen EXP-011 selection receipt | H050 paired `44b6` evaluation: registered motion versus fixed `0.9 × motion + 0.1 × learned probability`, plus amortized greedy physical arms. | 4 confirmation + 63 untouched audit movies | no test submission | T4; 67 movie-passes | Kaggle v1 COMPLETE; first H050/H052 fold PASS | On all 63 untouched movies motion-only scores `0.744130`; the frozen weak learned tie-break improves to `0.744864` (`+0.000734`). Registered motion also beats the paired greedy base `0.579940` by `+0.164190`, so the `44b6` half of H052 passes. Greedy `4/2` and `7/4` pruning improve total score by `+0.003073/+0.002380` but each loses both division TPs (`2→0`), so they do not satisfy the stricter H040/H041 division-TP gate. |
| EXP-051 | 2026-08-23 | EXP-010 checkpoint + frozen EXP-012 selection receipt | Reciprocal H050 paired `6bba` evaluation with the identical weak tie-break contract. | 4 confirmation + 120 untouched audit movies; no score-file read or reselection | no test submission | T4; 124 movie-passes | Kaggle v1 COMPLETE; H050/H052 reciprocal gates PASS | On all 120 untouched movies weak learned tie-break improves registered motion by `+0.000771`. More importantly for H052, registered motion scores `0.595767` versus greedy `0.466180`, delta `+0.129587`. Combined with EXP050, pooled registered−greedy is `+0.134782`; H052 promotes. Reciprocal analysis SHA `534416cd…f578`; EXP051 result SHA `07b183fd…e063`. |
| EXP-052 | 2026-08-23 | exact EXP-006 node rows | H052 registered-motion topology replacement: preserve all nodes/coordinates and replace only edges with median-inlier shift + `<7 µm` one-to-one Hungarian links. | label-free build; visible same-stem truth is reject-only | submit only after reciprocal EXP050/051 registered-vs-greedy gate | 15 s local/CPU | deterministic build/full audit + Kaggle v1 PASS; reject-only proxy PASS; promotion-gated | Exact 122,266 nodes are preserved. Edges change `118,156→117,708`, with 117,593 retained, 563 removed and 115 added; all 455 divisions are removed, degrees become `1/1`, output SHA `3791f74f…9fab`. Node/edge Jaccards versus EXP006 are `1.000000/0.994267`; local rebuild and Kaggle reproduce the exact SHA/full audit. Frozen visible-overlap EXP034 v10 is positive (`+0.004574874`): edge `TP/FP/FN 2029/164/98→2027/150/100`, division `0/12/3→0/0/3`; summary/receipt SHAs `0f5f6a50…73c7` / `efd0bad1…0d8f`. This removes the reject-only veto but cannot open the reciprocal promotion gate. |
| EXP-053 | 2026-08-23 | exact EXP-014 node rows + exact EXP-052 edge rows | H053 disjoint composition of detector-consensus coordinates and registered-motion topology. | label-free composition; visible same-stem truth is reject-only | submit only if EXP014 public LB is `>=0.919` and H052 passes both untouched registered-vs-greedy comparisons plus the pooled gate | 15 s local/CPU | v2 graph/reject-only audit PASS; byte-exact semantic-parent-row v3 running; promotion-gated | Exact `(dataset,node_id,t)` identity is shared by both parents; the graph contains 122,266 nodes / 117,708 edges / 0 divisions, moves 93,630 coordinates versus the topology parent and has max degrees `1/1`. V1 exposed Windows-CRLF/Kaggle-LF drift; v2 canonicalized LF at SHA `8103351b…02bc` and passed Kaggle/full audit. EXP034 v11 gives the strongest frozen reject-only delta so far, `+0.010674665`: edge `TP/FP/FN 2029/164/98→2031/139/96`, division `0/12/3→0/0/3`; summary/receipt SHAs `4c9e0abe…b663` / `5c50bcc0…5990`. A later exact-float audit found pandas changes up to `5.68e−14` on 10,779 nodes, so v3 copies every semantic CSV field after the disposable index comma byte-for-byte from EXP014 nodes and EXP052 edges, normalizes LF and rebuilds only the required consecutive index; expected SHA `9fd72382…e6d5`. No identity, coordinate string or graph edge is recomputed; all gates remain closed. |
| EXP-054 | 2026-08-23 | exact EXP-006 full inference + H052 registered relink | Hidden-compatible productionization of EXP052: preserve the dynamic test discovery, model inference and finalized rounded nodes, then replace only topology with the frozen registered Hungarian policy. | reciprocal registered-vs-greedy LOEO `+0.164190/+0.129587`; not an exact EXP006-topology CV comparison | **0.905**, submission `55705721` | 37 min T4 | complete; reject topology replacement | Exact hidden-compatible reproduction passed, but LB is `−0.014` versus EXP006 `0.919`. The honest CV result remains valid for registered versus the much weaker greedy arm; it did not establish superiority to EXP006's learned/ILP topology. This distinction is now frozen in the experiment ledger. |
| EXP-055 | 2026-08-23 | exact EXP-054 production inference + exact EXP-019 intensity rule | Hidden-compatible disjoint composition: freeze registered edges on rounded EXP006 nodes, then refine only emitted coordinates from each dynamically mounted raw test frame. | topology inherited from EXP054; no honest localization CV | **0.893**, submission `55706857` | 34 min T4 | complete; reject intensity correction | The only change from EXP054 is exact EXP019 intensity coordinates, so the paired LB delta is `−0.012`. Kill the intensity family and every EXP022/023 descendant that depends on it. |
| EXP-056 | 2026-08-23 | exact EXP-054 + exact EXP-008 inference sources | Hidden-compatible detector-consensus coordinates plus registered topology. Both parent pipelines rerun on every hidden movie; no public submission artifact is mounted. | strongest frozen reject-only coordinate/topology proxy; H052 reciprocal topology gate PASS | submit after exact public reproduction/full audit | expected <2 h T4 | production notebook built; launch blocked by weekly GPU quota | Build SHA `c9cfcc8f…df77`; the notebook preserves dynamic test discovery, runs both detector families, applies only the frozen `2 µm`, `alpha=0.5` mutual coordinate rule, and leaves all EXP054 edges untouched. Kaggle rejected the v1 push before execution with `Maximum weekly GPU quota of 30.00 hours reached`; the final daily slot is reserved until quota reset rather than risking a >12 h CPU rerun. |
| EXP-057 | 2026-08-23 | exact EXP-006 + exact EXP-008 full inference | Primary coordinate frontier: frozen `2 µm` mutual matches, `alpha=0.50`, exact EXP006 topology/divisions. | EXP014 frozen proxy `+0.005209`; no honest localization CV | submit after exact public reproduction/full audit | expected <2 h T4 | production notebook built; pending Kaggle v1 | One dual-inference notebook emits all EXP057/058/059 candidates. Build SHA `75744cd1…4b85`; no public artifact input. |
| EXP-058 | 2026-08-23 | exact EXP-057 matches + EXP006 topology | Conservative detector-consensus dose `alpha=0.25`; all node identities and edges exactly EXP006. | controlled robustness arm; no honest localization CV | submit after v1 audit if a slot is available | same run as EXP057 | declared before run/LB; pending Kaggle v1 | Shares predictions and mutual match set with EXP057; only interpolation weight differs. |
| EXP-059 | 2026-08-23 | EXP057 coordinates + registered ordinary links + EXP006 divisions | Diversified hybrid that preserves every original division-source edge while replacing only ordinary one-to-one topology. | H052 mechanism positive versus greedy, but EXP054 LB negative versus EXP006 | submit only after exact division/conflict/full audit | same run as EXP057 | declared before run/LB; pending Kaggle v1 | Designed to test whether EXP054's loss came primarily from deleting the high-value safe divisions; fail closed on max indegree/outdegree or any missing original division edge. |
| EXP-060 | 2026-08-24 | exact EXP-005 + exact EXP-008 public/full inference sources | Coordinate-only detector consensus on the `0.920` topology: mutual-nearest `<=2 µm`, `alpha=0.50`; no node identity, time, edge or division change. | no honest localization CV; label-free diversity only | submit after production rerun/full audit | expected <2 h T4 | local artifact + production build PASS; GPU quota-blocked | Public artifact matches 93,738/122,032 nodes (`76.81%`); donor disagreement mean/p95 `0.997/1.771 µm`, applied shift `0.499/0.885 µm`. Full vectorized audit PASS at 122,032 nodes / 117,594 edges / 67 divisions, max degrees `1/2`, SHA `5fb789ea…bb99`. Hidden-compatible dual-inference build SHA `71f3f0f1…15fb`; Kaggle refused launch with the 30 h weekly GPU limit. |
| EXP-061 | 2026-08-24 | exact EXP-060 matches + EXP-005 topology | Conservative coordinate dose `alpha=0.25`, otherwise byte-semantically the same graph policy. | controlled robustness arm; no honest localization CV | submit after same production rerun/full audit | same run as EXP060 | local artifact + production build PASS; GPU quota-blocked | Same 93,738 matches; applied shift mean/p95/max `0.249/0.443/0.500 µm`. Full audit PASS with exact EXP005 graph counts and degrees, SHA `ee54117f…f078`. Declared and built before any EXP008/060/061 account score. |
| EXP-062 | 2026-08-24 | EXP060 coordinates + registered ordinary links + EXP005 divisions | Diagnostic third output from the shared production run. | H052 does not compare against harmonic topology | do not submit: EXP054 already falsified wholesale registered relinking on LB | same run as EXP060 | built as diagnostic only; GPU quota-blocked | Preserved only because the shared generator emits a topology diagnostic. It is explicitly ineligible for a daily slot after EXP054 scored `0.905` versus harmonic `0.919–0.920`. |
| EXP-063 | 2026-08-24 | exact EXP050 holdout-`44b6` checkpoint/split | Honest 63-movie untouched OOF comparison of eight linkers on identical detections; export compressed candidate caches for later CPU arms. | embryo-disjoint by construction | not a test submission | expected comparable to EXP050 T4 | build/compile PASS; GPU quota-blocked | Source SHA pinned; output SHA `be710718…04b41`. Adds no threshold selection and opens labels only after every arm graph is frozen. Both push attempts were rejected before execution by the 30 h weekly GPU quota. |
| EXP-064 | 2026-08-24 | exact EXP051 holdout-`6bba` checkpoint/split | Reciprocal honest 120-movie OOF comparison with the exact EXP063 arm/cache contract. | embryo-disjoint by construction | not a test submission | expected comparable to EXP051 T4 | build/compile PASS; GPU quota-blocked | Source SHA pinned; output SHA `e2b7772d…0abf2`. Together with EXP063 this supplies paired per-movie results for registered, weak/heavy learned, public/support ILP, greedy and two physical-prune linkers. Push was rejected before execution by the same quota. |
| EXP-065 | 2026-08-25 | `evgendvorkin/biohub-0-927-lb` v12 | Clean harmonic forward/reverse tracker with DeepCenter epoch-2 veto and safe-division radii `8/11/10 µm`; independently freeze the newly exposed clean frontier. | public weights; no honest OOF | **0.924**, submission `55761017`; source title claimed `0.927` | source runtime | complete/full audit PASS; retain | 122,207 nodes / 117,919 edges / 263 divisions, SHA `33c179b0…2e6a`. Physical `2 µm` node/edge Jaccard to EXP005 is `0.949763/0.930624`. The account result is strong but fails to reproduce the title by `−0.003`, direct evidence that external score labels are not portable. |
| EXP-066 | 2026-08-25 | `rockerritesh/0-926-biohub-divsub` v1 | Clean dual-seed/DeepCenter tracker without harmonic reverse fusion, using conservative division caps and `8/11/10 µm` geometry. | public weights; no honest OOF | **0.926**, submission `55761018` | source runtime | complete/full audit PASS; current account leader | 120,748 nodes / 116,536 edges / 384 divisions, SHA `5f4ec83d…7bc`; byte-identical to current Kunal and Andrés outputs. Physical overlap to EXP005 is `0.937791/0.922486`. This is the strongest confirmed account score, but the exact public weights still have no unseen-embryo OOF. |
| EXP-067 | 2026-08-25 | `backtracking/biohub-general-v8` v1 | Continuation guard plus second-daughter completion; orthogonal clean topology hedge. | public weights; no honest OOF | **0.919**, submission `55761031` | source runtime | complete/full audit PASS; standalone reject | 120,236 nodes / 116,246 edges / 492 divisions, SHA `c7ea6f98…7d6b`. Physical overlap to EXP005 is `0.829598/0.792880`. Its orthogonality did not compensate for the lower public accuracy (`−0.007` to EXP066), but it remains structural diversity evidence. |
| EXP-068 | 2026-08-25/26 | `pawanmali/biohub-mcflow-v1` immutable v2 | Global min-cost-flow assignment instead of local harmonic/ILP association. | public weights; no honest OOF | `55761370` invalid wrapper; corrected `55781325` PENDING | source runtime | full-inference resubmitted | 116,860 public-test nodes / 110,063 edges / only 5 divisions, SHA `f7cf3977…6e34`; physical overlap to EXP005 is `0.716869/0.602068`. The invalid public-output wrapper was replaced by direct immutable full inference v2 at `2026-08-26 00:15:43 UTC`. |
| EXP-069 | 2026-08-25/26 | `flexonafft/biohub-harmonic-fusion` immutable v11 | Current high-frontier retention/division configuration. | public weights; no honest OOF | `55761371` invalid wrapper; corrected `55781326` PENDING | source runtime | full-inference resubmitted; exact duplicate of EXP070 | The current v11 output is 120,738 nodes / 116,526 edges / 384 divisions, SHA `2dbb8d02…4fa7`, not yesterday's older `fd77de2a…974a` artifact. Version-specific download and audit PASS. It is byte-identical to Ahmet v1/EXP070, discovered after both submissions were registered. |
| EXP-070 | 2026-08-26 | `ahmetyasreminolu/biohub-last-version` immutable v1 | High-frontier retention-sensitive clean variant. | public weights; no honest OOF | submission `55781466` PENDING | source runtime | submitted/full audit PASS; exact duplicate of EXP069R | 120,738 nodes / 116,526 edges / 384 divisions, SHA `2dbb8d02…4fa7`. Only 34/35 exact nodes/edges differ from EXP066; physical node/edge overlap is `0.999702/0.999674`. It was independently selected before exact-version download proved byte identity with Flex v11. Count it as a duplicate runtime check, not an independent model. |
| EXP-071 | 2026-08-26 | `arnav170/biohub-bi40` immutable v4 | Bidirectional/harmonic association weight `0.40` with a lower division count. | public weights; no honest OOF | submission `55781467` PENDING | source runtime | submitted/full audit PASS | 122,024 nodes / 117,745 edges / 262 divisions, SHA `04218340…f4b9`. Physical node/edge/division overlap to EXP066 is `0.900011/0.873648/0.274162`, giving a materially different high-frontier hedge. |
| EXP-072 | 2026-08-26 | `xstargate/biohub-v17-e2-reverse020` immutable v1 | Controlled harmonic reverse-association weight `0.20`. | public weights; no honest OOF | submission `55781468` PENDING | source runtime | submitted/full audit PASS | 122,209 nodes / 118,108 edges / 455 divisions, SHA `7a05c4e4…9453`. Physical node/edge/division overlap to EXP066 is `0.943609/0.928718/0.215942`; source and output scans find no metric exploit or invalid topology. |

EXP011 v1 failed before dependency/model/data access on the canonical parent-mount locator. V2 passed that guard and failed on `.zarr.geff` node-count metadata construction after first calibration inference; no metric was printed or saved. V3 passed both fixes, then the first ILP policy hit a `tracksdata` API contract: the solver returns a `GraphView`, while division scoring calls `.copy()` and requires an owned graph. Again no metric was printed or saved. V4 changes only `solver.solve(graph)` to the API-prescribed `solver.solve(graph).detach()` in both reciprocal sources, preserving identical nodes/edges. Frozen split, policy grid and physical arms remain unchanged; launcher source hashes are advanced fail-closed each time.

The frozen LOEO physical-arm analyzer requires each arm to fire on both folds and separately requires non-negative total score, adjusted-edge Jaccard and division TP on each untouched fold. It cannot authorize a submission by itself and explicitly treats donor consensus as out of scope; its source is committed before either audit exists.

The reciprocal EXP050/051 analyzer independently reconstructs the official micro-aggregate from the per-movie counts, enforces non-negative H050 score on each fold plus a positive pooled delta, and reports the amortized greedy physical arms separately. Geometry-only mechanism evidence is permanently marked `submission_authority=false`; it cannot be confused with the missing EXP005/008 donor-consensus gate.

EXP-007 from `ericwang03/biohub-daily-probe-lane-5` tests H-013 with equal-weight eight-view D4 edge TTA on shared detections. The public source does not claim a measured LB gain; timestamp proximity to a leaderboard entry is explicitly treated as insufficient evidence.

## Cross-prediction diversity (visible four movies)

- EXP-003 vs EXP-004: exact centroid-set Jaccard `0.414665`; exact coordinate-edge Jaccard `0.317917`.
- EXP-002 vs EXP-003: node Jaccard `0.013752`; edge Jaccard `0.003088`.
- EXP-002 vs EXP-004: node Jaccard `0.014303`; edge Jaccard `0.003137`.
- EXP-004 vs EXP-005: node Jaccard `0.792003`; edge Jaccard `0.763670`; divisions `297 -> 67`.
- EXP-005 vs EXP-006: node Jaccard `0.975946`; edge Jaccard `0.966517`; divisions `67 -> 455`; only `1,726/2,288` edges are left/right-only.
- EXP-006 vs EXP-007 source: exact centroid/edge Jaccard `0.410806/0.316735`; greedy physical agreement at `2 µm` is `0.789763/0.747972` for nodes/edges.
- EXP-006 vs EXP-008 source: exact coordinates are not comparable because EXP-008 emits refined floats; physical `2 µm` node/edge Jaccard is `0.603850/0.544912`.
- EXP-007 vs EXP-008 source: physical `2 µm` node/edge Jaccard is `0.589720/0.528380`.

Interpretation: dual-seed inference changes a material fraction of the learned graph, while the classical branch is nearly orthogonal. EXP-007 mostly perturbs a shared learned detector within `2 µm`; EXP-008 is materially more diverse and is the better candidate teacher/ensemble arm. Do not union graphs directly because the node-count penalty would dominate; use agreement as high-precision pseudo-labels or train a selector/ranker.

## Public frontier audit (2026-08-22)

The refreshed full leaderboard snapshot downloaded at 18:00 UTC contains 2,636 rows. Its score landmarks are `0.958` at rank 1, `0.943` at rank 10 and `0.929` at rank 50; 100 teams score at least `0.923`, 185 at least `0.920`, 204 at least `0.919`, 369 at least `0.917`, and 791 at least `0.913`. The account's completed best is the exact EXP-006 reproduction at `0.919`, rank 203 (`7.70%`). The nominal 5%/10% score lines remain `0.920/0.917` at ranks 132/264, so this is public bronze-zone evidence but not a confirmed medal; official eligibility and the final private leaderboard control the result. The live competition API reports a 2026-09-29 23:59 UTC deadline.

Kaggle's `scoreDescending` list currently places several notebooks above the clean `0.923` Yunus artifact. Code inspection rejects that apparent frontier: `xiaoleilian/biohub-ct-mix-divaug`, all three inspected Kaiwalya variants, `amanatar/biohub-v6-ultra-best`, `muhammaddanyalmalik/cell-tracking`, and the indexed `0.952` `boristown/dark-agi-biohub-cell-tracking-solution` explicitly add negative-time/out-of-volume hubs or fork components to inflate the division term. The `0.952` notebook uses a hub at `t=-1000, z=y=x=-10000`, up to 1,200 component-root edges and five fake forks. The other top entries advertise the same metric-hack lineage. These are not candidates for this project. The highest attributable, reproduced clean public artifact remains EXP-006 (`0.923`); EXP-007 has no attributable public score, and EXP-008 is sorted below EXP-006.

The 17:52 UTC refresh of `kunaldesale2408/biohub-cell-tracking` remains clean but is not a new frontier: its 19,102,928-byte submission is byte-for-byte EXP-008 (`SHA-256 d7ba9e6a…f2bb`; 126,419 nodes, 121,191 edges, audit PASS). Its source visibly combines three U-Nets, flip TTA, velocity/appearance Hungarian linking, snap-only gaps and safe divisions, yet the exact artifact proves it is still the same correlated `0.917` family rather than an independent ensemble vote or a result above `0.923`.

The completed 2026-08-22 refresh of `navazshfathi/best-score` independently produced EXP-006 byte-for-byte (`SHA-256 5c852379…1f4d`; 122,266 nodes, 118,156 edges, audit PASS). Its source was a clean harmonic/safe-division reimplementation, so this is useful reproducibility evidence for the `0.923` base rather than a new candidate.

Fresh `backtracking/biohub-general-v4` and `saitejabandaruin/biohub-masterpiece-tracker-version-16` artifacts are both clean and audit PASS, but neither moves the frontier. General V4 emits 119,563 nodes / 115,208 edges / 334 divisions (`SHA-256 eddb0ff9…a5f7`) and derives from a source-described verified `0.916` lane; its boundary rescue and division-continuation guard are retained only as future LOEO ablations. Masterpiece V16 exactly matches its documented `0.913` artifact (`SHA-256 8c1605b5…9e3f`; 120,797 / 116,501 / 314). No submission slot is allocated to either.

The 11:24 UTC Navaz rerun and newly indexed `mtoshidesu/test-notebook-v17-d17ce0` both produce EXP-006 byte-for-byte: 12,514,365 bytes, SHA-256 `5c852379…1f4d`. Their separate `scoreDescending` rows are duplicate clean reproductions, not a frontier advance; no submission or new experiment ID is warranted.

The completed `xiaoleilian/biohub-m001-ens3-sm6-sim2` run was independently downloaded after the refreshed public-kernel scan. It is clean and passes the full submission audit, but its 19,102,928-byte output is EXP-008 byte-for-byte: 126,419 nodes, 121,191 edges, SHA-256 `d7ba9e6a…f2bb`. Its three-model D4-TTA listing therefore adds no independent ensemble vote and receives no submission or experiment ID. The newer Anhad run was still `RUNNING`, so neither its order nor its prior snapshot output was treated as completed evidence.

The Anhad run later completed and its real 12,558,700-byte output was downloaded. It passes the full submission audit with 122,910 nodes, 118,395 edges, 328 divisions and SHA-256 `f326ea07…3445`; physical `2 µm` overlap with EXP-006 is `0.928212/0.904797` for nodes/edges. This is a nearby clean dual-seed/retention/boundary-rescue ablation, but its own quality receipt remains `candidate_unverified`, lacks the required promotion receipt and forbids submission. It is also ordered below known `0.917` entries, so it neither moves the attributable clean `0.923` frontier nor merits a submission/experiment ID.

`reyhanksatria/graph-patches-for-cell-tracking-0-917-lb` was downloaded because its title suggested a separate post-link mechanism. Its run log does execute gap/division patches, but the final clean artifact is EXP-008 byte-for-byte: 126,419 nodes, 121,191 edges, 352 divisions and SHA-256 `d7ba9e6a…f2bb`. Combined with the explicit `0.917 LB` title and its `scoreDescending` position in the `0.917` group, this supplies a concrete score attribution for EXP-008 rather than a new graph arm. No submission or new experiment ID is warranted.

## Run record template

Copy this block for every new run:

```text
Experiment:
Date / git commit:
Parent/control:
Hypothesis:
Only intended change:
Data split and leakage audit:
Metric implementation/version:
Config/checkpoint hashes:
Per-movie results:
Pooled official score:
Node ratio / edge TP-FP-FN / division TP-FP-FN:
Runtime and hardware:
Kaggle kernel/version/submission ID:
Public LB:
Unexpected observations:
Decision (promote / hold / kill):
Next experiment:
```

## 2026-09-08 — plan correction and independent Zebrahub pretraining

The decision criterion is corrected from “fill available LB slots while chasing gold” to “what verified artifact remains after this run even if the score does not improve?”. No new Kaggle submission was made after EXP128; the remaining daily quota is preserved until a candidate passes the revised evidence gate.

The first community-oriented deliverable is an independent-data pretraining run, not a clone of an open notebook. The existing authorized Zebrahub extraction was used: 256 train windows and 64 validation windows from one source track, with a 21-frame train/validation gap, 326,490 train nodes, 160,373 train edges, 1,636 train division edges, 92,209 validation nodes, 45,321 validation edges and 393 validation division edges. The source receipt SHA is `56f0cdca0028fab3ea480231e26f56195e701165f63494e107c5f96784ce8743`; raw track CSV is not included in the training package.

The complete dataset was transferred into the registered remote project root and passed the pinned validation script, including per-shard SHA checks. The run used one free Quadro RTX 6000 (24,576 MiB, driver 550.54.15), Python 3.11, PyTorch `2.6.0+cu124`, seed `314159`, batch size `2`, and 12 epochs. The default fused SDPA path failed on this GPU with `CUDA error: invalid configuration argument` inside temporal `MultiheadAttention`; a math-SDPA compatibility runner was added at `scripts/run_zebrahub_pretrain_math_sdp.py`, after which the full run completed.

Recorded result: best external validation selection score `0.9666307662353465`, accuracy `0.9998996682087374`, recall `0.9667277597631467`; checkpoint is 8,357,362 bytes with SHA `3300ccd2187af54644a9110c81ee954d34f261d000e767d61a176691d1ee4f0e`. The receipt is `outputs/research/zebrahub_pretrain_20260908/exp026_receipt.json`, and the reproducibility notebook is `notebooks/zebrahub_pretrain_repro_20260908.ipynb`.

This is external pretraining evidence only, not competition-LB or hidden-test evidence. The next promotion gate is a compute-matched competition-data fine-tune followed by reciprocal embryo-disjoint LOEO/OOF comparison against the competition-only baseline, with per-embryo stability. An optional LB submission remains conditional on that gate and the existing guarded submission workflow.

## 2026-09-08 — EXP027 pilot transfer diagnostic (research-only)

The complete 44b6 eight-movie pilot was transferred to the registered remote root after an interrupted transfer was discarded and retried; local and remote tar SHA-256 both equal `5665807a25ffe92bd994b146341f1961c9faf502904f679211ec9f398f959079`. Remote structure validation passed for 8 zarr datasets with 102 files each and 8 geff datasets with 21 files each. The original split receipt remains `outputs/research/external_inputs/pilot_download/pilot_single_44b6_splits.json`; a trainer-compatible list adapter is preserved separately as `pilot_single_44b6_trainer_splits.json`.

Using the same fold, data, batch size 2, downsample `(1,4,4)`, one epoch and 8 training iterations on one Quadro RTX 6000, scratch achieved `acc*recall=0.0000` while Zebrahub UNet initialization achieved `0.9203` (`acc=0.9992`, `recall=0.9210`). Both runs completed without CUDA errors under the checked-in math-SDPA launcher. The Zebrahub checkpoint loaded with `0 missing, 0 unexpected` keys. Remote output weight SHA is `e52ed1085bba70d8f064292514718715ab8aa26475e1835641bf7cf97c89b1ce`.

This is a paired within-embryo diagnostic only: 4 train movies and 4 held-out movies from the same embryo, intentionally too short to support promotion or LB submission. The result supports continuing toward the reciprocal 6bba fold and a full-inference Kaggle clean-run; it does not authorize consuming a submission slot.

The EXP027 GOLD_PUBLIC candidate notebook was built and locally compiled with source SHA `d746494acc5bc98eb1d7eefc777675d8b9e02954ff26273a0cf4e891c2518dcc`, output SHA `86c5a5b23a70165b218a3f4dedda66527a80f4043152bd858b04da95789e5deb`, Internet disabled, dynamic runtime test-set inference retained, and parent-weight fallback disabled. Its private model payload is prepared under `kaggle_datasets/exp027_zebrahub_finetuned_44b6/` and contains the 8,357,362-byte checkpoint SHA `082d3882ad183892b3bb7541ecbb1383670eef5ba474d110afb58ffef7f77583` plus the full5 receipt. Kaggle dataset creation was not attempted after the external safety control required explicit confirmation of this exact payload and destination; no LB quota was consumed.

The first clean Kaggle kernel version 2 completed runtime inference and wrote 192,428 rows from four dynamically discovered test datasets, but the local submission audit correctly rejected it with `max_in_degree=1, max_out_degree=3`; offending parents were `44b6_0113de3b:10200` and `6bba_05db0fb1:806`. No POST was made. Diagnosis found ILP/post-link output could retain a third child when the optional geometry cap was disabled. Version 3 enables the existing physical division geometry filter, preserving at most two valid children per parent before the next clean rerun.
## 2026-09-09 — EXP137 official24 data completion receipt

The complete 24-movie official training corpus is now staged inside the registered remote Kaggle root and independently bound by a frozen private-first split contract. The final five `6bba` movie pairs were selectively extracted from one official 81.4 GiB Kaggle archive; all 1,476 local `6bba` files matched the live manifest sizes before transport. A 1,995,770,368-byte tar was split into 20 parts, every remote part hash matched, and the reconstructed local/remote tar SHA-256 was `25484c7fea853639595576a5d2703f211a684ad56b74b94a444380a00ec8dda7`.

The full remote audit passes for 24 movies, 2,952 files, 10,658,385,974 bytes and 408 parsed Zarr-v3 metadata JSON files. Cryptographic content-tree hashes are recorded for every movie. The frozen contract SHA is `775e4fe3d8113ee76a1c721a01136233de5968eeb53f62ea624cd12c2bdc1923`; the reciprocal trainer split SHA is `5eb0c0426c8b2cc5331c4e2ea0b34e79d3caf48e8eef822def89c69da0b11b0b`; the audit-log SHA is `e8852b4176ecf872c1bece1eb8d406cb65c9610f574ebdd91326dc2c6cdd6711`. The split freezes, in each direction, 10 source-train movies, 2 source-only checkpoint-selection movies, 4 target-development movies and 8 target locked-audit movies. Locked labels remain unopened.

The 81.4 GiB archive and all local/remote transport tar parts were removed immediately after verification; only the verified official24 corpus, read-only train view, split contract and audit evidence remain. Detailed receipt: `reports/exp137_data_stage_batch3_20260909.json`. This infrastructure artifact has no Kaggle submission authority by itself.
## 2026-09-09 — EXP145 four-view edge-feature TTA pre-registration

The exact-source inspection of `reyhanksatria/biohub-cell-tracking-0-946-lb`
isolated one narrow mechanism: inverse-transform averaging of the U-Net feature
maps consumed by the edge predictor. EXP145 adapts that idea without importing
the source's public-tuned stack and without expanding our geometry from four to
eight views. Relative to the existing detector-TTA parent, the only intended
change is to retain the primary U-Net output from identity, flip-X, flip-Y and
flip-XY, inverse-transform each feature tensor and average it before edge
prediction. Detection logits already use those exact four views and remain
unchanged, as do checkpoints, threshold `0.985` and registered-motion linker.

Parent predictor SHA is
`f698f97c6b00ec92e41aec032bf24d317d565d4f14bab56610f7d4697c441d70`;
the compile-checked candidate SHA is
`4b6698ad7cfa8d7bc243107feb8783427ac01a2f76b77096c374e909eec3c4b1`.
The mechanism will be evaluated once on both development directions using each
source-selected seed-314159 Zebrahub checkpoint. Promotion requires
nonnegative score and recall deltas in each embryo, positive pooled score,
and no division-TP loss. It does not run before EXP137 finishes and has no
locked-audit or Kaggle authority. Receipt:
`reports/exp145_feature_tta_preregistration_20260909.json`.
## 2026-09-10 — EXP137 full reciprocal development result and EXP144 locked-audit pre-registration

EXP137 completed the exact pre-registered `6bba → 44b6` full fold: 10 source
movies for gradient training, two disjoint source movies for checkpoint
selection, seed `314159`, five epochs, threshold `0.985`, and registered-motion
Hungarian linking. Scratch selected epoch 4 (`acc×recall=0.9792`); the
Zebrahub-U-Net arm selected epoch 1 (`0.9732`). Both target results were saved
before their score was inspected. The RTX6000 process exited normally, the GPU
returned to 5 MiB/0%, and lease
`biohub-exp137-full-reciprocal-20260909` was released.

The hardened metric checker recomputed all aggregates from per-movie sufficient
statistics. On the original `44b6 → 6bba` direction, initialization changes
score `0.627534 → 0.629441` (`+0.001907`) and node recall by `+0.008276`. On
the new reverse direction it changes `0.729685 → 0.789186` (`+0.059501`) and
recall by `+0.029213`. Across all eight development movies, the micro-aggregate
changes `0.635297 → 0.641194` (`+0.005897`); the independent seed-repeat gate
also passes. Both embryo deltas are nonnegative, pooled delta is positive,
recall does not regress, and division TP does not fall, so the reciprocal
development gate authorizes the one-time locked audit. This is not yet Kaggle
submission authority. The reverse per-movie signs are only 2/4 positive and
include a `−0.099362` outlier, so stability must be decided by the locked set.

EXP144 freezes all four evaluations before opening any locked score: scratch
and initialized checkpoints on the eight remaining `6bba` movies, plus scratch
and initialized checkpoints on the eight remaining `44b6` movies. All use the
same evaluator, threshold and registered linker. No result is inspected until
all four files exist. Promotion requires nonnegative score and node-recall
deltas in each embryo, positive pooled score, and no division-TP loss. Receipt:
`reports/exp137_full_reciprocal_20260909.json`; exact gate artifact under
`outputs/research/exp130_official24_private_first/exp137_remote_artifacts/pair_seed314159/`.
## 2026-09-10 — EXP144 locked result and EXP145 mechanism diagnosis

EXP144 completed all four frozen 8-movie locked arms before any score was read.
The Zebrahub initialization failed in both embryo directions: `44b6→6bba`
changed `0.689519→0.669000` (`−0.020518`, 1/8 positive) and `6bba→44b6`
changed `0.698357→0.672045` (`−0.026311`, 2/8 positive). The pooled 16-movie
score changed `0.691449→0.669664` (`−0.021785`) while mean node recall rose by
`+0.007013`. Thus the initializer finds more cells but damages the registered
lineage edges enough to lose official score consistently across embryo folds.
There are zero division true positives and nine false negatives across these
movies, so the experiment supplies no positive division-quality evidence.

This reverses the development conclusion and is exactly why the locked audit
exists. Zebrahub initialization is rejected for PRIVATE_ROBUST and receives no
LB slot. The publication decision is `RETRY_BEFORE_OPENING_AS_AN_IMPROVED_MODEL`;
the negative transfer result remains publication-worthy evidence, but must not
be advertised as a private-ready improvement. Receipt:
`reports/exp144_locked_reciprocal_audit_20260910.json`.

EXP145 then tested the pre-registered four-view edge-feature TTA on both
development folds without reading any candidate locked score. Every per-movie
metric and graph summary was exactly identical to the parent (`pooled delta
0.0`). This is not a failed stochastic guess: the registered-motion arm ignores
learned edge probabilities, and the feature patch intentionally preserves the
detector logits/coordinates, so the mechanism cannot affect its output. Reject
the arm and do not spend locked compute or Kaggle quota. Feature TTA remains
potentially relevant only for a learned/weak linker, which would require a
separate pre-registered mechanism test. Receipt:
`reports/exp145_feature_tta_development_20260910.json`.

## 2026-09-10 — EXP146 scratch-seed consensus pre-registration

EXP146 returns to the scratch-only parent after EXP144 rejected external
initialization. Two independent five-epoch scratch fits (`314159`, `271828`)
are compared in each reciprocal embryo direction. Before new target inference,
the topology seed is selected solely by training-time `acc*recall` on the two
source-only checkpoint-selection movies; ties choose `314159`. The only target
transform is frozen mutual-nearest coordinate averaging below `2.0 µm` with
`alpha=0.5`; the selected seed's registered-motion topology is preserved.

This is a prospectively frozen candidate-specific full-OOF test over all 24
movies, not a second untouched locked audit: EXP144 already opened the 16
former locked labels for a different initializer hypothesis. Promotion needs
positive score delta in each embryo direction and pooled, nonnegative recall
and division-TP deltas in each direction, at least 8/12 nonnegative movies per
direction, and no movie worse than `-0.01`. Receipt:
`reports/exp146_scratch_seed_consensus_preregistration_20260910.json`. No Kaggle
slot is reserved before these local gates pass.

EXP146 launcher v1 exited before training or target inference because its
single-fold staged trainer JSON was addressed as split `1` instead of `0`.
Only an exception log was written; the GPU returned to `5 MiB, 0%`. The retry
changes only that index, preserving the exact movie membership and all frozen
model/ensemble gates. Failure receipt:
`reports/exp146_pre_target_launch_failure_20260910.json`.

During the retry's source-only epoch 3, a downstream path audit found that the
already-running launcher would later read the new checkpoint from `split_1`
although the corrected training fold writes `split_0`. Before target inference,
a compatibility symlink `split_1 -> split_0` was created only inside
`weights/exp146_scratch_6bba_seed271828/`; the local reproducible launcher now
uses `split_0` directly. Checkpoint bytes and experiment choices are unchanged.

## 2026-09-10 — EXP147 attributed conservative division repair pre-registration

The registered-motion parent is one-to-one and therefore recovered zero of
nine annotated divisions in the EXP144 16-movie audit. EXP147 freezes the
geometric core of `qrz1201/biohub-public-0-941-repro` v1 safe-division repair:
one nearest orphan second daughter, parent/new-daughter `≤4.7 µm`, existing
child `≤7.8 µm`, sisters `≤7.2 µm`, both daughters continuing one frame, and
granddaughter separation growing by at least `2.25 µm`, with the source's
frame/global caps. DeepCenter is deliberately not imported, isolating one
mechanism and avoiding an unvalidated model dependency.

This candidate will use EXP146's source-only-selected scratch topology in each
direction and will be evaluated once from cached predictions. Promotion needs
positive official score in both embryo directions, a positive pooled division
TP delta, pooled division precision at least `0.25`, no embryo adjusted-edge
loss worse than `0.005`, and no recall loss. Exact receipt:
`reports/exp147_safe_division_preregistration_20260910.json`.

EXP147 launcher v1 failed before data access or score because the isolated
run root omitted the already verified `evaluate_coordinate_consensus.py`
dependency that supplies `registered_links`. The exact failure log is retained;
the retry stages dependency SHA `426b4ee3…fad2` and changes no model,
parameter, movie or promotion gate. Receipt:
`reports/exp147_pre_score_launch_failure_20260910.json`.

## 2026-09-10 — EXP146 and EXP147 full-OOF results

EXP146 selected scratch seed `314159` in both directions using only source
checkpoint-validation (`0.8628>0.8233` and `0.9792>0.9703`). The fixed
seed-coordinate consensus then failed in both directions: `6bba` target
`0.670493→0.667762` (`−0.002730`, 4/12 nonnegative, worst `−0.021521`) and
`44b6` target `0.701969→0.698426` (`−0.003544`, 6/12 nonnegative, worst
`−0.051661`). Pooled 24-movie score changed `0.676146→0.673263`
(`−0.002883`). Stratified 10,000-draw movie bootstrap was
`[−0.008012,+0.002315]`, only 13.35% positive; every leave-one-movie-out delta
remained negative. This is stable rejection evidence, not a near miss. Receipt:
`reports/exp146_scratch_seed_consensus_result_20260910.json`.

EXP147's attributed conservative division repair produced a small edge-score
increase in both directions and pooled (`+0.000350`), but it recovered zero of
13 annotated divisions and added 43 false division parents (division precision
`0.0`). The positive edge delta therefore cannot satisfy the predeclared
division-purpose gate. Geometry-only second-daughter repair is rejected; a
learned division signal or independently validated visual veto is required.
Receipt: `reports/exp147_safe_division_result_20260910.json`. Neither experiment
has Kaggle submission authority; all five slots remain unused.

## 2026-09-10 — EXP149 cached native-ILP pre-registration

Longer scratch training is not promoted: source-only forward validation peaked
at epoch 3 and collapsed at epoch 4, while reverse validation still improved,
so one longer duration would increase domain asymmetry. EXP149 instead tests
the exact native ILP edges already returned by `predict_video(use_ilp=True)`
and stored in the seed-314159 caches. The registered parent discards these
edges and is structurally unable to predict divisions. Checkpoint, detections,
coordinates and threshold stay fixed; only topology changes. Promotion needs
positive official score in both embryo directions, division TP gain, pooled
division precision at least 0.25, no recall loss, and graph degree validity.
Receipt: `reports/exp149_cached_native_ilp_preregistration_20260910.json`.

## 2026-09-10 — EXP148 reciprocal weak-linker TTA and EXP149 native-ILP result

EXP148 reused the already computed feature-TTA caches with the weak learned
Hungarian arm. The forward four-movie development fold changed by `+0.000514`,
entirely from one movie, while the reciprocal fold was metric-inert
(`0.000000` on all four movies). This does not replicate across embryo domains
and receives neither locked-audit nor Kaggle authority. Receipt:
`reports/exp148_weak_linker_feature_tta_result_20260910.json`.

EXP149 failed closed before producing a complete fold score. On
`6bba_062c8d37.zarr`, the exact cached native ILP graph had maximum in/out
degrees `1/3`; competition lineage output permits at most two children. The
raw topology is therefore rejected, and no partial metric is interpreted.
The exact exception log and executed-source hash are preserved in
`reports/exp149_cached_native_ilp_result_20260910.json`. Any geometry-capped
variant is a distinct, prospectively specified experiment; no LB slot was used.

## 2026-09-10 — EXP150 source-attributed native-ILP geometry repair pre-registration

EXP150 freezes the existing public graph family's division-geometry filter
before reading a repaired score. Cached native edges are ranked by descending
learned probability then ascending physical distance. For every multi-edge
source, the top two are retained only if both target the next frame, both
parent distances are at most `10.5 µm`, and sister separation is at most
`8.0 µm`; an invalid fork is reduced to its top edge. This directly repairs
EXP149's out-degree-three anomaly without choosing a threshold from current
labels. Checkpoints, detections, coordinates and caches remain unchanged.

Both reciprocal 12-movie outputs must exist before comparison. Promotion still
requires positive score in each embryo direction and pooled, division-TP gain,
pooled division precision at least `0.25`, no recall regression, and valid
degrees. Exact source SHA and test evidence are in
`reports/exp150_native_ilp_geometry_preregistration_20260910.json`. No LB slot
is reserved before the gate passes.

## 2026-09-10 — EXP150 result and EXP151 learned-guided division pre-registration

EXP150 made the raw native graph schema-valid, but it cannot replace the
registered parent: pooled score collapsed `0.676146→0.002193` (`−0.673952`),
with zero division TP and three FP. Exact source inspection disproved the
initial suspicion of incompatible node IDs. The decisive telemetry is
sparsity: the inherited softmax-`>0.5` native graph contains only tens of edges
per movie, versus thousands to tens of thousands from registered assignment.
Receipt: `reports/exp150_native_ilp_geometry_result_20260910.json`.

EXP151 therefore freezes the only dataflow in which these sparse scores are
plausibly useful: add-only second-child evidence on top of registered topology.
It considers only native high-confidence edges to unclaimed children, then
applies the previously attributed `4.7/7.8/7.2 µm` geometry, one-frame
continuation, `2.25 µm` divergence-growth, and fixed frame/global caps. Both
12-movie directions are written before comparison. Promotion requires positive
score in each embryo and pooled, positive division-TP gain, at least `0.25`
division precision, valid degrees, and no recall regression. Receipt:
`reports/exp151_native_guided_division_preregistration_20260910.json`. No LB
slot is reserved.

## 2026-09-10 — EXP151 result and EXP152 dense learned-edge pre-registration

EXP151 was exactly inert in both 12-movie directions: the inherited
softmax-`>0.5` learned pool supplied zero second-child candidates surviving
the frozen geometry, continuation and divergence rules. Every score, recall
and division statistic equals the registered parent. Receipt:
`reports/exp151_native_guided_division_result_20260910.json`.

EXP152 tests the remaining falsifiable version of this mechanism with one GPU
pass at edge probability `0.02`. Candidate thresholds
`[0.5, 0.2, 0.1, 0.05, 0.02]` are selected independently in each direction
using only the two source checkpoint-validation movies; eligibility requires
nonnegative source score and division-TP deltas, then maximum source score and
a conservative higher-threshold tie break. Target inference is allowed only
after that selection freezes. Exact procedure and source hashes:
`reports/exp152_dense_native_source_selection_preregistration_20260910.json`.

Launch v1 completed the forward source cache but stopped before reverse source
inference because the frozen `6bba` source-validation list had not been staged
in the isolated run directory. Retry v1 then stopped before inference because
the reverse seed-314159 checkpoint is under historical trainer split `1`, not
split `0`. No source score was opened and no target inference had begun in
either failure. The final retry reuses the verified forward cache, stages the
contract-derived list, resolves the exact checkpoint path, and holds one
common-queue RTX6000 lease.

## 2026-09-10 — EXP152 dense learned-edge result

EXP152 completed under one common-queue RTX6000 lease and released it after
the GPU returned to 5 MiB and 0% utilization. On both source-only validation
folds, every threshold in `[0.5, 0.2, 0.1, 0.05, 0.02]` was exactly identical
to the registered parent, so the frozen conservative tie-break selected
`0.5` in both directions. The subsequent prospective 24-movie target OOF was
also exactly inert: forward `0.670493→0.670493`, reverse
`0.701969→0.701969`, and pooled `0.676146→0.676146`, with zero division-TP,
division-FP or recall change.

This rejects the hypothesis that the missing division signal is recoverable
by lowering one native-edge threshold. A 25-fold lower cutoff still supplies
no second-child candidate that survives the frozen geometry, continuation and
divergence checks. Further threshold sweeping is not justified; the next
candidate must change edge/division training or candidate construction. Two
pre-target retries failed before score inspection, but their redirected log
paths were overwritten by the successful retry; future launchers must use
attempt-specific output directories. Receipt:
`reports/exp152_dense_native_source_selection_result_20260910.json`. No Kaggle
slot was used; all five slots remain free.

## 2026-09-10 — EXP153 division-supervision diagnostic pre-registration

The frozen official splits contain only 1 division parent in 817 44b6 training
windows and none in its two checkpoint-selection movies; 6bba contains 11 in
970 training windows and one in selection. Moreover, the inherited loss
computes `div_rows` but assigns them weight `1.0`, while checkpoint selection
uses global accuracy×recall. An official-only reciprocal division-weight run
would therefore be underidentified, particularly in the direction where the
private-relevant 6bba target has 12 of the 13 observed division events.

Before retraining, EXP153 measures whether the existing independently trained
real-Zebrahub checkpoint encodes any fork signal on its 64 time-disjoint
external validation shards. The frozen teacher-forced diagnostic uses GT nodes
and reports edge recall plus division-parent recall/precision at
`[0.5, 0.2, 0.1, 0.05, 0.02]`. It is an external mechanism diagnostic, not
competition OOF. If recall is zero through `0.02`, correct loss/selection and
retrain externally; otherwise isolate transfer while preserving the robust
scratch detector. Receipt:
`reports/exp153_division_supervision_diagnostic_preregistration_20260910.json`.

### EXP153 result

The dtype-only retry completed on one RTX6000 and the lease was released after
the GPU returned to 5 MiB/0%. On 188 true division parents, the independent
real-Zebrahub model recovers 89 at threshold `0.5` (recall `0.4734`, precision
`0.2438`) and 155 at `0.2` (recall `0.8245`, precision `0.0508`). Thus the
external edge head contains genuine fork-ranking signal, but permissive
thresholding creates thousands of false forks. This explains why further
cutoff lowering is unsafe and why the next candidate must isolate the external
fork signal while preserving the robust scratch detector/topology and adding
a high-precision veto. Receipt:
`reports/exp153_division_supervision_diagnostic_result_20260910.json`.


Correction to the historical EXP136 prose: initializer SHA `3300ccd…4f0e`
is the independently trained **real Zebrahub** checkpoint from EXP026, not the
synthetic EXP024 checkpoint. The recorded negative transfer score and decision
remain unchanged; only the source description was wrong.

## 2026-09-10 — EXP154 external edge scorer on fixed scratch coordinates

EXP154 isolates the positive EXP153 mechanism from EXP136's failed detector
transfer. The source-selected scratch coordinates and registered topology are
kept byte-for-byte; the immutable real-Zebrahub model is used only to score
edges at those coordinates. Candidate second daughters still pass the frozen
EXP151 geometry, continuation, divergence and count caps. Thresholds `0.5` and
`0.2` are selected on the two source checkpoint movies in each direction;
only then may both 12-movie target folds run. Promotion requires positive score
in both embryos and pooled, positive division TP, division precision at least
0.25, no recall loss, and bounded adjusted-edge loss. Receipt:
`reports/exp154_external_edge_fixed_coordinates_preregistration_20260910.json`.

## 2026-09-10 — EXP154 result and EXP155 one-to-one tie-break result

EXP154 completed prospective 24-movie OOF. External learned scores on fixed
scratch coordinates produced small score gains in both directions and pooled
(`0.676146→0.676440`, `+0.000294`), confirming a transferable ordinary-edge
signal. It nevertheless recovered zero of 13 division parents and introduced
41 false forks, so it failed the frozen division-purpose gate and is rejected
for Kaggle submission. Receipt:
`reports/exp154_external_edge_fixed_coordinates_result_20260910.json`.

EXP155 tested whether that signal could safely break ordinary one-to-one
Hungarian ambiguities. On the untouched forward source-validation movies,
weights `0.05` and `0.10` reduced score by `0.001545` and `0.003081`
respectively, with unchanged recall. Both failed the preregistered nonnegative
source gate; reverse selection and all 24 target movies therefore remained
unopened. This rejects unconditional score mixing and preserves the target OOF
for a genuinely confidence-gated follow-up. Receipt:
`reports/exp155_external_weak_linker_result_20260910.json`. No LB slot was used.

## 2026-09-10 — EXP156 confidence-gated ordinary-edge pre-registration

EXP156 isolates the avoidable failure in EXP155: convex mixing reduced every
motion score and lowered the dummy threshold. The parent score, 7 µm gate and
dummy cost now remain byte-for-byte equivalent; only external edges above
confidence `0.5` or `0.8` may receive a bonus of `0.01` or `0.03`. Four
configurations are selected source-only in each reciprocal direction. The
24 target movies stay unopened unless both directions have an eligible frozen
configuration. Receipt:
`reports/exp156_external_confidence_gate_preregistration_20260910.json`.

## 2026-09-10 — EXP156 source-only result

All four confidence-gated configurations were exactly inert on the forward
source fold. On the reciprocal source fold every configuration regressed;
the least harmful (`p≥0.8`, bonus `0.01`) changed score by `-0.001564` with
unchanged recall. Because one direction had no eligible selection, no target
movie was opened. This rejects post-hoc external-probability bonus tuning and
points to explicit edge-head recalibration. Receipt:
`reports/exp156_external_confidence_gate_result_20260910.json`. No LB slot was
used.

## 2026-09-10 — EXP157 division-positive edge-head recalibration

The next model experiment addresses a verified training defect instead of
tuning inference again. The real-Zebrahub parent is resumed exactly, its U-Net
and detection head are frozen in eval mode, and only the temporal transformer
is trained for one epoch at `2e-5`. Existing focal-BCE weights stay 1 for
ordinary cells, become 2 for a division row, and 8 only for its two true
daughter cells. External time-validation division F1 is the first gate; no
competition target fold is opened unless this improves while edge recall stays
within `0.01`. Receipt:
`reports/exp157_division_positive_recalibration_preregistration_20260910.json`.

### EXP157 result

One epoch on RTX6000 completed with the visual U-Net and detector frozen. The
external time-validation gate narrowly passed: division F1 at `0.5` changed
`0.321881→0.323308` (`+0.001428`), while edge recall changed by `-0.003575`.
Both competition source folds then passed the permissive predeclared gate
(`+0.002565` / exact zero), allowing one prospective 24-movie target pass.

The target result is identical to EXP154 at the evaluated threshold: pooled
`0.676146→0.676440` (`+0.000294`), but zero of 13 true divisions were recovered
and 41 false division parents were introduced. The candidate therefore fails
the division-purpose gate and receives no LB submission. This isolates a
useful lesson: reweighting the existing probability head is too weak to alter
competition decisions; the next model must change candidate representation or
learn an explicit division objective. Receipt:
`reports/exp157_division_positive_recalibration_result_20260910.json`.

## 2026-09-10 — EXP158 explicit visual daughter-pair design

EXP158 is pre-registered before implementation or GPU allocation. It replaces
edge-wise daughter scoring with a symmetric classifier over one parent and an
explicit pair of daughter candidates. A shared 3D crop encoder supplies visual
features; physical parent/daughter distances, sister separation, midpoint
motion and continuation evidence supply geometry. Swapping the two daughters
must leave the score unchanged.

Training is restricted to the verified 256 real-Zebrahub training shards;
checkpoint and one operating threshold are selected on the independent
64-shard time validation with the existing 21-frame gap. External promotion
requires pair average-precision evidence and division-parent precision at least
`0.50` with recall at least `0.20`. Competition evaluation remains staged:
both reciprocal source-validation directions must pass before a single
prospective 24-movie target pass. No Kaggle slot is reserved. Receipt:
`reports/exp158_visual_daughter_pair_preregistration_20260910.json`.

### EXP158 stopped before competition data

The GPU run was stopped after four external epochs because the implementation
used only immediate pair geometry while the preregistration ambiguously named
future continuation/divergence as an input. It is not valid to repair that
contract after seeing metrics. No competition source or target label was
opened. The partial external pilot reached pair AP `0.230063`, proposal recall
ceiling `0.973404`, and precision/recall `0.52/0.0710`; it did not pass the
external gate. The owned PID was stopped, RTX6000 was observed at 5 MiB/0%,
and the lease was released. Receipt:
`reports/exp158_visual_daughter_pair_stopped_20260910.json`.

## 2026-09-10 — EXP159 corrected visual daughter-pair retry

EXP159 freezes the corrected interpretation before retry: the model sees
parent/daughter crops and immediate pair geometry only. Future continuation
and sister divergence remain a separate frozen graph-safety gate. CUDA
reproducibility is tightened by replacing MaxPool3d with AvgPool3d and setting
`CUBLAS_WORKSPACE_CONFIG=:4096:8` before launch. The original external
precision `>=0.50`, recall `>=0.20` gate remains unchanged; competition data
stay closed unless it passes. Receipt:
`reports/exp159_visual_daughter_pair_preregistration_20260910.json`.

### EXP159 result

The full eight-epoch external run rejected the scratch crop encoder before any
competition evaluation. The selected epoch 3 had pair AP `0.231913` and a
proposal recall ceiling of `0.973404`, but precision `0.50` was achievable at
only `0.0929` recall, below the frozen `0.20` gate. The raw JSON retained a
stale hard-coded EXP158 label; its SHA is preserved and a correcting receipt
binds it to EXP159 rather than silently rewriting evidence. AvgPool3d backward
also remained nondeterministic on the installed CUDA build. No source/target
competition labels were opened and no LB slot was used. Receipt:
`reports/exp159_visual_daughter_pair_result_20260910.json`.

## 2026-09-10 — EXP160 frozen pretrained-feature pair head

EXP160 is the mechanism-led successor to EXP159. Proposal K=4, deterministic
negative sampling, all-parent validation and the external precision/recall
gate are unchanged. The single representational change replaces the scratch
crop CNN with eval-only 32-channel node features from the independently
trained real-Zebrahub U-Net; only a symmetric daughter-pair MLP is trained.
The frozen backbone has no backward pass, avoiding the CUDA pooling
nondeterminism found in EXP159. Five implementation tests pass, including
exact daughter-swap invariance. Competition data remain closed unless external
precision `>=0.50` and recall `>=0.20`. Receipt:
`reports/exp160_pretrained_feature_pair_preregistration_20260910.json`.

### EXP160 result

Frozen real-Zebrahub node features improved the best observed high-precision
recall to `0.147541` at precision `0.519231` (epoch 10), versus EXP159's
`0.092896`, but still missed the preregistered `0.20` recall gate. Selection by
pair AP retained epoch 8 (`AP=0.200551`, precision/recall
`0.512821/0.109290`). The first launcher omitted `tracking_repo/src`; that
pre-metric failure is preserved separately and the retry used identical code,
data and hyperparameters. No competition fold or LB slot was used; GPU was
observed idle and the lease released. Receipt:
`reports/exp160_pretrained_feature_pair_result_20260910.json`.

## 2026-09-10 — EXP161 fixed visual-pair rank ensemble

Before ensemble inference, EXP161 freezes one mechanism-diverse candidate:
stable percentile ranks from the scratch 3D crop head and the frozen-pretrained
feature head are averaged `0.50/0.50` on the exact same K=4 pair pool. No
alternate weight or probability blend will be evaluated. The external gate is
unchanged: precision `>=0.50`, recall `>=0.20`; parent APs and score
correlation must also be reported. Competition data remain closed unless that
gate passes. Receipt:
`reports/exp161_visual_pair_rank_ensemble_preregistration_20260910.json`.

### EXP161 pre-metric checksum failure; EXP162 corrected retry

EXP161 stopped at the integrity guard because its receipt mistyped the EXP160
head SHA as `3cdc50…`; the immutable checkpoint and raw EXP160 result both say
`3cdc170…`. No validation shard or competition data was scored. The lease was
released and the log retained. EXP162 preregisters the exact same evaluator
and fixed `0.50/0.50` rank ensemble with only that checksum corrected; no
metric-facing choice changed. Receipts:
`reports/exp161_visual_pair_rank_ensemble_failure_20260910.json` and
`reports/exp162_visual_pair_rank_ensemble_preregistration_20260910.json`.

### EXP162 pre-metric CLI failure; EXP163 versioned launcher

EXP162 also stopped before data access because the manually transcribed remote
CLI corrupted the otherwise correct scratch SHA. The integrity guard rejected
it, the GPU was idle, and the lease was released. EXP163 preserves the same
model, ensemble and gate but moves every path/checksum into a versioned shell
launcher. Nine local tests verify its hashes and external-only scope; remote
`bash -n` is required before allocation. Receipts:
`reports/exp162_visual_pair_rank_ensemble_failure_20260910.json` and
`reports/exp163_visual_pair_rank_ensemble_preregistration_20260910.json`.

### EXP163 checksum discovery; EXP164 completed ensemble result

The versioned EXP163 launcher proved that the previously copied feature-head
SHA still combined the correct prefix with an unrelated suffix. Its integrity
guard stopped before validation data. Direct `sha256sum` of the remote
checkpoint and the immutable EXP160 raw result established the full SHA as
`3cdc17023606b8193cbdfb97f1035a5e8383a17763764b80c2c99ae0f1590d38`.
EXP164 bound that value in a unit-tested launcher and completed the one fixed
ensemble evaluation.

The scratch and pretrained-feature pair scores had correlation `0.784820`.
Their fixed equal rank ensemble achieved pair AP `0.229459`, precision `0.50`
and recall `0.153005` (28/183 covered true parents among 56 predictions). This
is better high-precision recall than either selected component operating
point, but below the frozen `0.20` gate. Therefore no competition source or
target fold was opened and no LB slot was used. RTX6000 was observed idle and
the lease released. Receipts:
`reports/exp163_visual_pair_rank_ensemble_failure_20260910.json` and
`reports/exp164_visual_pair_rank_ensemble_result_20260910.json`.

### EXP160 evidence-hash correction

An integrity review found that the EXP160 result receipt copied EXP159's raw
JSON SHA (`96e9d411…`) into its `raw_result_sha256` field. Direct SHA-256 of
the immutable EXP160 raw JSON is
`886965902989883dbed60ac327fb556885feb37c0ab89cfa0dfa0b5f985de91b`.
The checkpoint SHA and all reported metrics are unchanged. The original
receipt remains preserved; the append-only correction is
`reports/exp160_raw_hash_correction_20260910.json`.

## 2026-09-10 — EXP165 visual-pair error diagnostic

EXP165 freezes an external-only diagnostic before another model run. It will
measure within-parent positive-pair ranks, global parent calibration, the fixed
component operating-set union, and geometry-conditioned errors on the same 64
time-validation shards. It cannot select a new hyperparameter or open any
competition fold. Receipt:
`reports/exp165_visual_pair_error_diagnostic_preregistration_20260910.json`.

### EXP165 pre-metric import failure

EXP165 stopped during top-level imports because the isolated run omitted the
module that supplied percentile ranks. No shard was discovered or scored. PID
181177 was verified stopped and the RTX6000 lease was released. EXP166 may
repeat the identical diagnostic with that six-line helper embedded locally;
no metric-facing choice changes. Receipt:
`reports/exp165_visual_pair_error_diagnostic_failure_20260910.json`.

## 2026-09-10 — EXP166 self-contained diagnostic retry

EXP166 preserves every EXP165 input, output and interpretation constraint. The
only code change embeds the deterministic percentile-rank helper so the
isolated run no longer depends on an unstaged module. Ten tests pass; no
competition data or Kaggle slot is eligible. Receipt:
`reports/exp166_visual_pair_error_diagnostic_preregistration_20260910.json`.

### EXP166 pre-metric dependency-path failure

EXP166 stopped during top-level imports because the launcher did not expose
the retained EXP159/160 module directories. No shard was discovered or scored;
the lease was released. EXP167 changes only PYTHONPATH to those immutable
retained dependencies. Receipt:
`reports/exp166_visual_pair_error_diagnostic_failure_20260910.json`.

EXP167 preregisters the dependency-path-only retry, with the same external
diagnostic and no metric-facing change. Receipt:
`reports/exp167_visual_pair_error_diagnostic_preregistration_20260910.json`.

### EXP167 result and parent-calibration successor

EXP167 completed on 64 external shards. Correct pairs ranked first for 92.35%
of covered divisions with the scratch head and 91.80% with the feature head,
but the precision-0.50 operating sets recovered only 17 and 20 of 183 parents;
the fixed ensemble recovered 28. Parent propensity is the dominant bottleneck.
EXP168 preregistered time-disjoint pair-fit, parent-calibration and prospective
evaluation windows, but stopped before data because its launcher serialized
line continuations as plus arguments. EXP169 changes only to a one-line shell
command. Receipts: `reports/exp167_visual_pair_error_diagnostic_result_20260910.json`,
`reports/exp168_parent_calibrated_pair_preregistration_20260910.json`,
`reports/exp168_parent_calibrated_pair_failure_20260910.json`, and
`reports/exp169_parent_calibrated_pair_preregistration_20260910.json`.

### EXP170 launch safety rejection

EXP170 was staged and checksum-verified, but no process was launched. Two
generated launch commands contained malformed remote paths and were rejected
by execution safety before SSH execution. The reservation had no PID and was
released; RTX6000 remained untouched. A fresh explicit user confirmation is
required before a new request ID may invoke the exact verified launcher.
Receipt: `reports/exp170_launch_rejected_20260910.json`.

### EXP171 explicitly authorized retry

The user explicitly authorized EXP171 on RTX6000 after the EXP170 safety
rejection. EXP171 keeps the EXP168 model, split, seed, parameters and gate;
only the fresh run path, launcher name and queue request ID change. Nine local
tests pass. Receipt:
`reports/exp171_parent_calibrated_pair_preregistration_20260910.json`.

### EXP171 result

EXP171 completed the frozen three-window external experiment on RTX6000. The
pair head reached AP 0.237328 on calibration and 0.183717 on the prospective
evaluation window. The separately trained parent-propensity MLP reached parent
AP 0.134816, but no ranked prefix achieved precision 0.50; recall at the gate
was therefore zero. The external gate failed, so no competition fold or Kaggle
slot was opened. The result rejects a flexible parent MLP trained on only one
calibration window; the next candidate needs simpler, regularized calibration
or genuinely new parent evidence rather than more capacity. Receipt:
`reports/exp171_parent_calibrated_pair_result_20260910.json`.

### EXP169 queue metadata failure; EXP170 retry

EXP169 never launched: its queue-only run path used a hyphenated directory
that did not match the staged underscore path. The terminal request was
released with no PID and RTX6000 at 5 MiB/0%. EXP170 changes only the queue
path and request ID; code, split, seed, parameters and gate remain identical.
Receipt: `reports/exp170_parent_calibrated_pair_preregistration_20260910.json`.

### EXP172 frozen parent-calibrator diagnostic

EXP172 is registered after EXP171 and before allocation. It compares the raw
top daughter-pair score with the trained parent-MLP score on the unchanged
calibration and prospective external windows. This is diagnostic only: the
prospective window cannot select a threshold, model or hyperparameter, and no
competition data or Kaggle slot may be used. Its purpose is to determine
whether EXP171 lost useful parent ordering through overfit calibration or
whether genuinely new parent-level evidence is required. Receipt:
`reports/exp172_parent_calibrator_diagnostic_preregistration_20260910.json`.

### EXP172 result

The frozen diagnostic confirms that EXP171's parent MLP destroyed useful
ordering. On the untouched prospective window, raw top-pair parent AP was
`0.208731` versus `0.134816` for the MLP; their correlation was only
`0.489682`. The raw score reached precision `0.514286` at recall `0.098361`
(18/183 covered true parents), still far below the frozen `0.20` recall gate.
The calibration window showed the same ordering (`0.257615` versus
`0.195154`). The MLP is rejected, raw pair score remains a baseline, and a
successor must add genuinely new hidden-compatible parent evidence. No
competition data or Kaggle slot was used; PID 182666 was verified stopped,
RTX6000 was at 5 MiB/0%, and the lease was released. Receipt:
`reports/exp172_parent_calibrator_diagnostic_result_20260910.json`.

### EXP173 parent-appearance rank ensemble

EXP173 freezes a lower-capacity successor before GPU allocation. A single
regularized linear head is trained on the early fit window using only the
frozen 32-dimensional parent appearance vector. Three arms are reported: raw
top-pair score, appearance score, and one fixed equal-percentile-rank blend.
Each threshold is selected on calibration only and applied numerically
unchanged to the prospective window. Only the fixed blend may advance, and
only at prospective precision at least 0.50 and recall at least 0.20. No
competition data or Kaggle slot is eligible at this stage. Receipt:
`reports/exp173_parent_appearance_rank_ensemble_preregistration_20260910.json`.

### EXP173 pre-metric deterministic-CuBLAS failure; EXP174 retry

EXP173 stopped on the first fit-window batch because deterministic PyTorch
requires `CUBLAS_WORKSPACE_CONFIG` before process startup. No metric or
competition result was produced. The process stopped, RTX6000 returned to
5 MiB/0%, and the lease was released. EXP174 changes only the launcher by
exporting `CUBLAS_WORKSPACE_CONFIG=:4096:8`; all model-facing choices and the
honest calibration/prospective protocol remain frozen. Receipts:
`reports/exp173_parent_appearance_rank_ensemble_failure_20260910.json` and
`reports/exp174_parent_appearance_rank_ensemble_preregistration_20260910.json`.

### EXP174 result

The configuration-only retry completed. Calibration-only threshold transfer
exposed instability hidden by retrospective operating-point selection: raw
pair score retained recall `0.213115` on prospective data but precision fell
from `0.50` to `0.414894`. Parent appearance was nearly uninformative
(`AP=0.006862` prospective), and the fixed blend was worse (`AP=0.048667`,
zero true positives at its transferred threshold). The arm and blend are
rejected before competition data. PID 183437 stopped, RTX6000 returned to
5 MiB/0%, and the lease was released. Receipt:
`reports/exp174_parent_appearance_rank_ensemble_result_20260910.json`.

### EXP175 geometry-only parent signal

EXP175 preregistered one linear head over the five explicit top-pair geometry
features and one fixed equal-rank blend with the raw pair score. Thresholds
were selected on calibration only and transferred numerically unchanged. On
prospective external data, geometry AP was `0.254385` versus raw `0.208731`;
the blend reached recall `0.267760` but precision only `0.418803`. It therefore
failed the frozen precision-0.50 gate. This establishes useful geometry signal
and a real calibration-shift problem, but does not authorize retuning on the
now-consumed prospective window. No competition data or Kaggle slot was used;
the process stopped, RTX6000 was observed at 5 MiB/0%, and the lease was
released. Receipts:
`reports/exp175_parent_geometry_rank_ensemble_preregistration_20260910.json`
and `reports/exp175_parent_geometry_rank_ensemble_result_20260910.json`.

### Live Kaggle account state after EXP175

A read-only account query shows submission `56143472`, description
`PUB-LITE-20260910-R4 GOLD_PUBLIC SLOT1 factorized center v9`, created at
2026-09-10 11:44:57 and still `PENDING` with empty public/private scores. It
was not created by EXP171-175, but it consumes today's GOLD_PUBLIC slot 1.
Therefore four daily slots remain: GOLD_PUBLIC slot 2 and PRIVATE_ROBUST slots
3-5. EXP171-175 used zero slots. No current local candidate qualifies for any
of those four slots.

### EXP175 geometry rank ensemble result

EXP175 tested one preregistered, lower-capacity geometry mechanism under the
same calibration-only threshold protocol. Geometry improved prospective
parent AP from raw score `0.208731` to `0.254385`. The fixed equal-rank blend
reached AP `0.244731` and recall `0.267760`, but its calibration-selected
threshold transferred at precision only `0.418803`, below the frozen 0.50
gate. This exposes threshold transport, not candidate-pair coverage, as the
next validation problem. The prospective window is now observed and must not
be used to retune a successor. No competition data or Kaggle slot was used;
the process stopped, RTX6000 was 5 MiB/0%, and the lease was released.
Receipt: `reports/exp175_parent_geometry_rank_ensemble_result_20260910.json`.

### EXP176 nested robust calibration

EXP176 is frozen before allocation and excludes the consumed t650-789
prospective window and every competition fold. The 64 earlier calibration
shards are split into four contiguous 16-shard blocks. In each leave-one-block-
out fold, the fixed equal-rank pair-plus-geometry score selects a threshold
only where the one-sided 95% Wilson lower bound on precision is at least 0.50,
then transfers that threshold to the excluded block. All four blocks must keep
precision at least 0.50 with nonzero recall, and micro recall must reach 0.15.
Only a pass can authorize one candidate-specific reciprocal official-24 test;
EXP176 itself cannot use Kaggle quota. Receipt:
`reports/exp176_parent_geometry_robust_calibration_preregistration_20260910.json`.

### EXP177 import failure; EXP178 nested-calibration result

EXP177 stopped during top-level imports because the isolated run omitted the
already verified geometry helper module. No checkpoint or shard was read; the
RTX6000 lease was released. EXP178 added only that dependency and completed the
unchanged nested calibration. Held-block precision/recall was `0.438/0.117`,
`0/0`, `0.385/0.222`, and `0/0`. Even the full 64-shard calibration set had no
prefix whose one-sided 95% Wilson precision lower bound reached 0.50. Therefore
the geometry blend is not stable enough to open candidate-specific official-24
evaluation, and no Kaggle slot is authorized. Receipts:
`reports/exp177_parent_geometry_robust_calibration_failure_20260910.json`,
`reports/exp178_parent_geometry_robust_calibration_preregistration_20260910.json`,
and `reports/exp178_parent_geometry_robust_calibration_result_20260910.json`.

### EXP176/177 pre-data compatibility failures; EXP178 retry

EXP176 stopped while the safe loader rejected NumPy normalization arrays in
the SHA-verified owned EXP175 checkpoint. EXP177 enabled full loading only
after that hash guard, then stopped during top-level imports because the
isolated run omitted the module containing frozen rank helpers. Neither run
read a shard or competition data; both leases were released at RTX6000
5 MiB/0%. EXP178 changes only staging by including that verified module; the
nested protocol and gate remain unchanged. Receipts:
`reports/exp176_parent_geometry_robust_calibration_failure_20260910.json`,
`reports/exp177_parent_geometry_robust_calibration_failure_20260910.json`, and
`reports/exp178_parent_geometry_robust_calibration_preregistration_20260910.json`.

### EXP176 pre-data checkpoint-load failure; EXP177 retry

EXP176 stopped while loading the SHA-verified owned EXP175 geometry checkpoint:
its NumPy normalization arrays are intentionally unsupported by PyTorch's
`weights_only` loader. No shard or competition data was read. RTX6000 was
observed at 5 MiB/0% and the lease was released. EXP177 changes only this
compatibility path, using full deserialization after the exact SHA guard; the
nested folds, Wilson rule, score and gate remain unchanged. Receipts:
`reports/exp176_parent_geometry_robust_calibration_failure_20260910.json` and
`reports/exp177_parent_geometry_robust_calibration_preregistration_20260910.json`.

### EXP179 attributed observed-node gap close

EXP179 is frozen before source evaluation. It isolates QRZ v1's density-aware
single-frame gap assignment but permits only reuse of an already detected,
otherwise isolated middle-frame node. Synthetic detections and DeepCenter are
excluded, so this is a dynamic coordinate-graph mechanism rather than a copy
of the correlated public preset. The fixed parameters are evaluated on two
source-validation movies from each embryo. Adaptive density must alter the
candidate set, improve both embryo summaries, be nonnegative on all four
movies, and be no worse than fixed gap close before reciprocal official-24 may
open. This cached-coordinate stage is CPU-only and does not reserve RTX6000 or
Kaggle quota. Receipt:
`reports/exp179_observed_gap_source_preregistration_20260910.json`.

### EXP179 result

The source-only run completed on cached coordinates without a GPU lease.
Density adaptation expanded endpoint eligibility by 172 pairs across the two
`44b6` movies and 33 across the two `6bba` movies, so the rule was not
structurally inert. However, no selected endpoint pair had an otherwise
isolated observed middle-frame node within the frozen 3.2 um reuse radius.
Both fixed and adaptive observed-node arms therefore added zero edges and
exactly matched the registered parent: `0.594714` on the `44b6` source fold
and `0.886626` on the `6bba` source fold. The gate failed; reciprocal
official-24 remains unopened and no Kaggle slot was used. This narrows the
attributed QRZ mechanism: any benefit from its full gap closure must come from
synthetic midpoint recovery and/or DeepCenter confirmation, not reuse of
existing isolated detections. Receipt:
`reports/exp179_observed_gap_source_result_20260910.json`.

### EXP180 reciprocal DeepCenter source training

The public DeepCenter split manifest proves that its teacher trained on every
`44b6` movie, including the current `44b6` source-validation pair. Directly
using that checkpoint in both directions would therefore leak. EXP180 instead
freezes two independent source-only models: each uses the existing official
10/2 train/checkpoint-validation split of one embryo, seed 2026, exactly two
epochs and the attributed public architecture/loss defaults. The opposite
embryo is not discoverable by either training invocation. Success requires
both explicit manifests, finite two-epoch histories, and SHA-recorded best and
last checkpoints. EXP180 authorizes only a later source-validation gap
ablation, not target OOF or Kaggle. One RTX6000 is requested through the common
queue; the two folds run sequentially. Receipt:
`reports/exp180_reciprocal_deepcenter_training_preregistration_20260910.json`.

### EXP180 result

EXP180 completed both explicit source folds on the leased RTX6000 and passed
the pair verifier. The `44b6` validation loss improved from `0.025587` after
epoch 1 to `0.015097` after epoch 2; the `6bba` validation loss improved from
`0.056826` to `0.044798`. Each model saw exactly its preregistered 10 training
and two checkpoint-validation movies, and neither invocation discovered the
opposite embryo. Best checkpoint SHAs are `ac6e8ef8784f4eff3d0673accb77f8a0724a1f4dff585dd723666ed051dab91f`
and `ea0b53cb95c0bfd3cee6f7a73bcf2e32f07912fbee567f8fb38901c8627b118e`.
Observed worker VRAM was 4598 MiB. PID 186234 and all child workers stopped,
RTX6000 returned to 5 MiB/0%, and the lease was released. These checkpoints
authorize only EXP181 source-validation synthetic-gap evaluation; target OOF
and Kaggle remain closed. Receipt:
`reports/exp180_reciprocal_deepcenter_training_result_20260910.json`.

## 2026-09-11 — EXP181 synthetic-gap source gate

EXP181 freezes the next attributed QRZ ablation before GPU allocation. It uses
the registered scratch parent, density-aware one-frame endpoint assignment,
local intensity-refined synthetic midpoints and the fixed DeepCenter threshold
0.25. The two new EXP180 models are used only on their own held-out source
movies; an unvetoed arm is diagnostic. DeepCenter must be exercised and add a
node in both embryos; the gated arm must improve each embryo, avoid every
per-movie score/recall regression, and be no worse than no-veto before any
opposite-embryo OOF may open. No Kaggle slot is authorized. Receipt:
`reports/exp181_synthetic_gap_source_preregistration_20260911.json`.

### EXP180 cleanup completion

The preregistered cleanup was completed after the EXP180 verifier result was
copied locally. Two redundant `checkpoint_last.pt` files and duplicate remote
detailed gate CSVs were removed, reclaiming 84,859,270 bytes. The two SHA-
verified `best.pt` checkpoints remain remotely pinned only as active EXP181
dependencies; compact manifests, histories and logs remain, and the detailed
diagnostics are preserved under
`outputs/research/exp130_official24_private_first/exp180_training`. The result
receipt now records this actual cleanup. No model or result needed by EXP181
was deleted.

### EXP181 queue state

Prelaunch checks passed: five focused tests, Python compilation, exact remote
source/preregistration SHA verification, CUDA/PyTorch import and the presence
of both EXP180 checkpoints and both pairs of source caches. The three normal
SSH identity checks returned `prepost`, `ngpu01` and
`desktop-7t0uo8i\\user`. At allocation time the RTX6000 was physically occupied
by registered RSNA PID 187205 (9,106 MiB and active compute), with its common
queue lease `RUNNING/CURRENT`. EXP181 request
`biohub-exp181-synthetic-gap-source-20260911` therefore entered
`WAITING_RESOURCE`; it is not launched and the existing job is not preempted.
An additional data-free synthetic smoke test exercised the 9.0 um marginal
span branch: a heatmap above 0.25 produced exactly one midpoint and two edges,
a heatmap below 0.25 produced neither, and maximum in/out degree remained one.
An 8.0 um diagnostic correctly exercised the preregistered below-8.5 um bypass
instead of DeepCenter. This added no model/data observation and changed no
frozen source or parameter.

After 3,664 seconds of policy-compliant 2/5/10-minute backoff, the RTX6000
remained occupied by the same registered RSNA PID 187205. Final physical
observation was 9,396 MiB VRAM and 99% utilization. EXP181 had never received
a GPU or PID, had no launch receipt or lock, and opened no movie data. The
waiting request was therefore cancelled rather than left without a monitor;
the other job was not preempted and no alternate GPU was used. Exact small
staging plus the unique EXP180 best checkpoints are retained under a dated
one-day dependency pin for a fresh authorized RTX6000 retry. Receipt:
`reports/exp181_waiting_resource_20260911.json`. No Kaggle slot was used.

### EXP181 retry 2 and publication snapshot

On continuation the same RSNA PID 187205 remained alive with a freshly updated
`RUNNING/CURRENT` lease. RTX6000 briefly reported 0% utilization but still held
9,396 MiB, so the idle sample was not treated as ownership. Immutable EXP181
was requeued as `biohub-exp181-synthetic-gap-source-r2-20260911`; it remains
first in `WAITING_RESOURCE` with no GPU or PID assigned.

Useful CPU work updated the publication notebook to distinguish the leaked
public DeepCenter teacher from EXP180's explicit 10/2 source-only models and to
show EXP181 as pending rather than measured. The rebuilt 33-cell notebook is
valid JSON, 27,029 bytes, SHA
`987bcb183dca915b9234c0ae2441597aefb6e51d32d567f30c33dfe976a96be3`.
Its header still makes post-close private performance primary and retains
`RETRY_BEFORE_OPENING`; receipt:
`reports/notebook_snapshot_exp180_pending_exp181_20260911.json`.

The QRZ attribution audit also resolved an apparent hash mismatch. The source
receipt's `5fb5d5...` is SHA-256 of the canonical LF-joined notebook code,
while the extracted Windows file bytes use CRLF and hash to `19d64b...`;
decoded text normalized to LF is exactly identical. All 12 frozen gap/refine/
DeepCenter parameters match the archived source. Intentional deviations are
limited to the isolated mechanism, registered scratch parent and the two
leakage-controlled EXP180 checkpoints. Receipt:
`reports/exp181_qrz_attribution_audit_20260911.json`.

EXP181 retry 2 also remained unallocated through the 2/5/10-minute sequence.
At the final check, the same registered RSNA PID 187205 was alive at 9,396 MiB
and 100% GPU utilization. The r2 request had no GPU or PID and was cancelled;
no EXP181 process, movie access, partial result or Kaggle use occurred. The
runtime source stayed immutable. Receipt:
`reports/exp181_waiting_resource_r2_20260911.json`.

### EXP181 third blocked audit

At 2026-09-10T18:35:08Z the authoritative physical and queue checks again
found RTX6000 occupied by registered RSNA PID 187205: 9,396 MiB VRAM, 99%
utilization, process start tick 427776461, and lease
`rsna-s24-swin-20260910T1644Z` in `RUNNING/CURRENT` state with a fresh
heartbeat. This is the third consecutive goal turn with the same external
resource blocker. Both prior Biohub requests are terminal `CANCELLED`; there
is no active waiting request, assigned GPU, Biohub PID, data access, partial
output, or Kaggle use. GPU sharing and preemption remain prohibited, while
target OOF and Kaggle execution remain gated on the source-only EXP181 result.
The immutable staged run and two verified EXP180 best checkpoints are retained
as active dependencies. Work is therefore blocked until the RSNA process ends
and its lease is released, at which point a fresh request must be created and
the physical GPU state revalidated. Receipt:
`reports/exp181_rtx6000_blocked_audit_20260911.json` (SHA-256
`d958569ad18a0d971a04584178b5b89d9932338fde711eaf7ea71e045ec682d4`).

### EXP181 resumed retry 3

On resumption all three SSH identities again matched the documented hosts. The
RTX6000 had become physically idle (5 MiB, 0%, no compute process), and
registered RSNA PID 187205 no longer existed. Its common-queue lease remained
`RUNNING/UNKNOWN_STALE_STILL_RESERVED`, however, so it was not treated as
available and was not taken over. The RSNA owner task was asked to reconcile
its process tree, preserve results and release its own lease if verified
stopped. Immutable EXP181 remains ready under the same registered remote run;
a separate FIFO retry uses ID
`biohub-exp181-synthetic-gap-source-r3-20260911` and token
`exp181-r3-token-223702c4-99f4-4913-b493-b47f0d54fd60`. It may launch only on
a fresh `RESERVED/CURRENT` response plus a repeated physical GPU check.
Receipt: `reports/exp181_queue_retry_r3_20260911.json`.

EXP181 retry 3 received a fresh `RESERVED/CURRENT` RTX6000 allocation after
the RSNA owner verified its five-fold job complete and released its stale
lease. The immutable launch guard started PID 190419 (start tick 431333631),
but the worker terminated during Python import before opening source data or a
model checkpoint: the staged bundle omitted sibling module
`evaluate_coordinate_consensus.py`. The local tests had passed because the
full local `scripts/` directory was on `sys.path`, exposing a packaging-test
gap. No scientific result was produced and this is not a negative mechanism
result. The PID and child/GPU process absence were verified, RTX6000 was 5 MiB
at 0%, and the allocation was released. The traceback and launch receipt are
retained; no Kaggle slot was used. Any retry must be a separately
preregistered immutable bundle with all transitive local imports SHA-pinned
and a clean isolated remote import test before GPU allocation. Receipt:
`reports/exp181_source_packaging_failure_20260911.json`.

### EXP182 preregistered packaging repair

EXP182 changes no scientific code, parameters, source folds, parent, models or
promotion gate from EXP181. It repairs only the isolated run bundle by adding
and SHA-pinning all three transitive local imports:
`evaluate_coordinate_consensus.py`, `evaluate_observed_gap_close.py` and
`train_deepcenter_explicit_split.py`. Before any GPU request, the complete
remote bundle must match six recorded source hashes and both evaluator and
selector must pass `--help` from inside the isolated run directory using the
project interpreter. Only then may the same source-only gate request one
RTX6000. Opposite-embryo OOF and Kaggle remain unauthorized. Receipt:
`reports/exp182_synthetic_gap_source_preregistration_20260911.json`.

The complete EXP182 bundle was staged in its own registered run directory.
All seven preregistered files matched their local SHA-256 values; the launch
guard additionally hashes to `f11d0e...`. Using the project interpreter from
that isolated directory, both evaluator and selector `--help` checks exited
zero, proving the previously missing import chain is complete. Both EXP180
checkpoint hashes were reverified. EXP182 is therefore ready to request one
RTX6000 as `biohub-exp182-synthetic-gap-source-20260911`, token
`exp182-token-eac7819e-5cde-46f2-a911-d680ef1b2105`. Receipt:
`reports/exp182_prelaunch_and_queue_20260911.json`.

### EXP182 source result

EXP182 completed both source directions and passed every preregistered gate.
On `44b6`, DeepCenter-gated synthetic gaps improved registered Hungarian from
`0.594714` to `0.616462` (`+0.021748`) and exceeded no-veto by `+0.000667`;
on `6bba`, they improved `0.886626` to `0.894557` (`+0.007931`) and exceeded
no-veto by `+0.000853`. DeepCenter checked 534/122 candidate spans and the
gated arm added 2,766/785 synthetic nodes. All four movies had nonnegative
score and recall deltas. The local selector reproduced the gate semantically.
PID 191054 and all children ended, RTX6000 returned to 5 MiB/0%, and the lease
was released. Full JSON/log evidence and the launch receipt were copied and
SHA-recorded locally. Empty top-level logs and the exact duplicate gate log
were removed (1,644 bytes); active target-OOF dependencies remain pinned. This
authorizes one separately frozen reciprocal 24-movie target OOF, not Kaggle.
Receipt: `reports/exp182_synthetic_gap_source_result_20260911.json`.

### EXP183 reciprocal target OOF preregistration

Before opening any target movie, EXP183 freezes a single no-tuning reciprocal
evaluation: the `44b6` EXP180 model runs on all 12 `6bba` movies and the
`6bba` model runs on all 12 `44b6` movies, using the corresponding frozen
EXP152 target candidate caches. The two manifest hashes and 12+12 cache-file
coverage were recorded. Promotion requires strict DeepCenter-over-parent gain
in each embryo and pooled, exactly 24 movies, no negative score or node-recall
delta on any movie, model exercise and accepted synthetic nodes in each
embryo, and gated score no worse than no-veto in either embryo. Five focused
tests passed. A pass permits preparation of one hidden-compatible
PRIVATE_ROBUST runtime candidate, but does not itself authorize Kaggle.
Receipt: `reports/exp183_synthetic_gap_target_oof_preregistration_20260911.json`.

The staged EXP183 bundle matches all seven preregistered hashes; its launch
guard SHA is `eb6a65...`. Clean isolated evaluator/selector imports and shell
syntax passed. The guard additionally verifies both target manifest hashes,
both checkpoint hashes and exactly 12 NPZ caches per direction before launch.
The one-GPU request is `biohub-exp183-synthetic-gap-target-oof-20260911`,
token `exp183-token-3cce373e-7e1f-4d87-99eb-c1beb7c9b183`. Receipt:
`reports/exp183_prelaunch_and_queue_20260911.json`.

EXP183 received a fresh allocation and started PID 192371 (start tick
431465666), but stopped at target-manifest lookup before opening any target
movie or model checkpoint. The evaluator defaults to key
`source_checkpoint_validation`; both frozen all-12 manifests use
`target_development`, and the run script omitted an explicit `--movie-key`.
This is a config/interface failure, not target OOF evidence. Process absence
was verified and the lease released. The traceback and launch receipt remain
remote; no Kaggle slot was used. A new immutable retry must explicitly set the
target key and pass a prelaunch validator proving 12 manifest entries exactly
match 12 cache filenames per direction. Receipt:
`reports/exp183_target_manifest_key_failure_20260911.json`.

### EXP184 target OOF config-only retry

EXP184 preserves EXP183's scientific source and strict target gate, changing
only both invocations to pass `--movie-key target_development`. A new data-free
validator requires exactly 12 unique manifest names and exact equality with 12
cache stems per direction. Its accept, wrong-key reject and cache-mismatch
reject tests passed; the full focused suite passed 8/8 using a workspace-local
pytest basetemp, which was immediately removed. The earlier three errors were
solely an inaccessible global pytest temp directory and did not execute the
validator. Target movies remain unopened. Receipt:
`reports/exp184_synthetic_gap_target_oof_preregistration_20260911.json`.

The isolated remote EXP184 validators passed exact `target_development`
mapping for all 12 `6bba` and all 12 `44b6` cache stems. Eight bundle hashes,
both shell scripts, both manifests and both checkpoint guards passed. The
launch guard hashes to `37d4bf...`. EXP183's empty top-level log and 107,848
bytes of reproducible `__pycache__` were removed; its traceback and launch
receipt remain. EXP184 is ready under queue ID
`biohub-exp184-synthetic-gap-target-oof-20260911`, token
`exp184-token-a1a67515-d952-43cf-800d-9e67e55acfcd`. Receipt:
`reports/exp184_prelaunch_and_queue_20260911.json`.

### EXP184 user-requested pause

While EXP184 was running, the user requested an immediate temporary stop and
no further RTX6000 calculations. The forward `44b6 -> 6bba` target result had
already completed; reverse child PID 193283 was active under parent PID 192961.
Both owned processes received SIGTERM and were confirmed absent. RTX6000
returned to 5 MiB/0% with no compute process and the lease was released. The
forward score was not inspected for tuning or a decision. Its JSON, log and
launch receipt were copied locally and match their remote hashes; no reverse
JSON or target gate exists. Reproducible `__pycache__` (107,890 bytes) and two
empty logs were removed. No Kaggle work or slot was used. No new GPU work may
start until the user explicitly resumes; a future continuation must reuse the
frozen forward SHA, run reverse exactly once and apply the unchanged gate.
Receipt: `reports/exp184_user_paused_20260911.json`.

### EXP185 user-authorized target OOF continuation

The user explicitly resumed RTX6000 work. Live checks found no active Quadro
queue request, 5 MiB/0% on RTX6000 and no compute process. EXP185 is frozen
before reverse target access: copy the completed EXP184 forward JSON exactly
at SHA `1dfc9318...`, do not recompute or inspect it for tuning, run only the
missing `6bba -> 44b6` all-12 reverse direction once, then apply the unchanged
EXP183 target gate. Scientific code, parameters, manifests, models and
promotion criteria are unchanged. Kaggle remains unauthorized. Receipt:
`reports/exp185_synthetic_gap_target_oof_continuation_preregistration_20260911.json`.

EXP185 passed 8/8 focused tests and removed its workspace-local test temp.
Remote SHA verification passed for the complete bundle, preregistration and
byte-identical reused forward JSON (`1dfc9318...`). Reverse manifest/cache
mapping passed exactly 12 files, shell syntax passed, and no reverse/gate
output exists. The launch guard SHA is `00d175...`. Queue ID is
`biohub-exp185-synthetic-gap-target-oof-cont-20260911`, token
`exp185-token-f3267390-51af-465a-94d8-fc753b95156e`. Receipt:
`reports/exp185_prelaunch_and_queue_20260911.json`.

### EXP185 reciprocal target OOF result

EXP185 completed the missing reverse direction and applied the untouched
EXP183 gate to 24 opposite-embryo movies. Aggregate score improved from
`0.686231` to `0.699611` (`+0.013380`); both embryo directions improved
(`+0.002551` on `44b6 -> 6bba`, `+0.024208` on `6bba -> 44b6`), gated
DeepCenter exceeded no-veto in both, and node recall never decreased. However,
the candidate regressed score on 5/12 `6bba` movies and 3/12 `44b6` movies;
worst delta was `-0.014529`. The preregistered no-negative-movie gate therefore
failed. EXP185 is rejected for PRIVATE_ROBUST and no Kaggle run or POST is
authorized. The local selector reproduced the gate semantically. PID 200676
ended, RTX6000 returned to 5 MiB/0%, and the lease was released. Full unique
JSON/log evidence was copied locally and SHA-recorded; reproducible pyc, empty
top-level log and duplicate gate logs were removed. Future analysis of these
target labels is exploratory, not untouched confirmatory OOF. Receipt:
`reports/exp185_synthetic_gap_target_oof_result_20260911.json`.

### Publication notebook snapshot after EXP185

The human-facing private-first notebook now records the complete synthetic-gap
story rather than the stale EXP181 pending state. It reports EXP182's
`PASS_SOURCE_GATE`, EXP185's pooled `0.686231 -> 0.699611` gain, and the
decisive `REJECT_TARGET_OOF_GATE`: 8/24 movie regressions with worst delta
`-0.014529`. The header explicitly states that aggregate gain is not private
robustness, the post-close PRIVATE score is unobservable, and EXP185 authorizes
neither a Kaggle runtime run nor submission. The provenance table now carries
the same admission decision. The rebuilt 33-cell notebook parses as JSON and
contains no stale EXP181-pending claim. Snapshot receipt:
`reports/notebook_snapshot_exp185_target_reject_20260911.json`.

### Objective correction: pooled OOF first

The user replaced the prior private/LB/publication objective. The primary
research target is now the highest honest reproducible pooled OOF. Embryo
direction, per-movie stability, edge/adjusted-edge, node recall/count and
division metrics remain required diagnostics but no longer veto a positive
pooled local result. LB and publication are optional and cannot override the
submission-safety rules. A mechanism selected after target inspection must be
labelled exploratory; parameter tuning should use source-only or nested
selection rather than report an in-sample maximum as OOF.

Current Kaggle discussion evidence supports this distinction. One participant
reports approximately `0.96 CV` versus `0.93 LB`; another reports an edge
weight model gaining `+0.02–0.04` on each of five folds with approximately zero
LB gain. The same discussion recommends reporting score components. The
downloaded Yusuke fixed-8 notebook contributes a conservative length-five
short-track rescue mechanism, while the Evgen `PROXY_SCORE=0.9417` notebook
contributes cached post-processing and parameter ideas. Their absolute local
scores are not treated as comparable honest reciprocal OOF because the public
support weights may have seen the selected training movies.

### EXP186 nested pooled synthetic-gap sweep preregistration

EXP186 retains the successful EXP185 synthetic-gap family and freezes seven
physical variants over gap radius (`4.5`, `5.0`, `5.8` µm/step) and
DeepCenter threshold (`0.10`–`0.30`). Each direction uses its source-embryo
model on 12 opposite-embryo movies. For every held-out movie, the variant is
selected on the other 11 movies in that direction; only the 24 held-out rows
form the primary pooled score. The baseline `g50_t25` must exactly reproduce
EXP185. GPU heatmaps are cached once per model/movie/frame and reused across
the frozen grid. This is exploratory nested development OOF—not untouched
confirmation—because EXP185 motivated retaining the family. Any positive
nested pooled delta is valuable; negative movies are diagnostics, not a veto.
No Kaggle runtime or submission is authorized. Receipt:
`reports/exp186_nested_pooled_synthetic_gap_preregistration_20260911.json`.

### EXP187 nested short-track family preregistration

EXP187 freezes a physically distinct, CPU-only graph experiment before its
24 target rows are scored. It evaluates `no_filter` and minimum weak-component
lengths 2–6 on the frozen reciprocal EXP152 candidate caches, plus an
independent implementation of the public length-five rescue (`mean learned
probability >= 0.90`, `mean physical edge distance <= 2.75 µm`, and a
`min(0.6%, 60 nodes)` budget). For each held-out movie, an arm is selected only
on the other 11 movies in that direction; the 24 held-out selected rows form
the primary pooled score. The `no_filter` arm must reproduce every EXP152
registered-Hungarian metric within `1e-12`. This is exploratory nested OOF,
not untouched confirmation, and open-notebook proxy scores are not treated as
comparable evidence. Six focused tests and compilation passed. Any positive
nested pooled delta is retained; component and movie stability remain
diagnostics. No Kaggle action is authorized. Receipt:
`reports/exp187_nested_short_track_family_preregistration_20260911.json`.

### Public CV claims audit

Current discussion numbers are not directly comparable to our pooled OOF:
participants report roughly `0.96 CV / 0.93 LB`, public LB exceeding edge-CV
by `0.013–0.020`, and a learned edge-weight model improving five folds by
`0.02–0.04` while adding about zero LB. Split membership and training overlap
are not sufficiently specified, so these remain context only. A newly audited
open notebook gives a stronger validation design: denylist the four public-test
twins and group the other 195 volumes by embryo prefix. It reports a
parameter-free `0.483130` equal-weight CV versus `0.560` public LB (`+0.077`),
but explicitly says those figures came from private runs and omits the real
predictor/scorer, so the headline number is not reproducible from the notebook.
We retain its guard/split ideas, not its score. Our current 24-movie reciprocal
OOF is stricter about model-training embryo exclusion but narrower in coverage;
the remote root currently materializes official raw+GT for those 24, not all
195 non-twins. Receipt: `reports/public_cv_claims_audit_20260911.json`.

### EXP187 analysis-interface failure and EXP188 retry

Both frozen EXP187 directions completed, producing immutable forward SHA
`d68b656...` and reverse SHA `b401d68...`. The post-run control validator then
failed before nested selection because it requested a `score` key from
per-movie `per_sample_metrics` rows; those rows expose official components and
`adj_edge_jaccard`, while `score` exists only in summaries. No scientific
calculation failed and neither JSON needs recomputation. EXP188 is frozen as an
analysis-only retry: hash-check those two files, compare every available control
metrics to EXP152 at `1e-12`, then apply the unchanged nested selector. No GPU,
Kaggle runtime or submission is authorized. Receipt:
`reports/exp188_short_track_analysis_retry_preregistration_20260911.json`.

EXP188 hash-verified both immutable EXP187 result files, then stopped because
its validator still listed another summary-only key, `division_jaccard`.
EXP189 replaces the guessed metric list with exact row-key-set equality and a
dynamic comparison of every numeric per-movie field. Before preregistration,
the corrected validator was run against local copies of the same immutable
EXP187 inputs and EXP152 parents: both 12-movie directions matched with maximum
absolute error `0.0`. EXP189 will rerun only that validation and the unchanged
nested selector. Receipt:
`reports/exp189_short_track_analysis_retry_preregistration_20260911.json`.

### EXP186 corrected pooled result

EXP186 passed exact EXP185 baseline reproduction and nested selection. The
true 24-movie edge-mass pooled score is `0.676146 -> 0.683432`
(`+0.007286`); nested selection adds `+0.000919` over fixed `g50_t25`
(`0.682513`). Forward selected `g50_t30` for all 12 held-out movies; reverse
selected `g45_t20` ten times and `g50_t30` twice. Eight movies regressed, now
diagnostic rather than a veto. This exposes a historical naming error: EXP185's
reported pooled `0.686231` was the equal-weight mean of two direction summary
scores, not pooled aggregation over 24 movie edge masses. That historical row
is preserved, but the corrected baseline is `0.676146`. The GPU process ended,
the lease was released, all results were exported, and 1.4 GB of reproducible
heatmaps plus pycache/empty log were removed. Receipt:
`reports/exp186_nested_pooled_synthetic_gap_result_20260911.json`.

### EXP189 validated short-track result

The corrected dynamic validator matched every EXP187 no-filter per-movie field
to EXP152 with maximum error `0.0`. Nested embryo-direction-specific component
filtering raises true pooled OOF from `0.676146` to `0.740516`
(`+0.064370`), with node recall `0.95970 -> 0.93756` and only 2/24 negative
held-out movie deltas. Forward selected minimum component length 6 on every
held-out movie; reverse selected length 3 on every movie. The public rescue
triggered on 7/12 forward and 9/12 reverse movies but rescued zero components,
so its label merely won a lexical tie with plain `min6`; the scientific gain is
short-component pruning. This is the new local pooled frontier and remains
exploratory, not a Kaggle authorization. Receipt:
`reports/exp189_short_track_analysis_result_20260911.json`.

### EXP190 extended short-track length preregistration

Because EXP189's forward curve was still increasing at the frozen upper bound,
EXP190 freezes lengths `1,2,3,4,5,6,7,8,10,12,16,24` before rescoring. It uses
the same immutable reciprocal EXP152 caches and official metric, exact control,
and leave-one-movie-out arm selection. This is CPU-only and exploratory nested
OOF. Four focused tests and compilation passed; no Kaggle action is authorized.
Receipt: `reports/exp190_extended_short_track_lengths_preregistration_20260911.json`.

### EXP190 extended-length result and stability

EXP190 exact control again matched at error `0.0`. Extending the internal grid
raised the true nested pooled frontier from EXP189's `0.740516` to `0.743072`,
or `+0.066927` over no filtering. Forward leave-one-out selection chose `min8`
9 times and `min10` 3 times; reverse chose `min3` all 12 times, so neither
direction sits at the search boundary. Edge Jaccard is `0.736349`, node recall
is `0.916111`, and 3/24 movie deltas are negative. A 20,000-draw paired
bootstrap stratified by direction gives 95% interval `[0.032339, 0.096913]`
and `P(delta>0)=0.9999`; both directions gain (`+0.074327`, `+0.033530`) and
every leave-one-movie-out aggregate remains strongly positive (minimum
`+0.061277`). This is a stable exploratory result, not one-film domination.
Receipt: `reports/exp190_extended_short_track_lengths_result_20260911.json`.

### EXP191 synthetic-gap plus pruning composition preregistration

EXP191 tests whether the independent recall mechanism from EXP186 composes
with EXP190's precision mechanism. It freezes forward `g50_t30`, reverse
`g45_t20` and reverse `g50_t30`, writes exact selected-edge caches, and applies
component lengths `1,2,3,6,8,10,12`. Every cached no-filter graph must exactly
reproduce its source GPU metric before nested selection. Base, primary-gap and
g50-gap compositions are selected for each held-out movie only on the other 11
movies in that direction. Prior experiment-driven family selection is disclosed,
so this remains exploratory despite nested exclusion. One RTX6000 lease is
requested; no Kaggle action is authorized. Receipt:
`reports/exp191_gap_prune_composition_preregistration_20260911.json`.

### EXP191 exploratory composition result

All three exact selected-edge cache roundtrip controls matched their source GPU
evaluations with maximum absolute error `0.0`. Nested composition raises the
true 24-movie edge-mass pooled score from `0.676146` to a numerical frontier of
`0.744990` (`+0.068844`), with edge Jaccard `0.738444`, node recall `0.917637`,
and 4/24 negative movie deltas versus baseline. Forward reproduces EXP190's
base-only policy (`min8` 9 times, `min10` 3); reverse selects synthetic-gap plus
`min6` (`g45_t20` 9 times, `g50_t30` 3). Against baseline, a 20,000-draw paired
direction-stratified bootstrap gives 95% interval `[0.034088, 0.099023]` and
`P(delta>0)=0.9999`; every leave-one-movie-out aggregate remains positive.

The incremental evidence over EXP190 is weaker and must not be overstated:
observed pooled gain is only `+0.001918`, with bootstrap 95% interval
`[-0.000448, 0.004505]` and `P(delta>0)=0.94105`. Forward is unchanged; the
increment comes from reverse only. Thus EXP191 is the exploratory numerical
frontier, while EXP190 remains the simpler strongly supported reference until
an untouched embryo/movie set confirms the gap mechanism. The RTX6000 lease was
released after process verification. Results and scripts were preserved; 1.1 GB
of reproducible heatmaps, 11 MB of edge cache, pycache and an empty log were
removed from the registered remote root. No Kaggle action is authorized.
Receipt: `reports/exp191_gap_prune_composition_result_20260911.json`.

### EXP192 frozen honest-195 confirmation preregistration

The full live Kaggle inventory contains 24,477 train file records for 199 movies
and 85,703,559,720 bytes. After removing the four known public-test twins, the
honest reciprocal evaluation population is 195 movies / 83,797,184,170 bytes.
The verified official24 corpus already supplies 20 non-twin movies; the frozen
confirmation set is therefore all 175 previously unopened movies (59 `44b6`,
116 `6bba`, 75,045,173,746 bytes). A tested metadata-only builder produced the
exact missing-file manifest at SHA `ddf71e7f...a673add`.

Before downloading any of those 175 movies, EXP192 freezes two deployable
policies learned from the earlier 24-movie development work. EXP190 applies
base `min8` to 6bba targets and base `min3` to 44b6 targets. EXP191 is identical
on 6bba and applies `g45_t20 + min6` on 44b6. The primary score is pooled only
over the 175 unopened movies; the 195-movie aggregate is secondary/descriptive.
No intermediate score may alter any model or parameter. Promotion requires a
positive pooled delta, no target-prefix regression, and a direction-stratified
paired bootstrap 95% lower bound above zero; EXP191 must additionally beat
EXP190 on the unopened set. Data will be staged into the registered NSU root
with size/hash checks and immediate transport cleanup, then two reciprocal GPU
passes will use one queued RTX6000 lease. No Kaggle runtime or submission is
authorized. Receipt:
`reports/exp192_honest195_confirmation_preregistration_20260911.json`.

EXP192 preregistration correction, recorded before any EXP192 inference: the
base coordinate/candidate models are the frozen EXP152 scratch checkpoints
(`dc06a794...` for 44b6→6bba and `5c0f8358...` for 6bba→44b6), with detector
threshold `0.985`, candidate edge threshold `0.02`, and registered motion-only
Hungarian links reconstructed from coordinates. EXP180 DeepCenter is not the
base model; its reverse checkpoint `ea0b53cb...` is used only as the frozen
synthetic-gap gate for EXP191 on 44b6 targets. EXP190 remains base `min8/min3`;
EXP191 is base `min8` on 6bba and `g45_t20 + min6` on 44b6. Cohort, metrics,
anti-adaptation rule and promotion gates are unchanged. Receipt:
`reports/exp192_model_stack_correction_20260911.json`.

EXP192 execution-plan correction, also before inference: the 175-film pass is
split lexicographically into eight immutable chunks of at most 24 movies (five
6bba-target and three 44b6-target chunks). Each ready chunk gets its own
RTX6000 lease/run directory and releases the device after verified exit before
the project rejoins the queue. This improves interruption recovery and matches
the shared-resource preference for bounded chunks; it changes no scientific
choice. Chunk metrics and scientific logs remain unopened until all eight are
complete and merged. Receipt:
`reports/exp192_chunked_execution_correction_20260911.json`.

Before EXP192 inference, a no-metric structural validator was added to every
chunk. It checks the frozen movie membership, expected arm sets, row-schema
consistency, finite numeric values, completion statuses and SHA-256 hashes, but
emits no score or component metric. Local tests report 6 passed; local and
remote shell/import checks passed and all three deployed source hashes match.
This is an operational safeguard only and changes no model, parameter, cohort,
metric or promotion gate. Test caches and EXP192-owned bytecode were removed;
the active dataset download was preserved. Receipt:
`reports/exp192_no_metric_chunk_validator_receipt_20260911.json`.

### Updated public-CV context for the pooled-OOF objective

A current discussion supplies a directionally useful but non-comparable claim:
one participant reports about `0.919 CV` and `0.895 LB` for an edge algorithm,
while the first-place participant recommends complete-movie official scoring,
movie-level OOF, and separating missing endpoint nodes from association errors.
Other threads report an approximately `0.590` physical LoG/LAP local baseline,
warn that sub-`0.001` public changes and sparse division events are readily
overfit, and suggest count calibration or longer-window learned association.
None exposes enough split, overlap, pooling, metric-version and code detail to
be a numerical target. EXP192's 175 untouched full-movie official pooled score
therefore remains authoritative; the discussion ideas become only post-EXP192
mechanism candidates. Receipt: `reports/public_cv_claims_update_20260911.json`.

The live official competition archive downloaded with exit code 0 but is not
byte-identical to the September 9 receipt: `87,393,127,165` bytes and SHA-256
`538ed8a4...dfd19`, versus the prior `87,402,594,304` bytes. This was caught
before transfer, extraction or inference. A tested ZIP-catalog validator then
confirmed all `21,525` frozen EXP192 manifest paths / `75,045,173,746` bytes
are present with exact uncompressed sizes among 24,886 archive members (zero
missing and zero mismatched). The remote staging wrapper is corrected to the
current exact size and now repeats that catalog audit; selective extraction
will still verify CRC and the final audit will hash all 175 content trees.
Model, cohort, policy and promotion gates are unchanged. Receipt:
`reports/exp192_current_archive_correction_20260911.json`.

The eight queue identities and unique owner tokens are frozen before data
readiness in `reports/exp192_gpu_queue_plan_20260911.json`. Every request uses
the Quadro pool, one GPU, 8 CPUs, 32 GiB RAM, 5 GiB expected run growth and a
120-minute allocation. Requests remain blocked until the full data audit
passes; only one project chunk may hold a lease, retries reuse the exact same
ID/token/parameters, and release requires PID/descendant/GPU verification.

### EXP192 input-covariate coverage audit

An input-only aggregate audit compared the 20 non-twin development movies with
the 175 untouched confirmation movies before any target inference. All 195
images have shape `100x64x256x256`. Within embryo prefix, standardized shifts
for log compressed bytes and six recorded intensity quantiles are small: the
largest absolute value is `0.26777` (44b6 lower-tail `q0.01`); log-byte shifts
are `0.13818` for 44b6 and `0.08118` for 6bba. This argues against a gross
covariate mismatch, while the wider confirmation tails reinforce why 20-film
development results cannot substitute for EXP192. No graph, label metric,
score or per-movie result was read, and no frozen choice changes. Two tests
passed; test cache and owned bytecode were removed. Receipt:
`reports/exp192_input_covariate_audit_20260911.json`.

EXP192 queue-plan hash correction, before any request or inference: seven of
the eight movie-list SHA values in the newly written queue-plan receipt were
mistyped by expanding abbreviated summary strings manually. The authoritative
`chunk_index.json`, local chunk files and previously deployed remote
`movies.json` files remain intact. The corrected receipt records all eight full
SHA values copied from `chunk_index.json`; every launch must additionally hash
the remote file. Queue IDs/tokens/resources and all scientific choices are
unchanged. Receipt:
`reports/exp192_gpu_queue_plan_hash_correction_20260911.json`.

An all-chunk no-metric gate is now deployed before inference. It requires all
eight immutable run directories, exact local/remote movie-list hashes,
`116/59/175` unique directional/combined coverage, and a passing per-chunk
schema/finiteness validator before aggregation. Its output contains only
status, counts and hashes—not scientific values. Four tests, compilation,
diff-check, remote SHA and remote import pass. Receipt:
`reports/exp192_all_chunk_gate_receipt_20260911.json`.

A separate atomic data-readiness gate is deployed before extraction completes.
It can create `data_ready.json` for all eight runs only after exact audit
status/counts, 175 content hashes, every remote movie-list SHA and absence of
prior launch/output receipts are verified. It records current run, launcher
and chunk-validator hashes and refuses overwrite. One focused test,
compilation, diff-check, remote SHA and remote import pass. Receipt:
`reports/exp192_data_ready_gate_receipt_20260911.json`.

### EXP193 mechanism-diversity audit preregistration

EXP193 freezes a CPU-only analysis of already-opened 24-movie development OOF
while EXP192 data transfer continues. It compares movie-level adjusted-edge
deltas for external fixed-coordinate edges (EXP154), fixed and nested
synthetic gaps (EXP185/186), nested short-component pruning (EXP190), and the
gap+pruning composition (EXP191). All registered baselines must match at
`1e-12`. Pairwise Pearson/Spearman correlations, sign disagreement and
directional diagnostics may nominate a future graph-level composition, but
score-vector averaging is explicitly not evidence of an ensemble. This is
exploratory and cannot alter EXP192. Receipt:
`reports/exp193_mechanism_diversity_preregistration_20260911.json`.

### EXP193 mechanism-diversity result

All five mechanisms reproduce the common registered baseline with maximum
absolute error `0.0`. Fixed and nested synthetic gaps are nearly identical
error families (Pearson `0.9924`, Spearman `0.9678`). In contrast, nested gap
and short-component pruning have Pearson `-0.1461`, Spearman `-0.2374`, and 11
of 24 sign disagreements: recall repair and precision pruning are genuinely
complementary, although EXP191 showed that their unconditional graph-level
composition is still dominated by pruning and only weakly incremental.
External fixed-coordinate edges are also decorrelated from pruning (Pearson
`0.1430`, Spearman `0.0396`) but retain only a tiny pooled gain and previously
created 41 false forks. The next defensible post-EXP192 hypothesis is therefore
an embryo-aware nested gate between pruning-only and gap+pruning using only
inference-observable telemetry; external edges remain a one-to-one resolver
research lead, not a current ensemble arm. Score-vector averaging remains
forbidden as evidence. Two tests pass. Receipt:
`reports/exp193_mechanism_diversity_result_20260911.json`.

### EXP194 nested inference-time gate preregistration

EXP194 freezes the next CPU-only graph-choice experiment before gate scoring.
For each target direction it chooses between one complete pruning-only graph
and one complete gap+pruning graph using four inference-observable ratios:
synthetic additions, DeepCenter acceptance, selected gap endpoints and base
pruned-node fraction. For each held-out movie, q25/q50/q75 thresholds and the
rule are fitted only on the other 11 movies; candidates are two orientations
per threshold plus always-base/always-gap, with ties preferring always-base.
No score vectors are averaged. Retention requires positive pooled gain over
fixed EXP190, nonnegative gain in both directions and a positive lower 95%
direction-stratified paired-bootstrap bound. This remains sequentially
exploratory and cannot alter EXP192. Receipt:
`reports/exp194_nested_inference_gate_preregistration_20260911.json`.

### EXP194 nested inference-time gate result

EXP194 exactly reproduced all registered controls. The fixed deployable
`min8/min3` reference scores `0.748518`; the nested gate scores `0.749935`
(`+0.001417`) with node recall `+0.000784`. Forward selected base for all 12
held-out movies and is unchanged; reverse selected gap for 7/12 and gains
`+0.007570`. The 20,000-draw stratified paired bootstrap is not confirmatory:
95% interval `[-0.000946, 0.004072]`, `P(delta>0)=0.87025`, despite every
leave-one-movie-out aggregate remaining positive (minimum `+0.000621`). The
preregistered stability gate therefore fails. The unstable multi-rule selector
is rejected; its dominant reverse rule (`base_pruned_node_fraction <= train
q75`, selected in 9/12 folds) remains one simplified follow-up hypothesis.
EXP192 is unchanged. Receipt:
`reports/exp194_nested_inference_gate_result_20260911.json`.

### EXP195 simplified reverse gate preregistration

EXP195 is the single permitted simplification motivated by EXP194. Forward is
always frozen EXP190 `min8`. In reverse, each held-out movie uses the q75 of
`base_pruned_node_fraction` computed on the other 11 reverse movies and chooses
frozen `g45_t20+min6` only when its inference-time fraction is at or below that
threshold; otherwise it uses base `min3`. There is no per-fold feature, rule or
orientation selection. Retention requires a positive pooled delta, nonnegative
forward, positive reverse and bootstrap lower 95% bound above zero. It remains
sequentially exploratory and cannot alter EXP192. Receipt:
`reports/exp195_fixed_reverse_gate_preregistration_20260911.json`.

### EXP195 simplified reverse gate result

EXP195 passes the preregistered exploratory stability gate. Against the fixed
deployable `min8/min3` reference (`0.748518`), the nested single-rule gate
scores `0.751199` (`+0.002681`), raises node recall by `+0.003533`, leaves
forward unchanged, and gains `+0.014321` in reverse by choosing gap on 8/12
held-out movies. The 20,000-draw stratified paired bootstrap 95% interval is
`[0.000328, 0.005173]`, `P(delta>0)=0.9882`; every leave-one-movie-out
aggregate remains positive (minimum `+0.001891`). This is the new supported
exploratory deployable-policy frontier on the 24 development movies, not an
untouched result because EXP194 motivated the rule. It must be frozen on all
12 reverse development features before EXP192 target metrics are opened and
then confirmed independently. Receipt:
`reports/exp195_fixed_reverse_gate_result_20260911.json`.

### EXP195 deployable threshold and EXP192 confirmation amendment

Before any EXP192 inference, the EXP195 reverse rule was fitted once on all 12
previously opened reverse-development features. Its exact threshold is
`base_pruned_node_fraction <= 0.08388494131521039`; true chooses frozen
`g45_t20+min6`, false chooses base `min3`. Forward is always base `min8`.
Policy SHA is `23c9d355...e439`. This adds a third fixed policy to the untouched
175-movie confirmation using outputs already required for EXP190/191; it adds
no GPU computation and changes no original policy. Confirmation against EXP190
requires exact forward identity, positive reverse and pooled deltas, and a
paired-bootstrap lower 95% bound above zero. Target feature distributions and
metrics cannot alter the rule. Receipt:
`reports/exp195_exp192_confirmation_amendment_20260911.json`.

The frozen EXP195 confirmation builder is deployed before target inference.
It requires exact policy SHA, 116/59 unique coverage, 1e-12 registered control,
unique telemetry across the three reverse chunks and whole-graph selection.
Four focused tests, compilation, diff-check, remote SHA and remote import pass.
It may run only after the eight-chunk no-metric gate and immutable merge.
Receipt: `reports/exp195_confirmation_builder_receipt_20260911.json`.

The complete EXP192 postprocessing path now passes a synthetic end-to-end test
at the exact production chunk counts (`24/24/24/24/20` and `24/24/11`). The
test covers per-chunk and all-chunk no-metric gates, three immutable merges,
EXP190/191 frozen assembly and EXP195's exact-policy-SHA telemetry assembly,
ending with exactly 175 rows for every policy. Synthetic files, pytest temp and
owned bytecode were removed. Receipt:
`reports/exp192_postprocessing_integration_test_20260911.json`.

A read-only runtime feasibility audit used preserved remote log mtimes without
opening metrics. Earlier 12-movie full reciprocal inference took approximately
5.9 minutes forward and 7.7 minutes reverse; cached 12-movie gap/filter stages
took roughly 1.7–2.8 minutes each. Even with conservative scaling, the frozen
24-movie chunks fit comfortably within their 120-minute queue declarations.
The eight-chunk plan remains unchanged. Receipt:
`reports/exp192_chunk_runtime_feasibility_20260911.json`.

The slow archive path was tested without interrupting its concrete SCP handle.
A 57.3 MB probe through `nsu-a100` to the same NFS took 17.6 s and was slower;
an AES128 Quadro probe under concurrent transfer was slower again. There is no
evidence supporting a restart, so the original transfer remains authoritative.
Both exact probe files were verified and deleted immediately; the active
archive was preserved. Receipt:
`reports/exp192_transfer_route_probe_cleanup_20260911.json`.

### Public-CV mechanism update while EXP192 remains frozen

Current public discussions reinforce, but do not numerically calibrate, the
pooled-OOF program. A third-place participant recommends improving detection
before linking and divisions; the first-place participant independently
recommends complete-movie official scoring, movie-level OOF and splitting edge
errors into missing endpoints versus wrong associations. Other participants
report large movie-to-movie variability, crowded-frame division failures and
possibly interpolated or erroneous very-dim labels. A public classical
baseline identifies count calibration, physical-distance NMS/linking and
isolated-node pruning as useful mechanisms. None of these claims supplies a
split-and-scorer-compatible reproducible score, so EXP192 and its frozen
policies are unchanged. The post-confirmation decision rule is now explicit:
attribute pooled endpoint versus association error first, then select one
mechanism matching the dominant error instead of tuning another correlated
graph threshold. Receipt:
`reports/public_cv_claims_update2_20260911.json`.

### EXP196 official-match edge-failure attribution preregistration

Before any EXP192 metric is opened, EXP196 freezes a diagnostic of the final
175-movie selected policy and its two complete-graph controls. It lets the
official evaluator perform the exact 7-um matching, then partitions every GT
edge FN into missing-endpoint versus both-endpoints-matched/link-missing mass;
valid predicted non-TP edges are separately split into both-matched wrong
associations and one-sided sparse-GT anchors. Every per-movie partition must
sum exactly to the official TP/FP/FN counts. No threshold or arm is selected by
this diagnostic. Endpoint-dominated evidence routes the next experiment to
detection/count calibration; association-dominated evidence routes it to a
physically distinct or learned linker. Two pure unit tests and compilation
pass; the deployed remote source SHA matches and imports in the existing
environment. The analysis remains blocked by the all-eight-chunk no-metric
gate. Receipt:
`reports/exp196_edge_failure_attribution_preregistration_20260911.json`.

### Open detector notebook audit

The current public `hengck23/cell-point-detector` source was downloaded and
hashed rather than accepted from its headline. It is a genuinely different
three-level 3D U-Net detector using XY-by-four downsampling, local-max peaks and
a separately attached checkpoint. However, the downloaded notebook has zero
executed code cells, contains neither training code nor the checkpoint, and
validates only one fixed `6bba` movie with a custom node-recall diagnostic—not
reciprocal embryo-disjoint official pooled tracking OOF. The related discussion
claim of approximately `0.964` edge recall conditional on nodes is therefore
not reproduced. This remains a useful detector/pretraining lead only if EXP196
shows endpoint-limited errors dominate; it is not an ensemble arm. Receipt:
`reports/open_detector_notebook_audit_20260911.json`.

### EXP197 constant-velocity linker preregistration

EXP196's already-open development controls attribute `42.61%` of pooled edge
FNs to missing links despite both GT endpoints being officially matched. EXP197
therefore freezes a CPU-only, cache-only physical linker test before scoring:
two-pass Hungarian assignment blends registered global median drift with each
source's predecessor-derived constant velocity at alphas
`0/.25/.50/.75/1`. Forward keeps EXP190 `min8`; reverse keeps `min3`.
Alpha zero must reproduce EXP190 within `1e-12`. Each held-out movie's alpha is
chosen only from the other 11 movies in its direction, with ties preferring
zero. Retention requires positive nested pooled delta, nonnegative delta in
both directions and a positive lower 95% bound from 20,000 direction-stratified
paired bootstrap draws. Two focused tests and compilation pass. EXP192 remains
unchanged. Receipt:
`reports/exp197_constant_velocity_linker_preregistration_20260911.json`.

### EXP196 development attribution result

On the already-open EXP190 development control, endpoint-limited errors are a
pooled plurality: `1374/2394 = 57.39%` of edge FNs versus `1020/2394 = 42.61%`
with both endpoints matched but the link absent. Forward is `58.98%` endpoint
limited; reverse is nearly balanced at `50.12%`. The 20,000-draw stratified
movie bootstrap interval for endpoint share is `[0.4835, 0.6597]`, so this is
not stable evidence that detection is the sole bottleneck. Only one valid FP
across both directions has both endpoints matched to an incorrect GT pair;
most FPs are one-sided sparse-GT anchors. The defensible routing is parallel
detector/count-calibration and conservative-linker research, with no aggressive
relinking. The untouched 175-movie attribution remains pending. Receipt:
`reports/exp196_development_attribution_result_20260911.json`.

### EXP197 constant-velocity linker result

Alpha zero exactly reproduces EXP190 pooled score `0.7485183131`. On the
full-development diagnostic, alpha `.25` appears slightly positive in both
directions (`+0.000158` forward, `+0.002376` reverse), but the preregistered
nested estimate decisively rejects it: score `0.7450977420`, delta
`-0.0034205710`, both directions negative, 8 negative movies, and bootstrap
95% interval `[-0.006552, -0.000453]`. Every leave-one-movie-out aggregate is
negative. Larger velocity weights are strongly harmful. A packaging omission
stopped only the first selector invocation after both directional result files
were complete; SHA-matching dependencies were added and selection/stability
rerun without repeating scoring. Constant velocity is rejected and is not
added post hoc to EXP192. Receipt:
`reports/exp197_constant_velocity_linker_result_20260911.json`.

EXP196-development and EXP197 remote output copies were removed only after all
result hashes matched the downloaded local artifacts; exact-path absence was
verified. Owned local test bytecode was also removed. The active EXP192 archive
transfer, immutable run directories, code and dependencies were preserved.
Cleanup receipt: `reports/exp196_exp197_cleanup_20260911.json`.

### EXP198 parameter-free count-calibrated graph preregistration

EXP198 freezes a CPU-only rule inspired by the audited public classical
baseline and EXP196 endpoint attribution. For each movie it chooses one whole
EXP190 component-length graph solely by minimizing the absolute mismatch
between predicted nodes and the provided coarse `estimated_number_of_nodes`.
All twelve already evaluated lengths are eligible; exact ties prefer the
registered EXP190 parent (`min8` forward, `min3` reverse). Scores do not enter
selection. Retention requires positive pooled delta, nonnegative deltas in both
directions and a positive lower 95% direction-stratified paired-bootstrap
bound. Two focused tests and compilation pass. A failure rejects exact count
matching, not future learned/uncertainty-aware count calibration. EXP192 is
unchanged. Receipt:
`reports/exp198_count_calibrated_graph_preregistration_20260911.json`.

EXP198 selection completed, but stability stopped on a result-key mismatch:
the frozen analyzer requires `selected_rows`, while the new selector emitted
the same rows as `nested_selected_rows`. Before rerunning postprocessing, only
that compatibility key was renamed; policy, choices, metrics, candidate set
and inputs are unchanged. Two tests pass with the corrected source. Receipt:
`reports/exp198_postselection_schema_correction_20260911.json`.

### EXP198 count-calibrated graph result

The corrected deterministic rerun reproduces the original selection values and
decisively rejects exact count matching. The candidate pooled score is
`0.7067272292` versus EXP190 `0.7485183131`, delta `-0.0417910838`.
Direction deltas are both negative (`-0.044687` forward, `-0.029237`
reverse). The preregistered 20,000-draw direction-stratified paired bootstrap
interval is `[-0.065251, -0.015555]` with probability of positive delta
`0.0008`; all leave-one-movie-out deltas remain negative. Selecting a complete
graph merely because its predicted count is closest to the supplied coarse
estimate raises edge false positives and loses true edges, so count agreement
is not a sufficient proxy for graph quality. This does not reject learned
detection or uncertainty-aware count calibration. EXP192/EXP195 remain
unchanged and EXP198 is not submission-eligible. Receipt:
`reports/exp198_count_calibrated_graph_result_20260911.json`.

### EXP199 coherent frame-motion linker preregistration

EXP199 freezes a physically distinct CPU-only linker test on the existing 24
reciprocal embryo-disjoint coordinate caches. The parent is reproduced by the
exact registered-translation implementation. Four candidates weakly blend that
prediction (`alpha=.25/.50`) toward either a robust proper-rigid transform or a
guarded similarity transform whose frame scale is clipped to `[.97, 1.03]`.
Transforms use only inference-time coordinates: initial median translation,
mutual-nearest pairs within `4 um`, SVD fit and one MAD-trimmed refit. Frozen
detections, the `7 um` Hungarian gate, motion scale and EXP190 component
lengths (`8` forward, `3` reverse) remain unchanged. Each held-out movie's arm
is chosen from the other 11 movies in its direction. Promotion requires exact
parent reproduction, positive nested pooled delta, nonnegative directional
deltas and a positive lower 95% paired-bootstrap bound. Failure rejects these
global transforms, not local flow. EXP192 remains unchanged. Receipt:
`reports/exp199_coherent_motion_linker_preregistration_20260911.json`.

The first EXP199 invocation stopped at the evaluator's top-level import before
argument parsing, data access or scoring because the isolated run directory
omitted the existing `evaluate_coordinate_consensus.py` dependency. Before any
retry, the failure and dependency-only correction were recorded. The exact
verified dependency SHA is `426b4ee3...865fad2`; no policy, arm, parameter,
selector or promotion gate changes. Receipt:
`reports/exp199_prescore_dependency_failure_20260911.json`.

The dependency-only retry also stopped before movie-list/cache/label access:
`filter_family` was imported inside `main`, and its module was absent. A static
transitive-import review additionally found the shared summarizer required by
both frozen postprocessors. Before retry R2, only
`evaluate_cached_short_track_family.py` (`a9156bbb...c5bbba3`) and
`select_nested_pooled_synthetic_gap.py` (`0c9bdc68...9afcac`) were authorized
for packaging; experiment logic and all gates remain unchanged. Receipt:
`reports/exp199_prescore_dependency_failure_r2_20260911.json`.

### EXP199 coherent frame-motion linker result

The translation arm exactly reproduces EXP190 (`0.7485183131`). Although the
weak similarity arm has a small forward full-data diagnostic gain, the frozen
nested protocol rejects the family: selected pooled score `0.7468690072`,
delta `-0.0016493058`, with both directions negative (`-0.001337` forward,
`-0.002983` reverse). The 20,000-draw paired bootstrap interval is
`[-0.003960, +0.000967]`, probability positive `0.111`; every one of the 24
leave-one-movie-out aggregate deltas is negative. Global coherent
rotation/scale therefore does not robustly improve registered translation.
Local nonrigid flow remains untested. Remote and downloaded result SHAs match;
EXP192/EXP195 are unchanged. Receipt:
`reports/exp199_coherent_motion_linker_result_20260911.json`.

After all five substantive remote result hashes matched their local copies and
the worker had exited, the exact 1,865,900-byte EXP199 remote run directory was
removed and absence verified. Two generated local bytecode files were removed;
source, tests, receipts, logs and all result JSONs remain. The active EXP192
archive transfer and its dependencies were untouched. Cleanup receipt:
`reports/exp199_cleanup_20260911.json`.

### EXP200 bounded local-flow linker preregistration

EXP200 keeps EXP190 detections and component lengths fixed but replaces global
coherent motion with a local, inference-only residual field. After the exact
registered median shift, mutual-nearest pairs within `4 um` provide residual
vectors; each source receives the coordinatewise median from its 16 or 32
nearest paired sources, clipped to `2 um` and blended at `.25` or `.50`. The
translation arm is an exact parent control, and Hungarian gate/motion scale
remain `7/3 um`. Four flow arms are selected by leave-one-movie-out within each
direction. Promotion requires exact control, positive nested pooled delta,
nonnegative deltas in both directions and a positive 20,000-draw paired
bootstrap lower bound. Failure rejects this pseudo-flow family, not learned
optical flow. EXP192 is unchanged. Receipt:
`reports/exp200_local_flow_linker_preregistration_20260911.json`.

### EXP200 bounded local-flow linker result

Local residual flow is positive but misses the strict stability gate. Nested
pooled score rises from `0.7485183131` to `0.7498093390` (`+0.0012910259`);
forward is `+0.001590` and reverse is effectively flat but positive. Every
leave-one-movie-out aggregate remains positive, yet the 20,000-draw paired
bootstrap interval is `[-0.001196, +0.004009]` (`P(delta>0)=0.83545`). Thus
EXP200 is not a supported development frontier. The simplest direction-fixed
diagnostic—`k32,a=.50` forward and `k16,a=.25` reverse—scores `0.7510028014`
(`+0.0024844883`), but was chosen after viewing these 24 movies and is not
confirmatory. It may only be frozen now and tested once on the untouched 175
movies as EXP201. Remote/local result hashes match. Receipt:
`reports/exp200_local_flow_linker_result_20260911.json`.

### EXP201 untouched local-flow confirmation preregistration

Before the EXP192 archive is staged or any of its 175 target movies are
inferred, one simple EXP200 follow-up is frozen for the same untouched cohort.
Forward uses local residual flow `k=32, alpha=.50` followed by `min8`; reverse
uses `k=16, alpha=.25` followed by `min3`. Radius `4 um`, correction clip
`2 um`, Hungarian gate `7 um` and motion scale `3 um` are fixed. Each chunk
will emit only this arm and its exact translation control as `local_flow.json`;
scientific values remain hidden until all eight chunk structures pass. The
175-movie gate requires positive pooled delta, nonnegative deltas in both
prefixes, positive paired-bootstrap lower bound and positive minimum
leave-one-movie-out aggregate delta. Nine focused/integration tests pass with a
workspace basetemp; compilation passes. EXP190/191/195 remain unchanged.
Receipt:
`reports/exp201_local_flow_untouched_confirmation_preregistration_20260911.json`.

EXP201 integration passed before any untouched inference. All eight remote
chunks were verified unlaunched, then their `run.json` files were replaced by
locally matching manifests containing the amended launcher/run hashes. The
remote code matches local SHA, both shell scripts pass `bash -n`, imports pass,
and the synthetic no-metric/merge/frozen-policy pipeline includes EXP201. Test
batches passed `9/9` and `7/7`. `data_ready.json` will now record all local-flow
dependencies. EXP190/191/195 semantics are unchanged. Temporary pytest trees,
generated bytecode, the 145,211-byte remote code cache and the verified
2,330,167-byte EXP200 run were removed; preserved results and active transfer
remain. Receipts:
`reports/exp201_exp192_integration_receipt_20260911.json` and
`reports/exp200_cleanup_20260911.json`.

### EXP202 frozen direction-specific composition preregistration

Before untouched inference, EXP202 freezes a zero-extra-inference composition:
EXP201 `flow_k32_a050_min8` for 6bba-target movies and the exact EXP195 q75
base-vs-gap gate for 44b6-target movies. On the sequentially explored 24 movies
this would score `0.7531233749`, `+0.0019241302` over EXP195, but that is only
a hypothesis source. The builder requires EXP201's translation control to
match EXP195 forward `min8` at every numeric field, changes no reverse row, and
runs only after the all-eight no-metric gate. Promotion on 175 untouched movies
requires positive incremental pooled and forward deltas versus EXP195, exact
zero reverse difference, positive paired-bootstrap lower bound and positive
minimum leave-one-movie-out incremental delta. Seven tests and compilation
pass. Receipt:
`reports/exp202_composed_untouched_confirmation_preregistration_20260911.json`.

EXP202's builder is deployed before target inference with matching SHA and a
passing remote import. Its synthetic composition test and updated full EXP192
integration test pass (`7/7` batch), including exact forward-parent control.
Generated local/remote bytecode and pytest basetemp were removed after audit;
the active builder and archive transfer remain. Receipt:
`reports/exp202_exp192_integration_receipt_20260911.json`.

The frozen postprocessing path is now a single fail-closed orchestrator. It
checks all source/policy SHAs, requires a fresh atomic lock/output path, runs
the eight-chunk no-metric gate before any merge, then assembles EXP190/191/195/
201/202 and their paired bootstrap/LOMO comparisons. EXP202 is compared
incrementally with EXP195. Results and logs are hashed before one atomic final
rename. Remote SHA and `bash -n` pass; all pinned dependency SHAs match and the
contract/integration batch passes `5/5`. Test temp/bytecode were removed.
Receipt: `reports/exp192_frozen_postprocess_orchestrator_receipt_20260911.json`.

### EXP203 local-flow mechanism attribution preregistration

EXP203 is a diagnostic, not another selector. For the already frozen EXP201
arms (`k32,a=.50` forward; `k16,a=.25` reverse), it will report pooled and
directional TP/FP/FN changes, movie wins/losses, and correlations of score
delta with EXP196's association-FN share and inference-only flow telemetry.
Coverage and EXP196 FN partitions are asserted exactly. No resulting feature
may define a new gate or alter EXP192/201/202. One focused test and compilation
pass. Receipt:
`reports/exp203_local_flow_mechanism_attribution_preregistration_20260911.json`.

### EXP203 local-flow mechanism attribution result

The frozen flow policy changes pooled edge sufficient statistics by `+22 TP`,
`-26 FP`, `-22 FN`. Forward wins 8/12 movies and gains `+0.002369`; reverse
wins 9, ties 1 and loses 2, gaining `+0.002975`. Improvement is not positively
associated with EXP196 association-FN share (Pearson `-0.114/-0.241`), while
flow correction magnitude is more predictive (`0.446/0.732`) and mutual-pair
support especially matters forward (`0.656`). These correlations are post-hoc
and cannot define a gate. Crucially, the largest gain in each direction is a
public twin (`6bba_05db0fb1`, `44b6_0b24845f`), strengthening the need for the
already frozen non-twin EXP201/202 confirmation. Receipt:
`reports/exp203_local_flow_mechanism_attribution_result_20260911.json`.

### EXP204 non-twin policy sensitivity protocol

EXP204 freezes a scripted recomputation of the already fixed EXP190/195/201/202
development policies after removing exactly the four known public twins. The
aggregate non-twin scores were manually inspected before this protocol was
written, so this is explicitly post-hoc sensitivity analysis rather than a
preregistered confirmation. The script requires exactly ten remaining movies
per direction and exact reproduction of the EXP201 forward translation parent.
Its result cannot change EXP192/201/202 or replace the frozen 175-movie test.
One focused test and compilation pass. Protocol receipt:
`reports/exp204_non_twin_policy_sensitivity_protocol_20260911.json`.

### EXP204 non-twin policy sensitivity result

After excluding all four public twins, the fixed EXP190 score on 20 movies is
`0.7438710730`; EXP201 local flow scores `0.7449905954` (`+0.0011195224`).
The fixed EXP195 reverse gate scores `0.7471471452` (`+0.0032760722` versus
EXP190), and EXP202 scores `0.7477351873` (`+0.0005880421` versus EXP195).
Local flow remains positive separately in both directions (`+0.000745776`
forward, `+0.002502813` reverse), but the pooled/composed gains shrink
materially relative to the full 24-movie diagnostic. This supports mechanism
plausibility but is post-hoc and cannot establish transferability. EXP192/201/
202 stay frozen; the untouched 175-movie confirmation remains decisive.
Receipt: `reports/exp204_non_twin_policy_sensitivity_result_20260911.json`.

EXP204's owned pytest and bytecode temporary trees were removed after the test,
compile and result hashes were recorded. Source, test, result and receipts were
preserved; the active EXP192 transfer and frozen dependencies were untouched.
Cleanup receipt: `reports/exp204_cleanup_20260911.json`.

### Open classical-baseline mechanism audit

The current `xiaoleilian/biohub-cell-tracking-classical-baseline` source was
archived with notebook SHA `ef193c8c...87e088` and metadata SHA
`ebe4678a...f60439`. Its validation is a custom proxy/Traccuracy check on at
most one automatically selected movie per embryo, not official pooled
embryo-disjoint OOF. Most mechanisms map to completed evidence: isolated-node
pruning is part of the positive EXP187-190 family, predecessor velocity is
closely related to rejected EXP197, and exact count-driven selection was
rejected by EXP198. The genuinely useful unisolated lead is full-resolution
intensity-weighted centroid refinement plus physical NMS. It requires raw-image
inference and is deferred until EXP192 identifies whether endpoint localization
remains the dominant error. The full public notebook and its `0.763` public
score are not promoted. Receipt:
`reports/open_classical_baseline_audit_20260911.json`.

### EXP205 intensity-centroid refinement preregistration

EXP205 isolates the open classical baseline's main not-yet-tested physical
mechanism without importing its detector or public-tuned stack. On the existing
24 reciprocal embryo-disjoint caches, every frozen U-Net node is replaced by
the positive-intensity centroid in one fixed full-resolution crop
(`z=2,y=5,x=5` voxels after subtracting crop minimum). Time and node count are
preserved; the exact registered linker and EXP190 short-track lengths are then
recomputed. There is one candidate and no parameter selection. Parent
reproduction within `1e-12` is mandatory; positive pooled delta is exploratory,
while robust promotion additionally requires nonnegative direction deltas and
a positive 20,000-draw paired-bootstrap lower bound. This development result
cannot alter frozen EXP192/201/202. Five focused tests and Python compilation
pass; local WSL could not perform `bash -n`, so the remote shell check is a
mandatory pre-execution gate. Receipt:
`reports/exp205_intensity_centroid_refinement_preregistration_20260911.json`.

EXP205's first invocation stopped in its top-level dependency import before
movie-list loading, cache/raw-image access, graph construction or scoring: the
isolated run omitted the existing `evaluate_cached_short_track_family.py`.
No result JSON was created. Only that dependency (SHA
`a9156bbb...c5bbba3`) is authorized for packaging before the identical retry;
candidate, radii, data, parent, pruning and gates remain unchanged. Receipt:
`reports/exp205_prescore_dependency_failure_20260911.json`.

During the corrected EXP205 run, a progress-only `tail` command reached the
completed forward summary while reverse was already running. Candidate, code,
both commands and the no-selection comparison were frozen before launch, so
the eventual fixed pooled statistic remains mechanically defined; however,
directional blinding was violated. No code/parameter/process change is allowed,
and EXP205 is permanently labelled unblinded exploratory development evidence,
not untouched confirmation. Receipt:
`reports/exp205_early_direction_metric_exposure_20260911.json`.

### EXP205 intensity-centroid refinement result

The fixed centroid refinement exactly reproduces EXP190 as its control and
raises pooled development score from `0.7485183131` to `0.7542973497`
(`+0.0057790366`), changing edge sufficient statistics by `+37 TP`, `-76 FP`,
`-37 FN`. It wins 10/12 forward and 8/12 reverse movies and remains positive
after excluding all public twins (`+0.0041531034`). The mechanism is strongly
direction-asymmetric: forward gains `+0.0073197123`, reverse loses
`-0.0007888091`; the paired bootstrap interval is
`[-0.002601,+0.012911]`, so the full bidirectional arm fails the robust gate.
Shifts are small (mean about `0.33 um`, average movie p95 about `0.65-0.70 um`)
and no crop had zero weight. A forward-only composition with EXP195 reverse is
a strong development hypothesis (`0.7571390995`, `+0.0059398549` versus
EXP195; non-twin delta `+0.0044613056`) but is post-selection and requires a
separately frozen untouched confirmation. The early-summary exposure remains
part of its evidence grade. Remote SHA checks and local export hashes match.
Receipt: `reports/exp205_intensity_centroid_refinement_result_20260911.json`.

After the foreground worker exited, remote SHA verification passed and all
result/log hashes matched the local export. The exact 191,911-byte EXP205
remote run was removed and absence verified. Owned local pytest/bytecode trees
were removed. Source, tests, results, receipts and the active EXP192 transfer
remain. Cleanup receipt: `reports/exp205_cleanup_20260911.json`.

### EXP206 untouched forward-centroid composition preregistration

Before any EXP192 chunk launch or raw target staging, EXP206 freezes the
post-selected EXP205 mechanism for one untouched confirmation. Forward applies
the exact `intensity_centroid_r2_5_5 + min8` rule to all 116 non-twin
6bba-target movies; reverse remains the exact EXP195 q75 inference-only gate on
59 44b6-target movies. The parent is EXP195. All GPU chunk commands remain
unchanged: after their original all-eight no-metric gate and GPU release, the
atomic postprocessor runs five CPU-only refinements, requires a second
five-chunk no-metric structural gate, then merges/builds/scores EXP206. The gate
requires exact forward parent reproduction, positive incremental pooled and
forward deltas, exact zero reverse difference, positive paired-bootstrap lower
bound and positive minimum LOMO delta. Selection provenance includes the
EXP205 early-summary exposure; this is the first valid confirmation, not a
claim that development was blinded. Seven focused/integration tests and Python
compilation pass. Receipt:
`reports/exp206_centroid_untouched_confirmation_preregistration_20260911.json`.

EXP206 is now integrated into the frozen EXP192 confirmation code directory
before staging or target inference. Remote hashes match the locally tested
centroid evaluator, five-forward-chunk structural validator, EXP206 builder,
both imported dependencies and the amended fail-closed postprocessor. Remote
imports and `bash -n` pass; the focused plus full synthetic pipeline batch
passes `9/9`. The original eight GPU chunk commands are unchanged, no chunk or
postprocessor has launched, and no untouched metric was opened. Two failed
read-only diagnostics were quoting/path errors and had no scientific or data
effect. The active archive transfer remains the next dependency. Receipt:
`reports/exp206_exp192_integration_receipt_20260911.json`.

All five owned EXP206 pytest/compile temporary trees and the three generated
local bytecode files were removed after verification; absence was confirmed.
The final remote imports used bytecode suppression and left no matching remote
cache files. Tested sources, receipts and the active archive transfer were
preserved. Cleanup receipt: `reports/exp206_cleanup_20260911.json`.

### EXP207 exact eight-view edge-feature TTA preregistration

The current public `reyhanksatria/biohub-cell-tracking-0-946-lb` snapshot is
byte-identical to the source archived on September 9. Its claimed `0.946`
public score remains unverified and is not OOF evidence. The narrow mechanism
is nevertheless distinct from EXP145/148: those experiments adapted four-view
feature averaging on only four development movies per direction, whereas the
public source uses all eight D4 views. EXP207 therefore freezes a compute-
matched two-arm test on all 24 already-open reciprocal development movies and
the exact scratch checkpoints. Both arms use identical eight-view detector
logits; only `BIOHUB_EDGE_FEATURE_TTA=0/1` changes the features used by the
fixed `0.1` learned/motion linker. Forward/reverse short-track lengths remain
`8/3`; there is no selection. Promotion as a development mechanism requires
positive pooled and both-direction deltas, positive bootstrap lower bound,
positive minimum LOMO delta, exact coordinate controls and demonstrated edge-
probability activity. The separate four-to-eight-view detector comparison is
diagnostic and cannot rescue failed feature TTA. Eight source/evaluator/
comparison tests pass. EXP192 remains untouched, and EXP207 will not launch
while the active archive transfer or extraction materially contends for NFS.
Receipts: `reports/open_0946_edge_feature_tta_refresh_audit_20260911.json` and
`reports/exp207_d4_feature_tta8_preregistration_20260911.json`.

Before GPU inference, the generic four-file comparison builder was corrected
to accept the already frozen direction-specific `min8/min3` arm names. This is
an interface repair only; hypotheses, movies, models, thresholds and gates are
unchanged. The final runner also adds exact-coordinate, coordinate-linker and
learned-edge-activity controls. The complete focused batch now passes `13/13`.
Receipt: `reports/exp207_prescore_comparison_builder_correction_20260911.json`.

EXP207's CPU-only cached weak-linker preflight exactly reproduces the original
`registered_weak_hungarian` metrics on all 12 forward and 12 reverse movies;
maximum absolute error is `0.0` in each direction and all output hashes pass.
The slower reverse process was verified live and allowed to finish rather than
being restarted. No GPU lease or new inference was used. The preflight remains
an active dependency of the queued EXP207 run. Receipt:
`reports/exp207_cached_weak_preflight_result_20260911.json`.

A final prelaunch EXP207 audit caught a fail-closed contract bug before any GPU
inference: the labels `off/on` had been passed directly to an implementation
that disables feature TTA only for the literal value `0`, so both arms would
have enabled it. The runner now separates stable output labels from literal
`0/1` values and asserts the exact mapping. The launcher pins the corrected
runner, and the focused batch passes `13/13`. No metric, GPU lease, EXP192 file
or frozen scientific choice changed. The amended correction receipt is
`reports/exp207_prescore_comparison_builder_correction_20260911.json`.

EXP207's corrected code is now integrated in the registered remote root but
remains deliberately unlaunched. All twelve deployed hashes match local,
both shell scripts pass `bash -n`, all Python sources compile, no EXP207
process or GPU directory exists, and the remote code directory contains no
`__pycache__`. A full forward/reverse `src/scripts` comparison found only one
different generated predictor `.pyc`; after excluding bytecode, both source
manifests are exactly `8e647444...45ba88`. The isolated runner deletes copied
bytecode before installing the candidate predictor. The local focused batch
passes `13/13` and its owned pytest tree was removed. EXP192's active archive
transfer was not restarted and had reached `68,539,908,096` bytes during this
audit. Receipt: `reports/exp207_remote_integration_receipt_20260911.json`.

EXP192's selective staging path was refreshed while the archive transfer
continued. The remote stage still contains only the frozen manifest, no stage
process or chunk launch receipt exists, and the filesystem has about `7.24 TB`
free. All five staging/data-ready source hashes match local, `bash -n` passes,
and the focused validator/audit/data-ready tests pass `3/3`. The first local
test invocation executed no tests because its requested basetemp parent did
not exist; the parent was created, the identical test command passed, and the
owned tree was removed. No extraction, data-ready marker, GPU lease or metric
was produced. Receipt: `reports/exp192_stage_preflight_refresh_20260911.json`.

### EXP208 source-selected intensity-centroid radius family preregistration

EXP208 extends only the positive physical mechanism from EXP205; it does not
change detector weights or perform neural inference. Translation and six fixed
ZYX crop radii (`1,3,3`, `1,5,5`, `2,3,3`, `2,5,5`, `2,7,7`, `3,5,5`) are
evaluated first on the two checkpoint-validation source movies in each
reciprocal direction. Forward uses `min8`, reverse `min3`; each direction picks
maximum source pooled score with translation-first, listed-order ties. Only
the selected arm may then be evaluated on its 12 opposite-embryo target
movies, and both target files must exist before pooled/stability output.

The exact family was motivated after EXP205 exposed results on this 24-movie
cohort, so even source-only arm selection does not erase global cohort-level
adaptation. The result is development evidence; the untouched 175-movie EXP192
cohort remains confirmation. Positive pooled delta is the primary gate under
the corrected objective; direction, bootstrap/LOMO, edge, node/count and
division metrics remain diagnostics. The run is CPU-only, reuses verified
EXP152 caches, and is forbidden until archive transfer and exact staging finish.
Nine focused tests pass before any source or target metric. Receipt:
`reports/exp208_source_centroid_family_preregistration_20260911.json`.

EXP208's isolated CPU code is deployed with all eight remote hashes matching
local. Shell syntax and Python compilation pass, the code directory has no
bytecode cache, and the run directory does not exist. The focused test count is
now `9/9`; all three owned pytest trees were removed. No source/target metric,
GPU lease or Kaggle action occurred. The independent EXP192 archive transfer
was not restarted and had reached `72,712,093,696` bytes at verification.
Receipt: `reports/exp208_remote_integration_receipt_20260911.json`.

Before any EXP208 metric, its target structural control was strengthened to
require exact per-movie predicted-node-count invariance between translation
and the selected centroid arm. This matches the mechanism contract: only node
coordinates may move. The amended runner passes the same `9/9` batch; no
selection, target evaluation or run directory exists.

EXP208 now also has an atomic CPU-only launcher. Creation of its unique run
directory is the launch lock; a pre-spawn authorization file pins the runner,
and the post-spawn receipt records PID/start identity. Any failed or ambiguous
attempt therefore remains visible and cannot silently restart. The runner now
requires this authorization and a fresh results path. The complete batch passes
`10/10`; no process was launched and the staging prerequisite remains enforced.

A comparable-cohort pooled frontier snapshot is now recorded at
`reports/POOLED_OOF_FRONTIER_20260911.md`. It separates EXP195's supported
exploratory `0.7511992447` from the higher but post-selected EXP206 development
hypothesis `0.7571390995`, and keeps EXP190 nested versus fixed estimates
distinct. No public-weight score or different cohort is mixed into the table;
the untouched 175-movie score remains unavailable.

EXP192 staging now has a separately pinned, single-use persistent launcher.
It requires the exact `87,393,127,165`-byte archive contract, the immutable
stage runner, a stage containing only the frozen manifest, and absence of any
prior lock/receipt/audit/process. It then records PID and Linux start tick
before returning. Four focused staging/launcher tests pass. The launcher is
prepared only; the still-running SCP session prevents launch. Receipt:
`reports/exp192_stage_launcher_receipt_20260911.json`.

EXP192 now also has a fail-closed data-readiness finalizer for the boundary
between staging and GPU inference. It pins the current marker SHA (correcting
the superseded SHA in the historical gate receipt), chunk index and all seven
chunk-launch dependencies; requires terminal `PASS_EXP192_REMOTE_STAGE` and
verified `STAGING_SHA256SUMS`; rejects any prior readiness, launch or output;
then verifies exact eight-run coverage and every receipt hash before committing
the summary. Its verifier dependency is itself SHA-pinned before use. Six
focused tests pass, remote hashes and shell/Python preflight
match, and no metric, readiness marker, staging process or GPU lease was
created. The active archive transfer reached `80,313,712,640` of
`87,393,127,165` bytes and remains live. Receipt:
`reports/exp192_data_ready_finalizer_receipt_20260911.json`.

An attributed audit of the currently indexed competition discussions found no
numerical pooled OOF claim with enough split, checkpoint and aggregation detail
to compare directly with our reciprocal embryo-held-out protocol. The useful
community evidence is methodological: leave-one-embryo-out selection, very
large movie-level variation, public all-train checkpoint leakage, possible
public-LB optimism, and a suggested detection → linking → division work order.
No public score or per-movie range is converted into a synthetic pooled target.
Our exact pooled sufficient statistics, paired direction evidence and untouched
EXP192 confirmation remain authoritative. Report:
`reports/COMMUNITY_POOLED_OOF_AUDIT_20260911.md`; receipt:
`reports/community_pooled_oof_audit_receipt_20260911.json`.

The original EXP192 SCP session completed with exit code `0`. The remote archive
has the exact expected size `87,393,127,165` and full SHA-256
`538ed8a4...7dfd19`, matching the local source. The single-use persistent
staging launcher then started CPU/I/O-only PID `220563`, Linux start tick
`435364238`; the launch receipt and live `/proc` identity match. No GPU lease or
scientific metric exists. The exact process must reach
`PASS_EXP192_REMOTE_STAGE` and pass all staging/audit checks before readiness or
inference. Receipt:
`reports/exp192_archive_verified_stage_launch_20260911.json`.

While remote extraction continued, the complete existing local EXP192 pipeline
test set was rerun across staging, readiness, all-eight structural gates,
merging, EXP190/191/195/201/202/206 builders and the synthetic integration
pipeline: `32 passed`. The first hand-assembled invocation ran zero tests
because it named one nonexistent historical test file; actual files were then
enumerated and the corrected command passed without code/scientific changes.
Both owned pytest trees were removed. Receipt:
`reports/exp192_full_prelaunch_test_gate_20260911.json`.

The original EXP192 queue plan and its seven-hash correction are now resolved
into one execution manifest, preserving every preassigned request ID/token and
copying all eight exact movie hashes from the authoritative chunk index. A
machine check verified one-to-one direction/number mapping, movie counts,
tokens, run names and corrected hashes; the resolved manifest SHA is
`63269f0b...b56961f`. Only this resolved plan may drive queue requests after
data readiness. File:
`reports/exp192_gpu_queue_plan_resolved_20260911.json`.

EXP192 staging completed with exact `PASS_EXP192_REMOTE_STAGE`. All five staged
SHA entries verify; the final audit covers `21,525` files,
`75,045,173,746` bytes and 175 content-hashed movies (`59 44b6 + 116 6bba`),
with all 2,975 Zarr metadata JSON files parsed and no public twins. The
fail-closed finalizer created and independently verified all eight readiness
receipts under audit SHA `1abde88c...768de`. The now-unused verified transfer
ZIP was then removed by exact path, reclaiming `87,393,127,165` bytes; staged
data and evidence remain. Receipt:
`reports/exp192_stage_data_ready_cleanup_result_20260911.json`.

With exact data readiness established, the resolved first request
`exp192-confirm-forward-00-20260911` received fresh `RESERVED/CURRENT` on the
physical RTX6000 after an empty-queue and idle-device check. The pinned launcher
started PID `221962` / start tick `435724546`, worker PID `221968`; the queue is
`RUNNING/CURRENT` and the GPU process was observed. No chunk metric or log
content was read and no result SHA existed at the live check. Receipt:
`reports/exp192_forward00_queue_launch_20260911.json`.

EXP192 `forward_00` then exited normally. All SHA256SUMS entries verify and its
no-metric validator covers 24 exact movies and three required result files with
status `PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS`. The process tree and physical
GPU process were absent before its lease was released. No scientific output or
log content was inspected. Receipt:
`reports/exp192_forward00_structural_completion_20260911.json`.

After rejoining the empty queue, `forward_01` received a fresh
`RESERVED/CURRENT` RTX6000 lease. Exact movie/data-ready/audit hashes and
absence of prior launch/output were rechecked; PID `223585`, start tick
`435816567`, worker `223591` are registered as `RUNNING/CURRENT`. No metric was
opened. Receipt: `reports/exp192_forward01_queue_launch_20260911.json`.

EXP192 `forward_01` then exited normally. Every entry in its immutable
`SHA256SUMS` verifies, and the no-metric structural receipt covers the exact 24
movies and three required result files with
`PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS`; its movie-list hash is
`6483a378...952c9`. Both recorded PIDs, any matching process tree and the GPU
worker were absent before the lease was released as `RELEASED/CURRENT`. An
initial `pgrep` diagnostic matched its own literal command and failed closed
before validation or release; the corrected fragment-built check removed that
self-match. No scientific output or log content was opened. Receipt:
`reports/exp192_forward01_structural_completion_20260911.json`.

During the released-GPU boundary, EXP208's local physical centroid-family,
source-selection and atomic-launch contracts were rerun: `7/7` selected tests
pass, bytecode writes were disabled and the owned basetemp was removed. The
CPU-only experiment was deliberately not launched concurrently with EXP192,
because the active GPU request reserves eight CPUs on the same host. No source
or target metric was opened. Receipt:
`reports/exp208_local_contract_recheck_20260911.json`.

The resolved `forward_02` request then found zero nonterminal queue entries and
an idle physical RTX6000. Its exact movie, data-ready and audit hashes match;
the run contained only the three frozen input receipts and no prior launch or
output. The queue allocated the expected UUID, and the pinned launcher started
PID `225227` / start tick `435925979`, worker PID `225234`; the worker was
observed on that UUID with about 1026 MiB and the request is
`RUNNING/CURRENT`. No chunk log or scientific metric was opened. Receipt:
`reports/exp192_forward02_queue_launch_20260911.json`.

EXP192 `forward_02` exited normally after identity-aware heartbeat monitoring.
Every immutable SHA entry verifies; its no-metric structural receipt is
`PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS` for the exact 24 movies and three
required result files under movie hash `a1986066...64d66`. Both recorded PIDs,
all matching process-tree entries and the GPU worker were absent before the
lease became `RELEASED/CURRENT`. No scientific output or log content was
opened. Receipt:
`reports/exp192_forward02_structural_completion_20260911.json`.

The resolved `forward_03` preflight found no nonterminal request and no
physical GPU process. Exact movie (`040d17ad...9a00f`), data-ready and audit
hashes match, and no earlier launch/output exists. The queue allocated the
expected RTX6000 UUID; the pinned launcher started PID `226620` / start tick
`436019205`, worker `226628`, observed on the GPU with about 1028 MiB. The
request is `RUNNING/CURRENT`; no log or scientific metric was opened. Receipt:
`reports/exp192_forward03_queue_launch_20260911.json`.

EXP192 `forward_03` exited normally. All immutable SHA entries verify and its
structural receipt is `PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS` for the exact 24
movies and three required files under hash `040d17ad...9a00f`. The recorded
PIDs, matching process tree and GPU worker were absent before release to
`RELEASED/CURRENT`. No scientific output or log content was opened. Receipt:
`reports/exp192_forward03_structural_completion_20260911.json`.

The final forward chunk, `forward_04`, passed an empty-queue/idle-GPU and exact
movie (`33f1ce7a...7195a`), data-ready and audit hash preflight with no prior
launch/output. Its expected 20-movie request received the RTX6000; the pinned
launcher started PID `228017` / start tick `436114875`, worker `228025`, which
was observed on the allocated UUID with about 1026 MiB. Queue state is
`RUNNING/CURRENT`; no log or scientific metric was opened. Receipt:
`reports/exp192_forward04_queue_launch_20260911.json`.

EXP192 `forward_04` exited normally and completed forward coverage. Every SHA
entry verifies; the no-metric structural receipt is PASS for its exact 20
movies and three required result files under hash `33f1ce7a...7195a`. Both
recorded PIDs, all matching process entries and the GPU worker were absent
before release to `RELEASED/CURRENT`. No scientific output or log was opened.
Receipt: `reports/exp192_forward04_structural_completion_20260911.json`.

The first reverse chunk, `reverse_00`, passed an empty-queue/idle-GPU and exact
movie (`60b409b1...15ca6a`), data-ready and audit hash preflight with no prior
launch/output. Its 24-movie request received the RTX6000; the pinned launcher
started PID `229648` / start tick `436194856`, worker `229658`, observed on the
allocated UUID with about 1028 MiB. Queue state is `RUNNING/CURRENT`; no log or
scientific metric was opened. Receipt:
`reports/exp192_reverse00_queue_launch_20260911.json`.

EXP192 `reverse_00` exited normally. The original monitor session closed at the
same boundary, so terminal state was re-established directly from the recorded
PID, final manifest and GPU state rather than inferred from the client handle.
Every SHA entry verifies; the no-metric structural receipt passes for the exact
24 movies and all six reverse files under hash `60b409b1...15ca6a`. Recorded
PIDs, matching process entries and GPU worker were absent before release to
`RELEASED/CURRENT`. No scientific output or log was opened. Receipt:
`reports/exp192_reverse00_structural_completion_20260911.json`.

The resolved `reverse_01` preflight found an empty queue and idle physical GPU,
exact movie (`9cd9495b...48d30`), data-ready and audit hashes, and no prior
launch/output. The request received the RTX6000; the pinned launcher started
PID `232071` / start tick `436397530`, worker `232081`, observed on the
allocated UUID with about 1026 MiB. Queue state is `RUNNING/CURRENT`; no log or
scientific metric was opened. Its local launch receipt was parsed and all key
fields checked before this append. Receipt:
`reports/exp192_reverse01_queue_launch_20260911.json`.

On 2026-09-12, the persisted `reverse_01` run was rechecked from live remote
state after its monitor session was no longer available. Its recorded parent
was absent, the physical GPU was idle and the final manifest existed. Every SHA
entry verifies; the exact 24-movie, six-file receipt is
`PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS` under hash
`9cd9495b...48d30`. The lease was then released as `RELEASED/CURRENT`. Seven of
eight chunks are now structurally complete; no scientific output or log was
opened. Receipt:
`reports/exp192_reverse01_structural_completion_20260912.json`.

The final chunk, `reverse_02`, passed an empty-queue/idle-GPU and exact movie
(`b84bdfcd...ef457`), data-ready and audit hash preflight with no prior
launch/output. Its 11-movie request received the RTX6000; the pinned launcher
started PID `234738` / start tick `439658740`, worker `234748`, observed on the
allocated UUID with about 1026 MiB. Queue state is `RUNNING/CURRENT`; no log or
scientific metric was opened. Receipt:
`reports/exp192_reverse02_queue_launch_20260912.json`.

EXP192 `reverse_02` exited normally and completed all eight frozen chunks.
Every SHA entry verifies; the exact 11-movie, six-file structural receipt is
`PASS_EXP192_CHUNK_STRUCTURE_NO_METRICS` under movie hash
`b84bdfcd...ef457`. The recorded parent/initial worker, matching process tree
and all physical GPU processes were absent before release to
`RELEASED/CURRENT`. The RTX6000 is released. No scientific output or log was
opened. Receipt:
`reports/exp192_reverse02_structural_completion_20260912.json`.

The frozen EXP192 postprocessor then passed its all-eight no-metric gate over
all 175 exact movies before opening scientific results. EXP206 establishes the
new honest confirmation frontier at pooled OOF `0.6784542971`,
`+0.0681973895` over the raw common base and `+0.0044808928` over EXP195. The
paired movie bootstrap versus EXP195 has 95% interval
`[+0.0021909611,+0.0067969218]`, `P(delta>0)=0.99985`, and every LOMO delta is
positive (minimum `+0.0041295077`). EXP201 and EXP202 are not promoted because
their incremental bootstrap intervals cross zero. The frozen postprocessor's
original manifest contained relocated temporary absolute paths; it was
preserved, all 49 files were verified with a separately tested fail-closed
relocation verifier, and an independently valid `SHA256SUMS_RELOCATED` was
created. The complete results were exported and reverified locally. No Kaggle
action occurred. Reports: `reports/EXP192_UNTOUCHED_POOLED_OOF_RESULT_20260912.md`
and `reports/POOLED_OOF_FRONTIER_20260912.md`.

EXP208 ran CPU-only on `nsu-quadro` as PID `238883`, Linux start tick
`439970868`, with no GPU process. Both source selections and both 12-movie
target evaluations completed, but the run correctly did not emit a final
manifest: its post-target gate asserted exact predicted-node-count invariance
between translation and centroid arms. That added invariant was invalid because
the refined coordinates are re-linked and short-track pruning is rerun, so all
24 target movies can legitimately retain a different number of nodes. The
failed run and logs were exported; inference was not repeated. Receipt:
`reports/exp208_cpu_launch_and_failure_receipt_20260912.json`.

A preregistered post-failure assembly used only the four already frozen EXP208
selection/target files. Source selection chose forward centroid radius
`(3,5,5)` and reverse radius `(2,3,3)`. On the 24-movie development target the
composition scores `0.7562142111` versus translation `0.7485183131`, delta
`+0.0076958981`; paired-bootstrap 95% interval
`[+0.0022073780,+0.0131181900]`, `P(delta>0)=0.99685`, minimum LOMO
`+0.0065376408`. Forward improves `+0.0097296089`, while reverse regresses
`-0.0010606069`; this is promising transfer evidence but not a replacement for
the 175-movie EXP206 frontier. Receipts:
`reports/exp208_invalid_invariance_gate_correction_preregistration_20260912.json`
and `reports/exp208_post_failure_assembly_result_20260912.json`.

EXP209 preregisters the source-selected centroid transfer before either new
radius is evaluated on the 175-movie cohort: forward `(3,5,5)` with `min8` and
reverse `(2,3,3)` with `min3`. Three deterministic policies are frozen for
assembly after one all-eight no-metric gate: both selected directions, selected
forward plus EXP191 reverse, and selected forward plus EXP195 reverse. The last
comparison isolates the forward-radius change from EXP206. Ten focused tests
pass. Remote code hashes, shell syntax, Python compilation, all eight immutable
candidate caches, 246 GiB available RAM and the isolated run/code absence were
verified. CPU-only PID `240346`, Linux start tick `440181250`, was launched
atomically on `nsu-quadro` with affinity `0-7`; worker PID `240403` was observed
on the first forward chunk, with no GPU process and no opened metric. Receipts:
`reports/exp209_selected_centroid_confirmation_preregistration_20260912.json`
and `reports/exp209_remote_launch_receipt_20260912.json`.

While EXP209 ran, EXP210 tested a frozen inference-observable safety veto on
the already computed EXP206 centroid arm. On 12 development movies, using
translation when centroid re-linking increased removed nodes by more than
`0.5%` of raw candidates improved forward score from `0.7588369112` to
`0.7617522787`. On the 116 confirmation movies it vetoed three movies and
reduced the full 175-movie score from EXP206's `0.6784542971` to
`0.6782048153`, delta `-0.0002494818`; paired bootstrap 95% interval
`[-0.0006566860,+0.0000223179]`, probability positive `0.081`, and every LOMO
delta is negative. Two vetoed movies had large positive centroid effects, so
the development relation did not transfer. Reject this telemetry gate and
retain EXP206 unchanged. Five focused tests pass; no remote computation, GPU
or Kaggle action occurred. Receipts:
`reports/exp210_centroid_pruning_safety_veto_preregistration_20260912.json`
and `reports/exp210_centroid_pruning_safety_veto_result_20260912.json`.

The previously integrated EXP207 exact eight-view D4 feature-TTA experiment
was revalidated while EXP209 remained CPU-only. Both frozen preflight receipts
and exact runner/launcher hashes match, the GPU output directory and process
were absent, the common queue had no nonterminal conflict, and the physical
RTX6000 was idle at 5 MiB / 0%. Request
`biohub-exp207-d4-feature-tta8-20260912` received fresh
`RESERVED/CURRENT` for UUID `GPU-a4b01714-3774-ca39-a9d9-2f30429e84ba`.
The pinned launcher started PID `241019`, Linux start tick `440311597`, and
worker `241071`, observed on that GPU at about 1026 MiB. The queue is now
`RUNNING/CURRENT`; no metric or log content was opened. EXP209 continues on
eight CPU cores without a GPU. Receipt:
`reports/exp207_gpu_queue_launch_20260912.json`.

A fresh competition-discussion review still found no numerical pooled OOF
claim with a comparable embryo split, checkpoint selection, movie set and
aggregation definition. Recent comments add two mechanism leads: segment-level
appearance for association, consistent with EXP207's distinct feature arm, and
the already audited CC0 synthetic division dataset with 165,267 labelled
divisions. The latter remains high-prior synthetic supervision and cannot
replace reciprocal real-data validation. Report:
`reports/COMMUNITY_POOLED_OOF_UPDATE_20260912.md`; receipt:
`reports/community_pooled_oof_update_receipt_20260912.json`.

While EXP209 remained live, a post-hoc paired development comparison isolated
forward radius `(3,5,5)` from the earlier `(2,5,5)` radius using identical
reverse translation rows. The larger radius is ahead by `+0.0024098966` in
forward and `+0.0019625269` in the 24-movie pooled construction, but the paired
bootstrap interval `[-0.0029565024,+0.0087083592]` crosses zero and minimum
LOMO is `-0.0005854690`. This prevents premature promotion and reinforces the
need for EXP209's still-unopened 175-movie paired comparison. Receipt:
`reports/exp208_r3_vs_exp205_r2_posthoc_result_20260912.json`.

EXP209 is preregistered before any 175-movie metric for its two selected radii.
It evaluates only forward centroid `(3,5,5)` with `min8` and reverse centroid
`(2,3,3)` with `min3`, selected on EXP208's two source checkpoint-validation
movies per reciprocal direction. All eight chunk outputs must pass one
no-metric `116+59` structural gate before merging. Three compositions are
frozen: both selected directions, selected forward + EXP191 reverse, and
selected forward + EXP195 reverse; each is compared with raw base and EXP206.
The run is CPU-only, limited to eight CPU cores and 16 GiB RAM, with an atomic
single-launch contract. Ten focused tests pass. No remote launch, GPU lease,
175-movie selected-radius metric or Kaggle action has occurred. Receipt:
`reports/exp209_selected_centroid_confirmation_preregistration_20260912.json`.

The later EXP209 launch completed as the same single CPU-only PID `240346` /
Linux start tick `440181250`; this explicitly supersedes the pre-launch state
in the preceding preregistration entry. The parent and worker were absent
before result inspection. All 38 manifest entries verify, and the all-eight
no-metric gate passes exact coverage of 116 forward plus 59 reverse movies
before any scientific value was opened. The strongest of the three
preregistered compositions is forward intensity-centroid radius `(3,5,5)` /
`min8` plus the frozen EXP191 reverse gap-plus-pruning arm. It establishes a
new pooled OOF frontier of `0.6815218333`, `+0.0030675362` over EXP206 and
`+0.0712649257` over the raw base. The paired movie bootstrap versus EXP206 is
`[+0.0014898445,+0.0046280957]`, `P(delta>0)=1.0`; every LOMO delta is positive
(minimum `+0.0028973690`). Forward and reverse both improve versus EXP206 by
`+0.0032449048` and `+0.0020734110`. The source-selected reverse centroid arm
itself regresses `-0.0063925873`, so it is not promoted. Division TP remains
zero with 138 FN. Verified results were exported locally; the same 38 entries
verify under manifest SHA
`1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a`.
The compact 1,314,935-byte result set is preserved as reproducibility evidence;
no bulk cache was created and no Kaggle action occurred. Reports:
`reports/EXP209_SELECTED_CENTROID_CONFIRMATION_RESULT_20260912.md` and
`reports/exp209_selected_centroid_confirmation_result_20260912.json`.
Process/export/retention receipt:
`reports/exp209_completion_cleanup_receipt_20260912.json`.

EXP207 completed all four eight-view D4 inference passes under the common
RTX6000 lease as PID `241019` / start tick `440311597`. Exact process identity
was monitored through completion; parent, child and GPU processes were absent
before release to `RELEASED/CURRENT`. Its primary feature-TTA comparison gains
`+0.0005538700` across the 24 reciprocal development movies and has positive
direction and LOMO deltas, but fails the frozen gate because paired bootstrap
95% CI `[-0.0006214813,+0.0020187849]` crosses zero. Reject feature TTA for the
current weak-linker family. The separately preregistered eight-view detector
TTA diagnostic gains `+0.0119457974`, improves forward and reverse by
`+0.0147058021/+0.0003702260`, has CI
`[+0.0009265929,+0.0228854648]`, and minimum LOMO `+0.0091216580`; promote it
only to 175-movie confirmation, not directly to the frontier.

The EXP207 runner's immutable manifest listed its in-progress
`SHA256SUMS.tmp`, which was later renamed. No metric was opened after that
anomaly until a four-test fail-closed recovery verifier proved exactly one
missing temp entry, verified the other 109 hashes, and established exact file
coverage. The original manifest remains preserved. All 34 compact result files
were exported and rechecked; four reproducible candidate caches and the
disposable tracking repository (about 98 MiB) were removed. Remaining remote
artifacts pass a new post-cleanup manifest with SHA
`f0fddcc5b1e52bbd1c17a7ac5ff1d590264f362dec30c25c6598c7e38a8bda11`.
No Kaggle action occurred. Reports:
`reports/EXP207_D4_FEATURE_TTA_RESULT_20260912.md`,
`reports/exp207_d4_feature_tta_result_20260912.json`, and
`reports/exp207_manifest_self_temp_recovery_preregistration_20260912.json`.

Before opening any eight-view prediction on the 175-movie cohort, EXP211
freezes a full detector-D4 confirmation. It uses the exact EXP207 all-eight
inverse-aligned detector with identity-view edge features only, fixed
thresholds/checkpoints and the unchanged 116+59 EXP192 chunk partition. Each
of eight bounded GPU chunks must independently pass a no-metric structure and
SHA gate; one all-eight exact-coverage gate precedes any scientific read. The
pure D4 min8/min3 policy is compared with EXP190. Two fixed compositions then
test D4 forward with EXP191 reverse and D4 + intensity-centroid `(3,5,5)`
forward with EXP191 reverse against the new EXP209 frontier. Six focused tests
pass. No EXP211 remote launch or 175-movie D4 metric has occurred. Receipt:
`reports/exp211_d4_detector_175_confirmation_preregistration_20260912.json`.

EXP211 `forward_00` then passed remote code/movie/data hashes, shell syntax,
clean path and idle physical GPU checks. The queue allocated the expected
RTX6000 UUID to request `biohub-exp211-d4-forward00-20260912`; the atomic
launcher started PID `245712`, Linux start tick `440705525`, worker `245725`,
observed on that GPU at about 1028 MiB. Queue state is `RUNNING/CURRENT`. No
chunk log or scientific metric was opened. Receipt:
`reports/exp211_forward00_queue_launch_20260912.json`.

While `forward_00` retained the only Biohub GPU lease, the remaining seven
frozen EXP192 movie lists were byte-copied into isolated EXP211 run directories
without queue requests. Their seven SHA-256 values match the frozen chunk
index. The all-eight no-metric validator was implemented and passed two focused
tests; SHA is
`06e57b69b22055211118eedc7249dead99ef7af9c0abf7579af88766c8abc230`.
Together with the six launch/chunk/D4 tests, eight focused tests pass before
any 175-movie D4 metric is opened. Receipt:
`reports/exp211_remaining_movie_lists_staged_20260912.json`.

EXP211 `forward_00` completed all 24 detector-D4 inference movies, but its
first v1 postprocessing attempt then failed before filtering because the code
bundle omitted the transitive `evaluate_coordinate_consensus.py` dependency.
The raw D4 JSON and 24 candidate caches were frozen under failure-snapshot
manifest SHA
`bf8964e2bbbb9c56a81a4a731485b9a2201cebcb645305e2f07d3ff990ac51e9`;
no scientific metric was opened. After the exact GPU PID/process tree was
absent, the RTX6000 lease was released. Receipt:
`reports/exp211_forward00_packaging_failure_20260912.json`.

The preregistered EXP211 v2 packaging-only correction adds that missing file
and a snapshot-gated CPU resume path without changing detector inference,
thresholds, filters, movie membership or any scientific policy. Nine focused
tests pass; the corrected launcher SHA is
`a0cf9bef7191bc8983e077d5328a3ab294983d0d92bc6232b659903398c7cbbd`
and the CPU-resume SHA is
`c58ef661d147dc29e8d7c63100af6f9afcc064f0664929c479aa813df7d4cfbc`.
Receipt: `reports/exp211_v2_packaging_correction_preregistration_20260912.json`.

The cached CPU-only recovery then ran as PID `246909`, Linux start tick
`440891298`, on cores `0-7`. It reverified the entire failure snapshot and did
not repeat GPU inference or acquire a GPU lease. The parent and process tree
are absent after completion, the disposable tracking repository was removed,
and all 43 final manifest entries verify under manifest SHA
`d4479824d0d8a36864d1240c28e1b4e47595075f6c1decf20fba412ddfd3a698`.
The no-metric chunk gate passes 24/24 forward movies, 24 candidate caches and
`scientific_metrics_emitted=false`; structure SHA is
`75a0e4542cb7ea021577e348746d5026188c17bd8697ea6621fa784767d81faa`.
The complete 15,069,872-byte run remains pinned because its files are required
by the all-eight gate. No Kaggle action occurred. Receipt:
`reports/exp211_forward00_cpu_salvage_completion_20260912.json`.

A fresh community-evidence refresh found one numerical CV claim of about
`0.919 CV` with `0.895` LB, but the author does not disclose an embryo split,
movie cohort, checkpoint-selection protocol or pooled aggregation, so it is
not comparable with our 175-movie EXP209 frontier. More importantly, a leading
participant explicitly recommends complete-movie official scoring and
movie-level OOF, warning that random edge-level CV is misleading, and suggests
separating missing endpoint nodes from association errors. This supports our
current embryo-aware protocol and diagnostics without changing a frozen
experiment. EXP209's `0.6815218333` remains the only reproducible comparable
internal frontier. Report: `reports/COMMUNITY_POOLED_OOF_UPDATE_R2_20260912.md`;
receipt: `reports/community_pooled_oof_update_r2_receipt_20260912.json`.

Correction to the immediately preceding community-search entry: the `0.919
CV / 0.895 LB` claim and complete-movie/movie-level-OOF advice were already
captured on 2026-09-11 in `reports/public_cv_claims_update2_20260911.json`.
The 2026-09-12 search independently revalidated that evidence but did not find
a new numerical pooled OOF claim. The methodological conclusion and EXP209
frontier are unchanged. Correction receipt:
`reports/community_pooled_oof_update_r2_duplicate_correction_20260912.json`.

EXP211 `forward_01` passed the corrected v2 code hashes, movie/data hashes,
shell syntax, isolated-run and physical RTX6000 preflight. Eight focused tests
pass using a project-local pytest basetemp; the earlier five setup errors were
only the sandbox denying pytest's default `%TEMP%` and did not execute those
tests or indicate code failure. Common-queue request
`biohub-exp211-d4-forward01-20260912` received the sole RTX6000 as
`RESERVED/CURRENT`. The launcher started PID `247320`, Linux start tick
`440931198`; worker `247333` was observed on the assigned GPU at 1028 MiB and
the queue is `RUNNING/CURRENT`. No metric was opened. Receipt:
`reports/exp211_forward01_queue_launch_20260912.json`.

EXP211 `forward_01` subsequently completed all 24 movies. Its parent PID
`247320`, start tick `440931198`, worker and physical GPU process were absent
before release to `RELEASED/CURRENT`. All 40 final manifest entries verify
under SHA `e50c97254590f4d2571aabf6d3ca8992cdb6fc30bb69ba503090cbc5e5a2bc96`;
the no-metric gate reports 24 movies, 24 caches and
`scientific_metrics_emitted=false`, structure SHA
`3296f1620642373e410083c8eda763b05cad72c9220afe1c4ad03e41f7c3dc25`.
The disposable tracking repository was removed. EXP211 is deliberately paused
after two of eight chunks; six staged chunks remain active dependencies and no
GPU lease/process remains. Receipt:
`reports/exp211_forward01_structural_completion_20260912.json`.

## EXP212 — production form of the EXP209 OOF frontier (pre-POST)

Track/slot: `PRIVATE_ROBUST`, daily slot 3. Forward uses checkpoint `dc06a794...`,
centroid `(3,5,5)`, registered links and `min8`; reverse uses checkpoint
`5c0f8358...`, EXP191 DeepCenter `ea0b53cb...`, gap `4.5`, threshold `0.20`,
minimum confirmation span `8.5`, synthetic cap `0.05`, and `min6`. Parent
EXP209 has pooled OOF `0.6815218332750073` over 175 reciprocal embryo-held-out
movies, delta `+0.0030675362` versus EXP206, positive paired CI and LOMO.

Hidden embryos are disjoint from training, so production does not assume hidden
prefixes are `44b6/6bba`. Public-placeholder prefixes reproduce the exact
cross-fit arm. Unseen prefixes run both arms and use one frozen label-free
selector: maximize mutual-nearest 2-um agreement fraction, then continuity,
then prefer fewer nodes. This selector has no claimed OOF; `0.68152` remains
the cross-fit reference only.

Source `kaggle_notebooks/exp212_exp209_oof_frontier/exp209_oof_frontier.py`,
SHA `51c4bbffe66fe1080f927151a7722b2291d1d681f2c43bfe77599e69044b5c47`.
It dynamically discovers competition `test/*.zarr`, performs inference and
writes one root `submission.csv`; it reads no frozen submission. Expected
secondary output is `exp212_runtime_receipt.json`. Eighteen focused tests and
source compilation pass; the 54,697,405-byte private dataset verifies against
`SHA256SUMS`. Before POST require a clean Internet-off COMPLETE Kaggle run,
exact source SHA, one root CSV, exact runtime IDs, schema/types/finite/bounds,
consecutive edges, degree invariants and output SHA. Then submit once through
the guarded helper and inspect the full API object; stop on anomaly. Receipt:
`reports/exp212_exp209_oof_production_preregistration_20260912.json`.

Pre-run packaging correction: Kaggle created the dataset under its canonical
title-derived slug `dmitriigluzdov/biohub-exp209-pooled-oof-frontier-models`,
not the shorter requested slug in the first receipt. The ready dataset exposes
exactly the 15 expected files; checkpoint sizes and paths match the local
manifest. Before any kernel push or inference, only the two source lookup paths
and metadata attachment were corrected. Model bytes, selector, postprocessing,
test discovery and promotion gate are unchanged. Eighteen tests pass again;
the corrected source SHA is
`ab08de413e901669224fae7d434368203fd52b89601c236ac19e36287cbae6e4`.
Correction receipt:
`reports/exp212_dataset_slug_correction_20260912.json`.

EXP212 Kaggle v1 failed before model loading or inference. The downloaded log,
SHA `9b4205991e244bd1fd07e1cf1ed033c484c50ba46ac941a7b629aaa739276d54`,
shows that pip's dependency resolver upgraded NumPy to `2.4.6`, leaving the
preinstalled SciPy binary unable to import (`numpy.ufunc` missing
`__qualname__`). No `submission.csv` or runtime receipt was produced and no
competition POST occurred. The support requirements already enumerate every
needed direct package, so the packaging-only v2 correction adds pip
`--no-deps`, matching the dependency-preservation strategy used by the current
successful production lineage. Model bytes, inference, postprocessing and
selector are unchanged. Eighteen tests and compilation pass; corrected source
SHA is `ddd310cb1c2dfacba1fdc463f8a0680b8cdbb9297d8e2c7abc6657f6cbcff093`.
Retry only as Kaggle v2 of the same kernel. Receipt:
`reports/exp212_kaggle_v1_dependency_failure_v2_correction_20260912.json`.

EXP212 Kaggle v2 also failed before model loading/inference and produced no
submission. With transitive upgrades disabled, pip retained Kaggle's older
Polars, while the installed support-pack `tracksdata` requires `pl.Float16`.
The v2 log SHA is
`83e4b69ed0895eb1727490cca5f0f05b6eb02270304e3c1ca55bd1f7f3b2ce6c`.
The final packaging-only v3 correction force-reinstalls every explicitly listed
support package without transitive resolution and explicitly installs the
matched support wheels NumPy `2.4.6` plus SciPy `1.18.0`. This simultaneously
avoids the v1 mixed NumPy/SciPy ABI and the v2 old-Polars mismatch. No model or
scientific logic changes. Eighteen tests and compilation pass; v3 source SHA
is `9ebdc1e62494ac29e4178321c1989abefa31f3cf2a56be11dbc42e5a7421566f`.
One v3 retry is allowed; a further anomaly stops productionization. Receipt:
`reports/exp212_kaggle_v2_dependency_failure_v3_correction_20260912.json`.

EXP212 Kaggle v3 failed at SciPy import before model loading/inference. The
matched wheels were installed, but NumPy had already been imported at source
line 19 before pip replaced its files, leaving a mixed in-memory/on-disk module
state. Log SHA is
`28f044e41b38fcf65b93d1820f023a0e06ef6d83a167cd60e588f3dfaac628f7`.
No runtime receipt or `submission.csv` exists and no competition POST occurred.
The preregistered retry limit is reached, so EXP212 stops without an LB
submission. The next technical repair is clear but unexecuted: perform offline
dependency installation before importing NumPy/SciPy (or force only the
required Polars/Zarr packages while preserving Kaggle's compatible NumPy/SciPy
pair). It requires a new explicit continuation decision and clean audit.
Current live submission state remains one daily POST: ref `56177715` is still
`PENDING`, empty score/error and zero bytes; limits are 1 used, 4 available.
Receipt: `reports/exp212_kaggle_v3_failure_stop_20260912.json`.
