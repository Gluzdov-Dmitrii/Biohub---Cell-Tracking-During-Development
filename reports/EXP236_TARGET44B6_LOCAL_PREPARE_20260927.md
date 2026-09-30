# EXP236 reciprocal target44b6 local rollout ready for review

No remote stage, run, queue claim, GPU use, target GEFF access, target score, or Kaggle POST occurred in this preparation. The four local bundles are sealed for frozen assignment direction `6bba`: 15, 15, 15, and 14 distinct target `44b6_*` movies (59 total). No EXP236 target coordinator receipt or stage/launch artifact exists at this review.

## Fixed source and dataflow

- Preregistration SHA256 `a36787c0187284e07f465097153a30575c4a5ef722e4d627b955084eb1b8c400`; assignment SHA256 `9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4`.
- Source training recovery SHA256 `266732c9cbbaea76a45ad9a4706b3b025b11d36be0762b00f0838c0d8b8efcdb`; source11 handoff SHA256 `9d8c37c1d3b1d14e2e7589704d3899b678f2398cd16f120d89c09e3e16d9ba07`; source score receipt SHA256 `5b0e87506e6d95a7c8175825b9a122292ee664fa71bc7994e507969b81ac4737`. The 0.8458659187983504 score is source-inner monitoring, not target OOF.
- Source graph plan SHA256 `3633711ba0a3706be43c71907261afa5904db93d26cb1b29fb3dc19294474421`; parent code manifest SHA256 `92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2`; fixed epoch10 checkpoint SHA256 `d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813`.
- Each plan names only its assigned runtime `.zarr` images. The runner validates the frozen assignment and source chain, installs a GEFF/submission/unassigned-image audit hook, then uses Horaz `predict_one` and graph writer. The verifier checks exact output set, status, every CSV and receipt hash, schema, finite integer coordinates, image bounds, topology, exit0/no timeout, supervisor release, and control release. The coordinator additionally checks a fresh RELEASED lease and dead worker identity/group with no assigned GPU PIDs before advancing.

## Local artifacts

| Chunk | Local prepare receipt SHA256 | Bundle manifest SHA256 |
| --- | --- | --- |
| 00 | `e66185e544b3ea5a71b7e11a462d636a35faef72c33bc8afe18e9456338bd84b` | `39ea1958f53b198ce50e7edcb4803a4783f30458a4c47fea7855aa43fa4fea24` |
| 01 | `5b5499ae3d7de12f240530a2180e944eb658c4b6caf39170054f7d64c9144e0b` | `7e92aa7a2451ef13df3819c79f655fbca58f31259b335d91bb54276ead3cf3fa` |
| 02 | `99f05b432a19993119ae67d190a6549e2e58d9e5ccf2987911a3d444ec9a2c83` | `4e19929c6f10fa574148ec62be8e19f7e1d379931c0ffbcc3bcff7222131e5f2` |
| 03 | `244f7c8a3101b1afe65b450cc51a9f3e892dd1e298f35ade5e4c725e9e855825` | `7acd43d0dcc90e92629285fa23589a8cb64a69fdd93f40bb9c4617538b01dbce` |

The versioned local scripts are `prepare_exp236_target_chunk_local.py`, `run_exp236_target_chunk.py`, `verify_exp236_target_chunk.py`, `stage_exp236_target_chunk.py`, `launch_exp236_target_chunk.py`, and `coordinate_exp236_target44b6.py` in `scripts/`. Staging requires exact parent manifest/plan/checkpoint hashes and replaces the inherited wrapper assertion for `run_exp236_source_graph10_v2.py` exactly once. Launch independently repeats queue fairness and physical A100 idleness checks and rejects duplicate artifacts. The coordinator uses heartbeat-safe completion and stops on uncertain side effects.

## Validation and remaining gate

`python -m pytest -q tests/test_exp236_target_local_rollout.py`: 7 passed, 4 subtests passed. Python compilation passed. Generated stage preflight, stage, launch preflight, and launch sources were AST-parsed; stage preflight, stage, launch preflight, and launch were executed only in a fake temporary workspace. All four real local bundle gates passed. Remote parent files, checkpoint, physical GPU state, and runtime target images remain unverified by this local-only work and must pass the guarded live stage/launch/post-run gates after review. No target score exists.
