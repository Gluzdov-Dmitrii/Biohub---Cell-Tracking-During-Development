# Comparable pooled OOF frontier — 2026-09-11

This is a retrieval snapshot, not a replacement for experiment receipts. It
lists only results on the same 24 reciprocal scratch-model target movies unless
explicitly marked otherwise. Scores from public notebooks, reused public
weights, four-movie pilots and different cohorts are not numerically mixed in.

## What is currently true

- **Highest supported exploratory frontier:** EXP195 at `0.7511992447`.
  Its increment over the fixed EXP190 `min8/min3` parent is `+0.0026809316`,
  with paired-bootstrap 95% interval `[+0.0003278713, +0.0051730762]` and
  minimum leave-one-movie-out delta `+0.0018913617`. It remains sequentially
  selected and awaits the untouched 175-movie EXP192 confirmation.
- **Highest exact development hypothesis:** EXP206's forward-only centroid
  composition at `0.7571390995`, `+0.0059398549` versus EXP195. It was chosen
  after EXP205 metrics were visible, so this is not a supported frontier until
  its already frozen 175-movie confirmation passes.
- **Highest honest nested score from the broad short-track family:** EXP190 at
  `0.7430723145`, versus `0.6761456763` unfiltered. The later fixed
  `min8/min3` parent scores `0.7485183131`; it is the common comparison parent,
  not the cross-fitted nested estimate.
- **Untouched confirmation score:** unavailable. EXP192 has no opened metric;
  data transfer/staging and all eight no-metric chunks must finish first.

## Comparable 24-movie evidence

| Experiment/policy | Pooled score | Delta/reference | Evidence grade | Status |
| --- | ---: | ---: | --- | --- |
| EXP190 nested short-track selection | `0.7430723145` | `+0.0669266382` vs unfiltered | cross-fitted nested development | retained |
| EXP190 fixed `min8/min3` | `0.7485183131` | common fixed parent | development-fixed | parent |
| EXP195 reverse q75 gate | `0.7511992447` | `+0.0026809316` vs fixed parent | sequential exploratory; positive bootstrap/LOMO | supported exploratory frontier |
| EXP200 nested local flow | `0.7498093390` | `+0.0012910259` vs fixed parent | nested, but bootstrap q025 `-0.0011955241` | not frontier |
| EXP201 fixed local flow | `0.7510028014` | `+0.0024844883` vs fixed parent | post-selected fixed diagnostic | awaiting EXP192 |
| EXP202 flow + EXP195 composition | `0.7531233749` | `+0.0019241302` vs EXP195 | post-selected composition | awaiting EXP192 |
| EXP205 centroid both directions | `0.7542973497` | `+0.0057790366` vs fixed parent | fixed mechanism but early directional exposure; reverse `-0.0007888091` | positive pooled exploratory |
| EXP206 centroid forward + EXP195 reverse | `0.7571390995` | `+0.0059398549` vs EXP195 | post-selected composition | highest hypothesis; awaiting EXP192 |
| EXP207 exact 8-view edge-feature TTA | unavailable | — | compute-matched preregistration | queued after EXP192 priority |
| EXP208 source-selected centroid radius | unavailable | — | source-only arm selection; cohort-adaptive mechanism family | queued after staging |

## Decision rule after EXP192

The primary ranking statistic is pooled score on all 175 untouched movies.
Direction deltas, per-movie signs, paired bootstrap, leave-one-movie-out,
edge/adjusted-edge counts, node recall/count and division counts must be
reported alongside it. They diagnose transfer risk but, under the corrected
objective, do not erase a genuine positive pooled result. Any policy not frozen
before the 175-movie metric is opened remains development-only and cannot be
retroactively called confirmation.

Authoritative receipts:

- `reports/exp190_extended_short_track_lengths_result_20260911.json`
- `reports/exp195_fixed_reverse_gate_result_20260911.json`
- `reports/exp200_local_flow_linker_result_20260911.json`
- `reports/exp202_composed_untouched_confirmation_preregistration_20260911.json`
- `reports/exp205_intensity_centroid_refinement_result_20260911.json`
- `reports/exp206_centroid_untouched_confirmation_preregistration_20260911.json`
- `reports/exp207_d4_feature_tta8_preregistration_20260911.json`
- `reports/exp208_source_centroid_family_preregistration_20260911.json`
