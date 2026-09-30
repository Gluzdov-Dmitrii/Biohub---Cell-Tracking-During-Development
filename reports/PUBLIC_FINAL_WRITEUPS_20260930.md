# Biohub final writeups: primary-source evidence, 2026-09-30

Read-only research checked at approximately **2026-09-30 03:46 UTC**. This report creates only this file. No code, submissions, messages, or model jobs were changed. It does not repeat the local repository audit.

## Results are preliminary, but private scores are available

The live authenticated [official leaderboard](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/leaderboard) selected **Private**, covering **71%** of test data, and displayed:

> “The private leaderboard is preliminary and will be finalized after the results are verified.”

The competition ended September 29 at 23:59 UTC. Search-engine copies were stale public standings; the table below comes from the live page. “Final rank” in participant titles means the current post-close private rank, subject to verification.

| Private rank | Team | Private score | Public rank inferred from displayed change | Published solution found |
|---:|---|---:|---:|---|
| 1 | Sergio Alvarez | 0.977 | 3 | None attached to the leaderboard row; no full writeup found in the current recent-discussion list |
| 2 | Soheil Ayati | 0.970 | 28 | None attached to row; no full writeup found |
| 3 | yu4u | 0.967 | 1 | [3rd Place Solution](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/3rd-place-solution) |
| 4 | z7777 | 0.962 | 20 | No attached writeup found |
| 5 | Tang | 0.954 | 8 | No attached full writeup found |
| 12 | Corwin | 0.946 | 14 | [12th Place Solution](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/12th-place-solution) |
| 14 | Vibes & Edges Trade-Off | 0.944 | 43 | [14th-place writeup](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/14th-place-solution-from-vibes-and-edges-trade-off) |
| **1082** | **Big Cells** — Dmitrii Gluzdov / Arsgorynich | **0.917** | **367** | 108 entries; displayed **down 715** |

The live footer totaled **4,020** teams; Corwin's written snapshot says 4,017. Scores display only three decimals. Public ranks above are arithmetic from the live up/down changes, not independently fetched public rows. None of this certifies medals or finalized prizes.

## Actual participant methods and compute

### yu4u, private rank 3

[Primary writeup, September 30](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/3rd-place-solution).

Reported final public **0.977**, private **0.967**, CV **0.977801**; division Jaccard CV **0.540107**, private **0.47**. Detection ensembles 2.5D U-Nets with ImageNet-pretrained EfficientNetV2-L/B7 encoders and a fully 3D MONAI SegResNet. Sparse-label heatmap loss masks uncertain regions identified by DoG instead of teaching visible unannotated cells as background.

Tracking adds learned dense flow, an appearance/attention matcher, and supervised division parent/pre/post models using original and flow-aligned frames. Calibrated expected evaluated/correct probabilities drive a **joint node/link/division HiGHS LP/MILP**, followed by gaps, component filtering and affine coordinate refinement. The fixed-OOF ladder's A2→A3 gain combines multiple changes and is not an isolated division-model effect.

Video-level five-fold OOF also cross-fits downstream calibration, but overlapping crops and shared embryos violate independence. The author explicitly says:

> “this validation is not fully independent.”

Inference uses TensorRT, mixed precision and **two GPUs**; detector inference accounts for 55% of runtime. GPU type, training GPU count, training cost, and complete hidden runtime are **not stated**. This proves a different method, not a measured expensive-hardware advantage.

### Corwin, private rank 12

[Primary writeup, September 30](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/12th-place-solution).

Reported selected public **0.970**, private **0.946**, rank **12**, from public rank 14. They tuned public TemporalUNet3D/node-transformer models and the public ILP/post-chain **without retraining the production detector**. Added stages include graph consolidation, a trained mitosis specialist, repair/identity linking, learned recentring, and guarded integer CSV emission.

Their largest admitted mistake was validation:

> “Our largest error was validation”

Full-chain **0.975/0.979** reads were in-sample; weaker fold-retrained networks produced **0.881/0.888** without the final repair rules. Component cross-fitting on an in-sample detector graph was not honest whole-chain OOF. Additions after their base champion yielded +0.006 public versus +0.013 private; this does not isolate every component.

Final inference used **2×T4**. The stated **6.8–8.4 hours is submission-to-score time**, including unspecified scheduling/scoring overhead. A recentring benchmark used **RTX 2000 Ada**; a teammate supplied a gaming PC for training. Exact training GPU, total training hours and cost are **unstated**.

This demonstrates that substantial new image-based repair could improve a public-weight baseline, while also documenting why public-tuned detector knobs and an in-sample bench were unreliable.

### Vibes & Edges Trade-Off, private rank 14

[Primary writeup page](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/14th-place-solution-from-vibes-and-edges-trade-off), with [author-attached HTML](https://storage.googleapis.com/kaggle-forum-message-attachments/3530328/51776/14th_place_solution.html).

The live leaderboard confirms selected private **0.944**. The attachment describes public **0.964**, two complete pipelines: a public TemporalUNet/transformer branch supplies nodes/ordinary edges; an own FlowSeg branch supplies division donors. FlowSeg predicts center-directed instance flow; a GNN ranks Hungarian links; divflow learns displacement toward division centers. Additional geometric/GBDT and temporal furrow ViT evidence adds divisions conservatively.

Five video folds balance edge/division load. The attachment explicitly flags shared-embryo validation, leaked cross-fold ensemble reads, and a final FP-dropper fitted on the entire evaluation corpus. Some archived measurements lost their original logs. Parts of its metric explanation use old graph-wide division criteria, so the current official metric overrides it.

Training hardware/cost is **not stated**. The [linked notebook](https://www.kaggle.com/code/tom99763/merge-safe-tko-o12-ilpdiv04-readmit094-biohub), **version 2**, reports **40m 37s, GPU T4×2**, a save run on visible data, and private score **0.945**. That candidate score differs from the selected leaderboard **0.944**; this research does not resolve version/final-selection provenance and does not substitute it for the team result.

### hjyact: a strong unselected model, not an official high placing

[Primary September 30 writeup](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development/writeups/from-scratch-2-5d-convnext-detector-ilp-tracker), linked [inference notebook](https://www.kaggle.com/code/hjyact/biohub-model-inference), attributed to version 47.

Author-reported best **unselected** model: public **0.929**, private **0.939**. Two chosen versions instead scored private **0.917**. The page's placing metadata must not be presented as the hypothetical rank of the unselected 0.939 model.

Own 2.5D ConvNeXt-nano U-Net predicts heatmaps and offsets, ensembles probability maps before peak extraction, then uses learned-edge ILP, clean-up and a separate division model. The main detector reportedly trained 100 epochs. Inference uses a second **T4 with fp16** to stay within **nine hours**; training GPU/count/cost is **unstated**.

The author reports whole-pipeline official scoring on never-trained videos from both embryos. However, the text also describes a main training split containing all 128 6bba videos and half of 44b6. The validation account is therefore insufficient to certify reciprocal embryo-held-out evaluation. The reported selection failure illustrates public/private disagreement for that participant; it does not prove Big Cells possessed an unselected 0.939-private candidate.

## Metric and bounded interpretation

The authoritative [RoyerLab metric](https://github.com/royerlab/kaggle-cell-tracking-competition/blob/main/metrics.md) uses optimal timepoint-aware matching within **7 µm** and:

`score = adjusted_edge_jaccard + 0.1 * division_jaccard`

The node adjustment uses the host's coarse total-cell estimate, not the sparse annotated-node count. Edge FP rules include incorrect links competing with annotated connections. Divisions require local directed topology and two distinct, unmerged daughter branches within a ±1-frame window; merely sharing a graph component is insufficient. Per-video adjusted-edge values are size-weighted; division counts micro-aggregate.

For the parent postmortem, the supported inference is that high performers built detection/division evidence and measured the actual final graph, rather than merely scanning public post-processing knobs. Corwin shows public weights can still support a competitive pipeline with substantial learned repairs. The evidence does **not** establish a single cause of Big Cells' gap, prove all successful CV was embryo-independent, or support a quantified GPU-budget explanation.

No complete first- or second-place method was found in the inspected live recent-discussion list or attached leaderboard solutions. Their algorithms and training hardware remain unknown; yu4u is the highest private-ranked detailed method verified here. Search-engine notebook scores/titles were not treated as winners. The earlier [Pilkwang final-two note](https://pilkwangkim.github.io/posts/BioHub-Cell-Tracking-Working-Note-8-What-Went-Into-Choosing-the-Final-Two/) was a September 18 selection record updated September 23, with private results still unknown, and is not a post-close winning-solution report.
