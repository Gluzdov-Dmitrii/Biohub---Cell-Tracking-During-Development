# EXP222 saved comparison integrity audit — 2026-09-21

**PASS_SAVED_COMPARISON_WITH_PROVENANCE_LIMITS.** Reused completed EXP222; no detector/scorer rerun, new optimization, threshold selection or routing. A local JSON/AST audit passed13checks in0.50s. Script `scripts/audit_exp222_saved_comparison.py`; machine-readable findings `reports/exp222_saved_comparison_audit_20260921.json`.

The comparable measured result is **classical0.7409785635193241 vs EXP2140.7427291486246141**, classical-minus-DL **−0.00175058510529**, on exactly175movies (59×44b6,116×6bba). The minute floating-point discrepancy in reconstructed classical score,0.7409785635193237, is below1e−12 and comes from sum order.

| Check | Result |
|---|---|
|Completed run and empty process group|PASS|
|Every exported artifact matches saved remote SHA|PASS|
|Preregistration, prediction gate, timing entries, both score arms and frozen EXP214 all contain exact same175unique IDs|PASS|
|All baseline per-movie fields reproduce frozen EXP214, including counts, recall, node counts/ratios and adjusted Jaccard|PASS, floats within1e−12|
|All8baseline CSV path/hash pairs identical|PASS|
|Original classical source SHA matches local source, preregistration, prediction gate and final result|PASS|
|Official pooled aggregation independently reconstructed from saved sufficient statistics|PASS for both arms|
|Prediction gate written before target-label access; same evaluate/per_sample_metrics/summarise path for both arms|PASS local source audit|
|Full remote evaluator/wrapper byte version independently frozen in completion receipts|NOT ESTABLISHED: sourceSHAs not recorded for those files|
|Full remote prediction CSV locally rehashed|NOT DONE: recorded hash cross-checked between gate/result; CSV remains remote|

The scorer uses `biohub_tracking.metrics.evaluate`, `node_recall`, `per_sample_metrics`, `summarise` from the same repository path for both arms, image voxel scale from the same dataset metadata, and `estimated_number_of_nodes` from the same GEFF metadata. The exact reproduction of every frozen EXP214 score row is strong behavioral equivalence evidence on this cohort. It does not replace a cryptographic source-version receipt. This missing receipt is a provenance limitation, not an observed score mismatch; it does not justify another expensive inference run.

## Fixed classical parameter provenance

Original file `kaggle_notebooks/exp002_rule_based/biohub-rule-based-baseline.py` SHA256 is `e1edf7b5fc761ff713e818e01ecc5bc45349e8e8509b86d5932411b403294c1e`. Static AST inspection recovers unchanged defaults plus CONFIG_OVERRIDE: DoG scales(1.5,4.0)/(2.2,5.5)um, XYdownsample4, relative threshold0.045, min-distance3.2um, max40000peaks, centroid refinement, Hungarian8um, one-frame gap closure6um, isolated-node pruning, divisions disabled. Exact full configuration is in the auditJSON.

No learned checkpoint, optimizer, fitted threshold, target-label parameter estimation or pilot-based parameter change is used in EXP222. Per-image intensity preprocessing is part of fixed inference. We cannot reconstruct all public-author tuning that preceded historical EXP002; absence of that history prevents claiming the parameters were never exposed to any competition training data.

Only the execution packaging changed: the existing remote environment lacked pandas; loading omitted its sole import, and stdlibCSV serialized the same unchanged graph_to_rows dictionaries. The detector, coordinate refinement, linking, gap closure and rule parameters were not modified. Original failed startup was retained. Original source file SHA was checked before this packaging adaptation.

## Correct interpretation

For the nontrained classical algorithm, the useful comparison is **fixed classical inference on the identical held-out movie cohort**, not training-fold OOF of learned weights. EXP214's detector weights are source-embryo trained, whereas EXP222 has no learned weights to cross-fit. Both pipelines are evaluated on the same175movies with the same official metric calculation.

This cohort has already been used repeatedly for development, and two pilot movies were chosen from known failures. The full175membership was frozen without selecting by pilot scores, and all175predictions completed before full scoring, but that does not turn the collection into a pristine new test. The comparison is honest and directly comparable as a **development benchmark**, with explicit historical selection limitations. It does not prove equivalent future performance, a physical-method upper bound, or0.8independentCV. No need to repeat the completed run to answer the current baseline question.

## Remote byte audit amendment,08:07:36UTC

A bounded read-only remote audit now hashes the actual414,921,008-byte predictionCSV in place: SHA256 `2297279e64f02a6b303d6312bfd02783ed074e859afeffd20137b1937641fab9` exactly matches the prediction gate and result. No large file transfer, detector inference or scoring rerun occurred. This closes the missing-direct-CSV-hash check; the CSV remains remote.

Current deployed source pins, rooted at `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/`:

- `runs/exp222_classical_full175_20260921/run_exp222_classical_pilot.py`: `b850963ea4bff8d3a17fab688fa99025d75a715c1dd534118660341f6c7ce7dc`.
- `code/exp214_honest_refit_v4_20260912/tracking_repo/src/biohub_tracking/metrics.py`: `31baf45b54c78f68bab4f65dd8f4b38bca702abb644171c6df7c46cdeef55d83`.
- Same repository `src/biohub_tracking/io.py`: `efae135b088cecaab463d889f16c885ef6da3ad27b0747327d8ddc28d866b7bd`.
- Same repository `scripts/predict_unet_transformer.py`: `c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`.
- Original EXP002 source remains `e1edf7b5fc761ff713e818e01ecc5bc45349e8e8509b86d5932411b403294c1e`.

Current environment metadata: numpy2.4.6,scipy1.17.1,tracksdata0.1.0rc9,geff1.3.1.1.3,polars1.44.1,zarr3.1.6,torch2.6.0+cu124. Full current BiohubPython-tree hashes, sizes, mtimes, checkedUTC and exact paths are in `reports/exp222_remote_current_hash_audit_20260921.json`.

Temporal limitation remains explicit: this pins current deployed source bytes, not an independently saved execution-time source fingerprint. File mtimes alone cannot prove historical immutability. Exact replay of175baseline metric rows remains the historical behavioral-equivalence evidence.
