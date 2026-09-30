# EXP234 source-only detector threshold calibration — 2026-09-26

Parent for the honest frontier is EXP209 (`0.6815218333` official pooled OOF175). EXP214 gapfix90 (`0.7427291486`) is a stronger development-adapted reciprocal comparator but its graph policy was developed using these embryo domains. Horaz selected50/20 (`0.7949879415`) uses target-selected epochs and is not an honest comparator.

## Frozen hypothesis and scope

The weak 44b6→6bba direction suffers from missed endpoints. Lowering the COMPACT47 detector threshold may recover true cells, but may also increase false detections and graph errors. Compare exactly `0.900`, `0.940`, and the original `0.965` with the same clean EXP214 primary90, secondary60, DeepCenter source-fold weights and unchanged public graph. No new model training, graph tuning, Kaggle run, or submission is part of EXP234.

Selection uses only source-embryo validation movies excluded from detector gradient training. For 44b6 use its eight frozen source-validation movies. For 6bba use its thirteen frozen source-validation movies **minus** `6bba_05b6850b` and `6bba_062c8d37`, which the source DeepCenter training split saw; eleven remain. Verify all actual training splits and checkpoint hashes before inference. For each direction, run all three threshold arms and hash every graph before opening any source-validation labels. Select the highest official aggregate source-validation score; exact ties choose original `0.965`, then `0.940`, then `0.900`. Report node recall, edge TP/FP/FN, divisions, and per-movie signs; source scores are selection evidence, not OOF.

After both thresholds are frozen, infer all reciprocal 175 target movies without target-label access. Reuse the official scorer only after complete no-label coverage, exact source/weight/hash verification, graph checks and a baseline replay gate. Report both embryo directions and pooled score against EXP209 and EXP214, paired movie diagnostics, and failures. These target labels have been opened by historical development; this is a leakage-controlled prospective follow-up on a development cohort, not a pristine independent test. A target-movie pilot must never select the threshold.

Compute: two bounded A100 source-selection jobs, one per direction, each at most three hours with eight CPU cores and 64 GiB RAM; source44 starts first. Each run is immutable and releases its lease only after verified process/GPU exit. No automatic target rollout or threshold sweep beyond the three frozen arms.
