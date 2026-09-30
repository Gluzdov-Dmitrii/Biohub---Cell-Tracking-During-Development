# x138 assembled reciprocal embryo inference v1: local preregistration

Date: 2026-09-28 (Asia/Novosibirsk). Status: **preregistered source design only; no runnable candidate or OOF result**.

## Fixed question and population

Measure the frozen x138 assembled inference policy on the reciprocal 199-embryo split. Fold 0 trains only on the 44b6 source embryos and infers on the 128 6bba outer embryos. Fold 1 trains only on the 6bba source embryos and infers on the 71 44b6 outer embryos. An embryo ID occurs in exactly one outer fold. The outer view contains runtime images and metadata needed to enumerate frames, never outer GEFF labels. The historical development of x138 and this split involved target-label exposure; this reciprocal result must be described as source-only reciprocal OOF, not an untouched prospective holdout.

ID authority is `work/x138_loeo_bootstrap/split_receipt.json`, SHA-256 `26a9324c0a9556708ffa2bf0f1e230f842c0ef1581ac22d19af28fd15b7ba142`; its `outer_target_ids_sealed` lists contain 128 and 71 IDs. The source-inner trainer split SHA-256 recorded there is `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.

## Frozen source and graph policy

Base is `work/x138_original/source.py`, SHA-256 `eace83c4e4ec8f967aa03edf516acdbb3eb35bbcfaf02fbef93465fa26680775`. Preserve its primary and secondary temporal model architecture, detector thresholds, association, motion/gap/division and DeepCenter add-only veto policy, V1284 refinement logic, graph filter, and output writer. No score-guided tuning, fold-specific threshold change, graph policy change, test-time training, fallback to published weights, or ensemble substitution is allowed. The only output-coordinate policy correction is the x162 final writer bound: after rounding, clamp each coordinate to `[0, runtime Zarr axis length - 1]` with time/axis validity checks, following `work/lb_pair_20260927/x162_submission_source_v1.py`, SHA-256 `d761174044943f68f0bf0501c8691ab496b28611779a5a232d13ba27e01c0c51`. Record nonzero clamp counts for audit. This correction must not alter pre-writer graph decisions.

Deadline degradation and graph-repair fallback are **acceptance failures**. If the deadline branch would disable motion, gap, division, or line fit, or graph filtering raises and would invoke `fallback_output_graph`, stop the fold with an explicit failure receipt. Do not accept a graph or score from either branch. The nominal x138 path is the only accepted policy.

## Required fold-matched assets and lineage

For each fold, require all four real source-trained artifacts before assembly or remote execution: (1) primary UNet/transformer checkpoint, (2) secondary temporal checkpoint, (3) V1284 coordinate head trained from the same fold's source-only capture, and (4) DeepCenter selected-epoch checkpoint. Every artifact needs its exact byte SHA-256, fold/source/outer identities, source-only training or capture receipt and SHA-256, independent terminal audit receipt and SHA-256, and selected epoch where applicable. The V1284 capture must identify the fold-matched primary and secondary parent checkpoint hashes. The DeepCenter selected epoch must come from its source-inner selection receipt; do not assume the published epoch 2. All training/capture selection uses source-inner embryos only; outer images are inference-only. Reject missing, mixed-fold, mismatched-parent, published, or unaudited assets.

Pinned support source checks and Python import/inference dependency checks remain required. A source manifest must pin the assembled source hash, original x138 hash, x162 clamp source hash, four artifact hashes, audit and selection receipt hashes, split manifest hashes, image-only view hash, and chunk plan hash. No public-LB artifact or checkpoint path may resolve during reciprocal inference. The public x138 score 0.953 is historical public leaderboard evidence, not an OOF estimate.

## Runtime and acceptance contract

Process each outer fold in deterministic, disjoint batches of at most four whole embryos; do not load all 199 movies at once. Launch **one fresh child process and fresh working directory per batch** so x138 cell 0 resets `BIOHUB_KERNEL_START_TS` for that batch. Persist a per-batch completion receipt with input embryo IDs, image-view paths, exact model/source hashes, output hash, start/end/PID/exit0, and graph diagnostics. A reused process or working directory is invalid. Resume only a batch with identical manifest hashes; an incomplete batch is rerun from scratch. Merge only after every expected ID appears once, all batches independently exit0 and pass, no unsupported fallback/degradation occurred, and all graphs, coordinates, submission schema and runtime output hashes pass independent checks. The coordinator must verify actual runtime image reads, not frozen public CSV replay. The full candidate also needs measured end-to-end runtime with margin against the competition limit; chunking alone is not proof of deadline safety.

Before any outer inference: independently verify all training, capture and selection audits, exact checkpoint hashes and no-label image view; confirm the x138 base policy diff contains only the predeclared asset/view wiring, chunk orchestration, fail-closed branches and final writer clamp. After inference: inspect per-batch diagnostics, exact 199 coverage, no duplicates, source-only lineage, no deadline/repair fallback, output validity and immutable prediction hashes before reading any outer labels for scoring. Any missing receipt or transient access error is inconclusive, never an OOF PASS.

## Local implementation boundary

This preregistration authorizes a local source assembler/validator and synthetic tests only. Without the real four audited checkpoints for each fold, it must refuse final source emission and execution. No SSH, staging, queue, GPU, Kaggle mutation, target GEFF read or `EXPERIMENTS.md` edit is part of this preparation.
