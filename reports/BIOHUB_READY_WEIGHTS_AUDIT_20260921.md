# Ready public weights audit — 2026-09-21

Read-only Kaggle API inventory/metadata and individual text downloads; no weights downloaded or loaded and no downloaded code executed. Evidence: `work/biohub_public_audit_20260921/weights_audit/` (API download flattens source basenames).

## Findings

1. https://www.kaggle.com/datasets/horaz0/biohub-top-cv-0803-artifact
   Title says CV0.8031, but actual README and artifact_manifest.json claim **0.8135597342657821 on 199 datasets**, report `outputs/cfg_embryo_cv/experiments/round2_full_final_default.json`. That report, prediction files and per-movie score records are NOT in the published file inventory. Selected fold0 epoch50 / fold1 epoch20 weights are available (8.36MB each).
   Code supports a real embryo-disjoint structure: cv.py groups complete embryos (one embryo per fold), inference.py:223-246 loads the corresponding fold model and predicts its held-out embryo. train.py:149 builds a fresh model by default; resume is fold-local. No all-train pretrained initializer seen in this training entry point; actual historical execution/checkpoint provenance is still not independently proven.
   **Selection bias is explicit:** train.py:29 checks epochs10,20,30,40,50; lines428-435 select each fold epoch by maximum score on that same held-out fold; line493 records `per_fold_actual_competition_score`. Thus selected-fold CV is development-selected, not a untouched outer estimate. Config also contains many finely specified density/intensity/postprocessing regimes; their tuning provenance is not supplied. This is a promising stronger candidate, not proof of superior trustworthy generalization.
   Additional comparability limits:199 datasets vs our175; downloaded inference uses a custom metric.py implementation (aggregate weighted adjusted edge Jaccard +0.1 pooled division Jaccard), although official_competition_metric.py is bundled. Exact parity with our current official scorer is unverified. README describes the final two-model inference ensemble; that ensemble must NOT be applied to the training embryos and called OOF because one component trained on the target embryo. Published run_cv itself correctly uses a single corresponding fold.

2. https://www.kaggle.com/datasets/horaz0/biohub-cfg-embryo-cv-last-folds
   Published fixed last epoch50 weights for both folds, source and config, no local metric in manifest. Potentially useful control against selected-epoch optimism, but not an independently proven >0.74273 baseline. Training source still contains outer-fold checkpoint selection machinery; use last files only in the fixed-last control.

3. https://www.kaggle.com/datasets/rudispresence/biohub-loeo-fold0-fixed-final-checkpoint
   Manifest explicitly splits 199 movies: fold0 trains128 embryo6bba, tests71 embryo44b6; fold1 reciprocal. training_config.json says3epochs, seed20260830, checkpoint_policy=fixed_final. No metric evidence supplied. Stronger methodological label than selected-fold checkpoint, but no evidence it beats ours.

4. https://www.kaggle.com/datasets/rudispresence/biohub-cross-embryo-fold1-fixed-final
   Weight+inference source+architecture config, no training manifest or score report in published inventory. Pair likely complements preceding dataset, but title alone does not establish exact provenance or result.

## Decision

Do not answer that no public CV-weight candidates exist: they DO exist, including a documented **claim0.81356**, and deserve reproduction. Do not replace our verified development-adapted reciprocal official175 score0.742729 with this claim. The evidence does not establish an independently verified, comparably scored and more trustworthy stronger solution.

Next bounded experiment: download immutable weights with manifest SHA verification, inspect safely, run each fold only on its held-out embryo; score saved outputs with our exact official scorer on the identical175 movie list, report per-embryo/paired per-movie deltas. Separately evaluate fixed-last50 to quantify epoch-selection advantage. Preserve199 comparison separately, identify24 extra movies before claiming full comparability. Never average both complementary models on either training embryo during OOF. No Kaggle submission is necessary for this verification.
