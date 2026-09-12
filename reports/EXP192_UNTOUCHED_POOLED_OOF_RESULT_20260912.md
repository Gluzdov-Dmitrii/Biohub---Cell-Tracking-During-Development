# EXP192 untouched 175-movie pooled OOF confirmation — 2026-09-12

## Outcome

EXP192 completed all eight preregistered inference chunks before any scientific
metric was opened. The no-metric gate passed for all `175` held-out movies
(`116` forward and `59` reverse). On this confirmation cohort, EXP206 is the
new honest pooled frontier:

| Policy | Pooled OOF | Delta vs raw base | Forward | Reverse |
| --- | ---: | ---: | ---: | ---: |
| Raw common base | `0.6102569076` | — | `0.5906673669` | `0.7313638594` |
| EXP190 short-track filtering | `0.6725934215` | `+0.0623365139` | `0.6574291671` | `0.7603365308` |
| EXP191 reverse gap prune | `0.6742747999` | `+0.0640178924` | `0.6574291671` | `0.7716450342` |
| EXP195 frozen composition | `0.6739734043` | `+0.0637164967` | `0.6574291671` | `0.7695716232` |
| EXP201 local flow | `0.6730398381` | `+0.0627829306` | `0.6581367608` | `0.7592092091` |
| EXP202 flow + EXP195 | `0.6745779981` | `+0.0643210905` | `0.6581367608` | `0.7695716232` |
| **EXP206 centroid + EXP195** | **`0.6784542971`** | **`+0.0681973895`** | **`0.6626455988`** | **`0.7695716232`** |

EXP206 improves on its frozen EXP195 parent by `+0.0044808928`. The paired
movie bootstrap gives `P(delta > 0)=0.99985` and a 95% interval of
`[+0.0021909611, +0.0067969218]`; every leave-one-movie-out estimate remains
positive, with minimum `+0.0041295077`. This is a statistically stable pooled
improvement, not merely a public-LB observation.

## Mechanism and failure modes

EXP206 changes only the forward-direction coordinate refinement to the fixed
intensity-centroid radius `(2,5,5)` and retains EXP195 in reverse. Against
EXP195 it improves `78` of `116` forward movies and worsens `38`; the mean
per-movie delta is `+0.0049959241`, with range
`[-0.0446510135, +0.0489830980]`. The effect is therefore broad but
heterogeneous.

Across the 116 forward movies, the centroid transform processed `1,552,213`
predicted nodes; its node-count contract is invariant by movie. The weighted
mean coordinate shift is `0.3450195924 um`
(movie means `0.2940936341` to `0.4477718818 um`). It reduces removed nodes
from `466327` to `463661`, a difference of `-2666`.

The strongest remaining scientific weakness is division tracking: every
confirmed policy has `0` division true positives and `138` division false
negatives. Further gains should target division or another genuinely distinct
mechanism, while retaining the centroid arm as the current pooled parent.

## Pairwise interpretation

- EXP191 is slightly stronger than EXP195 on the same cohort by
  `+0.0003013957`, almost entirely in reverse. Its bootstrap lower endpoint is
  only `+0.0000042756`, so the difference is real-looking but very small.
- EXP206 remains above EXP191 by `+0.0041794972`, with 95% interval
  `[+0.0018621721, +0.0065245347]` and positive minimum LOMO
  `+0.0038248372`, despite EXP191's stronger reverse arm.
- EXP206 remains above EXP202 by `+0.0038762990`, with 95% interval
  `[+0.0016765408, +0.0061115562]` and positive minimum LOMO
  `+0.0035852814`.
- EXP201 and EXP202 have positive pooled point estimates over their parents,
  but their paired 95% intervals cross zero. They are not promoted as robust
  frontier improvements.

## Integrity and reproducibility

The all-eight gate is `PASS_EXP192_ALL_CHUNKS_NO_METRICS`; its local SHA-256 is
`4056e558900b37113f91193ae709327496fd2b44b72a80fae9f42d8157813026`.
All six confirmation files report `PASS_FROZEN_CONFIRMATION_ASSEMBLY` and
`eligible_for_kaggle_submission=false`.

The frozen postprocessor's original `SHA256SUMS` embedded absolute paths under
the temporary directory that was later atomically renamed. Standard checking
therefore failed on paths, not bytes. The original manifest was preserved
(SHA-256 `b19d1cc90733ccc7ec6f69a01730a6547e36fe9e3f4d78f51018588aec901830`).
A separate fail-closed relocation verifier checked all `49/49` files and wrote
`SHA256SUMS_RELOCATED` (SHA-256
`2a8355232ce5ae0fd5978705d77cd7e76dfc9250b686eaebae549b33ea6a06d0`),
which independently verifies from `/`. The complete final result was exported
to `outputs/research/exp192_frozen_postprocess_20260911` and reverified locally.

No Kaggle submission was made or authorized by this confirmation run.
