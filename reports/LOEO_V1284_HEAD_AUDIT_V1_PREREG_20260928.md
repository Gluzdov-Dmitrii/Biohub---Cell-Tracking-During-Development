# V1284 source-only head independent audit v1 — preregistration

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC), before any fold head
training or audit implementation. Status: **protocol only**. No fold head,
source GEFF read, outer graph or OOF score exists at this point.

## Input and scope

Audit one fold's output of the fixed `head_refit.py` (SHA256
`acc24bf0ac2e8dba019d907acf3c92b0652124243b645f8b79c6606a0f198d02`)
against the independently completed same-fold V1284 capture receipt, exact
split file, source-only capture shards, exact source GEFF view, training report
and head checkpoint. Fold 0 source is exactly 71 `44b6` embryos (56 fit/15
inner); fold 1 source is exactly 128 `6bba` embryos (102 fit/26 inner). The
opposite fold is outer and must not occur in any training/capture/label path.
Require the capture receipt to pass its separate frame/shard/runtime audit,
including fold-matched primary and secondary parent hashes. Do not accept
self-declared `PASS` strings as proof of source-only lineage.

The auditor is read-only until every input check and recomputation succeeds.
It writes one new immutable pass/fail/inconclusive receipt, with input paths,
byte SHA256, fold/ID sets, source parent hashes, result and all comparisons.
Missing or transiently unreadable inputs are INCONCLUSIVE and must not become
an immutable failure. Never overwrite an existing terminal receipt.

## Independent checks

1. Rehash code, split, capture receipt, every capture shard, training report,
   checkpoint, and source GEFF aliases; verify each alias resolves inside the
   approved official source-label parent with the exact stem. Refuse extra or
   missing source IDs, outer IDs, unsafe links, or changed capture bytes.
2. Check checkpoint schema and finite tensors for the exact 224→32→3 SiLU
   head and 224-element mean/scale. Require matching fold, split hash,
   capture-receipt hash and selected epoch in checkpoint/report. Require
   selected epoch to be the earliest argmin of the complete 80-epoch finite
   source-inner history. Verify checkpoint SHA against the report.
3. Independently reconstruct the source-inner greedy 5 µm one-to-one matches
   from capture coordinates and source GEFF nodes, with native `(z,y,x)`
   divided by `(1,4,4)` and voxel spacing `(1.625,1.625,1.625)` µm. Recompute
   fit and inner match counts. Load the stored head and mean/scale on CPU,
   apply the exact bounded displacement, and recompute pooled and per-movie
   before/after mean and p95 localization errors. Compare to the report with
   a fixed numerical tolerance of `1e-5` µm for means and `1e-4` µm for p95.
4. Independently evaluate the preregistered promotion gate: pooled mean
   improvement at least 0.05 µm and 3%, plus improvement in at least 60% of
   source-inner movies. A failed gate preserves the model as a rejected
   diagnostic; only a passing gate with all checks allows an audited head
   artifact for the matching fold.

The audit does **not** prove the 80-epoch training run was replayed byte for
byte; it verifies lineage, selected state, and the actual reported source-inner
performance. It does not read an outer GEFF or claim an outer OOF gain. The
assembled-x138 source builder must require this independent role-specific
audit and exact head hash before emission, then lock image-only outer graphs
before any separate outer scoring.

## Implementation boundary

Implement a separate local auditor and synthetic tests, without modifying
`head_refit.py` or the sealed capture package. Tests must cover hash/parent/
fold failures, missing and extra IDs, malformed or NaN checkpoint, wrong
selected epoch, metric/gate mismatch, no outer GEFF access, and no immutable
receipt for transient input failures. Do not SSH, stage, reserve GPU, train a
head, read real GEFF labels, mutate Kaggle, or edit `EXPERIMENTS.md` during
implementation. Future real invocation requires the capture to finish and
pass its own independent verifier first.
