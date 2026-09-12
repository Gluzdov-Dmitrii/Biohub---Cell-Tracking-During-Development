# Biohub compact checkpoint — 2026-09-12

## Proven result

- Honest frontier: EXP209 pooled OOF **0.6815218332750073** on 175 reciprocal
  embryo-held-out movies (116 forward + 59 reverse).
- Delta vs EXP206: **+0.0030675361973779847**; paired movie-bootstrap 95% CI
  **[+0.0014898445239081154, +0.004628095713171574]**; P(delta>0)=1.0;
  minimum LOMO **+0.00289736899354609**.
- Forward: 44b6-trained checkpoint -> held-out 6bba, centroid radius (3,5,5),
  registered relink, min track 8. Reverse: 6bba-trained checkpoint -> held-out
  44b6, EXP191 DeepCenter gap 4.5/threshold .20/min span 8.5/cap .05, min 6.
- Exact checkpoint SHAs: forward `dc06a794...fdbb`, reverse
  `5c0f835...99366`, DeepCenter `ea0b53cb...b118e`.
- Main evidence: `reports/EXP209_SELECTED_CENTROID_CONFIRMATION_RESULT_20260912.md`,
  `reports/exp209_selected_centroid_confirmation_result_20260912.json`, and
  `outputs/research/exp209_selected_centroid_confirmation_20260912` (38-file
  manifest SHA `1d9bd5c8...ff8a`, 1.31 MB; output directory is git-ignored).

## Production/submission state

- Private Kaggle model dataset is ready:
  `dmitriigluzdov/biohub-exp209-pooled-oof-frontier-models`, 15 expected files,
  exact weights plus source manifest, no predictions or labels.
- Kernel `dmitriigluzdov/biohub-exp212-exp209-oof-frontier-production` reached
  versions 1-3 but all failed before model loading/inference; no
  `submission.csv`, no guarded POST, and no LB quota consumed.
- v1 mixed newly resolved NumPy 2.4.6 with old SciPy; v2 preserved an old Polars
  lacking `Float16`; v3 imported NumPy before replacing NumPy/SciPy on disk.
- Stop condition is active. Do not push v4 without a new continuation decision.
  The likely repair is to install dependencies before importing NumPy/SciPy,
  or force only Polars/Zarr while preserving Kaggle's NumPy/SciPy pair. Then
  rerun tests, record a new source SHA, clean-run/audit, and only then use
  `scripts/submit_code_file_once.py`.
- Live competition submissions: ref `56177715` (unrelated GOLD_PUBLIC slot 1)
  remained PENDING with empty score/error and zero bytes. Daily limits at the
  last read: 1 used, 4 available. EXP209/EXP212 was **not submitted**.

## Tested hypotheses worth retaining

- Keep: EXP209 forward intensity centroid (3,5,5) + EXP191 reverse; both
  directions improve EXP206 and paired uncertainty/LOMO are positive.
- Reject: source-selected reverse centroid (2,3,3), delta -0.00639 in reverse.
- Reject: EXP210 label-free pruning safety veto; full-cohort delta -0.000249,
  CI crosses/below zero, all LOMO negative.
- Reject: EXP207 feature TTA; +0.000554 but CI crosses zero.
- Promote only to unfinished confirmation: EXP207 detector D4, development
  delta +0.011946 with positive CI/LOMO.
- Reject: naive U-Net weight soup (EXP141) and dual-detector logit fusion
  (EXP142, target delta -0.02786).
- Unsolved: division TP remains 0/138 FN; EXP209 improves association/pruning,
  not division recovery.

## Next hypotheses, ordered

1. Fix EXP212 packaging only, then clean-run and audit the existing source. Do
   not alter model policy in the same retry.
2. Complete EXP211 detector-D4 confirmation: forward_00 and forward_01 are
   structurally complete; six staged chunks remain. Open no scientific values
   until the all-eight no-metric gate passes.
3. Validate an unseen-embryo production selector. EXP209 is cross-fit OOF; its
   current 2-um agreement selector for new embryo IDs has no OOF score. Prefer
   a third labelled embryo or nested source-only rule before claiming it as
   private-validated.
4. Train a final all-labelled-data checkpoint only after fixing a full-data
   training contract; report it as a deployment fit derived from CV, not as
   the checkpoint that scored 0.68152.
5. Pursue division only with a separately validated high-precision mechanism;
   do not trade the established edge/recall gain for unvalidated forks.

## Compute state

- SSH identities verified now: `nsu-quadro -> prepost`, `nsu-a100 -> ngpu01`,
  `nsu-pc -> desktop-7t0uo8i\\user`.
- EXP211 GPU leases are RELEASED; no Biohub GPU job is active. Six retained
  chunk directories are active dependencies, not cleanup candidates.
