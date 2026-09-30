# Biohub — conserved competition, 2026-09-30

Competition finished September 29. Big Cells preliminary private result: **0.917, rank1082/4020**, down715. Best recorded public: **0.956**. Do not resume historical experiment queues.

Read [Russian postmortem](reports/POSTMORTEM_20260930_RU.md) and [primary final writeups](reports/PUBLIC_FINAL_WRITEUPS_20260930.md). [Closeout receipt](reports/CLOSEOUT_20260930.json) records actual preservation and cleanup, including local deletion limitations.

## Preserved

- `scripts/`, `kaggle_notebooks/`, `tests/`: own training, physical baseline, graph comparison, pinned evaluation, guarded one-shot submission and contract checks.
- `docs/`, `reports/`, `EXPERIMENTS.md`: positive/negative evidence, exact provenance and validation limitations.
- `final_kernels/`: current source and metadata of centered EDGE, edge relink and Horaz all199 E10/E20, downloaded read-only after close. Exact submitted version refs remain in the live API snapshot; current pulls alone do not certify byte equality to those versions.
- Local `work/`, `outputs/`, `publication/`: selected small scientific receipts/source snapshots; omitted from public Git.
- Local `local-artifacts/models/`: deduplicated Frontier90 checkpoint content; mapping in `reports/CLOSEOUT_COPY_MANIFEST_20260930.json`.
- Local `local-artifacts/remote-evidence/`: 4241 SHA-verified remote source/receipt files, including Horaz source-only reciprocal E10 fold checkpoints and all199 E10/E20. Mapping in `reports/CLOSEOUT_REMOTE_MANIFEST_20260930.json`.
- Local `goals-log.txt`: user file preserved, excluded from public Git.

## Restore boundaries

This checkout has its own `.git` and no dependency on the original Desktop folder or Codex worktree. Git history and current useful changes are preserved. Model binaries are local only; retain this archive if their exact bytes matter. Kaggle source metadata records external public model/support-pack datasets, which would need to be mounted again. Re-download competition data and rebuild pinned environments for any future authorized reproduction; no raw images, submission CSV replay or temporary virtual environments belong to the conserved solution.

Archive verification: 19 guard/code-contract tests passed. One historical EXP212 dataset-manifest test was deselected because its old checkpoint package was intentionally not retained. This is not a claim that the whole historical test suite or all Kaggle notebooks run without restored data/dependencies.

## Final measurements

| Candidate | Public | Private |
| --- | ---: | ---: |
| centered EDGE | .956 | .917 |
| edge relink v2 | .955 | .917 |
| x162 | .953 | .917 |
| own Frontier90 | .922 | .899 |
| Horaz all199 E10 | .910 | .887 |
| Horaz all199 E20 | .908 | .889 |

Standings are preliminary pending Kaggle verification. Local CV is development evidence, not an exact private forecast; the postmortem preserves split/routing/metric caveats.
