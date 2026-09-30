# V1284 source-v5/control-v7 local handoff — 2026-09-28

Control-v7 is a distinct local-only successor to rejected control-v6. Source-v5
manifest SHA256 `3b8407413dc2837991dbf0d33b597543dcd8eac8c58e6039ea80c47164889a72`
and rejected parent control-v6 manifest SHA256
`4d41d66d3ab65392c37689e72b3c767de733abad81942c0aab90f0ceeab7eced`
remain unchanged. No fresh f0 v5 attempt, archive, remote stage, queue
mutation or GPU run occurred.

- Preregistration:
  `reports/LOEO_V1284_CAPTURE_CONTROL_V7_TERMINAL_QUEUE_IDENTITY_PREREG_20260928.md`,
  SHA256 `157bd58e04351196c7f488e7fdc70d8673c0f7b89aaf3b85764a51da553ab38a`.
- Output/protocol addendum:
  `reports/LOEO_V1284_CAPTURE_CONTROL_V7_TOKEN_OUTPUT_ADDENDUM_20260928.md`,
  SHA256 `471c319b263696a56a5d47652b8795e733dcd20c712cdc2eb1fbc41d794635ca`.
- New control package:
  `work/loeo-v1284-capture-v5-control-v7-20260928/control_manifest.json`,
  SHA256 `cf0829b00a2773c9317526b66ca9d5065472bae61aa007a7ab77f197dc25433c`,
  schema 7, seven files, purpose `v1284_capture_v5_one_shot_control_v7`.

The independent terminal audit now requires one exact released live queue row
whose token, owner, project, run, alias, host, pool, count, CPU, RAM, disk,
duration, created/allocated identity and health match the durable reservation
and prepared config. It requires `gpus=[]`, a finite finish time after child
exit, and retained `process={pid,start}` matching the verified launched child.
Missing or duplicate rows remain inconclusive; foreign or malformed fields
fail. The unlaunched reconciliation path still requires `process=None`.
Reconcile CLI stdout now includes only status, lease ID and plan SHA; raw
token-bearing rows remain in fsynced receipts.

The sealed source-v5 verifier's outcome literal
`PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6` remains a compatibility protocol
label. Successful v7 completion also records `runtime_audit.control_release`
as `v7` and the actual control-v7 manifest SHA256. Head audit must require
those fields independently. Watcher and wrapper are byte-identical to v6;
one-shot request, cancel, release and lost-reply recovery behavior is intact.

`python -B -m unittest discover -s
work/loeo-v1284-capture-v5-control-v7-20260928 -p test_control_local.py -v`
passed 32/32 tests. These include full terminal-row mutation tests,
missing/duplicate rows, malformed retained process metadata, token-free CLI,
source-v5 verifier compatibility, and inherited one-shot queue/release
branches. Independent readback passed seven manifest entries, six Python
ASTs, no caches, and source-v5/parent-v6 seals.

Independent second review of control-v7 is required before a fresh CPU-only
stage; a later GPU request additionally requires exact remote readback,
diagnostic-write canary and fresh live preflight. No target-label/outer-GEFF
read, Kaggle POST, EXPERIMENTS.md edit or current-state report edit occurred.
