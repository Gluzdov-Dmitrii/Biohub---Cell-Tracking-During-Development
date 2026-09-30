# LOEO secondary fold-0 one-movie proof v1 — local handoff, 2026-09-27

**State: prepared locally; no remote stage, launch, lease, inference, target-label read, CPU score or Kaggle POST.** Root is the sole operator of a later GPU proof job. This is one technical inference-path proof and a preselected directional observation for standalone secondary only, never assembled x138 OOF or a 0.9 claim.

## Sealed identity and inputs

- Identity/code/run/lease: `loeo-secondary-proof-f0-v1-20260927`, with distinct remote `code/` and `runs/` paths. No shared `EXP242` number and no reuse of v3 pilot paths.
- Before executable preparation: `reports/LOEO_SECONDARY_PROOF_F0_V1_PREREG_20260927.md` SHA256 `275f331fbe4448d7a393a0b3d4dd2b2c12c68c3385d6cbe011b84427e2ef8dbc`. Parent plan `work/x138_loeo_fold0_proof/plan.json` SHA256 `c2504ffccc3d1b4eb2f0ca55a88dc12af0ed0e408277c7654839d57ce400afb7`; fixed target `6bba_32db13fc`.
- `work/loeo-secondary-proof-f0-v1-20260927/bundle/manifest.json` SHA256 `f4f5cada6ddcf52956568665ee7e10af6fc05565439e33fe96657361cc63beea` seals 27 exact files, including public standalone predictor SHA256 `c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`, public trainer SHA256 `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`, v3 16-update checkpoint SHA256 `e90453d53b7e4485752222f74b816269aa23f0e9eaa8c12ac18292c23a555122`, checkpoint config SHA256 `e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`, and pinned current-organizer metric sources. The checkpoint/config were copied read-only from the completed v3 remote run and hashed locally.
- `work/loeo-secondary-proof-f0-v1-20260927/launch_plan.json` SHA256 `182c7397b439e3f2e116fe059f2ef93799b84a884ec251132af72bd4d8f88468` fixes a 1,800-second process-group hard cap and 40-minute lease. It has a private queue token; avoid pasting its contents into logs or reports.

The unchanged public predictor is imported directly. The runner fixes math-only SDPA, full 100-frame input, detection 0.99, flip-XY TTA, 3 µm pool, edge softmax threshold 0.5, UNet batch 4 and no ILP/evaluation. It creates one input-view symlink only, rejects any `.geff`/alternate embryo/network access with a fsynced denial log, then seals exactly one predicted GEFF tree and checks graph nodes, coordinates, forward adjacent edges and degrees. The separate CPU scorer imports the pinned current-organizer metric and opens selected target GEFF only after a fresh independent graph and lease-release receipt passes again.

## Validation and overlap

Six label-free local tests passed, including legal/adverse graph topology, GEFF/other-embryo/network denial logging, overlap/other-project queue rejection, a receipt generated through the actual independent verifier schema and tamper/failed-exit rejection by the CPU score gate, plus generated remote stage/launch/verify/score-launch template compilation. `py_compile`, exact manifest readback and both local `review` modes passed. Test source: `work/loeo-secondary-proof-f0-v1-20260927/test_proof_local.py` SHA256 `b03ac4bb58f9e648fe6613027e47e90180f90d408cc0753e5852dc2fd0f917db`.

One read-only remote preflight passed during local preparation: code, upload-stage and run paths all absent; no same-identity lease or waiting other-project request; selected source image symlink resolves to the approved parent; shape `[100,64,256,256]` and required quantiles present. This is volatile queue evidence, so repeat `preflight` immediately before any stage and again with `--staged` before launch. No overlapping proof run was found.

The earliest unsealed scorer draft incorrectly compared a `plan_sha256` field to the bundle SHA. It was corrected to require `bundle_manifest_sha256` **before** the 27-file manifest above was sealed. The sealed `bundle/run_score.py` SHA256 is `54a47c24dc6efa239191b5a4067282921553137bde21723018ce37291508609d`, matching the local source. Later local tests exposed two generated-command placeholder substitutions (`PYTHON`/`CODE` inside `PYTHONDONTWRITEBYTECODE`); only the non-bundled control scripts were corrected, and their generated templates now compile. There was no prior remote stage or worker for these drafts.

## Exact root-operated sequence

All commands run from the repository root. Control source `work/loeo-secondary-proof-f0-v1-20260927/proof_control.py` SHA256 `c83a3c89e18c2618ea7fb52b678b6155b12ed654f3dd83341beeb91a68b6bb06`; independent verifier and scorer control `verify_and_score.py` SHA256 `de75a0fe724cf89b6dcde1293dc3cc136b0810e3132c8ff5004a41832a1c27c5`.

```powershell
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py review
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py preflight
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py stage
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py preflight --staged
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py launch
python work/loeo-secondary-proof-f0-v1-20260927/proof_control.py monitor
python work/loeo-secondary-proof-f0-v1-20260927/verify_and_score.py verify
```

`stage` uploads to a fresh `.upload` path, hashes every remote file and atomically renames to the final code path. `launch` requires the exact stage receipt, a fresh queue check, a newly reserved A100 with zero compute process/memory/utilization, and writes launch intent before starting the supervised wrapper. The observer/controller retains the lease until process-group and GPU PID absence; `monitor` is read-only. One failed or timed-out identity stays recorded, with no silent retry. `verify` reopens only the **predicted** GEFF, independently recomputes tree SHA and graph topology, and requires exit 0, zero denials, dead process group/GPU PID and `RELEASED` queue state before it writes local `verified_inference.json`.

Only after `verify` succeeds, the separate CPU stage/launch sequence is:

```powershell
python work/loeo-secondary-proof-f0-v1-20260927/verify_and_score.py score-stage
python work/loeo-secondary-proof-f0-v1-20260927/verify_and_score.py score-launch
python work/loeo-secondary-proof-f0-v1-20260927/verify_and_score.py score-verify
```

`score-stage` copies only the independent receipt and verifies remote hash readback. `score-launch` requires that exact receipt and released GPU lease; the CPU wrapper hides CUDA and caps scoring at 30 minutes. The scorer rechecks exit, graph audit and immutable tree SHA, writes a durable `pre_label_gate.json`, then opens only the selected target GEFF. `score-verify` requires CPU exit 0, a finite one-movie score and both gate/result receipts. No score exists at local handoff.
