# EXP214 two requested leaderboard diagnostics

Registered before opening EXP214 target metrics. These are the user's two remaining submissions for the current UTC quota day, PRIVATE_ROBUST slots 4 and 5. Do not borrow future or additional slots. Latest live quota receipt at 18:47 UTC: 3 used, 2 available. Recheck immediately before each POST.

Both candidates use the same four source-only scratch detector refits, two clean EXP180 centers, fixed 12-epoch training plan SHA `983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a`, and the same label-free unknown-embryo routing. All four completed checkpoints must pass the model-pack manifest gate. Neither candidate may use public all-train weights or frozen predictions.

| Slot | Kernel | Local exact source SHA256 | Hypothesis |
|---|---|---|---|
| PRIVATE_ROBUST 4 | `dmitriigluzdov/biohub-exp214-reduced-public-graph` | `a517f0543681f05af3cfef72530b021d9994e0d83314a1361ff527cd4c21d662` | Public COMPACT47-v20 processing on independently refitted reduced-data detectors provides an informative cross-embryo and LB diagnostic. |
| PRIVATE_ROBUST 5 | `dmitriigluzdov/biohub-exp214-reduced-local-graph` | `b30cefe428f5e4b0ab0b3cda241590663422013726e1e861b9d151f31b9607e5` | EXP209 processing on the identical detections tests whether local graph gains transfer beyond the historical detector family. |

Parents: EXP209 historical OOF pipeline / EXP212 v5 deployment and archived COMPACT47-v20 scientific pipeline. Exact kernel version, scriptVersionId, model manifest SHA and output SHA are recorded after the first clean run, before POST. Initial kernels are new candidates, not retries of EXP212.

Runtime dataflow: discover the actual competition `test/*.zarr` directories; infer with the clean reciprocal fold models; derive public and, for slot 5, local graphs from their candidate coordinates; use opposite-source models for known embryo prefixes and frozen agreement/continuity routing for new prefixes; serialize dynamic runtime dataset IDs. Intermediate CSVs are renamed `predictions.csv`; the sole `submission.csv` is at `/kaggle/working/submission.csv`. Unknown-embryo routing is not assigned an OOF score.

Run with Internet off. Offline packages install before NumPy/SciPy imports, preserving installed numerical-stack versions. Verify remote source identity and actual successful execution, download all output, and pass `scripts/audit_exp214_kaggle_output.py`. Required checks include one root submission, exact column order/types, finite coordinates, runtime ID equality, graph invariants and SHA. The guarded helper and audit tests passed 17 tests before these clean runs; rerun if relevant code changes.

Evidence gate for the two diagnostic POSTs: all four source refits complete; both graph arms on both folds pass the frozen 40-movie no-metric gate; official pooled metrics are finite and receipts are complete; clean Kaggle output audits pass; no daily submission anomaly. This is a preregistered paired mechanism comparison, not a correlated parameter sweep or automatic promotion of the lower-scoring arm. Final portfolio promotion requires the full 175-movie paired results and stability analysis. Keep the reduced60 data-quality control separate from these fixed 12-epoch submissions.

Use only `scripts/submit_code_file_once.py`, exactly once per candidate after the checks. Read full API status, error_description, score, bytes, ref, URL and quota after each POST. A pending earlier submission with no error does not block the independently registered second candidate. Any completed empty-score/error anomaly stops further POSTs that day.


Packaging-only source amendment before any EXP214 target score/push: remove the owned runtime_test symlinks after inference, verifying each points inside the actual TEST directory; original test images are untouched. This prevents unnecessary input archives in Kaggle outputs. Final initial source SHAs superseding the table above: public258a41a6cc61bb8b03c942473c858d320150717f89629705d3e43aaa8761ccc4, local914e2502064cf78d6831d19f344369bce3aaeb0f129447f1f465487acb5fd00d. Scientific models/graph/routing unchanged; both sources compile.

Packaging v2: independent source-fold processes concurrently use distinct T4s (single GPU each), including center processing. Models/graph/routing unchanged. Public SHA6ab0f7ab382a2c538a2da2b4cba2a0f7043b5e035fa5827ba0c50a6098355497; local8adef01a0d471f6925bbe8e60f378c463e3b899e9fa587b3bdd5e1d40988d844. New clean offline run and exact final-CSV parity against clean v1 are required before posting v2. This is a runtime packaging amendment, not a new scientific candidate or an additional submission slot.
