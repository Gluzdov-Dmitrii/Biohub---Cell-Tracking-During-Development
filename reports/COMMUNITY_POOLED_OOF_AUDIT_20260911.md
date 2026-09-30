# Community pooled-OOF audit — 2026-09-11

## Conclusion

The indexed Biohub discussions do **not** currently provide a numerical pooled
OOF benchmark that is demonstrably comparable with our reciprocal embryo-held-
out protocol. The most useful public evidence supports the protocol rather than
a target number: leave-one-embryo-out model selection, large movie-level
dispersion, leakage in public all-train weights, and a public LB that may be
materially more optimistic than a true holdout.

Therefore `0.7511992447` (EXP195, supported exploratory) and the forthcoming
175-movie EXP192 confirmation must not be described as above/below “community
OOF”. Until another participant publishes sufficient statistics or an exact
aggregation recipe, the honest comparison target is internal paired evidence:
pooled sufficient statistics on identical movies, both embryo directions,
bootstrap/LOMO stability, and an untouched cohort.

## Attributed claims and comparability

| Source | Public claim | What is specified | Comparability decision |
| --- | --- | --- | --- |
| [Does CV match LB?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/730160) | Mendrika Ramarlina reports public LB almost 10% more optimistic, movie variability about ±0.14, CV 18%, range 0.460–0.984; later says leave-one-embryo-out is used for model selection. | Split family and per-movie spread, but no pooled score, model/data membership, sufficient statistics, or exact aggregation. | Directionally relevant, not a numerical benchmark. It strengthens embryo-level and pooled-over-movies reporting. |
| [Does CV match LB?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/730160) | Adarsh and Mark_RowSet warn that public weights were trained on all annotated videos; Mark reports a local `+0.0184` ablation whose LB sign reversed (`0.912` baseline to `0.909`). | Concrete leakage mechanism and one failed transfer example. | Supports rejecting scores from public all-train weights as honest OOF. It does not identify an honest pooled frontier. |
| [What layer did gains come from?](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737543) | Tang, shown as 3rd at crawl time, recommends the order detection → linking → division and says gains came from all three. | Mechanism ordering only; no CV protocol or OOF number. | Useful prioritization after EXP192 attribution; not metric evidence. |
| [How much points are you guys getting](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/734192) | Participants distinguish adjusted edge score from `0.1 × division_jaccard`; one reports public edge `0.898` and weighted division contribution `0.03`. | Public-LB ablation, not local OOF. | Useful metric interpretation only. Do not compare these components to local pooled OOF. |
| [Division Jaccard](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737577) | Jawad Ahmed reports scratch-model division Jaccard staying near zero because false divisions dominate. | One development path; no embryo-disjoint pooled protocol. | Supports retaining division diagnostics and avoiding weight-only sweeps; not a benchmark. |
| [The linking radius is 8.4 µm](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/733973) | Luka Duvanov reports p99 frame-to-frame displacement `8.38 µm`, voxel scale `1.625 × 0.40625 × 0.40625 µm`, and recommends stored `0.1%/99.9%` intensity quantiles. | Descriptive statistics over 199 train movies, not an embryo-held-out model score. | Already represented: our inference reads stored `0.001/0.999` quantiles and all registered/local-flow linkers work in physical units. Our `7 µm` gate applies after global-motion compensation, so it is not directly contradicted by the raw-displacement p99. No duplicate arm is admitted. |

Participant ranks and claims are time-dependent, self-reported and not
independently reproduced here. The URLs above are primary discussion sources;
the table deliberately does not convert their public scores, per-movie ranges,
or relative deltas into a synthetic pooled OOF estimate.

## Operational consequences

1. Keep pooled sufficient-statistic aggregation as the primary score; never
   average movie scores and call that pooled OOF.
2. Always report both embryo directions and movie-level dispersion because a
   pooled gain can hide direction asymmetry (already observed in EXP205).
3. Use only checkpoints whose held-out movies were excluded from training for
   honest OOF. Public all-train weights remain attribution/inference references.
4. Treat the untouched 175-movie EXP192 run as the current decisive calibration
   of effect size and stability, not as another parameter-selection surface.
5. After EXP192, prioritize the error layer supported by its diagnostics;
   community advice suggests detection first, then linking, then division, but
   our paired evidence decides whether that ordering applies here.
6. Do not create an `8.4 µm` sweep merely from the public descriptive result:
   it measures raw displacement, while our gate measures residual displacement
   after registration. A radius experiment would first need a source-only
   residual-distance distribution and one frozen target candidate.

## What would make a future community score comparable

A claim needs: exact train/holdout embryo membership, checkpoint provenance,
movie list, whether public twins were excluded, graph postprocessing policy,
pooled TP/FP/FN (and adjusted-edge/division components), and whether the value
was used for selection. Without these fields it remains contextual evidence.
