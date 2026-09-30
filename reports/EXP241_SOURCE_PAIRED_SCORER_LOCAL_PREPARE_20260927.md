# EXP241 source-inner paired scorer — local-only preparation

The fixed candidate and promotion rule were frozen in
`EXP241_FIXED_TWO_PEAK_SOURCE_CANDIDATE_PREREG_20260927.md` SHA256
`6e602f1374f74282493541cfaa214de6bdff82396e22eec8995674e48bd4fe0f`.
The independent label-free candidate graph receipt is
`exp241_fixed_two_peak_source_candidate_verified_20260927.json` SHA256
`90d0b3882cdcb53092bdce37f1dd619e3566e5cbd8f1b7e6dbcc4c630947cad4`;
it pins graph result SHA256
`488e4fce3944cb87d01bc0dba65be31b9f5a5146e57fef755394935ed919e824`
and graph bundle manifest SHA256
`95e04f9358b629f03d76103761491e3e8ec44a86d55f6c45310842da9453a48f`.

## Sealed scorer

- Local package: `work/exp241_source_paired_scorer_v1_20260927/manifest.json`
  SHA256 `bd585c361c68b8b9e67bd1ebe0ba132a11c682dd5dec2116de6f78b36e714975`.
  It seals exactly 12 files. Config SHA256
  `9be1124f92a3d9600ac424f16163ab36d03e1456d175ae0f69a24651744b26a2`;
  runner SHA256
  `174cefb283b330e71b65ec4cae57702f21ac72086dabec87053f19edfd3d6bf9`.
- Local preparer: `scripts/prepare_exp241_source_paired_scorer_local.py`
  SHA256 `804db2698bfcb4b55a10113e8da806371e627a964438315bcf37c5cb9e9fa14f`.
  It only copies pinned local source files, then seals after the independent
  graph receipt exists. It has no SSH or scorer invocation.
- Pinned predecessor: independently verified source-inner v2 result SHA256
  `4dc9035c64691416a070d9a2c67948a13b859ccccf14123e1a6538b2e54f680f`,
  verification receipt SHA256
  `eb8de29eea2aec8ee926f8b90fb46aed05b594029e440018dbbe579f27b675d6`.
  The copied evaluator is the current organizer commit
  `075fc5f5a52d11077f9dc2b074644618f26939e2`; runtime check pins
  tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`.

The one-shot runner checks exact package file set and hashes, independent graph
receipt and graph result hashes, all 19 ordered candidate CSV hashes, original
byte prefixes, added row IDs/counts, graph topology, historical source scorer
receipts, image metadata, and the pinned metric environment. It writes and
fsyncs `no_label_gate.json` before any `.geff` read. Its audit hook restricts
GEFF access to the exact 19 source-inner trees.

After that gate, it replays the parent historical rows and current organizer
per-movie rows and cohort summaries within `1e-12`, and writes a separate
`parent_replay_pass.json` before any candidate metric call. It scores the fixed
candidate against the same 19 source GEFF trees in that process. Official
`metric.summarise` pools the 8, 11, and 19 movie rows; edge/division TP/FP/FN
and annotated-frame node TP/FP/FN are summed. The fixed promotion decision
requires score gain `>=+0.005` in each cohort and pooled19, plus no decline
beyond `1e-12` in adjusted edge Jaccard, division Jaccard, or either official
or micro node recall in either cohort. The output includes per-movie and pooled
added-node matched/unmatched and added-edge matched/valid-unmatched/ignored
counts on annotated frames. It verifies GT tree hashes before and after and
records both scores even if the promotion gate fails.

## Local checks and correction

Eleven synthetic tests pass across
`tests/test_exp241_source_paired_scorer_local.py` SHA256
`78d6e4e6234556fdd8431ac8b89e2f447ad3f1820cdd77b40a7173f74152989d`
and `tests/test_exp241_source_paired_stage_launch_verify.py` SHA256
`f1185d7ccc2dc398f47a887bf7878599e8f1ace005517a9ca112e23d20306858`.
They cover exact original prefix, changed-prefix rejection, one-frame edge
invariant, two-chain interleaved row IDs, the fixed promotion rule, `1e-12`
replay tolerance, node sufficient-stat pooling, sealed stage/launch templates,
read-only verifier GEFF denial and a missing-division NaN case. Python
compilation and the final exact 12-file manifest readback pass.

The first local draft manifest SHA256 `1d3e4f169769a46215b095ed9de562f0de99f171822d219bc1850d3b61d7a751`
assumed all appended nodes preceded all appended edges. The graph writer appends
two nodes then two edges **per chain**. A two-chain synthetic case exposed this;
the runner was corrected and locally resealed before remote stage or label access.
The subsequent local threshold check was tightened from `0.005-1e-12` to the
literal preregistered `>=0.005`; the final seal above includes that correction.

## Root handoff

One-shot stage, launch and independent completion verifier scripts are prepared:

- `scripts/stage_exp241_source_paired_scorer.py` SHA256
  `f3b4812c3f803a95d668f4fe8a77d9e1c0669562e7111b136ebee7650dda3d69`;
- `scripts/launch_exp241_source_paired_scorer.py` SHA256
  `1161fca1c350a7194da4d3a4b94d7e95a4958ffbea71d010bb1fe9a900c77a19`;
- `scripts/verify_exp241_source_paired_scorer.py` SHA256
  `187f25cb248155bca3bdd2a5a398961583eed5801e8907ceffd5fd480aa69715`.

All three default review modes completed locally with no SSH. Root can run,
from the repository root, in order:

```powershell
python -B scripts/stage_exp241_source_paired_scorer.py --execute
python -B scripts/launch_exp241_source_paired_scorer.py --execute
# After worker exit 0, no timeout and no surviving child:
python -B scripts/verify_exp241_source_paired_scorer.py --execute
```

The one-shot stage script writes exclusive local intent and receipt, and stages
the 12 sealed files to
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp241_source_paired_scorer_v1_20260927`
with exact remote byte readback. The launch script writes its own exclusive
intent and receipt and starts one bounded CPU process with the
pinned Python 3.11 environment, `PYTHONOPTIMIZE=0`, `CUDA_VISIBLE_DEVICES=''`,
`POLARS_MAX_THREADS=4`, `OPENBLAS_NUM_THREADS=4`, `-B`, and
`--manifest-sha256 bd585c361c68b8b9e67bd1ebe0ba132a11c682dd5dec2116de6f78b36e714975`.
The runner itself limits affinity to CPUs 24–27, 16 GiB address space,
6000 CPU seconds and 7200 wall seconds; the outer wrapper bounds wall time to
7500 seconds. Its dedicated output path must be
absent before launch.

After exit0/no timeout, independently verify staged files, no-label gate,
parent replay receipt, full 19-movie result, official sufficient-stat arithmetic,
all GT before/after hashes, fixed promotion Boolean and absence of a surviving
worker. The independent verifier denies `.geff` opening and validates the
result against the pinned predecessor receipt and official metric summarise
without rereading source labels. A failed quality gate is still a completed,
reportable experiment.
No source GEFF was opened, scorer process staged/launched, remote scorer result
read, GPU lease used, target data accessed, Kaggle kernel pushed or competition
POST made in this local preparation.
