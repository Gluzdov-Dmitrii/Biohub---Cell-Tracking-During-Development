# V1284 capture v3 one-shot control v2 — local handoff

**State:** distinct source-only local correction complete; no checkpoint pair,
capture plan, SSH, stage, fair-queue request, lease, GPU work, GEFF read,
Kaggle action or `EXPERIMENTS.md` edit occurred. The rejected control v1 and
capture v2 packages remain unchanged.

The correction preregistration is
`LOEO_V1284_CAPTURE_CONTROL_V3_CORRECTION_PREREG_20260928.md`, SHA256
`fd373ca958322bf7537d6d5ab951b7328eb6e3e05c07656979e058bb0a039d8f`.
The pinned capture v3 27-file manifest SHA256 is
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`.
The successor controller is
`work/loeo-v1284-capture-v3-control-v2-20260928/`; its seven-file
`control_manifest.json` SHA256 is
`befdd03f885c05fcd3e16e970f7db7214eae23787174d3f2707494bb5f496eda`.
Use that SHA as the external `--expected-control-manifest-sha256` at future
read-only preparation and independent audit. It is not derived from the
mutable package at audit time.

## Corrected gates

The new controller and wrapper require the exact capture v3 package, v3
plan/attempt, same-fold source IDs and independently passed primary/secondary
model audit files. Queue fairness and physical idle A100 gates remain before
reservation; the allocated GPU is rechecked before the one-shot launch.
The wrapper now checks the entire process group after leader exit. Timeout
cleanup sends SIGTERM, waits a bounded grace, sends SIGKILL to surviving
descendants even when the leader exited, and refuses to claim dead-group
cleanup if any live member remains. Its wait budget leaves room for cleanup
under the 28,800-second hard cap.

The watcher probes again after any queue `started` RPC. It records probe
start/end and release-call start/reply times, requiring the release reply
within 20 seconds of the actual probe end. It still requires exact launch/
exit identity, dead PID and group, allocated-GPU compute PID emptiness and
raw queue reply `id` plus `state=RELEASED`.

The independent auditor requires an existing regular, zero-byte
`denied_access.jsonl`, with SHA256 of the empty file. It confirms an absent
log twice before calling it a failure; transport or changing observations
remain inconclusive. It rehashes the executed remote wrapper, launch intent,
runtime artifacts, staged capture package, plan and model/audit files, then
checks a live RELEASED queue row. Only its completion includes
`runtime_audit.outcome=PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2` and the
capture/control manifest, plan, denied-log, wrapper, intent, runtime artifact
and queue-row evidence required by capture v3 `verify_capture.py`. A watcher
receipt alone fails the v3 completion contract.

## Local validation and limits

`python -B -m unittest discover -s
work/loeo-v1284-capture-v3-control-v2-20260928 -p test_control_local.py -v`:
**16 passed**. Synthetic regressions cover watcher-only completion rejection,
missing access log, changed intent/wrapper hashes, leader exit with surviving
group, failed group cleanup, long queue `started` RPC followed by a busy GPU,
malformed release reply, transient audit evidence, and positive v3 completion
compatibility. All source files AST-parse, the complete package hashes back
to its manifest, and no package cache directory is present.

This is a local synthetic control proof. Linux dependencies, real process
groups, remote source-image inventory, fair-queue behavior, throughput and
physical GPU observations remain untested. A future remote run requires the
preregistered two full-training quality receipts, fresh v3 plan, exact stage
readback, fair queue and physical idle A100, then independent runtime and
shard audits. The source labels remain closed until those gates pass.
