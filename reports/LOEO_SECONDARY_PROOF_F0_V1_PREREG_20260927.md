# LOEO secondary fold-0 one-movie inference-path proof v1 — preregistration

**Registered before executable preparation on 2026-09-27. State: local preparation only.**
Identity: `loeo-secondary-proof-f0-v1-20260927`. This is a technical path proof and one preselected directional observation. It cannot establish full OOF, private performance of assembled x138, a 0.9 score, or a Kaggle submission gate.

## Fixed inputs and inference

- Parent: successful 16-update fold-0 pilot `work/x138_loeo_runtime_v3/pilot_final_reconciliation.json` SHA256 `65e17c3a9ddd1ad1962587dd2615f093d37eac226d82d7e73b24aafb1edb352a`; source-only 56 `44b6` fit movies and 15 disjoint source-inner selection movies, zero outer `6bba` use. Checkpoint SHA256 `e90453d53b7e4485752222f74b816269aa23f0e9eaa8c12ac18292c23a555122`.
- Selection and configuration: immutable `work/x138_loeo_fold0_proof/plan.json` SHA256 `c2504ffccc3d1b4eb2f0ca55a88dc12af0ed0e408277c7654839d57ce400afb7`; target `6bba_32db13fc`, selected by minimum SHA256 of ID among the 128 sealed outer IDs before image or label inspection. One input view entry, `6bba_32db13fc.zarr`, only. Resolved source-image path must be the approved `honest195_missing/train` parent. No target `.geff` in the input view and no other embryo ID.
- Public standalone `predict_unet_transformer.py` SHA256 `c44e771ba5980b820f93091e03a303c25dfe8f3232e501f54dc9565731c234b9`, imported without changing its prediction functions. Public trainer/model source SHA256 `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`. Load the exact pilot checkpoint and checkpoint `config.json`; no fallback. Run all 100 frames with math-only SDPA, detection threshold `0.99`, XY-flip TTA, 3 µm pool kernel, edge softmax and `>0.5`, UNet batch 4, no ILP, no evaluation call or threshold sweep. Do not use the assembled x138 inference graph.
- One queue-free, physically idle A100; queue lease 40 minutes, independent process-group hard cap 1,800 seconds with TERM then KILL. No GPU reuse or same-identity retry. If runtime, queue, source or access evidence fails, preserve the failed receipt and stop.

## Sealing and independent checks

Before a GPU request, stage the immutable bundle under a new code path with exact file/hash readback, checkpoint and config readback, approved single symlink resolution, absent `.geff` view and fresh queue/physical GPU evidence. A Python audit hook records and rejects all target `.geff`, alternate embryo, nonapproved data and network access during inference. A hook denial is failure even if the model exits zero. The denied log must be exactly empty.

The GPU runner must write exactly one `6bba_32db13fc.geff` prediction tree, no other `.geff`, then seal every tree-file path/size/SHA256 and the whole tree-content SHA. A separate read-only verifier requires process exit 0, no hard timeout, zero denied accesses, released lease and dead process group/GPU PID. It checks GEFF readability; node IDs and finite `t,z,y,x`; all `t` in 0–99 and coordinates in the `[64,256,256]` volume; every edge endpoint exists, moves exactly one frame, has at most one incoming/two outgoing links; and counts nodes, edges and divisions. A missing or failed graph receipt blocks scoring.

Only after this inference receipt is verified may a separate CPU scorer read the single selected target GEFF label tree. It must revalidate the inference gate and immutable prediction SHA before its first target-label read, use current organizer commit `075fc5f5a52d11077f9dc2b074644618f26939e2`, metric SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444` and division metric SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`, target voxel scale and `estimated_number_of_nodes` from its GEFF metadata. Report one-movie adjusted edge Jaccard, raw edge Jaccard, node recall, division TP/FP/FN, edge TP/FP/FN, graph counts and complete score. Any missing metadata or nonfinite metric is a failure. No model selection or retuning from this one result.

## Execution boundary

This preregistration authorizes building and testing a local package only. Root must review exact stage/launch commands, refreshed queue and idle-GPU state, and the sealed bundle before any remote mutation or GPU request. No target label tree is opened during preparation. No Kaggle competition POST is authorized.
