# Secondary full fold0 one-movie outer v3 — local template handoff

2026-09-28 Asia/Novosibirsk. **Status: BLOCKED for real plan, seal, stage, launch and scoring pending independent read-only v3 review.** This is a local-only successor template for the fixed source44 fold0 to target `6bba_32db13fc`. The separate v2 template remains rejected for scoring and unchanged; its manifest SHA256 is `57891c0c6eec1899bc2094d19379ba35b0a04620b2089dcef96721351695a9fb`.

## Preregistered correction and implementation

- Preregistration: `reports/LOEO_SECONDARY_F0_OUTER_V3_SCORE_COUNT_CORRECTION_PREREG_20260928.md`, SHA256 `6c68d657cbd70492ef9eb84479d632cf1e6aeaeea204c965cd0e3bc3f2a1a131`.
- Template: `work/loeo-secondary-full-f0-outer-v3-20260928`; `template_manifest.json` SHA256 `f9c807b0c2638bced85f4738a1b1fa053292a5602dc8eb92adf2cb36f044cc47`. It records 13 Python sources plus the preregistration, each by bytes and SHA256; status `LOCAL_TEMPLATE_UNBOUND`.
- In `score_audit.py`, verified result components must satisfy `edge_tp + edge_fp <= locked_graph.edges` and `division_tp + division_fp <= locked_graph.divisions`. The auditor first binds the score result and independent remote graph recheck to the rehashed inference lock, then checks nonnegative integer counts and these inequalities, then recomputes Jaccard and combined score.
- V3 uses its own identity and pinned preregistration. The existing exact 27-key terminal full-training audit, branch-specific separate release gate, source-inner selected-checkpoint quality gate, checkpoint/config SHA binding, image-only inference view, graph lock before target GEFF read, math-only SDPA, separate CPU scorer, and 1800-second inference cap are carried forward from v2.

## Synthetic validation

- `python -B -m unittest discover -s work/loeo-secondary-full-f0-outer-v3-20260928 -p test_local.py -v`: **22 passed**, including the original 20 behaviors, positive count-at-boundary score fixture, and adversarial count cases.
- Adversarial edge cases (`edge_tp=100, edge_fp=1` and `edge_tp=8, edge_fp=2` versus nine locked edges) and division cases (`division_tp=100, division_fp=1` and `division_tp=1, division_fp=2` versus two locked divisions) retain arithmetically coherent metric scalars. The preserved v2 auditor accepts each; v3 rejects each against its locked graph.
- The integrated `score_verify()` synthetic path rejects the impossible edge count and writes no verified score receipt.
- The suite parses all template Python sources and compiles generated remote inference, independent graph-audit, and score-artifact scripts. It exercises a local synthetic temporary seal and confirms a second seal fails. No real checkpoint or target data is used by tests.
- Exact readback rehashed all 14 v3 manifest entries and all 14 preserved v2 entries. The v3 directory contains only the 13 Python sources and template manifest: no Python cache, binding, bundle, launch plan, or partial seal. The copied real checkpoint and config hashes matched their pinned values, and neither was copied into v3.

## Remaining launch inputs and boundary

The exact real checkpoint and architecture config are locally available at `work/loeo-secondary-full-f0-assets-20260928/edge_predictor_best.pth` (SHA256 `82115428795e51a31a6a44a8fa983c6743ef4d052539b0daccc04db4ffd568ae`) and `work/loeo-secondary-full-f0-assets-20260928/config.json` (SHA256 `e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`). Neither asset was copied into this template or sealed. The full terminal audit and separate release receipts remain required and must be rechecked by the real plan. After independent v3 review passes, real plan/seal requires these exact files and receipts. Remote stage/launch additionally requires the managed cluster lease and eligible queue; scoring requires an already verified image-only inference lock and the separate CPU score gate. None was attempted in this correction. No SSH, GPU, target image or GEFF access, Kaggle POST, or `EXPERIMENTS.md` edit occurred.
