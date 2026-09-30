# EXP216 Next Path Decision, 15 September 2026

Current honest development-adapted frontier remains EXP214 gapfix 90/60 public
graph:

| Scope | Score |
|---|---:|
| OOF175 pooled | 0.7427291486 |
| target44b6 | 0.8052068737 |
| target6bba | 0.7318060132 |
| 90/60 local graph | 0.7132851518 |

## External Inspiration Checked

- Kaggle discussion "Stuck at 0.928": Soheil Ayati recommends decomposing
  missed edges into missing endpoint nodes versus wrong associations and using
  complete-movie official scoring rather than random CV.
- Kaggle discussion "what layer did ur gains actually come from": Tang frames
  the order as detection, then linking, then division.
- Kaggle discussion "focus3d": hengck23 suggests dense Focus3D-style labels,
  offset heads, augmented frame-pair linker training, and longer-window
  transformer/SuperGlue-like linking as the credible higher-ceiling direction.
- Kaggle notebook "Biohub 0.942 LB, one knob past the public line": the public
  gain came from tiny detector threshold/edge-weight knobs, but its local
  four-movie validator moved opposite LB, so proxy-only Optuna is weak evidence.

## Local Evidence

EXP214 gapfix already shows the measured bottleneck:

- 90/60 public minus 60/60 public: `+0.0065772136`.
- 90/60 local minus 60/60 local: `+0.0009412147`, confidence interval crosses
  zero.
- The useful gain is concentrated in source44b6 -> target6bba.
- Worst target6bba movies are detection-heavy failures by recorded node recall:
  `6bba_6feb10f0` has node recall `0.1937`, `6bba_ab78413d` `0.3936`,
  `6bba_474be664` `0.5103`.

EXP215 tests the best remaining "more epochs" version of this idea: full-cache
source44b6 seed2026 continuation. p03 reached epoch57 and nudged source
selection from `0.9457744601` to `0.9458208348`; p04 is now running only to
reach the preregistered `>=60` epoch gate.

## Decision

Do not start broad Optuna, bigger layers, or wider hidden dimensions next.
Those are expensive and currently under-identified. The best next path is:

1. Finish EXP215 full-source44 to `>=60` epochs and freeze the best source-only
   checkpoint if the receipts remain clean.
2. Run EXP216 final-graph failure attribution on the frozen EXP214 gapfix
   submission CSVs to quantify endpoint-limited versus association-limited edge
   FN on all 175 movies.
3. If endpoint-limited FN dominates, prioritize detector/data processing:
   dense pseudo-labels, Focus3D-style detector distillation, count/threshold
   calibration, and hard movie targeted augmentation.
4. If association-limited FN dominates, prioritize linker work:
   longer temporal window, physical-motion transformer/SuperGlue-style matching,
   or calibrated edge replacement. Division remains secondary until ordinary
   edge attribution improves.

The immediate compute path is therefore detector/data evidence first, not a
parameter sweep.
