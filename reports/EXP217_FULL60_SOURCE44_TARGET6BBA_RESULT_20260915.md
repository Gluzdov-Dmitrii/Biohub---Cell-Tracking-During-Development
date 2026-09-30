# EXP217 Full60 Source44 Target6bba Result, 15 September 2026

EXP217 tested the EXP215 full-cache source44b6 checkpoint as the primary model
only on the weak target6bba side. All five new paired target6bba shards finished
with `PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS` and verified queue release
before the CPU scorer opened target labels. The target44b6 side was reused from
the frozen EXP214 gapfix90 baseline to isolate this one model change. No Kaggle
POST was made.

Result: reject the "more full-source44 epochs" path for this model family.

| Arm | Full175 Score | target6bba | target44b6 |
|---|---:|---:|---:|
| EXP214 gapfix90 public baseline | `0.7427291486` | `0.7318060132` | `0.8052068737` |
| EXP217 full60 source44 public candidate | `0.7368554865` | `0.7248658383` | `0.8052068737` |
| EXP214 gapfix90 local baseline | `0.7132851518` | `0.7005062983` | `0.7868730539` |
| EXP217 full60 source44 local candidate | `0.7073277838` | `0.6935545210` | `0.7868730539` |

Paired deltas:

- Public candidate minus baseline: `-0.0058736621`, conditional movie 95%
  interval `[-0.0112080918, -0.0006684900]`.
- Local candidate minus baseline: `-0.0059573680`, conditional movie 95%
  interval `[-0.0093339693, -0.0025747375]`.

Artifacts:

- Remote/local score status:
  `outputs/research/exp217_full60_source44_target6bba_score175_20260915/status.json`
- Full comparison:
  `outputs/research/exp217_full60_source44_target6bba_score175_20260915/output/comparison.json`
- Full metrics:
  `outputs/research/exp217_full60_source44_target6bba_score175_20260915/output/full175/metrics.json`
- Prediction progress:
  `reports/exp217_full60_source44_target6bba_prediction_progress_20260915.json`

Interpretation: EXP215 improved source-selection score, but that source-only
proxy did not transfer to target6bba. The current honest development-adapted
frontier remains EXP214 gapfix90 public graph `0.7427291486246141`. The next
credible local path should not be additional source44 epoch continuation; it
should move to detector/data processing or Focus3D-style dense-label/pseudo-label
routes, guided by endpoint-versus-association failure attribution.
