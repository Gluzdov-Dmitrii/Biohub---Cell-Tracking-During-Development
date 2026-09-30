# EXP240 source-only two-peak chain screen — local preparation

This is a label-free CPU feasibility screen under the preregistration
`EXP240_SOURCE_TWO_PEAK_CHAIN_FEASIBILITY_PREREG_20260927.md` SHA256
`e2f9547dd3b3d874f53c03c93c90e663e04d1de1317eb0d668cabdec78e21e35`.
The EXP238 verified CPU audit receipt SHA256
`04cdb945f1b955ea2960b819706ea03a9c1c0a37f8ed4715052035f37111b3af`
is used only as a pin; no label/case rows from that audit enter this screen.

## Local bundle and validation

- Immutable bundle: `work/exp240_source_two_peak_chain_v1_20260927/manifest.json`
  SHA256 `5bd3fd540e6df6a9b357965d0fd7c37556fe8afc2844274537cc94fb1873c370`,
  six sealed files. Config SHA256 `555fc2843e5cee813a362ba43064abcabe04ef61e42242224aee2d0059c34e23`;
  runner SHA256 `fd8bdc456ac16d30d321528d5505058caed6e6d0e865533bee40227ea73e5bfb`.
- Exact copied cache receipts: source44 `1b27c1db...`, guarded source44 recheck
  `ca95fc50...`, source44 optimization correction `9a797e6e...`, source6
  `9272f5f0...`. The builder checked the parent graph CSV/receipt hashes against
  the separately sealed source-inner19 config, plus the EXP238 cache plans.
- Five focused geometry/guard tests passed. Python AST and all remote templates
  compiled. Optimized Python was rejected by the runner. Stage, launch and
  verifier default review modes passed locally without SSH.
- The runner installs a deny-all `.geff` and data-tree audit hook, checks the
  exact receipts/graph/cache hashes, and durably fsyncs a no-label gate before
  loading graph rows or peak NPY values. It counts all legal pairs, distinct
  seeds and deterministic conflict-free chains. Only JSON counts/selection
  evidence are written to a new run; original graph edges remain untouched.

## Root-only stage, run and read-only verification

The reviewed local commands, from the repository root, are:

```powershell
python -B scripts/stage_exp240_source_two_peak_chain.py --execute
python -B scripts/launch_exp240_source_two_peak_chain.py --execute
# After bounded worker exit0 and no timeout:
python -B scripts/verify_exp240_source_two_peak_chain.py --execute
```

Stage script SHA256 `ee4ac6a56122c82b358f749ea77768f045544ef447e10d08071b7520e941a719`;
launch script SHA256 `0b9710b43ff3773055cc7dc3d7573f51b09fe0c127e83b1450c5d627df3f4154`;
independent verifier SHA256
`2e00e581dddf1298c7adc48c75be6815f1ab386117967c2b121f23deed86b0f1`.
All three use `PYTHONOPTIMIZE=0` and explicit assertion guards. The worker is
bounded to CPU 24–27, 16 GiB, 2400 CPU seconds and 2800 wrapper wall seconds,
with CUDA hidden. The new remote code/run paths are respectively
`code/exp240_source_two_peak_chain_v1_20260927` and
`runs/exp240_source_two_peak_chain_v1_20260927` under the pinned Biohub root
on `nsu-quadro`/`prepost`.

No stage, launch, remote read, `.geff` access, target access, graph mutation,
metric/score, GPU lease or Kaggle POST has occurred in this local preparation.
No feasibility or quality result is claimed until the one-shot worker and
independent verifier complete.
