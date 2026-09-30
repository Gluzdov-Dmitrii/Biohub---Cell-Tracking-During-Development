# Community pooled-OOF update R2 — 2026-09-12

## Question

Is there a public numerical pooled OOF result for Biohub Cell Tracking that is
comparable with our honest reciprocal embryo-level 175-movie protocol?

## New evidence

The Kaggle discussion *Stuck at 0.928* contains the most relevant numerical CV
claim found in this refresh. The author reports approximately `0.919 CV` and
`0.895` leaderboard score for their own edge algorithms. The post does not
define the movie cohort, embryo split, checkpoint selection, pooling formula,
node detector, or whether the official full-graph metric was pooled over all
movies. It is therefore not a comparable pooled OOF benchmark.

In the same discussion, a leading participant recommends validating complete
movies with the official scorer and movie-level OOF splits, warning that
edge-level random CV can be highly misleading. They also recommend separating
missed edges caused by absent endpoint nodes from incorrect associations. This
is methodologically consistent with our embryo-aware reciprocal protocol and
with our node-recall versus association diagnostics.

Another discussion reports a local full-CSV round-trip score of `0.5735` for a
small Cellpose-plus-Hungarian example, but it is not an embryo-held-out pooled
cohort and therefore is also not comparable. Its later diagnosis that temporal
subsampling created non-consecutive edges is a deployment validity warning,
not OOF evidence.

Sources:

- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/737101
- https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/discussion/728613

## Comparison decision

No public claim found in this refresh provides all of: embryo-held-out model
selection, complete-movie official scoring, the 175-movie cohort, and the same
pooled aggregation. We therefore retain `0.6815218332750073` from EXP209 as
our reproducible internal frontier and do not rank it numerically against the
reported `0.919 CV`.

The actionable external guidance is already represented in our protocol:

1. preserve complete movies as the evaluation unit;
2. hold out embryos rather than random edges;
3. report pooled score together with direction and per-movie stability;
4. diagnose endpoint-node misses separately from association errors.

No Kaggle submission or external artifact import was performed for this
review.
