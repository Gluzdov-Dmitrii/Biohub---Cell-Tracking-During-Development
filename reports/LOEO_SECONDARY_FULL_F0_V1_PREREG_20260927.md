# LOEO secondary full fold 0 v1 — preregistration, 2026-09-27

**Status at registration:** local plan only. No full-training bundle, remote stage, queue reservation, A100 lease, target read, inference, or Kaggle POST exists. This registration precedes implementation. The unique local identity is `loeo-secondary-full-f0-v1-20260927`; it must never reuse the v1–v3 technical-pilot runs.

## Hypothesis and boundary

Train only the public support-pack secondary UNet/transformer from scratch on source embryo `44b6`. A full source fit, selected on disjoint source-inner movies, may produce a usable secondary checkpoint for a **later** one-movie execution-path observation. It does not validate the assembled x138 pipeline or establish honest OOF 0.9+. The original x138 primary, V1284 head, DeepCenter and graph policy are outside this training run and lack the required common held-out provenance.

The fixed nested split is SHA256 `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`: fold 0 has 56 `44b6` fit movies (5,001 two-frame windows), 15 disjoint `44b6` source-inner selection movies (1,314 windows), and 128 sealed `6bba` outer movies. The training process receives exactly 71 source `.zarr`/`.geff` pairs through a new isolated view. Every `6bba` ID, image and label is excluded from that view; an access guard denies target paths and external/pretrained checkpoints. There is no target-label access for training, model selection or inference. The one target `.geff` label tree can be opened only by a separately authorized CPU scorer after prediction graph, output SHA and process/lease receipts are locked.

Parent evidence: v3 pilot reconciliation SHA256 `65e17c3a9ddd1ad1962587dd2615f093d37eac226d82d7e73b24aafb1edb352a` passed 19/19 technical checks. The public support-pack trainer SHA256 is `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`; predictor SHA256 is `c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`; support manifest SHA256 is `a6f57ca8232e43711253326eb20356ae625ac123ba4e5d52ee4aba87c1c07d5b`. No pilot checkpoint initializes the full run.

## Fixed training and selection

- 50 complete epochs, all 5,001 fit windows exactly once per epoch in shuffled batches of 8 (`ceil(5001/8)=626` batches), `max_iters=None`, no dropped final batch; source-inner evaluation processes all 1,314 windows (`165` batches) after every epoch. Fixed seed `20260927` applies to trainer DataLoader/random initialization. Keep default augmentation and all public model/trainer source unchanged.
- One A100, two DataLoader workers, no data parallelism, math-only SDPA across the entire `trainer.train()` call. Fixed architecture `[32,64,128]`, 32 output channels, downsample `(1,4,4)`, window size 2, LR `1e-4`, detection loss weight `1.0`, negative weight `0.01`, pooling radius 5.0 µm, no pretrained weights.
- The unmodified public trainer saves `edge_predictor_best.pth` when source-inner `accuracy × recall` is greater **or equal** to prior best. Ties select the latest epoch. Record all 50 training/validation rows, exact per-epoch window and batch counts, selected epoch/score, final checkpoint and architecture SHA256, and public predictor CPU load/finite-state check. Stop if any count, metric or artifact fails.
- No early stopping, retuning, outer-label feedback, resume from a partial checkpoint, or retry under the same run identity. A timeout/failure remains a failed attempt and requires an explicit new registration.

## Resources and fair queue

The v3 16-batch pilot took 9.2 seconds for train batches and 49.1 seconds for full inner validation. Linear lower estimate is about 5.7 A100 hours for 50 epochs, excluding preload/checkpoints/system overhead; expected **6–9 A100 hours**. Reserve at most one A100 with 8 CPU, 32 GiB RAM and 8 GiB disk growth; hard child runtime cap **32,400 seconds (9 hours)** and lease duration **555 minutes (9 hours 15 minutes)** including release margin. A job that cannot finish 50 full epochs inside the cap fails the fixed experiment. Check queue and physical GPU immediately before reservation. Do not request while another project is waiting, preempt anyone, hold multiple Biohub training leases, or automatically requeue. A short CPU-only staged-code smoke is allowed only after exact stage hash readback; it cannot train or read labels.

## Quality and later one-movie gate

Technical success requires exit 0 without timeout, 50 complete epochs, every exact fit/inner window count, 71/71 source IDs loaded, zero `6bba` IDs and denied accesses, finite metrics, a best checkpoint compatible with the public predictor, pinned source/bundle/config hashes, no surviving process/GPU PID, and RELEASED lease. **Quality gate for considering outer inference:** selected source-inner `accuracy × recall >= 0.80`, source-inner `recall >= 0.80`, and `accuracy >= 0.97`. These thresholds are fixed before training and are source-inner diagnostics, not honest outer scores. A failure stops the one-movie follow-up; a pass authorizes review of a separate inference preregistration, not automatic target access or a competition POST.

Only after full training and independent verification, the preselected outer movie is **`6bba_32db13fc`**, chosen by the minimum SHA256 of the ID string among all 128 sealed target IDs, as fixed in `work/x138_loeo_fold0_proof/plan.json` SHA256 `c2504ffccc3d1b4eb2f0ca55a88dc12af0ed0e408277c7654839d57ce400afb7`. A new source-only checkpoint would require its own immutable predictor plan and graph lock; do not reuse the v3 16-update checkpoint as a quality candidate. A single movie is directional evidence only. Honest local OOF 0.9+ and PRIVATE_ROBUST promotion require reciprocal embryo directions and held-out provenance for **every** active learned component, fixed graph policy and paired current-organizer scores.

## Stop boundary

Implement and locally test a new sealed bundle, stage/launch/monitor controller and independent read-only verifier under this identity. Do **not** execute remote stage or launch, obtain a GPU lease, access a target `.geff`, push a Kaggle notebook, or submit to the competition as part of this preparation.
