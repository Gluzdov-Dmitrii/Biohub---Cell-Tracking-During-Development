# Distinct V1284 fold0 source capture v5 on NSU

Date: 2026-09-28. Track: local source-only research, no Kaggle submission or outer-fold score.

## Parent, scope and hypothesis

Parent f0 v4 identity `loeo_v1284_capture_f0_v4_ba382850b115` failed on its first source movie because the generated predictor wrote diagnostics to absent `/kaggle/working`. A second active coordinate-manifest write targeted the same root. Its immutable log, exit and watcher receipts remain preserved. No features were verified and the failed identity must not be retried.

The distinct source-v5 package moves those two diagnostic writes and its cache directory under the validated run-local `work_dir`. Generated model, feature extraction and graph code are otherwise unchanged. The hypothesis is operational: source-v5 can capture source44b6 V1284 features without Kaggle-only filesystem assumptions. This does not predict an OOF gain.

## Fixed source and model inputs

- Source-v5 29-file manifest SHA256 `3b8407413dc2837991dbf0d33b597543dcd8eac8c58e6039ea80c47164889a72`; prereg SHA256 `d9fed996a751c572d12db5f88a688e237952168caea351c63ce11b8b254215e7`. Generated predictor LF SHA256 `c5b3a5d80f8a2d7c7e6aad19352a92ef0b62893c27d6d39e0eab885b230bd85f`; V1284 module LF SHA256 `940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`.
- Control-v6 seven-file manifest SHA256 `4d41d66d3ab65392c37689e72b3c767de733abad81942c0aab90f0ceeab7eced`; prereg SHA256 `7daf5d61fcd6ae88e4f5ef1bed057964d08628f2b83d3d7bd616c7875acbd4a4`. Runtime outcome literal: `PASS_CAPTURE_V5_RUNTIME_RELEASE_CONTROL_V6`.
- Source cohort: exactly 71 approved `44b6` image `.zarr` IDs, partitioned into 56 fit and 15 inner by the sealed split. The 128 `6bba` IDs are outer and disjoint. Do not enumerate/open outer `.geff` labels. Use the same independently audited full source-only primary and secondary f0 checkpoints and final receipts as the prior capture plan; rehash all six component files in the fresh plan.
- New plan schema 5, purpose `v1284_source_image_capture_v5`, identity `loeo_v1284_capture_f0_v5_<fresh-12-hex>`; a matching distinct control lease ID, code/plan/run paths and no alias to the v4 failed run.

## Sequential promotion gates

1. Obtain independent static PASS for source-v5 and control-v6 exact seals. No remote stage before both. Create a fresh immutable plan and CPU-only stage intent for the new identity.
2. On cluster CPU, check exact remote paths absent, source images and component receipts; upload only the exact staged archives. Rehash every remote source/control byte and plan. Run the production interpreter canary: generate both LF files, import the real child, and **execute both diagnostic JSONL write blocks** under a new isolated run-local directory. Reject any executed `/kaggle/working` write. Record source IDs, no target-label access and run absence.
3. Only after independent CPU-stage readback, run control-v6's fresh full live preflight for exact lease absence, no foreign waiting/other active Biohub request and physically idle A100. Make at most one durable-intent queue request; preserve raw request/reply, launch, watcher and release evidence. Ambiguous replies use the v6 one-shot reconciliation path without duplicate mutation.
4. Require complete source feature files for all 71 source IDs, exact output hashes, empty denied-access log, no outer GEFF access, clean exit, matching process identity, and exact queue `RELEASED/gpus=[]` with dead process/group/GPU PID. An independent terminal audit must PASS before head fit. A failure freezes this new attempt; a further attempt needs a separately preregistered successor.

The downstream head-audit successor must pin the actual source-v5/control-v6 manifests and real completion receipt before promoting a head. Graph inference on outer images and locked-graph scoring remain separate stages. No successful capture, source-inner score or public leaderboard value is an honest outer OOF score.
