# V1284 capture v2 one-shot A100 control v1 — preregistration

Written 2026-09-28 before controller implementation, stage, queue request or
feature capture. This is an infrastructure protocol for the unchanged
`work/loeo-v1284-source-capture-v2-20260928/` 27-file manifest SHA256
`ef81cb60c9ebe9cbe7760dbc189d840f26b338fe101a6bb0c0d7648d742733f1`
and correction prereg SHA256
`64b9905999120c456c7154587c47a0240bdf558fb10bbd4f488dbf1a1e35964c`.
The rejected v1 capture package remains untouched. No checkpoint or capture
plan currently exists for this controller.

## Input and identity gate

For one fold/attempt only, accept a remote Linux plan created by the pinned
v2 `plan_capture.py` after independently verified, source-only, same-fold
primary and secondary full-training `PASS_FULL_TRAIN_QUALITY_GATE` receipts.
Re-run v2 `validate_plan(require_files=True)` against the actual remote
checkpoint/config/audit files before any queue request. Read back the complete
staged v2 package and its exact file manifest; the remote package must match
the pinned local package SHA byte-for-byte and contain no extra files or
`__pycache__`. The plan's source ID set must be exactly fold0 71 `44b6` or
fold1 128 `6bba`, with the opposite 128/71 IDs sealed. Inspect the official
source catalog's `.zarr` symlinks and approved resolved image parents only;
never inspect or open any `.geff` path. The runtime view is created by v2
`run_capture.py` and must contain source images only. Preserve the exact
plan/attempt, model SHA, stage SHA and source IDs in every receipt. Require a
fresh, unused run path and lease ID; no automatic retry or warm start.

## Queue, GPU and lifetime

One `nsu-a100` A100, 8 CPU, 32 GiB RAM, up to 32 GiB disk growth, hard child
cap 28,800 seconds, 510-minute lease. Defer if any other project is waiting
or any other Biohub lease is active. Query the fair queue immediately before
reservation and verify a physical A100 has zero used MiB, zero utilization
and no compute app. After reservation, require a matching `id`, `run_path`,
`alias=nsu-a100`, `state=RESERVED`, `health=CURRENT`, and exactly one GPU UUID;
recheck that allocated UUID is idle before spawning. Write a durable launch
intent before the child. The wrapper starts one child session under
`CUDA_VISIBLE_DEVICES=<allocated UUID>`, offline environment and
`PYTHONDONTWRITEBYTECODE=1`; it records PID+`/proc` start identity, exit code,
hard-timeout flag and any error. The child runs only `run_capture.py --plan`
with `V1284_HEAD` removed. A timeout terminates the whole child group.

Use an observer/controller with bounded heartbeats. Release only after an
exit receipt exists, the recorded PID identity and process group are dead,
and the allocated GPU has no compute PIDs. Capture that exact release-time
probe, then require the raw queue `release` reply to have the same lease `id`
and `state=RELEASED`; otherwise keep the lease unresolved. The controller
records observation, release action/reply and ordered timestamps, with no
unverified RELEASED claim. A later tenant's GPU use does not invalidate the
durable release-time empty observation.

## Independent gate and local validation

A separate read-only auditor rehashes the staged package, plan, model and
audit files, launch/exit/runtime status, child access log and saved release
reply. It requires exit0/no timeout, exact run/PID/GPU/lease identity,
ordered fresh release observation, dead process group, release-time empty GPU,
raw reply `id`+`state=RELEASED`, and a live queue row RELEASED. Missing or
temporarily unreadable artifacts and transport failures are inconclusive and
must not write an immutable terminal failure. Only a complete PASS may emit
the `completion` contract consumed by v2 `verify_capture.py`; that separate
verifier still checks Zarr frame counts and every empty/nonempty shard before
any source GEFF label read. No graph score is produced here.

Before any remote use, synthetic local tests must cover source/audit/stage
hash failures, source-only image inventory, foreign waiting and active Biohub
queue rows, busy and wrong allocated GPU, duplicate launch identity, timeout
and process-group termination, heartbeat versus release, malformed release
reply, transient audit observations, durable release-time GPU-empty evidence,
and compatibility with the v2 completion contract. AST and exact control
manifest readback must pass with zero caches. The controller is implemented
and tested locally only in this task; no SSH, stage, reservation, launch,
label read, Kaggle action or `EXPERIMENTS.md` edit is authorized here.
