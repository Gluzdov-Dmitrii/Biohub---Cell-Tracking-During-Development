# LOEO secondary full fold 0 v1 — sealed local handoff, 2026-09-27

**State:** prepared locally for root review. No SSH/preflight, remote stage, queue request, A100 lease, training, target image or label read, Kaggle notebook push, or competition POST was performed by this preparation.

## Objective and fixed boundary

The preregistration was written before implementation at `reports/LOEO_SECONDARY_FULL_F0_V1_PREREG_20260927.md`, SHA256 `4dba2327d1bb48bc2331d9b18591098e2e9924885c085dd499ce71f9b057241a`. The fixed fold has 56 source `44b6` fit movies / 5,001 windows and 15 disjoint source-inner movies / 1,314 windows; all 128 `6bba` movies are sealed. This package trains only the public secondary UNet/transformer from scratch. It does not establish assembled-x138 honest OOF or a 0.9+ score. The only preselected later target is `6bba_32db13fc`, and even that one-movie inference requires separate graph-locked authorization after full training and the fixed source-inner quality gate.

## Preserved local draft and correction

The first local seal was a draft: plan SHA256 `a9f204a744bd65415098fc925c0323812c11ce51a42b23c13b2aa58c015d06ec`, manifest SHA256 `e839d3e95a87dc4b15eea3795e7d99cb9434f49636705ae22c0ab6e1b62b06a8`. Review found that the public trainer's `seed` argument fixes DataLoader order and worker NumPy RNG but does not seed initial model weights. That contradicted the preregistered initialization seed. The draft plan and bundle were preserved in `work/loeo-secondary-full-f0-v1-20260927/draft_unseeded_20260927/`; neither was staged or run. This is a **superseded local draft**, not a remote failed training attempt.

The final runner now calls `random.seed`, `numpy.random.seed`, `torch.manual_seed`, and `torch.cuda.manual_seed_all` with 20260927 before importing the public trainer and constructing its model. It records the seeded CPU/NumPy RNG fingerprints in output status. A local test repeats all three sampled RNG sequences and verifies the seed call precedes the trainer import. The exact corrected runner in the sealed bundle has SHA256 `3c1931be18753f9f0fa1cca7c16f5f369e60f2d46b4cc986ac1946c9c4d71ace`.

## Final sealed package

- Local package: `work/loeo-secondary-full-f0-v1-20260927/`
- Immutable final plan: `full_plan.json`, SHA256 `138e7f8114ef64979e5c655ac3d3136209a223b87a8ffb0bcfe785f96135b295`
- Exact 20-file bundle: `full_bundle/bundle_manifest.json`, SHA256 `3b479421aa4752a19c8575ed1cd04d73c282efb4be73c6b78445bd1c5a2a686a`
- Attempt: `4d58a75fd839`; remote code/run paths are respectively `code/loeo_secondary_full_f0_v1_4d58a75fd839` and `runs/loeo_secondary_full_f0_v1_4d58a75fd839` under the Biohub project root. Dedicated lease ID: `loeo-secondary-full-f0-v1-4d58a75fd839`.
- Fixed job: 50 complete epochs, 626 fit batches of all 5,001 windows per epoch, 165 inner-validation batches of all 1,314 windows per epoch, batch 8, two workers, math-only SDPA, no pretrained weights. Public trainer/predictor and exact split/source hashes are in the plan and manifest. Checkpoint selection is the public trainer's best source-inner `accuracy × recall`, latest epoch on ties; runner and verifier reproduce this provenance.
- Expected 6–9 A100 hours; one A100, 8 CPU, 32 GiB RAM, 8 GiB disk-growth request, 32,400-second child hard cap, 555-minute lease. No second active Biohub lease or foreign waiting request; physical idle A100 check before reservation and again for the allocated GPU at launch.
- Technical verifier requires 50 finite epoch rows, exact window/batch counts, 71/71 source IDs, zero target IDs/access denials, a finite CPU-loadable public predictor checkpoint with matching SHA, exit0/no timeout, no surviving process/GPU PID and released lease. The separately reported quality gate is selected source-inner `accuracy × recall >= 0.80`, recall `>= 0.80`, accuracy `>= 0.97`; a pass is only a gate to review later outer inference.

Eight focused local tests passed, including source/target guard behavior, fixed split/args, exact temp bundle and immutable plan, AST-valid generated remote scripts, fair queue/physical idle checks, exact 5,001-window coverage, latest-tie selection, math-only SDPA, seed-before-model reproducibility and the 10-hour finite supervisor. `python -m compileall -q work/loeo-secondary-full-f0-v1-20260927` passed. Final plan and all 20 local bundle file hashes were reread successfully. No stage, reservation, launch or reconcile receipt exists.

## Root review commands (not executed)

Run these **sequentially** from the repository root after reviewing the final plan, bundle and live cluster state:

```powershell
python work/loeo-secondary-full-f0-v1-20260927/full_control.py --preflight
python work/loeo-secondary-full-f0-v1-20260927/full_control.py stage
python work/loeo-secondary-full-f0-v1-20260927/full_control.py launch
```

`--preflight` is read-only. `stage` performs exact remote 20-file hash readback and makes the code read-only; `launch` requires its stage receipt, refreshed fair queue and physical-idle checks, and a unique lease. After completion, the existing queue observer/controller should release the lease. Then:

```powershell
python work/loeo-secondary-full-f0-v1-20260927/full_control.py reconcile
python work/loeo-secondary-full-f0-v1-20260927/audit_completed_full.py
```

`reconcile` may release a verified-stopped lease; the independent verifier is read-only and writes one local immutable reconciliation receipt. If a full fold-0 attempt already exists elsewhere or live preflight fails, do not launch this duplicate. If the quality gate fails, stop before any target inference. Do not claim honest OOF 0.9+ from this one component or one movie.

## Newest correction — independent release audit, 2026-09-27

**The “Final sealed package” hashes and attempt above are superseded local evidence.** That bundle/plan pair is preserved byte-for-byte as `work/loeo-secondary-full-f0-v1-20260927/draft_gpu_reuse_hazard_20260927/`: plan SHA256 `138e7f8114ef64979e5c655ac3d3136209a223b87a8ffb0bcfe785f96135b295`, manifest SHA256 `3b479421aa4752a19c8575ed1cd04d73c282efb4be73c6b78445bd1c5a2a686a`. It was never staged or launched. Prelaunch review identified two verifier hazards:

1. The old verifier required `monitor.probe().gpu_pids == []` after RELEASED. That list includes every process on the assigned GPU, so a later tenant could cause a false immutable `AUDIT_FAILED`. The corrected supervisor now embeds the exact GPU-empty observation used for release in its fsynced `supervision/complete.json`. The verifier checks that durable observation, exit, run/lease/GPU identity and ordered release timestamps. A manual `reconcile` release writes a distinct immutable local release receipt with its exact GPU-empty probe. The live probe now checks only this run's PID and process group; later tenant GPU PIDs do not fail the audit.
2. The old CPU predictor check caught any exception, including SSH timeout, and wrote a final failure. The corrected remote check returns structured JSON for a completed model-load failure. SSH/transport or malformed-response exceptions raise `InconclusiveAudit` before the exclusive final receipt is opened; an observation can be retried. Missing exit, unclosed queue and not-yet-visible release evidence are likewise inconclusive.

**Current sealed attempt for review:** `07911298d0f9`; plan SHA256 `af4bbe339c3bb665152028db7861b09501e3ddc093e48406ee067bbb6974baf3`; 20-file manifest SHA256 `49d49d16683505853cd950ae2b088fdc9ff7c21c380fe601d6652263da9b9cb2`; bundled supervisor SHA256 `ac9cf0a20912a3ca390bbc27fa2fdadf0f6f9fa140bdedf48756c8244a2e661e`; unchanged corrected runner SHA256 `3c1931be18753f9f0fa1cca7c16f5f369e60f2d46b4cc986ac1946c9c4d71ace`; local controller SHA256 `40b488ff17f618443f6128b4c9afc0dcbdef00587dd089afb975a058f31c633c`; independent verifier SHA256 `914f1d7d661e22939b9a79166db4556361abe2b11c2aef710c980b99de4d5650`. Unique lease ID `loeo-secondary-full-f0-v1-07911298d0f9`; final code/run paths are `code/loeo_secondary_full_f0_v1_07911298d0f9` and `runs/loeo_secondary_full_f0_v1_07911298d0f9` under the pinned Biohub remote root.

Ten local tests pass, including a synthetic new tenant PID after release, a nonempty release-time PID rejection, manual-release fallback and transient CPU probe failure with **no final receipt**. The current plan and all 20 final bundle files were reverified by hash. The root review commands in the previous section are unchanged and refer to this current final plan. No SSH/preflight, remote stage, queue request, GPU lease, target access or Kaggle POST has been performed for either sealed draft or final attempt.

### Shared-workspace stage update — after local handoff

The prior sentence describes this preparation agent's actions at handoff time. A parallel root workflow subsequently wrote `work/loeo-secondary-full-f0-v1-20260927/full_stage_receipt.json` SHA256 `8713966d833a9abff8958d9b71a58e49a52cbafde46341324d0ebdab7511239b` at 2026-09-27 16:01:39 UTC. Its readback verifies the **current** plan SHA256 `af4bbe339c3bb665152028db7861b09501e3ddc093e48406ee067bbb6974baf3` and exact 20-file manifest SHA256 `49d49d16683505853cd950ae2b088fdc9ff7c21c380fe601d6652263da9b9cb2`. Do not repeat `stage` for this identity. This preparation agent did not stage or launch; no launch receipt was observed at this local check, and no live remote state was queried here.
