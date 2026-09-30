# SOURCE-INNER epoch10 error decomposition: local preparation

Status: **local bundle prepared and tested; no remote stage or run, no new source-label read, no reciprocal target label, target score, GPU, or Kaggle POST.** This is post hoc training-monitor evidence, not honest embryo OOF.

## Fixed question and cohorts

Test whether unmatched detected nodes explain enough official edge misses to justify a **source-only detection-proposal experiment**. Parents are the sealed EXP227 source44b6 epoch10 eight-movie graphs, checkpoint `df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79`, verified historical source score `0.8114014924249717`; and the sealed EXP236 source6bba epoch10 eleven-movie graphs, checkpoint `d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813`, verified historical source score `0.8458659187983504`. Their source score receipts are `reports/exp227_source_graph10_score_20260927.json` and `reports/exp236_source_graph10_score_20260927.json`. These cohorts have different embryos and movie counts; their aggregate scores must not be compared as a paired improvement.

The exact ordered 8/11 IDs, inference/scorer paths, CSV/receipt SHA256 values, scorer result/gate SHA256 values, checkpoint hashes, and source44b6 GEFF tree hashes are in the sealed bundle `config.json`. The source6bba scorer receipt does **not** pin individual GEFF tree digests; the audit will record each source6bba tree hash before and after its own read and replay every recorded historical source-score row to `1e-12`. It must stop if any graph, receipt, source44b6 label hash, legacy row, or final tree rehash disagrees. It must never open reciprocal target labels outside the exact 19 source-inner GEFF roots.

## Pinned organizer semantics

Use current organizer commit `075fc5f5a52d11077f9dc2b074644618f26939e2`, exact `metrics.py` SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`, `division_metrics.py` SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`, and tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, as pinned by `reports/EXP236_TARGET44B6_CURRENT_METRIC_SCORER_LOCAL_PREPARE_20260927.md`. Use the verified isolated Python 3.11 environment `envs/current-organizer-py311-e13cf-v1/bin/python`. The bundled synthetic directed-fork contract must pass before source labels open. Image-only scale metadata for all 19 IDs is checked against `reports/exp234_current_image_scale_audit_20260927.json` SHA256 `7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c` and both Zarr metadata-file hashes. Graph gates reuse the existing EXP227/EXP236 source scorer `gate()` implementations and sealed no-metric gate receipts; the new run writes its own `no_label_gate.json` before source GEFF access.

## Metrics and fixed interpretation

For each movie, report distinct matched predicted/GT nodes, total predicted/GT nodes, matched-node precision and recall; official edge TP/FP/FN; GT edge FN partition into both endpoints unmatched, source only unmatched, target only unmatched, and both endpoints matched but correct edge absent; and official valid FP plus ignored predicted edges. An edge is TP only when it survives the **current organizer** matched-edge filtering and has the official matched-edge flag. The FN categories partition every GT edge not counted as a TP, including any GT edge the current metric counts as FN due to edge filtering. Precision is distinct matched predicted nodes divided by predicted nodes; recall is distinct matched GT nodes divided by GT nodes. Report per-movie values and micro pooled counts within each cohort.

Report current-organizer division TP/FP/FN and pooled division Jaccard, adjusted edge Jaccard, weighted division term `0.1 × division_jaccard`, and total score for each source cohort. Verify `score = adjusted_edge_jaccard + weighted_division_term`; a missing division term follows the pinned organizer implementation. The older source score is replayed solely as an integrity check, not substituted for the current score.

Before viewing results, the **research signal** for a cohort is fixed as: at least half of pooled edge FNs have an unmatched GT endpoint; more than half of all its 8 or 11 movies individually have FNs and at least half their FNs are endpoint-limited; pooled matched-node recall ≤0.95; and pooled matched-node precision ≥0.90. A signal permits writing a separately registered source-only detection proposal, with FP and division guards. It does not authorize model tuning, target inference, promotion, or Kaggle POST. A failed signal redirects mechanism review to association/false positives rather than a threshold sweep. Report each cohort separately, and retain all rows regardless of the signal. The retained Horaz artifacts contain final graph CSVs and stats, not detector logits or proposal features; testing an adaptive peak-threshold candidate would need a new GPU inference pass unless a separate feature cache is built. This CPU audit performs neither.

## Bundle and resource boundary

Local bundle: `work/source_inner_error_decomposition_20260927`, 7 sealed files, manifest SHA256 `17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e`; audit source SHA256 `9931eb439a1bb7695323c3b95d191d17a57be63d0ae46b37c57579ef98ac4623`; config SHA256 `4b8720083617f84bc034b07123c5ae2ffa884a536ab67f7716386abdf280a013`; local preparer `scripts/prepare_source_inner_error_decomposition_local.py` SHA256 `b17ed4468a23da21a440df20f3c2eb02d2a37c1ac845b8541d338713f459e350`. The manifest pins the audit script, config, packaged organizer metric, runtime checker and image-scale audit byte for byte. The sole output path, if later approved and run, is `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/source_inner_error_decomposition_v1_20260927/output`; it must be absent beforehand. No active train, graph, scorer or target directory is written.

Runtime caps in the audit: CPU affinity 24–27, `CUDA_VISIBLE_DEVICES=''`, four Polars/OpenBLAS threads, 16 GiB virtual address space, 2400 CPU seconds and 2700 wall seconds. Estimated normal run: roughly 2–10 minutes on nsu-quadro given prior source8 CPU diagnostics, with a hard 45-minute wall limit. There is no GPU or fair-queue claim. These are estimates, not observed run times for this bundle.

Local verification: tiny endpoint-classification fixture **1 passed**; Python compilation passed; all seven bundle hashes rechecked; the bundled pinned metric imported under the local isolated runtime and its directed-fork synthetic contract passed. Full source graph/GEFF gates and numerical decomposition remain unrun until root review.

Future handoff after review: byte-preserve all seven files into remote `code/source_inner_error_decomposition_v1_20260927`, verify `manifest.json` SHA256 above, then execute with the verified Python, CUDA hidden, four thread variables, and `--bundle-sha256 17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e`. Preserve stdout/stderr, exit code, `no_label_gate.json`, and `result.json`; independently rehash the result and source GEFF trees after a PASS. No remote step has been performed by this preparation.

Exact future invocation from the remote project root, after byte-preserving stage and an absent output-path check:

```bash
env CUDA_VISIBLE_DEVICES='' POLARS_MAX_THREADS=4 OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  timeout --signal=TERM 2700 \
  envs/current-organizer-py311-e13cf-v1/bin/python -B \
  code/source_inner_error_decomposition_v1_20260927/audit_source_inner.py \
  --bundle-sha256 17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e
```
