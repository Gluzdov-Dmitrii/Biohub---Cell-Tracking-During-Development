# Fold0 V1284 source-v5 remote attempt — control-v7 correction addendum

Written 2026-09-28 before any f0 v5 attempt identity, archive, remote stage,
queue request or GPU launch. The append-only parent preregistration is
`reports/LOEO_V1284_CAPTURE_F0_V5_REMOTE_ATTEMPT_PREREG_20260928.md`
SHA256 `37fded2b05a958dc984354676d38a8c14c73d81cec16bd8a3e2860a9a68be739`.
Its source-only cohort, same-fold model receipts, feature boundary and
one-shot queue policy remain fixed.

Independent review rejected locally sealed control-v6 manifest SHA256
`4d41d66d3ab65392c37689e72b3c767de733abad81942c0aab90f0ceeab7eced`
because its independent terminal audit did not bind the full released live
queue identity. It must not be staged or used to launch this attempt. The
distinct control-v7 manifest SHA256 is
`cf0829b00a2773c9317526b66ca9d5065472bae61aa007a7ab77f197dc25433c`
(schema 7, purpose `v1284_capture_v5_one_shot_control_v7`). Its prereg and
token-output addendum SHA256 values are respectively
`157bd58e04351196c7f488e7fdc70d8673c0f7b89aaf3b85764a51da553ab38a`
and `471c319b263696a56a5d47652b8795e733dcd20c712cdc2eb1fbc41d794635ca`.
Use only this exact control-v7 package after an independent second PASS.

The sealed source-v5 verifier still requires the literal
`PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6`. In control-v7 this is a
compatibility protocol label. A successful independent completion must also
state `runtime_audit.control_release="v7"` and bind the exact control-v7
manifest SHA256. The downstream head audit must independently require all
three fields and verify the terminal queue row's full lease/resource identity,
`RELEASED/gpus=[]`, and retained PID/start metadata matching the launched
and stopped child.

No fresh stage may start until source-v5 and control-v7 have independent
PASS. After that gate, CPU-only source-v5/control-v7 stage and production
interpreter diagnostic-write canary may proceed while another job owns the
GPU; no queue request follows without a separate fresh live preflight. Any
failure freezes the new attempt. No target-label/outer-GEFF read or scoring
is part of this workflow.
