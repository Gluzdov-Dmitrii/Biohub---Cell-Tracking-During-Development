# V1284 source-v5/control-v6 local handoff — 2026-09-28

Control-v6 is a distinct local-only successor to sealed control-v5 for the
source-v5 run-local diagnostic-path correction. The failed f0 v4 identity
`loeo_v1284_capture_f0_v4_ba382850b115`, sealed source-v4/control-v5, and
their remote failure and release receipts were left unchanged. No new capture
plan/attempt was staged or queued.

## Sealed lineage

- Control-v6 preregistration
  `reports/LOEO_V1284_CAPTURE_CONTROL_V6_SOURCE_V5_PREREG_20260928.md`:
  SHA256 `7daf5d61fcd6ae88e4f5ef1bed057964d08628f2b83d3d7bd616c7875acbd4a4`.
- Source-v5 package
  `work/loeo-v1284-source-capture-v5-20260928/package_manifest.json`:
  SHA256 `3b8407413dc2837991dbf0d33b597543dcd8eac8c58e6039ea80c47164889a72`,
  29 files, package schema 3. Source-v5 prereg SHA256
  `d9fed996a751c572d12db5f88a688e237952168caea351c63ce11b8b254215e7`.
- Parent control-v5 manifest SHA256
  `9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`.
- New control-v6 package
  `work/loeo-v1284-capture-v5-control-v6-20260928/control_manifest.json`:
  SHA256 `4d41d66d3ab65392c37689e72b3c767de733abad81942c0aab90f0ceeab7eced`,
  seven files, schema 6, purpose `v1284_capture_v5_one_shot_control_v6`.

Control-v6 pins source-v5 plan schema 5, purpose
`v1284_source_image_capture_v5`, identity
`loeo_v1284_capture_f{fold}_v5_{attempt}`, and matching lease ID. It pins
source-v5 capture cells SHA256
`83fdb10c026f88b11b8f503b4d212c5e101affeb107cefdde2d7fe7b6e9f3bf8`,
generated LF predictor SHA256
`c5b3a5d80f8a2d7c7e6aad19352a92ef0b62893c27d6d39e0eab885b230bd85f`,
and unchanged LF module SHA256
`940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`.
The independent runtime outcome is
`PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6`; the source-v5 verifier uses
that exact literal.

## Safety and local validation

The inherited one-shot request, cancel, release and watcher behavior remains
intact. `capture_watch.py` is byte-identical to control-v5. The main
controller changes only its versioned identity message and request-intent
purpose; the runtime auditor changes only its versioned outcome and matching
request-intent purpose. The wrapper and contract repin source-v5. The suite
also rejects v4 plans, failed v4 identity, v4 control configs, stale hashes,
and old audit outcome.

`python -B -m unittest discover -s
work/loeo-v1284-capture-v5-control-v6-20260928 -p test_control_local.py -v`
passed 30/30 tests. These include lost queue request/cancel/release replies,
WAITING-to-RESERVED race, foreign/missing rows, GPU/process-busy cases,
repeated reconciliation, arbitrary-cwd watcher, and independent source-v5
verifier integration. The live queue's launched `RELEASED` shape with
`gpus=[]` and retained process metadata is accepted by the independent
runtime auditor; unlaunched reconciliation still requires `process=None`.

An independent exact-byte readback passed all seven manifest entries, six
Python ASTs, source-v5 and parent control-v5 manifest pins, and no cache or
pending-placeholder files. No target label/outer GEFF was read, and no remote
stage, queue mutation, GPU run, Kaggle POST, EXPERIMENTS.md edit or current
state report edit occurred.

Independent second review of source-v5/control-v6 and its downstream head
audit is required before any fresh remote stage or lease. After stage, the
sealed source-v5 CPU diagnostic-write canary and exact remote readback must
pass before a one-shot GPU request.
