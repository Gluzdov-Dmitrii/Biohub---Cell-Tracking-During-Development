# x138 assembled reciprocal inference v1 — local preparation handoff

Date: 2026-09-28 Asia/Novosibirsk. Status: **local preregistration, source assembler, label-free validator and synthetic tests complete; no runnable real fold source emitted**.

## Sealed local evidence

| File | SHA-256 |
| --- | --- |
| `reports/LOEO_X138_ASSEMBLED_RECIPROCAL_V1_PREREG_20260928.md` | `1f9bf32a0eb588a419ecfb10b023a17bc7c7dc73497177ce2b8788c8149a5e0d` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/assemble.py` | `aa8319ac04d17181bfddd21f9b57479b5b0d9d9509062c1ffa15ea67c5c09acf` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/test_assemble.py` | `b4b0ec9ad0e93a041ba6c508daec3821b502887c5cb33584879a8ec6e5857518` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/README.md` | `60172796802209479a169a77ded3ce87e7c4964ea9a373403ef9ea852acb5b87` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/plans/fold0_chunks.json` | `5d54bffd5b650cb5a2f21b996463e6663f6fd50bdba57a44e002fc8da5cdd2bd` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/plans/fold1_chunks.json` | `66eb3bda00b9ca762c9bbe10eee6fb0a8ab0af74b85c713693cc8ab3df1b9e7d` |
| `work/loeo-x138-assembled-reciprocal-v1-20260928/sealed_package_manifest.json` | `1c8b16b5dcc85eb9b0524e56f8062072eb46a2261b2acf89638c3c6ddd110336` |

The sealed package manifest covers 56 files: this preregistration, code/test/README, two fold plans and 50 per-chunk manifests. Independent readback found all 56 SHA-256 values exact. No checkpoint or assembled source is in the package.

## What is frozen and locally verified

- Original x138 base SHA `eace83c4e4ec8f967aa03edf516acdbb3eb35bbcfaf02fbef93465fa26680775`; x162 clamp source SHA `d761174044943f68f0bf0501c8691ab496b28611779a5a232d13ba27e01c0c51`; split receipt SHA `26a9324c0a9556708ffa2bf0f1e230f842c0ef1581ac22d19af28fd15b7ba142`.
- Fold0 source `44b6` to 128 `6bba` IDs in 32 chunks; fold1 source `6bba` to 71 `44b6` IDs in 18 chunks; union exactly 199 unique IDs. Max four whole embryos per fresh process/working directory.
- In-memory transformed source compiles for both folds. Published primary/secondary/DeepCenter lookup and V1284 head glob are replaced by exact same-fold bundle paths. Original graph policy is frozen; deadline degradation and repair fallback call sites raise. Only the final writer gets x162 upper-bound coordinate clamping. Disabled target-label validator and post-process sweep cells are omitted.
- `check-bundle` rehashes the support Python manifest, four checkpoint/config files, role-specific raw independent audits, fold/source/selection identities, V1284 capture parents and attestations. It rejects arbitrary raw audit JSON even when a matching PASS attestation is supplied. `check-output` checks process identity/exit0, dynamic per-frame detector diagnostics, no degradation/fallback, x162 clamp diagnostics, graph/schema/coordinate bounds and exact hashes. `check-reciprocal` checks 50 exact chunk receipts and 199 unique IDs, while retaining a separate full-candidate runtime gate.

Validation command: `python -m unittest discover -s work/loeo-x138-assembled-reciprocal-v1-20260928 -p test_assemble.py -v`. Result: **9 passed**. Tests are synthetic and do not establish actual model accuracy, GPU execution or receipt authenticity.

## Hard blockers before any real source emission or OOF

1. For **both folds**, obtain real primary, secondary, V1284 head and DeepCenter source-only checkpoints, configs, selected epochs, exact byte SHAs, terminal independent training/capture/selection audits and an immutable four-role bundle. Fold0 secondary also needs its separate saved-release-reply gate.
2. Replace the current V1284 capture v2 verifier/control v1 with distinct corrected versions and independently review their complete runtime receipts. The current capture controller has fail-open denied-access, stale probe, process-group termination and `.geff` path-order hazards; its current PASS string is insufficient. The independent V1284 head audit preregistered in `reports/LOEO_V1284_HEAD_AUDIT_V1_PREREG_20260928.md` must be implemented and pass for each fold. Production auditor pins are intentionally `None` until those corrected sources are reviewed and hashed. The `assemble` CLI therefore blocks today even for a synthetic complete bundle.
3. Build exact image-only views, run each chunk in a fresh child process, collect independent exit and diagnostics receipts, then verify all 50 outputs and measure full-candidate end-to-end runtime with margin. Lock all prediction hashes before any separate outer-label score. No outer labels were read here.

Public x138 LB 0.953 is historical public evidence, not reciprocal OOF. The 199 labeled embryos have historical development exposure; an eventual reciprocal result must retain that limitation. No SSH, staging, lease, GPU, Kaggle action or `EXPERIMENTS.md` edit occurred in this preparation.
