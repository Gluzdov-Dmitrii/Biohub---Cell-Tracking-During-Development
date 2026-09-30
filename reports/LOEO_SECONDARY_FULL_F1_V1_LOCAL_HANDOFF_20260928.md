# LOEO secondary full fold 1 v1 — sealed local handoff, 2026-09-28

**State:** local package prepared and verified. The only cluster access in this preparation was read-only `6bba` source metadata and symlink-parent inspection. No remote stage, queue request, GPU lease, training, `44b6` outer image/label read, Kaggle kernel push, or competition POST occurred. Do not stage or launch while the active fold0 secondary lease `loeo-secondary-full-f0-v1-07911298d0f9` is open; refresh its queue/process/release state before either action.

## Fixed source-only experiment

Preregistration: `reports/LOEO_SECONDARY_FULL_F1_V1_PREREG_20260928.md` SHA256 `e3c06b8188bd610619a112d90549788199491370c12ff1eaeaa951330f0f4d13`, written before implementation. Pinned split SHA256 `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`: fold1 fits 102 source `6bba` movies and selects on 26 disjoint source `6bba` movies; all 71 `44b6` IDs are sealed outer targets. Read-only per-movie source metadata SHA256 `584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7` yields **9,949 fit / 2,443 inner** windows, 1,244 / 306 batches at batch8. No `44b6` label path was opened. The 128 source GEFF symlinks resolve under approved `pilot_single_6bba` (12) and `honest195_missing/train` (116) parents.

Full 50-epoch source-only fit uses seed `20260929` before model import, unchanged public trainer/model/augmentation, math-only SDPA for forward and backward, two DataLoader workers, one A100, no warm start, and latest-epoch tie selection on source-inner `accuracy × recall`. A trainer window audit and independent final audit require every exact epoch count and each pinned per-movie window count. The quality gate is selected source-inner `accuracy × recall >= 0.80`, `recall >= 0.80`, `accuracy >= 0.97`. One component passing this gate permits only review of a later outer-inference registration. The preselected outer movie `44b6_341df25f` was chosen by minimum SHA256 of the ID string without image/label inspection. This experiment cannot alone establish assembled x138 OOF or local 0.9+.

## Current immutable package and hashes

- Local package: `work/loeo-secondary-full-f1-v1-20260928/`
- Unique attempt `2e8e17588e2d`; lease ID `loeo-secondary-full-f1-v1-2e8e17588e2d`
- Plan `full_plan.json` SHA256 `bd99d3ebe23a7038e6c56a2f6ea39b668966b2e5cfedd47bd1b2525ff378ba06`
- Exact 21-file bundle `full_bundle/bundle_manifest.json` SHA256 `3349a7619ab47fcfa0c2a12a50c3ee276b56b6068873d979488f28b6e4298f6a`
- Bundled trainer runner SHA256 `d59da08bceade68c7b8125c051be42faffe651e6add4f6cb6b777268e30f891c`
- Local stage/launch/reconcile controller SHA256 `21b8857675d6eaf30f2818935c1419ca84978352a9450322b6613e71e1bbe423`
- Independent completion verifier SHA256 `df1eb40bfcc0237e7ad57c421f599d59437dc9dec08ea30c8fe5ee409f5000c8`
- Source metadata `source6_window_metadata.json` SHA256 `584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`
- Remote code path: `code/loeo_secondary_full_f1_v1_2e8e17588e2d`; remote run path: `runs/loeo_secondary_full_f1_v1_2e8e17588e2d` under the pinned Biohub project root.

One A100, 8 CPU, 32 GiB RAM, and 8 GiB disk growth are fixed. Child hard cap is 64,800 seconds (18 hours); lease is 1,110 minutes (18 hours 30 minutes), with no automatic retry. The stage preflight rejects another active Biohub lease or a foreign waiter; launch repeats fair-queue checks and checks the allocated A100 has zero memory, utilization, and compute PIDs. Staging verifies every remote bundle file hash and makes the code read-only. The supervisor fsyncs the exact process/group/GPU-empty observation used at release; the independent verifier checks that durable observation instead of later tenant GPU PIDs. A transient predictor SSH/load transport failure leaves the audit inconclusive with no final immutable failure receipt.

## Local validation and execution handoff

Ten focused local tests passed using `python -B`, covering split and source-only guard, metadata, seeded model/DataLoader RNG, 9,949-window coverage, latest-tie checkpoint selection, math-only SDPA, fair queue, clean release-time evidence, later-tenant PID tolerance, and transient-safe verifier behavior. The final plan and all 21 bundle files passed exact hash readback. AST parsing passed for 27 local/bundled Python files. No `__pycache__` or `.pyc` is inside the sealed bundle.

After fold0 is independently verified released and a fresh queue/physical-GPU check passes, the parent may run these in order from the repository root (none were run in this preparation):

```powershell
python -B work/loeo-secondary-full-f1-v1-20260928/full_control.py --preflight
python -B work/loeo-secondary-full-f1-v1-20260928/full_control.py stage
python -B work/loeo-secondary-full-f1-v1-20260928/full_control.py launch
```

The existing observer/controller owns heartbeats and release. After the one run exits, reconcile once and then run the independent verifier:

```powershell
python -B work/loeo-secondary-full-f1-v1-20260928/full_control.py reconcile
python -B work/loeo-secondary-full-f1-v1-20260928/audit_completed_full.py
```

If stage or launch preflight fails, preserve that state and wait; do not bypass the fair queue. If the fixed quality gate fails, stop before any outer inference. Neither result can be promoted to honest assembled OOF without held-out provenance for the other learned components and fixed graph policy.
