# V1284 fold0 v4 CPU stage preflight blocker — 2026-09-28

Independent control-v5 static review passed and was appended to
`EXPERIMENTS.md` at 09:22 UTC, pinning seven-file control manifest SHA256
`9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`.
The remote-attempt preregistration SHA256 is
`40107695c8501b9de96f62257d3e9fff101921b35edccc7cc9d86ba570605161`.

A fresh one-shot local identity `loeo_v1284_capture_f0_v4_ba382850b115`
was created, with lease ID `loeo-v1284-capture-f0-v4-ba382850b115`.
It differs from failed parent `loeo_v1284_capture_f0_v3_1de3d2be98c3`
in both version and 12-hex suffix. The local exclusive fsynced
`work/loeo-v1284-f0-v4-cpu-stage-20260928/loeo_v1284_capture_f0_v4_ba382850b115/stage_intent.json`
has SHA256 `a97e251c5b59196bb0e30c33a4d2d5bc8a939df6a0f3ddbed5c686b74521bd44`.
The exact local source and control archives were independently unpacked and
compared byte-for-byte with their sealed package files, SHA256
`e19df7bc90f864b47f67435661dff5d73ccad18e701472040d9d4312dabbfd1c`
and `20977c45e8d3e62425c0e4f38fca42d2a89b632acbb90786f6d03e8762e4b62b`.
The first local archive fsync attempted a read-only descriptor and failed;
the same complete archive was then verified and fsynced with a writable
descriptor before the stage intent. No remote action occurred in that step.

Read-only `nsu-a100` path preflight reported all six exact code, inert
control, plan, run and archive paths absent. An isolated read-only
`nsu-quadro` queue status returned 370 rows and zero matching lease rows in
4.12 seconds. The combined pre-stage queue status then timed out at 90
seconds; a bounded retry using remote `timeout 20s` timed out locally at 35
seconds. Error receipts are
`work/loeo-v1284-f0-v4-cpu-stage-20260928/loeo_v1284_capture_f0_v4_ba382850b115/prestage_queue_error.json`
SHA256 `a05583c1b9fb01f27229fb47388243b6f59a1bf4e1cec93dcc92e8c9c1b909d1`
and `prestage_queue_error_retry.json` SHA256
`a5dde78767bf33ba37472c10eefb73ebee02498c674c32cc04ed0b5a496460de`.
Basic SSH `printf READY` succeeded on nsu-a100 and nsu-quadro, so the
unresolved condition is the queue status read, not general SSH reachability.

The exact pre-stage policy requires a completed live queue status. **CPU
stage is paused before upload.** No remote source/control copy, plan, CPU
canary, queue mutation, GPU launch, target-label read or score occurred for
this v4 identity. Resume only after a fresh exact queue read succeeds and
confirms zero matching lease rows; then repeat remote path absence and
continue the workflow draft
`reports/LOEO_V1284_CAPTURE_F0_V4_STAGE_CANARY_WORKFLOW_DRAFT_20260928.md`
SHA256 `7d4afabf6988fbe4b39a104f0b800515acc8c34761c65219386701bb193508e2`.
