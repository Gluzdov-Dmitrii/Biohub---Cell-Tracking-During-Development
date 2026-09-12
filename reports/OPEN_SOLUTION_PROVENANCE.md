# Open-solution provenance and private-first admission rules

This registry separates reproducible public code from evidence about expected
post-close private performance. A notebook title or public-LB label is not local
validation. No frozen `submission.csv` is reused: only mechanisms that can infer
from the runtime test set are eligible.

## Archived public sources

| Kaggle source | immutable local evidence | mechanisms inspected | current admission status |
|---|---|---|---|
| `qrz1201/biohub-public-0-941-repro`, v1 | source SHA `24253cae5a958b83d69e201719388031f5758080c5d01ca1a8e374f3a8225389`; extracted-code SHA `5fb5d5b17d207dd111105eef8053c513d7c4ce0f179e0a35872010467f1fbe46`; Internet off; receipt `outputs/research/frontier_20260905/sources/qrz1201__biohub-public-0-941-repro__1/source_receipt.json` | dual-seed TemporalUNet3D detection, harmonic bidirectional association, registered-motion relinking, density-aware gap close, DeepCenter veto, division guards | source is verified and attributable; the full preset is **not** private-admitted because its many public-tuned knobs lack embryo-disjoint ablation |
| `tangai1/biohub-c33-public0933-v19-fallback`, v1 | source SHA `e331890e925437ca33e41b3fdce62ae4b56518052f1ee65edb2b7f31af49d4c9`; extracted-code SHA `bd2fb1634b11a523302be9f34b4d046e1d963439ad087f2ca93aa02e2a13ed8c`; Internet off; receipt `outputs/research/frontier_20260831/tangai1__biohub-c33-public0933-v19-fallback__1/source_receipt.json` | secondary-detector fusion, harmonic bidirectional association, ILP constraints, short-track recovery and DeepCenter checks | source is verified and attributable; retained as a mechanism donor, not copied as a private-ready model |
| `pilkwang/biohub-tracking-support-pack-50ep-v1` and related model datasets | recorded as the common runtime dataset source by both receipts above; exact local support-pack implementation is preserved under `outputs/research/support_pack/repo` | TemporalUNet3D + transformer inference, graph IO/evaluation and registered-motion association | base implementation admitted only where exact runtime and OOF receipts exist |
| `reyhanksatria/biohub-cell-tracking-0-946-lb`, current public snapshot last run 2026-09-08 | source SHA `ae8e01a262211045161984e469e8be23e3386bab9140fe12df503dc6a1e010e6`; retrieval receipt under `outputs/research/open_candidates_20260909/` | inverse-transform D4 averaging of U-Net features used by the edge predictor, in addition to detector-logit TTA | exact source snapshot verified; EXP145 proved edge-feature TTA is inert under the coordinate-only registered linker (all eight development movie deltas exactly zero); full correlated public-tuned stack not admitted |
| `xiaoleilian/biohub-cell-tracking-classical-baseline`, current public source pulled 2026-09-11 | notebook SHA `ef193c8c...87e088`; metadata SHA `ebe4678a...f60439`; receipt `reports/open_classical_baseline_audit_20260911.json` | classical local-max detector, intensity centroid refinement, physical NMS, tight/full Hungarian, predecessor velocity and isolated-node pruning | full notebook not admitted: its validation is not official pooled embryo-disjoint OOF; pruning is already validated, velocity/count relatives were rejected, while centroid refinement/NMS remains a post-EXP192 detector candidate |

## Mechanisms with honest local evidence

| mechanism | embryo-disjoint evidence | decision |
|---|---|---|
| registered-motion Hungarian association | held-out `44b6` `0.744130`; held-out `6bba` `0.595767`; pooled `0.615980` | retained as robust default |
| registered motion + 10% learned ambiguity tie-break | held-out `44b6` `0.744130`; held-out `6bba` `0.596538`; pooled `0.616747` | retained as a weak, fixed mechanism; gain is too small to justify retuning |
| mutual-nearest coordinate consensus, radius 2 µm, alpha 0.5 | positive pooled deltas in two fixed comparisons, but at least one target-development movie regressed in each | rejected by the strict stability gate |
| full real-Zebrahub temporal/head transfer | score `0.599429` versus U-Net-only parent `0.671116`; large node excess | rejected; transfer visual U-Net features only |
| source-only global detector-threshold calibration | seed `271828` selected `0.95` and gained `+0.005686`, but seed `314159` selected `0.99` and lost `-0.001650` | rejected as seed-unstable; two source-validation movies are insufficient for a global threshold |
| aligned two-seed U-Net weight soup, alpha 0.5 | all 136 tensors matched, but source-validation score collapsed from `0.552416` to `0.0` | rejected; independently fine-tuned weights are not linearly compatible |
| dual-seed detector-logit fusion, weight 0.5 | source pooled gain `+0.063815`, then target-development loss `-0.027858`; 3/4 target movies regressed | rejected; one-sided proposal-retention fallback failed to control excess detections |
| Zebrahub U-Net initialization | reciprocal development pooled `+0.005897`, but one-time 16-movie locked audit `-0.021785`; both embryo directions negative while recall rose `+0.007013` | rejected for PRIVATE_ROBUST; sensitivity improved but lineage-edge quality did not generalize |
| four-view inverse-aligned edge-feature TTA | exact zero delta on all eight reciprocal development movies | rejected as structurally inert under registered-motion linking; revisit only with a learned linker |
| weak-linker four-view feature TTA | `+0.000514` on one of four forward movies, exact zero on all four reverse movies | rejected; one-movie effect does not replicate across embryo domains |
| raw / geometry-capped native ILP topology | raw graph violated max out-degree; capped 24-movie score `0.002193` versus registered `0.676146`, 0 division TP | rejected as a replacement topology; inherited `softmax>0.5` pool is orders of magnitude too sparse |
| native-guided conservative second-child repair | exact zero on all 24 movies; no candidate survived geometry, continuation and divergence gates | rejected at the inherited threshold; denser pool requires source-only selection before target evaluation |
| source-selected dense native-edge pool | all five thresholds from `0.5` to `0.02` were inert on both source folds; selected `0.5` then produced exact zero delta on prospective 24-movie OOF | rejected; threshold tuning is exhausted and a division-aware training or proposal change is required |
| real-Zebrahub edge-head fork signal | teacher-forced external validation: 188 true parents; at `0.5`, recall `0.4734`, precision `0.2438`; at `0.2`, recall `0.8245`, precision `0.0508` | useful external diagnostic, not competition promotion evidence; isolate a precision-guarded transfer without importing the unstable detector |
| independent scratch-seed coordinate consensus, radius 2 µm, alpha 0.5 | prospective 24-movie pooled `-0.002883`; both embryo directions negative; bootstrap only 13.35% positive and every leave-one-movie-out delta negative | rejected; unconditional localization averaging is not robust |
| attributed geometric safe-division repair | prospective 24-movie edge component `+0.000350`, but 0/13 division TP and 43 division FP | rejected; geometry-only fork proposals need a learned signal or independently validated visual veto |
| real-Zebrahub scores as add-only division evidence | prospective 24-movie pooled `+0.000294`, but 0/13 division TP and 41 division FP | rejected for division repair; the small cross-domain ordinary-edge signal motivated a separate one-to-one test |
| unconditional external weak Hungarian tie-break | forward source-only deltas `-0.001545` at weight `0.05` and `-0.003081` at `0.10`; target OOF remained unopened | rejected at source gate; preserve registered score/dummy threshold and require explicit confidence gating |
| confidence-gated external edge bonus | forward source folds inert; reciprocal source delta at best `-0.001564`; target OOF remained unopened | rejected at source gate; inference-time calibration cannot repair the cross-domain head |
| division-positive transformer-only recalibration | external division F1 `0.321881→0.323308`, but prospective 24-movie competition OOF repeated EXP154 exactly: pooled `+0.000294`, 0/13 division TP and 41 FP | rejected; loss weighting did not change competition decisions, so the next model needs explicit division representation or new candidates |
| explicit visual daughter-pair classifiers and fixed rank ensemble | external proposal ceiling `0.9734`; scratch pair AP `0.2319`, pretrained-feature AP `0.2006`, ensemble AP `0.2295`; best ensemble precision/recall `0.50/0.1530`, component correlation `0.7848` | rejected before competition data; explicit pairs improve candidate coverage but still lack enough high-precision ranking signal |
| parent geometry and statistically protected calibration | geometry prospective AP `0.254385`, but the transferred operating point had precision `0.418803`; four nested held blocks had precision/recall `0.438/0.117`, `0/0`, `0.385/0.222`, `0/0` | rejected before official-24; useful ranking signal did not yield a stable high-precision threshold |
| QRZ density-aware observed-node gap closure | frozen source-only ablation expanded 172 endpoint candidates on `44b6` and 33 on `6bba`, but reused zero middle nodes and added zero edges; scores exactly matched both parents | rejected before official-24; full QRZ gap benefit, if any, requires synthetic midpoint recovery and/or DeepCenter, not observed isolated-node reuse |
| leakage-controlled reciprocal DeepCenter + synthetic midpoint recovery | two independent epoch-2 models used explicit disjoint 10-train/2-checkpoint-validation source manifests; EXP182 passed both source folds (`+0.021748` on `44b6`, `+0.007931` on `6bba`), but EXP185 reciprocal target OOF regressed on 8/24 movies (pooled `+0.013380`, worst movie `-0.014529`) | rejected for PRIVATE_ROBUST by the preregistered per-movie stability gate; target labels are consumed, and neither a Kaggle run nor submission is authorized |
| source-selected intensity-centroid refinement | source folds selected forward radius `(3,5,5)`; on the untouched 175-movie reciprocal cohort, forward centroid `min8` plus frozen EXP191 reverse improves EXP206 by `+0.0030675362`, paired-bootstrap CI `[+0.0014898445,+0.0046280957]`, probability positive `1.0`, and minimum LOMO `+0.0028973690` | promoted as EXP209 and current honest pooled frontier `0.6815218333`; the separately selected reverse-centroid arm regressed and is rejected |
| exact eight-view inverse-aligned detector-logit D4 TTA | prospective 24-movie development delta `+0.0119457974`, direction deltas `+0.0147058021/+0.0003702260`, CI `[+0.0009265929,+0.0228854648]`, minimum LOMO `+0.0091216580` | promising detector mechanism, but not yet admitted; EXP211 is confirming the frozen policy on all 175 movies behind an all-chunk no-metric gate |

The reciprocal mechanism figures are reproduced in
`reports/oof_stability.json`; experiment-specific immutable receipts are in
`reports/exp129_oof_repro_20260909.json`,
`reports/exp132_coordinate_consensus_20260909.json`,
`reports/exp134_dual_seed_consensus_20260909.json` and
`reports/exp136_full_model_transfer_20260909.json`. Later mechanism receipts are
`reports/exp139_source_threshold_20260909.json`,
`reports/exp140_source_threshold_seed314159_20260909.json`,
`reports/exp141_unet_weight_soup_20260909.json` and
`reports/exp142_dual_detector_fusion_20260909.json`.
The full reciprocal and locked transfer receipts are
`reports/exp137_full_reciprocal_20260909.json` and
`reports/exp144_locked_reciprocal_audit_20260910.json`; the feature-TTA
diagnosis is `reports/exp145_feature_tta_development_20260910.json`.
The scratch-seed and attributed safe-division receipts are
`reports/exp146_scratch_seed_consensus_result_20260910.json` and
`reports/exp147_safe_division_result_20260910.json`.
The learned-linker/native-topology sequence is recorded in EXP148–EXP152
receipts, including the prospective source-only threshold-selection protocol.
External learned-score diagnostics and guarded transfers are recorded in
EXP153–EXP156 receipts.
Parent-calibration and geometry evidence is recorded in EXP171–EXP178; the
attributed observed-node gap ablation is recorded in EXP179, and the explicit
leakage-controlled DeepCenter source training is recorded in EXP180. The
synthetic-midpoint source pass and reciprocal target rejection are recorded in
EXP182 and EXP185 respectively.
EXP181's parameter-by-parameter QRZ attribution and line-ending normalization
audit is recorded in `reports/exp181_qrz_attribution_audit_20260911.json`.
The source receipt's `code_sha256` is the canonical LF notebook-code string;
the different Windows file-byte SHA is CRLF storage, not altered decoded code.

## Admission rule for additional open work

1. Archive the exact notebook version, source SHA, extracted-code SHA, runtime
   settings and attached model datasets.
2. Identify one mechanism-level change. Do not import a correlated public-LB
   preset as if it were one hypothesis.
3. Reimplement or adapt it as dynamic runtime inference and freeze its rule
   before target evaluation.
4. Require embryo-disjoint paired evidence, worst-fold reporting and the
   predeclared stability gate before opening the locked audit.
5. Describe public-LB numbers as runtime/regression diagnostics only; report
   post-close PRIVATE performance as the primary target and never as known in
   advance.
