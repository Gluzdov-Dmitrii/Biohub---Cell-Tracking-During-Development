# EXP241 fixed two-peak source graph — local preparation

The fixed label-free candidate is built from preregistration
`EXP241_FIXED_TWO_PEAK_SOURCE_CANDIDATE_PREREG_20260927.md` SHA256
`6e602f1374f74282493541cfaa214de6bdff82396e22eec8995674e48bd4fe0f`.
It pins the independently verified EXP240 receipt SHA256
`68ea60bc71f0dbca5b0c8664515b027a195a73d11a5bd88be18850c72c6dc161`,
EXP240 manifest SHA256
`5bd3fd540e6df6a9b357965d0fd7c37556fe8afc2844274537cc94fb1873c370`,
and the remote EXP240 result SHA256
`696c951c11a68817ee45505c98173f1a9d89e200477016de992d4504425961b2`.

## Sealed local bundle

`work/exp241_fixed_two_peak_source_candidate_v1_20260927/manifest.json`
SHA256 `95e04f9358b629f03d76103761491e3e8ec44a86d55f6c45310842da9453a48f`
contains the config SHA256
`df7d704cbbc6c029c5f5b026efb5e17a827ff818dd87d34f5b8846789f9e21ff`
and CPU builder SHA256
`8bf6d4d21eda076ed45f6a3308673b1c346a253ab464accab3e2fb3fb26bf096`.
The builder pins all old sealed source-only input receipts and graph/peak hashes,
installs a deny-all GEFF/data audit hook, and fsyncs its no-label gate before
parsing CSV or NPY values. It checks every EXP240 selected chain against the
original graph and peak record. For chains sorted by `(seed ID, p1, p2)`, it
retains the original CSV bytes as a prefix and appends two nodes and two edges
with consecutive unique IDs. The expected cohort additions are source44
1,670 nodes/edges and source6 716 nodes/edges across exactly 19 graph CSVs.

The independent verifier checks exact original byte and row preservation,
selected peak keys and probabilities, geometric legality, expected node/edge
rows and IDs, unique dataset IDs, finite in-bounds coordinates, adjacent-frame
edges, indegree/outdegree limits, and exclusive new paths. It records candidate
CSV hashes, the result SHA and the durable no-label gate SHA. Its receipt is
`reports/exp241_fixed_two_peak_source_candidate_verified_20260927.json` only
after successful remote readback.

## Local validation

`python -B -m pytest -q tests/test_exp241_fixed_two_peak_source_candidate.py --basetemp work/_pytest_exp241_graph_builder`
gave **5 passed**. AST parsing of the builder, stage, launch, verifier and tests
passed. The launch wrapper and independent remote verifier templates compile.
All three default local review commands passed without SSH:

```powershell
python -B scripts/stage_exp241_fixed_two_peak_source_candidate.py
python -B scripts/launch_exp241_fixed_two_peak_source_candidate.py
python -B scripts/verify_exp241_fixed_two_peak_source_candidate.py
```

Stage script SHA256
`babdcfaf6460dedc70cf955afb48ca37cc6b8db482f1ec6b9d742356d7f102e1`,
launch script SHA256
`4de3e91b68eb5c1a0d3ec39093ec9c045d52ba37bedc942c9d521f36c8231801`,
independent verifier SHA256
`664089e3b70be7d513183ac49dbc3eed8380707bf35b3857ad108fec4bc62493`,
and test SHA256
`30c310d5c495414828acaf0e2ed4b486b8669fd97f81c68f7b823c2c3622c446`.

## Root stage and verification commands

After review, from the repository root:

```powershell
python -B scripts/stage_exp241_fixed_two_peak_source_candidate.py --execute
python -B scripts/launch_exp241_fixed_two_peak_source_candidate.py --execute
# After bounded worker exit0 and no timeout:
python -B scripts/verify_exp241_fixed_two_peak_source_candidate.py --execute
```

The bounded worker uses the pinned current-organizer Python on CPU 24–27,
16 GiB RAM, 2,400 CPU seconds and a 2,800 second wrapper timeout, with
`PYTHONOPTIMIZE=0`, explicit `__debug__`, and CUDA hidden. Remote code and run
paths are `code/exp241_fixed_two_peak_source_candidate_v1_20260927` and
`runs/exp241_fixed_two_peak_source_candidate_v1_20260927` under the pinned
Biohub root on `nsu-quadro`/`prepost`.

No remote stage, launch, graph creation, GEFF/source-label access, target-data
access, metric score, GPU use, or Kaggle POST occurred in this local preparation.
The graph candidate is not cleared for scoring until the independent graph
verifier succeeds and its receipt SHA is pinned by the separate source scorer.
