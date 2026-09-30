# Comparable CV protocol — 2026-09-21 user follow-up

User asks actual comparable physical baseline and Horaz0 local validation, and delegates difficult analysis to Grok. Exact Grok session e846074e-a315-4d7a-a10d-6667c57186bd resumed through cursor-delegate; model confirmed Cursor Grok4.6 ExtraHigh, result work/cursor/biohub_comparable_cv_20260921/result.md, status completed.

## Accepted protocol

Use the immutable EXP214/EXP222175 cohort (59 movies44b6,116movies6bba), exact official scorer/config and pooled aggregation, with paired per-embryo/node/edge/division statistics. Author Horaz199claim is not directly comparable. Classical has no learned weights: fixed-rule heldout development benchmark is a more accurate label than trained OOF. Do not rerun completed inference absent an artifact failure.

Horaz has two preregistered arms selected50/20 and fixed-last50, same selected-source decoder/config. Target44b6 only fold0 trained6bba; target6bba only fold1 trained44b6. No complementary-fold ensemble. Verify immutable SHA, negative routing tests, no-label runner, atomic per-movie outputs, hashes, graph invariants, fixed manifest, valid resume. Corrupt outputs cause an explicit failure, not silent replacement. Both arms must finish and pass gates BEFORE any target scorer. Remote representative source benchmark<=900s before choosing chunks<=3h, fresh leases and remote process supervision.

## Corrections to worker advice

Grok's pseudocode scored the first arm before completing the second: rejected; BOTH-arm gate retained. Its proposed new primary fixed-last label is not adopted retroactively. Fixed-last reduces epoch selection dependence but does not eliminate recipe/postprocessing selection bias. Its claim that classical is development-adapted only after embryo routing is too narrow: historical parameter/research choices and repeated cohort use already matter. Exact repeated GPU CSV hashes are not imposed without a deterministic execution contract; a repeated expensive benchmark is not automatically required. Runtime extrapolation must account for volume and graph complexity, not only movie count.

## Interpretation

EXP2140.742729 and EXP2220.740979 are comparable development measurements, not proof of independent generalization. Horaz official175 will become numerically comparable only after full routing/scorer/artifact gates. Two embryos do not support a reliable independent-embryo confidence interval. Selected-versus-last differences are descriptive evidence of checkpoint dependence; they do not alone quantify all selection optimism. No individual embryo model router, target-driven tuning, training extension or Kaggle POST is authorized by this comparison.
