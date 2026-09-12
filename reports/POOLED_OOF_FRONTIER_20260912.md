# Honest pooled OOF frontier — 2026-09-12

The primary comparison is now the untouched, reciprocal embryo-held-out
EXP192 cohort of 175 movies. Earlier 24-movie development scores remain useful
for hypothesis generation but are not mixed into this ranking.

## Current frontier

| Rank | Policy | Pooled OOF | Delta vs raw base | Robustness decision |
| ---: | --- | ---: | ---: | --- |
| 1 | **EXP209 forward centroid `(3,5,5)` + EXP191 reverse** | **`0.6815218333`** | **`+0.0712649257`** | **promoted; vs EXP206 CI `[+0.0014898,+0.0046281]`, min LOMO `+0.0028974`** |
| 2 | EXP209 forward centroid `(3,5,5)` + EXP195 reverse | `0.6812194523` | `+0.0709625447` | confirmed vs EXP206; CI `[+0.0012164,+0.0042957]` |
| 3 | EXP209 both source-selected centroid directions | `0.6802263871` | `+0.0699694796` | pooled gain passes narrowly; reverse regresses `-0.0063926` |
| 4 | EXP206 centroid forward + EXP195 reverse | `0.6784542971` | `+0.0681973895` | previous promoted frontier |
| 5 | EXP202 flow forward + EXP195 reverse | `0.6745779981` | `+0.0643210905` | not promoted; incremental CI crosses zero |
| 6 | EXP191 gap-pruned reverse | `0.6742747999` | `+0.0640178924` | credible alternative reverse arm; `+0.0003014` vs EXP195 |
| 7 | EXP195 frozen composition | `0.6739734043` | `+0.0637164967` | confirmed parent |
| 8 | EXP201 local flow | `0.6730398381` | `+0.0627829306` | not promoted; reverse regresses and CI crosses zero |
| 9 | EXP190 short-track filtering | `0.6725934215` | `+0.0623365139` | confirmed base mechanism |

Raw common base: `0.6102569076`.

## Decision policy

The next candidate must improve the EXP209 frontier on an embryo-aware source-selected
or otherwise leakage-controlled protocol. Directional score, paired bootstrap,
leave-one-movie-out, per-movie signs, edge/adjusted-edge, node recall/count and
division counts are mandatory diagnostics. A pooled gain may remain valuable
despite one weaker direction, but promotion over EXP206 requires credible
evidence that the gain is not concentrated in a few movies or created by
post-selection on the evaluation cohort. EXP209's promoted composition is the
new comparison parent at `0.6815218333`.

EXP209 evaluated all eight selected-centroid chunks behind one exact no-metric
coverage gate. Forward radius `(3,5,5)` transfers across 116 confirmation
movies and adds `+0.0032449` relative to EXP206's forward arm. The selected
reverse centroid radius regresses, but the preregistered composition with the
independent EXP191 reverse gap-plus-pruning arm reaches `0.6815218333`, adds
`+0.0030675` over EXP206, and has positive paired bootstrap and LOMO evidence.
This composition is promoted without retuning on the confirmation cohort.

EXP208 completed its source-selected 24-movie development evaluation. Radius
`(3,5,5)` was selected for forward and `(2,3,3)` for reverse. Together they
score `0.7562142111` versus translation `0.7485183131`, delta
`+0.0076958981`, bootstrap 95% interval
`[+0.0022073780,+0.0131181900]`, and minimum LOMO `+0.0065376408`.
Forward improves `+0.0097296089`, while reverse regresses `-0.0010606069`.
The original run stopped after target generation because an added node-count
invariance assertion was invalid for re-linking followed by component pruning;
the already frozen outputs were assembled without rerunning inference and the
failure remains explicitly recorded. This is promising development evidence,
not a new 175-movie frontier.

No new GPU run or Kaggle submission is implied by this snapshot.

## Rejected adaptive gate

EXP210 froze a physically motivated safety veto on 12 development movies:
fall back to translation when centroid re-linking increases removed nodes by
more than `0.5%` of raw candidates. On the 116 confirmation forward movies it
vetoed three cases, but two of those had large positive centroid effects. The
result falls to `0.6782048153`, or `-0.0002494818` versus EXP206; every LOMO
delta is negative. Added pruning is therefore not a reliable damage proxy, and
this gate is rejected rather than retuned on confirmation data.

Detailed evidence: `reports/EXP192_UNTOUCHED_POOLED_OOF_RESULT_20260912.md`
and `reports/EXP209_SELECTED_CENTROID_CONFIRMATION_RESULT_20260912.md`.
