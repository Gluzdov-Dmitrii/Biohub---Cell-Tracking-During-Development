# Primary full fold1 v7 source-path correction: local handoff

Status: **LOCAL PACKAGE SEALED; NOT STAGED OR LAUNCHED**. Independent
read-only review is required before remote stage.

## Identity and correction

- Pre-code preregistration:
  `reports/LOEO_PRIMARY_FULL_F1_V7_SOURCE_PATH_PREREG_20260928.md`, SHA256
  `fa55b52e007daaa3e84380d4aefeb194bb8b8865c710d51866c9c09f92b287fb`.
- Parent v6 plan SHA256
  `51bff74097e56c42cb9a8b00d1edec80b555e101913f1423cc9c85ffaa9ea224`;
  parent 21-file manifest SHA256
  `857b712521801d16948c51b32f430bb40f73965a09e4371681e1b8ee4f1ef5f1`.
  V6 remains untouched and unstaged.
- Distinct v7 attempt `80e94204bb39`, plan
  `work/loeo-primary-full-f1-v7-20260928/full_plan.json` SHA256
  `b3837101e54703cca518a97a1b022cd7b77e9d3a5992f69e9459387e063bad60`;
  21-file bundle manifest
  `work/loeo-primary-full-f1-v7-20260928/full_bundle/bundle_manifest.json`
  SHA256 `9eed5e11f4384d522256b16804c3e5c5dc298023187292ccf791fe3f187eaecb`.
- V7 controller SHA256
  `731b7e2f954813a9e592644490b5855a783d4b0272b61168289d418821bf00db`;
  local test SHA256
  `98dcc05ee83753c07ecc574baaae87e50b0f13be034fd49c71f952be810cfbb8`.

`remote_snapshot()` now sends a narrow source-root/code/stage/run/Python
configuration, approved source parents and the 128 pinned source IDs to its
remote script. It probes the exact 256
source Zarr/GEFF symlinks and validates existence, strict ID-preserving
resolution, approved parents and unique targets. It neither glob-scans nor
iterates the shared-view directory. Its gate requires 256 paths, 256
resolved paths, 256 unique resolutions and an exact empty invalid list.
The local pinned split still verifies the full 199-ID catalog SHA.

## Local checks

- `python -B -m unittest -q test_full_local.py`: **44/44 passed**. The new
  negative fixture contains 71 target GEFF names and raises on any target
  probe, global glob or shared-directory iteration; the source-only snapshot
  and preflight pass, while missing or foreign source pairs fail.
- `python -B build_full_bundle.py validate-inputs`: 128 source, 71 outer,
  13 support files.
- No-cache compilation passed for eight local Python files. `read_plan()`
  and full manifest verification read back all 21 exact bundle files.
- Only bundled `full_contract.py` (v7 identity and prereg SHA) and
  `preregistration.md` differ from v6. `run_full.py`, `full_wrapper.py`,
  `full_supervisor.py`, `audit_completed_full.py`, source-window metadata,
  public support code and pinned split are byte-identical.
- No local stage or request-intent receipt exists. No SSH, remote stage,
  queue/GPU action, target image/GEFF/label read, OOF result or Kaggle POST
  occurred in this implementation.

Remaining gate: independent second review of v7 local source/manifest and
the exact source-only preflight contract before any remote stage. The exact
remote runtime has not executed for v7.
