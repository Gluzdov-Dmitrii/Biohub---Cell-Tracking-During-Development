# Secondary full fold0 one-movie outer v2 — exact gate correction

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC) before successor code.
The local-only v1 13-file template manifest SHA256
`948990e25246c75c583672e6a25d80719d451562e6dd7c4e1efd156e9db6998c`
is preserved, unsealed for real weights and unrun. Its fixed source44 model,
outer ID `6bba_32db13fc`, one-movie image-only inference policy, 1,800-second
child cap, graph-lock-before-label sequence, and scorer are unchanged.

Independent read-only review found two acceptance gaps before real use. V1
`readiness.py` accepts an arbitrary count of all-true checks in full-training
and release receipts. Its own mock uses `check_0..24` and `release_0..7`, so a
receipt lacking source-only, checkpoint-selection, process or saved release
checks could pass if outcome strings were forged. V1 `score_verify` accepts a
minimal result with four finite scalars and does not bind the full metric
components, fold, graph/tree SHA or pre-label gate to the locked inference
receipt. No real terminal checkpoint, target graph or label read was involved.

Create a distinct v2 template. Pin the existing full auditor source SHA256
`914f1d7d661e22939b9a79166db4556361abe2b11c2aef710c980b99de4d5650`
and release verifier source SHA256
`e3f48cc6ebfee49a93fcbdf9a71a8f3718a38ffbff1e49d09a07771e83e441d3`.
Require **exactly** the following 27 full-audit check names, each boolean
true, no extras or omissions: `plan_and_bundle_pinned`,
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
`process_receipts_match`, `lease_released`. Preserve the fixed quality gate,
all 50 epochs, 5,001/1,314 windows each, selected checkpoint/config hashes.

Require release `branch` exactly `supervisor` or `manual`, `outcome=PASS`,
`failed_checks=[]`, actual verifier SHA, matching run/lease/GPU/exit hashes and
raw queue `id/state=RELEASED`. Its `checks` must have exactly four common
true names: `remote_config_equals_sealed_launch_intent`,
`queue_request_run_matches_plan`, `exit_zero_no_timeout`,
`exit_matches_launch_identity`. Supervisor additionally requires exactly:
`complete_plan_run_lease_gpu_exit`, `release_time_no_process_gpu_empty`,
`release_timestamps_ordered`, `saved_queue_action_and_reply`. Manual
additionally requires exactly: `manual_receipt_hash_present`,
`manual_plan_run_lease_gpu`, `release_time_no_process_gpu_empty`,
`release_timestamps_ordered`, `saved_queue_action_and_reply`. Reject a
missing, wrong-branch or substituted check dictionary before plan/seal/stage.

After image-only inference and graph lock, independent CPU score verification
must rehash the exact `verified_inference.json`, predicted tree, result and
`pre_label_gate.json`. The pre-label gate must match the locked inference
receipt SHA, tree-content SHA, checkpoint/config/full-audit/release-gate
hashes, metric code hashes, target ID, `status=PASS_BEFORE_TARGET_GEFF` and
`labels_read=false`. The result must have `fold=0`, exact target/tree SHA,
`labels_read=true`, ordered start/finish, nonnegative integer graph and
edge/division TP/FP/FN counts, node recall, edge/adjusted-edge/division
Jaccard (nullable only under the scorer's no-division rule), finite score,
voxel scale and the expected interpretation. Recompute the metric components
and final score from the counts using the pinned current organizer metric or
reject if a component cannot be independently reproduced; do not accept a
four-number summary. Preserve the one-movie directional interpretation.

Synthetic tests must reproduce v1 count-only false passes and minimal score
pass, then show v2 rejection; include positive exact 27-check and both release
branches, wrong/missing check names, pre-label/graph mismatch, malformed
counts/components, no-label guard ordering, compile, exact manifest readback
and no-cache seal. Separate independent review before stage/launch. This
correction is local only; no SSH, GPU, target image/GEFF, Kaggle or OOF score.
