# EXP225 P26 research notebook

Open `biohub-exp225-p26-research.ipynb`. Russian explanations and English identifiers describe the full model-to-graph pipeline.
Kaggle kernel: [Biohub EXP225](https://www.kaggle.com/code/dmitriigluzdov/biohub-exp225-p26-research-and-frozen-inference). Use this exact slug for updates; Kaggle derives it from the title.

This is a frozen production derivative of [P26](https://www.kaggle.com/code/zhehaoliang/biohub-p26-o01-exact-public-0947), historical account public score **0.947**, submission **56243810**. EXP225 v2 completed its clean offline run in **30m37s**, passed the independent output audit, and reproduced the parent's public CSV byte-for-byte. Exactly one submission was accepted: **56464735**, initially **PENDING** on 2026-09-22 at 12:45 UTC. Its own LB score is not yet known. Public weights do not have exact honest OOF here. Horaz selected development175 **0.7949879415** and our EXP214 **0.7427291486** are separate, development-adapted evidence; clean-fold EXP219 public **0.922** is also a different model bundle.

## Run

Kaggle T4 ×2, Internet **OFF**, the competition and three attached datasets from `kernel-metadata.json`. Use Restart & Run All. The original Docker digest and notebook dataset-version metadata are retained; embedded SHA256 guards pin materialized sources/checkpoints. Final output: `/kaggle/working/submission.csv`.

## Changes and provenance

- Upstream file SHA256: `cf9ab34b35bb5fc3879860eebec6a5173a6d4438945eb5aa8110f1dd1441fd5b`.
- Core original cells 2–4 (configuration reading, dependencies and GPU inference) retain exact source text and AST, split only at top-level boundaries. In original cell 5, every top-level AST is unchanged except `write_test_submission`.
- v2 fixes only CSV z/y/x serialization: read the actual runtime TZYX shape, round the coordinate, then clip to `0..dimension-1`. Internal graph coordinates, edge endpoints, node IDs and t remain unchanged. v1 artifacts were backed up to `work/exp225_20260922/v1/` before this correction.
- Frozen `BIOHUB_MOTION_RELINK_TIGHT_UM=5.5`, `BIOHUB_VALIDATOR_ENABLE=0` before configuration reading; removed original train-validator/sweep cells 7–10. This preserves the historical selected setting but does not erase its train-proxy selection bias.
- Retention/graph audit logic is unchanged. Diagnostic metadata now records resolved values, P26 parent and historical label/proxy selection accurately.
- The local source keeps outputs and execution counts empty. The linked Kaggle **version 2** contains this candidate's executed outputs; downloaded artifacts and audit are under `outputs/kaggle/exp225_p26_research_v2/`.
- 35 code cells; 36 explanatory cells; maximum 269 code lines per cell. Original large runtime-patch string literals remain intact.
- Models and original method authors are credited in notebook section 0.4. Primary, secondary and DeepCenter are inference inputs, not new training products of this notebook.

## Rebuild / Review

From repository root: `python scripts/build_exp225_notebook.py`.
Append the separately reviewed final audit with `--append-audit scripts/exp225_output_audit.py`.
Optional `--runtime-overrides path.json` is an explicit experimental environment overlay; changing it creates a new candidate requiring fresh validation.

`build_receipt.json` records static compilation, source/AST parity and hashes. This builder never executes GPU inference or sends a Kaggle submission. Runtime success and submission audits are separate gates.

For further work: preregister one hypothesis, use clean source-only checkpoint selection with embryo-level heldout inference, compare complete paired predictions with the official scorer, then run an Internet-off production version. Keep public leaderboard and private-robust evidence distinct.
