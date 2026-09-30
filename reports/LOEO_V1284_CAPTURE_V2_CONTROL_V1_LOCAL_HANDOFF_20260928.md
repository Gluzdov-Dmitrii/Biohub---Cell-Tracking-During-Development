# V1284 capture v2 one-shot controller — local handoff

**State:** source-only local implementation and synthetic checks complete. No
fold primary/secondary checkpoint pair or sealed capture plan exists yet. No
SSH, stage, fair-queue request, lease, GPU work, label read, Kaggle action or
`EXPERIMENTS.md` edit occurred in this task.

The protocol was preregistered before controller implementation at
`LOEO_V1284_CAPTURE_V2_CONTROL_V1_PREREG_20260928.md`, SHA256
`7be60943244f4a049d458ca2f432beabcea14408955798ce4158e9ef4573b132`.
Its “Written 2026-09-28” date is **Asia/Novosibirsk local time**; UTC was
still September 27. The prereg file remains unchanged. The separate V1284
v2 capture source package remains unchanged, manifest SHA256
`ef81cb60c9ebe9cbe7760dbc189d840f26b338fe101a6bb0c0d7648d742733f1`.

## Sealed local package

`work/loeo-v1284-capture-v2-control-v1-20260928/` contains seven files plus
`control_manifest.json`. The manifest SHA256 is
`c7b57925bee3a1908221344d8b57602aec86e73c6f9afa220f28634d9ee583d1`.
Its independent file hashes include:

| File | SHA256 |
| --- | --- |
| `control_contract.py` | `c2f51c8f917e9eb53fd57cbc45dd46301e92cc42b0e48c381502a6406d0bbf5a` |
| `capture_control.py` | `c37790022a1bab6bbeb7e9257a774233d7cc247e172883bc3b5db8c164d381ef` |
| `capture_wrapper.py` | `b65473f01f346b501148026898b4a156ba453b1b19af1ac1f9a04f4da45eb890` |
| `capture_watch.py` | `cd5d5925039cc35cb6bc0e41e3b390ea7f13e74672e695c61864e7d5400be5c1` |
| `audit_capture_runtime.py` | `f276192efb5617e8e870d000cc7e05db582903cdf8157f36b7d23b544dbbd740` |

`prepare` is future read-only remote preflight. It accepts exact v2 code/plan
paths and re-runs `validate_plan(require_files=True)` against actual same-fold
primary and secondary weight/config/audit files. The stage's complete v2
manifest, source IDs, 71/128 `.zarr` image symlinks and approved resolved
parents, runtime modules and physical GPUs must read back exactly. It does
not open `.geff` data or a V1284 head. `launch` is a distinct, one-shot
future mutation: fresh queue preflight, one reserved A100, exact allocated
UUID/idle/stage recheck, durable intent, byte-identical wrapper, child group
hard cap 28,800 seconds and offline/no-head environment. The local detached
watcher heartbeats every 45 seconds and releases only from a matching exit,
dead child identity/group and GPU-empty observation; it preserves the raw
queue release reply. Ambiguous release is held for manual reconciliation.

The independent read-only auditor rehashes remote stage/model audit files,
runtime config, launch/exit/status/child identity and denied-access log. It
compares the saved observation and raw reply to a live RELEASED queue row and
dead run-owned process identity. Only a complete pass writes a v2-compatible
`completion.json`; its run-time view must also contain only the exact source
image symlinks. Missing or transport-unstable evidence is inconclusive and
does not write a terminal receipt. The separate v2 `verify_capture.py` still
must audit source Zarr frame counts and every empty/nonempty shard before
source label matching.

## Validation and remaining runtime gates

`python -B -m unittest discover -s
work/loeo-v1284-capture-v2-control-v1-20260928 -p test_control_local.py -v`:
**12 passed**. Tests cover exact fold IDs and opposite-prefix rejection,
stage/image gate, contention, wrong/busy allocated GPU, duplicate launch,
exact wrapper bytes without the queue token, timeout process-group kill,
heartbeat versus release, malformed raw release reply, failed child release,
transient audit with no completion, positive independent audit and v2
completion contract. All six Python files AST-parse, all seven manifest entries
hash/read back exactly, and there is no `__pycache__` in the package.

The 8-hour hard child cap allows at most **225 seconds per fold1 movie** on
average for 128 movies, before startup/model load and finalization; fold0's
71 movies have at most about 406 seconds each. Actual V1284 capture runtime
has not been measured. The fixed cap and no-retry rule remain in force; full
fold completion is not guaranteed. The watcher is a detached process on the
local host, so the host and its SSH path must stay active through the run;
loss or ambiguity leaves the lease unresolved for read-only reconciliation.
Actual Linux dependencies, GPU capture, fair-queue responses and release
behavior remain untested. A passed local `completion.json` would need exact
byte transfer to the remote verifier; that transfer and shard verification
are future gates.
