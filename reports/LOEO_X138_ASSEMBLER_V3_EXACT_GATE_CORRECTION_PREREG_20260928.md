# x138 reciprocal assembler v3 — exact audit and image identity correction

Written 2026-09-28 Asia/Novosibirsk before successor implementation. The
sealed local-only assembler v2 package SHA256 is
`876894ec27d5e4b9c43827787d566554a34f10882fda57281b2ba8d026c5d9a3`.
The v2 independent review rejected real source emission for two P1 gates.
Keep v2 unchanged. No real reciprocal source, outer graph, or OOF score exists.

Create a distinct local-only v3. Preserve the fixed x138 inference, x162
coordinate clamp, reciprocal split, 50 chunks and 199 outer IDs. Change the
authorization and image-only identity checks as follows.

For primary and secondary full-training receipts, require **exactly** the
following 27 boolean-true checks in fold0 and these 27 plus
`remote_source_metadata_matches` in fold1: `plan_and_bundle_pinned`,
`remote_manifest_matches`, `remote_split_matches`, `run_status_pass`,
`global_seed_before_model_import`, `exit_clean`, `status_exit_identity`,
`log_nonempty`, `log_50_ordered_epoch_rows`, `progress_50_epochs`,
`denied_empty`, `loaded_exact_source`, `view_status_exact_source`,
`no_outer_target_loaded`, `remote_view_exact_pairs`,
`finite_train_validation_metrics`, `exact_per_epoch_window_coverage`,
`exact_loaded_source_window_totals`, `checkpoint_selection_reproduced`,
`quality_gate_reproduced`, `checkpoint_hash_matches_status`,
`architecture_hash_matches_status`, `public_predictor_cpu_load_finite`,
`no_live_run_owned_process`, `durable_release_time_gpu_empty`,
`process_receipts_match`, `lease_released`. Reject missing, extra or non-true
checks. Keep the existing exact auditor SHA, split, source IDs, checkpoint,
selected epoch, quality and queue lineage gates.

For DeepCenter fold0 and fold1 receipts, require **exactly** 16 boolean-true
checks: `local_plan_and_bundles_pinned`, `stage_receipt_bound`,
`launch_receipt_bound`, `reservation_exact`, `remote_config_bound`,
`remote_training_bundle_hash`, `remote_control_bundle_hash`,
`remote_plan_hash`, `clean_exit`, `launch_exit_identity`,
`source_view_has_no_outer_name`, `denied_log_empty`, `fold_verifier_pass`,
`no_live_run_owned_process`, `release_time_gpu_empty`, `lease_released`.
Keep the existing DeepCenter auditor SHA, selected checkpoint and released
queue gates.

For secondary fold0 separate release verification, require `outcome=PASS`,
the pinned release verifier SHA, matching lease/run/GPU/exit identity and raw
RELEASED queue reply. Require `branch=supervisor` or `branch=manual`, no failed
checks, and exactly the branch's boolean-true check names. Four common names:
`remote_config_equals_sealed_launch_intent`,
`queue_request_run_matches_plan`, `exit_zero_no_timeout`,
`exit_matches_launch_identity`. Supervisor adds
`complete_plan_run_lease_gpu_exit`, `release_time_no_process_gpu_empty`,
`release_timestamps_ordered`, `saved_queue_action_and_reply`. Manual adds
`manual_receipt_hash_present`, `manual_plan_run_lease_gpu`,
`release_time_no_process_gpu_empty`, `release_timestamps_ordered`,
`saved_queue_action_and_reply`. The actual fold0 secondary release is a
supervisor receipt; manual is a schema-compatible alternative only.

For each image-only outer chunk, both generated runtime preflight and local
output verification must require each `<ID>.zarr` alias to resolve to the
**same `<ID>.zarr` basename**, under the pinned allowed image root, and be a
directory. Reject a link to another source or outer ID even when it remains
inside the allowed root. Keep exact sorted chunk alias names and immutable
chunk IDs. Tests must construct wrong-target symlinks for both paths and show
rejection, including a 6bba alias to a different 6bba movie and to a 44b6
source movie.

Synthetic tests must reproduce both v2 pass-throughs, verify v3 rejection,
verify positive exact receipts and both release branches, compile the emitted
source, and read back exact manifest hashes with no cache. Independent read-only
review is required before any real source emission. This correction is local
only: no SSH, GPU, target image/GEFF, Kaggle POST, or OOF score.
