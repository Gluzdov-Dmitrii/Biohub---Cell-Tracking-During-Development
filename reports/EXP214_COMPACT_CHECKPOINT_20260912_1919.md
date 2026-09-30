# EXP214 live checkpoint, 2026-09-12 19:19 UTC

Continue the user's authorized task to completion: honest broad OOF comparison, actual reduced-data training/quality test, and two remaining submissions today. No EXP214 target metric or POST yet. Do not stop with a plan or call the budgeted refit OOF of the published0.946 weights. User max48h; exact400epoch reproduction rejected.

Read newest EXPERIMENTS entries and prior EXP213/214 reports. All remote paths below share root `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development` (R). Python: `R/envs/prepost/py3.11-stdlib-v1/bin/python`, verified immutable bothhosts. All queue commands through `ssh nsu-quadro`, helper `/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py`. At most2 Biohub GPUs total across hosts only when no other project waiting; one under contention. Never touch another project's lease/process. Common queue plus physical preflight, started PID/start, monitor45s, verified release.

## Running now

- A100first `GPU-61c0078d-a4a6-37a2-3aba-0378e7794c46`: last core detector, source6bba seed314159. Lease `biohub-exp214-reduced6bba-s314159-resume-20260912`, token `exp214-reduced6bba-s314159-resume`. Wrapper171476; Windows monitor1456. Config `reports/exp214_reduced6bba_s314159_resume_config_20260912.json`. Run `R/runs/exp214_reduced6bba_s314159_resume_20260912`; output symlink to original `R/runs/exp214_reduced6bba_s314159_20260912/output`. Same immutable trainer v5, same contract, resumed epoch2 model+optimizer. Expected10remainingepochs about50min, not a guarantee. Monitor receipt same config name with `_monitor_`.
- A100second `GPU-04efb7bd-1f45-38cd-4a13-c79b6aeaa002`: equal-time reduced60 source44b6 seed2026 control. Lease `biohub-exp214-equal-time44b6-s2026-20260912`, token `exp214-equal-time44b6-s2026`. Wrapper171574; Windows monitor30176. Config `reports/exp214_equal_time44b6_s2026_config_20260912.json`; code `R/code/exp214_equal_time_v1_20260912`, run `R/runs/exp214_equal_time44b6_s2026_20260912`. Correctly resumed epoch12; epoch13 completed161.68s including validation. Fixed60, no target tuning. Expected total continuation~2.2h.
- RTX6000 is released. Last detector's first2epochs ran on RTX (737.35/717.35s), then owned PID261303/start445777703 was SIGTERM'd after atomic epoch2 checkpoint. Receipt `reports/exp214_rtx_migration_stop_20260912.json`; checkpoint SHA `bc52d3fd60bc7efc38198cfc1ea4db494c8a008b6746f74731879ac8855e0c82`. Windows monitor18448 verified tree/GPU absence and release. This intentional stop is not a failed refit; original output will receive the completed resumed result. A100 original waiting request was CANCELLED before launch. RSNA pilot had finished/released at last read; inspect live before reserving anything.

## Completed core models / inference

Core plan `reports/exp214_budgeted_refit_plan_20260912.json`, SHA `983d2953c915d91d41db33bf8fafa14bd17ed6e5aeefd5f67c0dda8d7759090a`. Source44b6 two seeds COMPLETE12, best SHAs2026=`f8e25074a98b651a64740ce9ab013ac957fb8d61462d9c7df982efb4db8e8605`,314159=`6af80254fdab1d4d826833730d37eaa27eb9283fdcf48839e432cca403b52c53`. Source6bba2026 COMPLETE12, SHA `fe929a4935972369c25f516e9895ba57eb515cc403b2e0e24553960aaa620e25`. Paths `R/runs/exp214_reduced<FOLD>_s<SEED>_20260912/output/edge_predictor_best.pth`.

First paired20 target6bba movies COMPLETE, both public and local graphs, no target metrics. Run `R/runs/exp214_paired_44b6_00_20260912/output`; public/local subdirs each have submission.csv and inference_receipt.json; root status.json is PASS_PAIRED_SHARD_PREDICTIONS_NO_METRICS. Lease released. Local `reports/exp214_paired_44b6_00_receipt_20260912.json`. Do not look at score until reverse20 complete too.

Frozen44bundle `R/code/exp214_evaluation_inputs_20260912/44b6_bundle.json`, copied locally `reports/exp214_44b6_frozen_bundle_20260912.json`. After last6model completes, freeze6bundle with `R/code/exp214_freeze_fold.py --root R --plan R/code/exp214_honest_refit_v4_20260912/plan.json --fold 6bba --output R/code/exp214_evaluation_inputs_20260912/6bba_bundle.json`.

Eight frozen shards in `reports/exp214_evaluation_shards_20260912.json`:44b6_00 first20 done,44b6_01..04 remaining24each;6bba_00 diagnostic20,6bba_01 remaining24,6bba_02 remaining15. All175 exact historical cohort. All configs `reports/exp214_paired_<fold>_<nn>_config_20260912.json`. Code `R/code/exp214_inference_v6_20260912`, movie lists already staged under evaluation_inputs. Launch through `scripts/launch_exp214_job.py --config ... --mode inference`. Adapt only GPU/cpu_affinity to actual available lease; current launcher checks exactGPU and can reserve before mismatch error, so reconcile reservation rather than duplicate. `_44b6_01_rtx_config_...` is prepared but not requested; choose A100 instead if free. No more than2 jobs total.

## Local orchestration changes

`launch_exp214_job.py` and `monitor_exp213_job.py` now accept optional pool/alias (defaultA100). Launcher also permits `resume_output` symlink only after original job's queue entries are released/cancelled, exit receipt exists, PID identity absent, correct fold/seed contract and checkpoint exist. Remote immutable scientific code unchanged. Existing monitoring processes already loaded their code. `scripts/snapshot_exp214_progress.py` gives compact states/candidate counts without opening any target metrics; saves `reports/exp214_progress_snapshot_20260912.json`.

## Metrics readiness

Staged ready manifests, local and `R/code/exp214_evaluation_inputs_20260912/`:
- `exp214_score40_manifest_20260912.json`
- `exp214_score175_manifest_20260912.json`
- `exp214_data_control_score_manifest_20260912.json`
- `exp214_frozen_exp209_baseline_rows_20260912.json`

`score_exp214_paired.py` in inferencev6 requires all arm/fold receipts/SHAs/graphs before writing no_metric_gate.json, then official scorer labels. CLI --repo (v4/tracking_repo) --data (exp213_source_view) --manifest --output(new owned run). Follow with `compare_exp214_results.py --metrics <metrics.json> --baseline <frozen baseline> --output <comparison.json>`, which adds EXP209 on same40/175,10k paired embryo-stratified movie bootstrap, bothembryos,LOO. CPU budget8/RAM64GiB; don't hold GPU for standalone scoring. No retuning between40 and175.

## Three-way data reduction control

Plan `reports/exp214_equal_time_plan_20260912.json`, SHA `9b1fd764a4571669d0ed7c51ea4e8f4a3cdd49d455ae8af957413b45c9e398e3`. Same source44b6/seed2026,20 target6bba, same v20 graph and clean center, each single model duplicated in primary/secondary roles. Arms full12 / reduced12 / reduced60. Full12 pinned SHA `2d929a856c317208e30056e38f5f74d7ffc91be36b27e217e596ffc210d4dcc4` under `R/models/exp214_full_control_12epoch_20260912`. Full12+red12 control bundles ALREADY frozen at evaluation_inputs `<short>_control_bundle.json` via `R/code/exp214_freeze_data_control.py`. Freeze60 with same tool `--root R --arm reduced60 --output .../reduced60_control_bundle.json` only after COMPLETE60.

Three prepared inference configs `reports/exp214_control_full12_config_20260912.json`, reduced12, reduced60; all v6 public-only runner. No control inference started yet. All60 predictions required before control metric. Dedicated scorer `R/code/exp214_score_data_control.py` (local scripts/score_exp214_data_control.py) accepts --plan (equal_time code/plan.json), --manifest (stagedcontrolmanifest), --repo, --inference-code v6, --data, --output. Do not weaken primary scorer's40/175 gate. Report actual equal-time runtime using sum of ALL60 epoch history, not only elapsed_seconds of resumed48epochs. Upstream augmentation RNG is unseeded, and some CUDA operations nondeterministic; no exact-replay or noise-free one-seed contrast claim.

## Kaggle two submissions still pending

Live18:47UTC:3used/2available; unrelated publicv21 ref56187070 PENDING,error empty,0bytes. EXP212 v5 ref56181132 COMPLETE0.718,error empty,255985567bytes. Best COMPACT47v20 ref56177715 COMPLETE0.946,error empty,207569232bytes. `.tmp/read_exp212_live.py` refreshes fullAPI+quota; check beforePOST.

New prereg `reports/EXP214_KAGGLE_DIAGNOSTICS_PREREG_20260912.md`, appendedEXP. SlotsPRIVATE4/5 are diagnostic public/local graph comparison. Gate fourCOMPLETE12 + honest40finite + cleanofflineaudit. Final promotion requires175 stability; diagnosticarm may be inferior without becoming a promoted final model.

Sources ready in `kaggle_notebooks/exp214_reduced_public` and `_local`. ExactSHAs public `a517f0543681f05af3cfef72530b021d9994e0d83314a1361ff527cd4c21d662`, local `b30cefe428f5e4b0ab0b3cda241590663422013726e1e861b9d151f31b9607e5`. Titles corrected to match intended slugs: `dmitriigluzdov/biohub-exp214-reduced-public-graph` and `...-local-graph`. Both Internetoff/private/T4. No push yet.

Model pack script remote `R/code/exp214_pack_models.py --root R --plan v4/plan.json --code inferencev6 --output R/models/exp214_dataset_pack_20260912` waits for all4complete. Creates verified~110MB bundle of only best detectors/cleancenters/code/plan/history, no public contaminatedweights orpredictions. Need tar/download/verify locally then private Kaggle datasetcreate, liveverifyready/private/filelist, then push/run clean kernels and audit downloaded outputs.

Local dataset dir already has ONLY metadata andREADME: `kaggle_datasets/exp214_reduced_honest_fold_models`. Title/id `Biohub EXP214 Reduced Honest Fold Models` / `dmitriigluzdov/biohub-exp214-reduced-honest-fold-models`; licenses other, README preserves upstreamterms. Add description fromREADME beforecreate. No actual model files there yet. Kaggle official metadata docs confirm other is supported.

Guard/audit17 tests passed at19:00ish: test_submit_code_file_once.py + test_exp214_kaggle_audit.py. Only POST via scripts/submit_code_file_once.py after exact kernelversion/sourceSHA/outputSHA recorded. Neverrawsubmit. Preserve one root submission only; runtime renames intermediateCSV to predictions.csv. FullAPIerror/score/bytes/status/ref/URL/quota afterPOST. Stopdailyonfirstanomaly. Pendingnoerror doesn'tblocksecondindependentdiagnostic. NoautoPOST backgroundjob exists.

## Compression / research / final reporting

Originalimage85.701GB -> all-frame exact detectorinput5.303GBinclallfiles -> reduced2.893336649GBinclmetadata/provenance. Everyretainedrawframeexact;12normalizedwindowsbitwise; portableloadwithoutoriginalimagesverified. Full12control9510.75s vsred121944.25s =4.8917× inclval; sourceproxy.9428611vs.9343308 is NOTOOF. Paths/usage in new `reports/EXP214_REDUCED_DATASET_USAGE_20260912.md`. Cache+models/output growthbound16GiB onNFS; originalsuntouched.

CurrentRussian workingreport `reports/EXP214_COMPARISON_AND_COMPRESSION_20260912.md`; scientificfigure compression_training.png under outputs/research/exp214_comparison_20260912. Update with40/175/control/LB actuals, concise finalanalysis andnextsteps. EXP209historical175 .6815218333, its ownpostprocgain+.0712649257; baseline development-adapted. Publicgap.228 does not predict privatecollapse. Only2biologicalembryos even175movies. Unknownselector noOOF. Original400epoch publicsecondaryall199 contaminated,135.447traininghours, GPUunknown.

Research reaffirmed authorPilkwangOOFnote has fixed100epochtwofold plan but no finalnumericOOF incheckedpage. Tenpublicalternatives0.92+ mostlysamealltrainweights; noverifiedcleanbundlefound. Extra tossowski/BioHub reportsrawedgeJ.768 on16movies, not ourmetric/notverified0.92+LB. Anotherrepo0.97 is goal notscore. Distillationfromtarget-seenteacherleaks; no pretrainedcleanOOFshortcut. Frame-redundancy/data-pruning papers supporthypothesis, notBiohubqualityguarantee. Links inreports. Don'texpandexperimentfurther; finish existing pipeline.

## Update ~19:33UTC
Kaggle initial source hashes changed by packaging-only removal of owned runtime_test symlinks after inference: PUBLIC258a41a6cc61bb8b03c942473c858d320150717f89629705d3e43aaa8761ccc4, LOCAL914e2502064cf78d6831d19f344369bce3aaeb0f129447f1f465487acb5fd00d. Both files copied/compiled,17guard/audit tests repass, prereg/EXP append correction. No source push/target metrics yet. Local dataset metadata description now containsREADME. First20 graph-only no-label auditpasses, receipt reports/exp214_paired_44b6_00_no_label_audit_20260912.json. Lastdetector epoch5, control17 atlastread. Extra public output metadata downloaded under outputs/research/exp214_public_output_provenance_20260912 confirms same alltrain199 secondary/best381; path5090is onlyhint, notverifiedtrainingGPU.

## Update ~20:00UTC
New critical interpretation correction: prior BF16 probe used freshly augmented batches in each mode (unseeded default_rng), so its0.776 update-cosine does not isolate precision. Main models remainFP32. Corrected short source-only same-materialized-batch probe prepared: config reports/exp214_identical_batch_precision_config_20260912.json, code R/code/exp214_precision_v1_20260912, script probe_exp214_precision.py SHA cde3cf76190670ad4d13e3c3e055f9846e58e11c85c7c393a454e36f5598e17f. It runs FP32repeat/BF16 with identical inputs/model/TorchRNG, no modelpromotion, max10min (expectedseconds), firstA100aftercorelastrelease thenreverse20. Not started yet. Lastcore epoch10, control26 atlastread. Additional analysis script staged R/code/exp214_compare_data_control.py with paired10kbootstrap and all60epoch trainingtime accounting; local scripts/compare_exp214_data_control.py. Model unpack verifier local scripts/unpack_exp214_model_artifact.py is ready for --archive --destination --receipt. Kaggle12hourGPU runtime verified official; v20 inference automatically shards over2T4s.
