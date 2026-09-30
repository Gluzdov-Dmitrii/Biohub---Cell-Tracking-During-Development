# EXP218 Conservative Short-Track Rescue Result 2026-09-15

## Summary

EXP218 tested a narrow data/postprocess path after EXP216 showed that the
current frontier is still dominated by endpoint-limited edge false negatives,
especially on target6bba. The candidate enabled the existing adaptive
short-track rescue only for the source44b6 -> target6bba public graph shards,
with conservative caps:

- `BIOHUB_ADAPTIVE_SHORT_TRACK_RESCUE=1`
- `BIOHUB_SHORT_TRACK_RESCUE_MIN_LEN=4`
- `BIOHUB_SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB=0.88`
- `BIOHUB_SHORT_TRACK_RESCUE_MAX_MEAN_EDGE_DIST_UM=3.0`
- `BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_FRAC=0.012`
- `BIOHUB_SHORT_TRACK_RESCUE_MAX_NODES_ABS=120`

The result is a clean neutral outcome, not an improvement. The candidate tied
the EXP214 gapfix90 public baseline exactly on the preregistered paired-175
local scorer.

## Scores

| arm | full175 score | target44b6 | target6bba |
| --- | ---: | ---: | ---: |
| EXP214 gapfix90 public baseline | 0.7427291486246141 | 0.8052068737218 | 0.7318060132031643 |
| EXP218 short-track rescue candidate | 0.7427291486246141 | 0.8052068737218 | 0.7318060132031643 |

Candidate-minus-baseline delta: `0.0`.

Bootstrap and leave-one-movie diagnostics were also identically neutral:
conditional movie 95% interval `[0.0, 0.0]`, resample fraction positive `0.0`,
leave-one-movie min/max delta `0.0`.

The aggregate official-style metrics were unchanged:

- edge Jaccard `0.7437858951398753`
- adjusted edge Jaccard `0.7406014890501463`
- node recall `0.9294928806005553`
- division Jaccard `0.02127659574468085`
- division TP/FP/FN `4/50/134`

## Receipts

Prediction status:
`reports/exp218_short_track_rescue_prediction_progress_20260915.json`
reported `COMPLETE_EXP218_SHORT_TRACK_RESCUE_PREDICTIONS` for all five shards
and `movies=116` before the scorer opened labels.

Metric gate:
`outputs/research/exp218_short_track_rescue_score175_20260915/output/full175/no_metric_gate.json`
reported `PASS_ALL_ARMS_COMPLETE_BEFORE_LABEL_ACCESS` over all 175 movies.

Scoring status:
`outputs/research/exp218_short_track_rescue_score175_20260915/status.json`
reported `COMPLETE_EXP218_SHORT_TRACK_RESCUE_PAIRED175_COMPARISON`.

Hash receipts:

- comparison JSON SHA256:
  `e750c5df2aa8d08480a2c858719610fe6686909f511819eb084d935f3ed7c8de`
- full175 metrics JSON SHA256:
  `fd00c871dfa747600f9c3dd48d1d47440b72a17bab03d01f6f3e403f8fbcb877`
- no-metric gate JSON SHA256:
  `288e21a2f8f4b98d31382a43b584b0fa441b54e71b57ef3df60237b215169aaa`
- scorer stdout log SHA256:
  `04255077e9cb70f923b26740331bba67f69a11762d48d6d122aa958bbcc96470`
- prediction progress JSON SHA256:
  `192c95de96545af46f9b720f77fca00ad746b9ce65dbb3f32a053a36eb263fa8`

Cluster resource state at handoff: all five EXP218 A100 leases were
`RELEASED`; the CPU scorer completed. No Kaggle POST occurred.

## Interpretation

The conservative short-track rescue did not move the honest local OOF. In the
scored manifest, only the first candidate source44b6 -> target6bba CSV hash
changed versus the matched EXP214 shard; the scorer found no metric-visible
movie deltas anywhere. This suggests the current caps either rescue no
officially matched endpoint/edge errors, or alter rows that do not affect the
official graph score.

Promotion gate failed. The active frontier remains EXP214 gapfix90 public graph
with full175 score `0.7427291486246141`.

Recommended next path: do not spend more time on this conservative short-track
rescue knob as-is, and do not return to source44 epoch continuation for this
architecture. The next useful work should inspect the changed EXP218 shard to
quantify what rows changed, then move toward detector/data improvements on the
target6bba endpoint failures highlighted by EXP216: dense-label/Focus3D-style
training data, endpoint-specific detector recall diagnostics, or a more direct
dynamic threshold/rescue mechanism with per-movie edge-FP safeguards.
