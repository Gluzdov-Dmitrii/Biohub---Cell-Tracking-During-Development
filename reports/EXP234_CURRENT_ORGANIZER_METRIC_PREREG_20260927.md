# EXP234 current-organizer target175 paired rescore — preregistration

Status: **prepared locally only**. No remote environment or scorer was staged or
launched, and this work opened no target labels. The historical scorer output
and STOPPED handoff remain immutable.

## Question and fixed comparison

The EXP214-pinned historical evaluator gave EXP234 0.7426705533442897 and
EXP214 0.7427291486246141, but its division implementation uses weak-component
spanning. Re-evaluate the **same** 175 EXP234 graphs and the **same** 175 EXP214
baseline graphs under organizer commit
`075fc5f5a52d11077f9dc2b074644618f26939e2`, without changing inference,
thresholds, graph bytes, embryo assignment, or historical output. This is a
leakage-controlled reciprocal evaluation on historically exposed domains; it
will not be called pristine OOF or a Kaggle leaderboard score.

The organizer metric files are SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`
for `metrics.py` and `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`
for `division_metrics.py`. The isolated runtime must use Python 3.11 and
`tracksdata` commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, with
the exact package versions in
`scripts/requirements_current_organizer_py311.txt`. Intended interpreter:
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/current-organizer-py311-e13cf-v1/bin/python`.
This runtime specification and synthetic contract are reusable by a later
EXP227 current-metric scorer; no EXP227 source is changed here.

## Immutable inputs and label boundary

- Historical 12-candidate/8-baseline no-metric gate SHA256
  `37b07134c9ff27bf3eaf318d51185fdefb11737cb4721a1bf2fdd390dd94a664`;
  historical result SHA256
  `124541f647432c7b01a9e2223ef76524927ff2587ec95f8609f7b1765e43c07c`.
  The new scorer reruns the exact historical no-label graph/release/hash gate
  and requires its entire gate object to equal the sealed one before metrics.
- Historical staged scorer SHA256
  `64cc0fe20c0a7b14eb18d2170470ada1cd1e04a0e196ad3d82e67f7957409877`,
  code manifest SHA256
  `58f42f9b7640680739092025e106fe755da7c53df4fdccf496f9fd3f36e90e80`,
  and score config SHA256
  `45c9a8931e8e8ff243c0e8f09840ee0530a5855fa42b1d26eb91430ab31055a3`.
  The original STOPPED handoff SHA256 remains
  `336757ebebf325712f22ffc80d432d35a274654a81d5fc60666b8f0cb7ae9bc1`.
- Before GEFF access, validate the new code manifest, organizer source hashes,
  isolated runtime versions/commit, local-fork synthetic contract, exact
  175-image metadata shapes/scales, 12 candidate CSV/status/plan/receipt hashes,
  eight EXP214 CSV/receipt hashes, source selections, and RELEASED leases.
  Write a new `no_metric_gate.json` in a new output directory first.
- Only after that gate, hash all 175 sibling GEFF trees, then load each once
  for paired EXP214/EXP234 evaluation with the same scale, 7 µm matching and
  estimated total-node count. Rehash all GEFF trees after scoring and require
  equality. Preserve the tree manifest and per-movie rows.

## Prepared artifacts and promotion gate

Local immutable bundle: `work/exp234_current_organizer_v1`;
code manifest SHA256 `ae071f81ae1886a91d5c882f46b67a7ba949cc11822f6760ba77843206bf3260`;
score config SHA256 `6a7eaca7fa58249c34695788370b0799b616cb0a483a8081d367c570d9757e95`.
Prepare receipt: `reports/exp234_current_organizer_prepare_20260927.json`
SHA256 `f0e9e2cfac4a32bccaae89e0ccad6cc93a414f3200cd80a76ff574606aa98eb6`.
Intended new remote run:
`runs/exp234_current_organizer_score175_v1_20260927/output`.

The future result qualifies only with clean CPU-only exit, no timeout, an exact
prelabel gate, all 175 rows for both arms, finite current-organizer summaries,
unchanged GEFF tree hashes, verified process release, and a readback of the
entire new output and its hashes. Report both current-metric arm scores and
their paired delta, embryo-specific summaries, and the historical-metric
identity separately. Stop at any failed gate; no Kaggle POST is part of this
rescore. No score or direction of change is presumed from the historical delta.
