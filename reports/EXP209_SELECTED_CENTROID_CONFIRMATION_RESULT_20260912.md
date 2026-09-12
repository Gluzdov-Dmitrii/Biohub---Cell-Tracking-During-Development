# EXP209 selected-centroid confirmation — 2026-09-12

## Result

EXP209 establishes a new 175-movie reciprocal embryo-held-out pooled OOF
frontier. The strongest preregistered composition uses the source-selected
forward intensity-centroid radius `(3,5,5)` with minimum track length 8 and
the already frozen EXP191 reverse gap-plus-pruning arm:

| Policy | Pooled OOF | Delta vs EXP206 | 95% paired bootstrap CI | P(Delta > 0) | Minimum LOMO |
| --- | ---: | ---: | ---: | ---: | ---: |
| forward `(3,5,5)` + EXP191 reverse | **`0.6815218333`** | **`+0.0030675362`** | **`[+0.0014898445,+0.0046280957]`** | **`1.0000`** | **`+0.0028973690`** |
| forward `(3,5,5)` + EXP195 reverse | `0.6812194523` | `+0.0027651552` | `[+0.0012164432,+0.0042956519]` | `0.9997` | `+0.0025922127` |
| both source-selected centroid directions | `0.6802263871` | `+0.0017720901` | `[+0.0000104968,+0.0035433402]` | `0.9756` | `+0.0015911228` |

All three policies were frozen before any selected-radius metric was opened on
the 175-movie cohort. The family is development-adapted, but the exact forward
and reverse radii were selected only on the reciprocal source
checkpoint-validation movies in EXP208.

## Primary diagnostics

For the promoted composition:

- pooled score versus the raw common base is `+0.0712649257`, with paired
  bootstrap interval `[+0.0610600593,+0.0814674925]`;
- forward score is `0.6658905036`, `+0.0032449048` versus EXP206's forward arm;
- reverse score is `0.7716450342`, `+0.0020734110` versus EXP206's reverse arm;
- every leave-one-movie-out aggregate remains positive versus EXP206:
  `[+0.0028973690,+0.0033339234]`;
- 24 of 175 movies are individually below the raw base, so the policy is not
  interpreted as a universal per-movie improvement;
- pooled edge counts are TP `87,389`, FP `15,414`, FN `26,967`; edge Jaccard
  is `0.6734145026` and node recall is `0.8738311372`;
- versus EXP206 this is `+398` edge TP, `-6` edge FP, `-398` edge FN and
  `+0.0023603040` pooled node recall. The forward replacement improves 79 of
  116 movies and regresses 37; the frozen reverse gate changes only ten movies
  versus EXP195 and improves seven of them, with three regressions;
- division TP remains zero with 138 FN. EXP209 improves association and
  pruning, not the still-unsolved division mechanism.

The fully source-selected reverse centroid radius does not transfer: its
reverse contribution is `-0.0063925873` versus EXP206. Keeping the independent
EXP191 reverse mechanism is therefore both numerically stronger and more
mechanistically diverse.

## Integrity and execution

EXP209 ran CPU-only on `nsu-quadro` as PID `240346` with affinity `0-7`; no
GPU lease was used. After the parent and worker ended, all eight immutable
chunks passed `PASS_EXP209_ALL_SELECTED_CENTROID_CHUNKS_NO_METRICS` with exact
coverage of 116 forward and 59 reverse movies. Only then were the three frozen
policies assembled and their metrics opened.

The remote manifest verifies all 38 listed artifacts. The results were copied
to `outputs/research/exp209_selected_centroid_confirmation_20260912`, and the
same 38 hashes verify locally; manifest SHA-256 is
`1d9bd5c800958d9fa0d5de8982fc12afcaf6d9e776ccd995408033f1c67eff8a`.
The 1,314,935-byte result set is retained as compact reproducibility evidence.
No Kaggle action occurred.
