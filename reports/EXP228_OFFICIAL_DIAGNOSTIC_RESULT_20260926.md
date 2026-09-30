# EXP228 Horaz 0.5/0.5 snapshot ensemble — 2026-09-26

All eight Quadro chunks passed exit, lease-release, exact-plan, CSV hash and graph audits (116/116 new 6bba graphs). The official scorer gated these plus 175 pinned reference graphs before labels, replayed the original EXP223 rows and aggregate to `1e-12`, and finished exit 0. Result SHA256: `9b9639d6e3d8acc4276080f5f8dd0329fa63108aec258277086ca556956a885d`; no-metric gate SHA256: `9f65d2ad1584a4fef427668bd0cb1cd0fb2c7f93a3b1fea2ed833ad819988295`. Compact verification receipt: `reports/exp228_official_score175_20260926.json`.

| Official score | Selected50/20 reference | 0.5/0.5 ensemble | Delta |
| --- | ---: | ---: | ---: |
| Pooled 175 | 0.7949879415 | 0.7759164900 | −0.0190714514 |
| Held-out 44b6, 59 movies | 0.8367193999 | 0.8367193999 | 0 (byte-identical reference graphs) |
| Held-out 6bba, 116 movies | 0.7873724522 | 0.7648776209 | −0.0224948313 |

For the 116 newly inferred 6bba movies, paired adjusted-edge score improved in 34 and worsened in 82. Its aggregate node recall fell from `0.9078215392` to `0.8898553616`; adjusted-edge Jaccard fell from `0.7820033247` to `0.7606818167`. Reject the fixed equal-weight ensemble. Do not retune its mixture on these target labels.

Both ensemble checkpoints inherit the historical selected-epoch bias. This is a development diagnostic and is not honest OOF or private-validation evidence. No Kaggle submission was made.
