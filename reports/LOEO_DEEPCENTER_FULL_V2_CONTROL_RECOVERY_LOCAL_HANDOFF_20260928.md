# DeepCenter reciprocal v2 local handoff — 2026-09-28

## Scope and identity

This distinct local-only successor implements the correction preregistration
`LOEO_DEEPCENTER_FULL_V2_CONTROL_RECOVERY_PREREG_20260928.md`, SHA256
`cbce2a0b7d5d658091b9dc602523232c0edb9507c537a866939dee9390f57fd7`.
The sealed v1 training and control packages were not edited, staged, or run.
The v2 plans pin their v1 parent plan/training/control manifest SHA256 values.

| Fold | New attempt / lease suffix | Plan SHA256 | Training manifest SHA256 | Remote control manifest SHA256 |
| --- | --- | --- | --- | --- |
| 0, source `44b6`, 56 fit/15 inner | `ab73fcf04609` | `da8b9c0abef9f21c148766104539541a2d515bf10a4e5e7e7a7dcc49760cf835` | `31b3ad9b403063c48179198d58e62978f61ac92650c3d42478653a241612d778` | `e6aca868b4f41f32acb27770bdbee45bbc05080b4cb42d0b7b6e3d9e586fb2be` |
| 1, source `6bba`, 102 fit/26 inner | `2d7c829a4bf1` | `f359a1f1e29bdbcce46227a2cac7af525265bddef6dd53bfd5437ddb2930c05e` | `21f3b1907b30a98d1639afb806f46a90cc1849935252a8eabe6b300d90fc4acc` | `4491c5abd6e0cb10a72277d28f89a61f6f26ede39c5107ec606dc8c040d7c4c0` |

Local directories are `work/loeo-deepcenter-full-f0-v2-20260928`,
`work/loeo-deepcenter-full-f1-v2-20260928`, and corresponding
`-control-v2-20260928` siblings. Lease IDs have the
`loeo-deepcenter-full-f{fold}-v2-{attempt}` form. Remote code/run stems use
the same distinct fold/attempt and remain uncreated. The unchanged trainer
SHA256 is `6314efc742acbf67e3fce66033f1e3736a9d0f88de72ebe630b7bba12d5f7425`;
the unchanged explicit split SHA256 is
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.
Two epochs, seed 2026, cold start, full source-inner BCE selection, and the
fixed quality thresholds remain unchanged.

## Control correction

Before a queue request, both staged preflights resolve every approved source
`.zarr`/`.geff` pair, read each source Zarr shape, reject invalid or wrong-ID
links, and calculate exact per-ID fit/inner frame and batch totals. Fold 1
also retains its 10,200/2,600 frame and 1,275/325 batch pins. Fold 0 now
measures all 71 source movies before reservation; its exact totals will be
observed on the cluster, not guessed locally. Launch durably writes
`frame_metadata_receipt.json` before `launch_intent.json` and binds its SHA
to that intent. The final auditor compares the receipt's per-ID frame map and
resolved source targets to the run's independent verifier and source-view
manifest, including plan/split/source-root identity and receipt ordering.

An intent without `reservation_receipt.json` is treated as an ambiguous queue
transaction. Reconciliation takes a fresh exact-ID/project/run-path queue
snapshot. Missing, delayed, duplicate, mismatched, or RUNNING rows remain
inconclusive. For a current RESERVED row, it reads fresh remote run/control
path, matching process/group, and physical allocated-GPU evidence. It issues
one release only if all absence checks pass. A durable release-attempt receipt
precedes that request; transport uncertainty or a raw reply lacking the exact
lease `id` and `state=RELEASED` forbids retry. The normal remote supervisor
now also records a one-shot release attempt and raw reply before declaring
completion. Local reconciliation sees that remote attempt and will not issue
a second release. The standalone sidecar monitor entry point is disabled;
the sealed supervisor remains the execution path.

Controller SHA256: fold 0
`84fecd2c0c112ba152d22161a11c7f2145eec0eb7b2c0d14b7491d9ad2708d26`,
fold 1 `64b6ae978dcc58941fc1a7fb2fb31b1cf474e59cd45853ed1d4800306d424076`.
Independent auditor SHA256: fold 0
`197fed434b3cd949c081b7213d6ba2d335e9fd01ebd4654d3cf95fd59cbcf23d`,
fold 1 `72f0c91beea9683f7fb471fb690647183e6bbff8887e5c7bc28dc99b64b78f03`.
The shared, locally SHA-pinned recovery source is
`6b71159139873242a33b5f42d05fc44e3e6edcd4762d3ace9048f03e869deb0e`.

## Local validation and limits

- Existing training tests: 6/6 per fold. Existing control tests: 10/10 fold 0
  and 13/13 fold 1. Unchanged explicit-trainer tests: 3/3.
- New adversarial recovery tests: 11/11 per fold, including accepted-then-lost
  queue reply, no reservation receipt, delayed/missing/wrong queue identity,
  RUNNING row, live worker/group, busy GPU, remote-probe failure, exact safe
  release, wrong release reply, transport uncertainty, remote-supervisor
  one-shot behavior, and no duplicate request/release.
- `verify_bundle.py` passed both nine-entry training bundles. The local
  readback script `work/loeo-deepcenter-v2-local-build-20260928/verify_local.py`
  passed every training and remote-control manifest file/size/SHA, confirmed
  the old six v1 seals unchanged, parsed all 14 Python files per fold in memory,
  and found no bytecode caches. Generated preflight, stage, launch, fold
  verifier, and recovery transport scripts AST-parse in synthetic tests.

No SSH, remote stage, queue call, GPU allocation, target image/GEFF read,
Kaggle action, `EXPERIMENTS.md`, current-state, or x138 file mutation occurred.
Remote Linux process/GPU behavior and actual fold-0 frame totals remain
unverified until a separately authorized stage/preflight. Independent review
of these exact hashes is required before that step. The x138 assembler's old
DeepCenter auditor SHA pins remain stale and require a separate versioned
update before any source emission.
