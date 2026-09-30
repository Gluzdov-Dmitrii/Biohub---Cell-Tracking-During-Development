# EXP241 v1 failure reconciliation and v2 local correction — 2026-09-27

## V1 sealed failure

The read-only reconciliation receipt is
`reports/exp241_source_paired_scorer_v1_failure_reconciled_20260927.json`,
SHA256 `8cf1410b6f175b42c97344ad125713136577e68d9e3a84a9a56840333b2deb76`.
It ties the exact v1 stage and launch receipts to the remote manifest,
launch, wrapper, child, exit, worker log and sole output file hashes.
The worker exited 1 without timeout. The sole output was
`output/no_label_gate.json` (SHA256
`086fbe5937234b9607fd2fcceb8866bf181a2a081cafb2f9022e8dff91fc6177`).
The worker traceback stopped at runner line 422, the assertion comparing
`prior["no_label_gate_sha256"]` with `SOURCE_GATE_SHA`; the first
`audit.score_cohort` call is at line 427. No parent replay or candidate
metric ran and no source GEFF was reached. The reconciler itself denied GEFF
access and only read the pinned prior result and run artifacts.

The archived prior result SHA256 is
`4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f`.
Its actual no-label gate SHA256 is
`735496f5cf6dca2e24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e`.
The v1 runner instead pinned
`735496f5cf6d2a24aed7e0649647709b13f58a0f1eb93a357d9c379b7bf52e`.
This is a transcription error in a pre-label dependency check. The v1
package, remote code/run, stage receipt and launch receipt remain unchanged.

## V2 sealed correction

The distinct v2 package is
`work/exp241_source_paired_scorer_v2_20260927`; its manifest SHA256 is
`ed8c7ac72c5a3f73d30570d24133f4aff7124b4e7dbf52d9e0a6cfe098424ce1`.
The runner SHA256 is
`975f79879739c791219c0f7bbe024a452d56d28c4ceea1415af350bccae20955`,
and config SHA256 is
`251062a7bbccb65d2219d78ede6d09bb617088d79905b02edd53fb06aea6685c`.
Compared with v1, only the runner and config changed. The runner edits are
the exact corrected source gate pin, new output run path and V2 seal status;
the config edits are the new output run path and V2 seal status. The other
ten package files are byte-identical to v1. The candidate graphs, metric
source, cohort lists, thresholds, scoring and promotion logic are unchanged.

The new local regression test checks the corrected pin against both the
v1 remote failure reconciliation and the independent archived prior source
verification receipt. It also checks the prior result SHA, graph result/gate
pins, organizer and metric source pins, v2 command/path and exact two-file
delta. Thirteen EXP241 local tests passed. The stage, launch and verifier
default review modes passed with no SSH. No v2 remote stage, launch or GEFF
read was performed in this preparation.

## One-shot root handoff

The v2 scripts are separate from v1 and use an exclusive v2 run and
receipts. Stage requires the exact v1 failure receipt above before remote
mutation. Script SHA256 values:

- `scripts/stage_exp241_source_paired_scorer_v2.py`:
  `0285833237922bc135ef7e1fb51b549b6552a7479d2ac261df2ee17d793907a9`;
- `scripts/launch_exp241_source_paired_scorer_v2.py`:
  `c4210f6b41d00f639bd9d21c94d40c153dad5e40b698a96a4f05d7b1e9471237`;
- `scripts/verify_exp241_source_paired_scorer_v2.py`:
  `006e049d71b2de807319d23623064ade0a8305bc92d7ce90c15eddafbad44961`.

Root may execute in order:

```powershell
python -B scripts/stage_exp241_source_paired_scorer_v2.py --execute
python -B scripts/launch_exp241_source_paired_scorer_v2.py --execute
# After exit 0 without timeout:
python -B scripts/verify_exp241_source_paired_scorer_v2.py --execute
```

The completion verifier is read-only and denies GEFF. It checks exact
stage/launch/exit/worker identity, the no-label gate, 19-row parent replay,
official per-cohort and pooled sufficient-stat arithmetic, the fixed
promotion decision, source GT before/after hashes and worker absence.
EXP241 remains source-only; no target, GPU or Kaggle POST is involved.
