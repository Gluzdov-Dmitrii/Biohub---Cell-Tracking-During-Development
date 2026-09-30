# EXP214 gapfix rerun result, 14 September 2026

The corrected synthetic-gap endpoint occupancy rerun completed all 16 fixed
paired shards before target scoring. Every shard monitor reports
`RELEASED_AFTER_VERIFIED_EXIT`, `returncode=0`, and
`PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS`. No Kaggle POST was made.

Scoring run:
`outputs/research/exp214_gapfix_score175_20260914/`.

| Variant | OOF175 pooled | 44b6 | 6bba |
|---|---:|---:|---:|
| 90/60 public graph | **0.7427291486** | 0.8052068737 | **0.7318060132** |
| 90/60 local graph | 0.7132851518 | 0.7868730539 | 0.7005062983 |
| 60/60 public graph | 0.7361519350 | **0.8061469899** | 0.7244120509 |
| 60/60 local graph | 0.7123439370 | 0.7893336140 | 0.6990132880 |

Controlled deltas:

- 90/60 public minus 60/60 public: `+0.0065772136`,
  conditional movie 95% interval `[+0.0021434465, +0.0109861967]`.
- 90/60 local minus 60/60 local: `+0.0009412147`,
  conditional movie 95% interval `[-0.0024478945, +0.0042157157]`.
- 90/60 public minus 90/60 local: `+0.0294439969`,
  conditional movie 95% interval `[+0.0222132498, +0.0369226302]`.

The local OOF `0.8+` target is not reached. The current honest
development-adapted frontier is the 90/60 public graph at `0.7427291486`.
The useful signal from the 60-to-90 continuation is concentrated in the
source44b6 -> target6bba direction; source6bba -> target44b6 is essentially
flat/slightly lower.

Key hashes:

- `output/base60/metrics.json`:
  `f004fc45a8ce4f564830483eeb42a0be901ab5f8c462f05e6d542cdac43d33c2`
- `output/new90/metrics.json`:
  `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5`
- `output/comparison.json`:
  `cbee22e77ac6e321562a13a1be5324de267efb8b9838c4991307d1a33ad7c789`
- Resume-only coordinator patch:
  `scripts/finish_exp214_gapfix_predictions.py`
  `d725c1720c3e52ebe1172604c537259ec74db3e3f601648770970e4383478de2`

Operational note: the resumed prediction coordinator needed an
infrastructure-only resume fix for an existing claim file and transient SSH
retry. This did not alter inference code, weights, thresholds, graph policy,
target cohort, or scoring formula.
