# Private-first local validation protocol

## Objective

Optimize expected post-close private leaderboard performance. The public
leaderboard is only a hidden-runtime and gross-regression check. It must not
override embryo-disjoint local evidence, and the actual private score is not
observable before competition close.

## Unit of separation

Split by embryo identity, never by random movie. Movies from one embryo share
appearance, density, motion and acquisition characteristics; random movie CV
therefore leaks domain identity and understates deployment shift. With the two
official training embryos, always report both reciprocal directions:

1. train/checkpoint-select on `44b6`, evaluate on `6bba`;
2. train/checkpoint-select on `6bba`, evaluate on `44b6`.

Inside each source embryo, keep checkpoint-selection movies separate from
gradient training. Inside each target embryo, freeze a development subset and
an unopened audit subset before model training. Do not retune threshold,
linker, ensemble weight or postprocessing after opening the audit.

## Data-integrity gate

- Build the file list from the live official Kaggle manifest.
- Reject duplicate, absolute, traversal or non-`train/` manifest paths; verify
  every relative path and exact byte count before use.
- Require, per movie, 102 Zarr files and 21 GEFF files in this competition
  snapshot.
- Parse every `zarr.json` and require valid Zarr v3 array/group metadata.
- For final reciprocal runs, compute a per-movie SHA-256 tree digest binding
  relative names, declared sizes and file bytes. The official manifest does
  not publish content hashes, so this digest proves identity across our local
  and remote copies, not identity to an independently published official hash.
- Record split JSON and SHA-256 before training.
- Reject missing/duplicate movies, source/target embryo overlap, unexpected
  dataset IDs, failed metric rows, non-finite values and changed checkpoint
  hashes.
- Downloading and byte-validating locked files is allowed; reading their
  images, labels or scores before the gate is not.

## Exact local metric

Use the checked competition implementation in `biohub_tracking.metrics`.
Centroid matching uses physical voxel scale and a 7 µm maximum distance.
For each movie, compute edge TP/FP/FN, division TP/FP/FN, predicted-node count,
node recall and:

`J_adj = max(0, edge_Jaccard * (1 - 0.1 * node_count_error_ratio))`.

Aggregate `J_adj` by edge-denominator weight (`TP + FP + FN`), not by a plain
movie average. Micro-average division counts and add
`0.1 * division_Jaccard`. When an evaluated subset contains no division event,
the division term is absent; explicitly state that the result supplies no
division-quality evidence.

The downstream promotion gate must not trust a stored aggregate blindly. It
recomputes edge Jaccard, adjusted weighted score, division counts/term and mean
node recall from the saved per-movie TP/FP/FN sufficient statistics, then
requires agreement with the stored summary to absolute tolerance `1e-12`.

## Model-comparison gate

For every candidate and parent, use identical movies and frozen inference
settings. Preserve per-movie sufficient statistics, not only the aggregate.
Report:

- score in each embryo direction and pooled sufficient-statistic score;
- worst embryo fold and embryo-fold gap;
- paired per-movie deltas and sign count;
- node recall and division TP/FP/FN regressions;
- seed-to-seed direction when training contains nondeterministic CUDA ops;
- checkpoint, source, split and result hashes.

A candidate may open locked audit only when its mechanism-level delta is
nonnegative in both reciprocal development directions and positive pooled,
without a material node-recall or division regression. A small delta must also
repeat under a second seed. Locked audit is evaluated once after all choices
are frozen.

After a locked audit has been opened, it is permanently consumed. A later
mechanism may still be frozen before its own first evaluation on those movies
and reported as a prospective candidate-specific full-OOF test, but it must not
be renamed an untouched audit. Such follow-ups are suitable for mechanism
diagnosis and community documentation; a PRIVATE_ROBUST claim needs fresh
evidence such as nested source-embryo folds, a new independent domain, or a
separately preserved audit set.

## Uncertainty language

Bootstrap movies within embryo to quantify finite-movie sensitivity, and use a
stratified bootstrap when pooling. This interval is conditional on the two
observed embryo domains. With only two embryos it is not a population
confidence interval for unseen embryos and must not be advertised as one.
Treat the worst reciprocal fold as more decision-relevant than a narrow random
movie-CV interval.

Also report leave-one-movie-out influence for the pooled paired delta. A model
whose sign flips after omitting one movie is fragile even when its nominal
bootstrap interval is positive.

## Kaggle submission gate

Only a frozen candidate that passes the local gate may enter a clean,
Internet-off Kaggle version. It must dynamically discover and infer from the
runtime competition test set, produce exactly one root `submission.csv`, pass
schema/types/finiteness/dataset-ID/graph-degree checks, and be submitted only
through `scripts/submit_code_file_once.py` with a full receipt. Five available
daily slots are a ceiling, not a target.
