# EXP227 target6bba all116 wait-safe finalizer: local preparation

Status: **PREPARED, NOT RUN**. Chunk07 v2 has no completed launch result at preparation time. No target labels were opened, no scorer was run, and no remote mutation, GPU launch, Kaggle POST, or final receipt was made by this preparation.

## Immutable inputs

- Original recovered coordinator STOPPED receipt SHA-256: `8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3`. Its first seven chunks contain 102 accepted graph and receipt hashes; its chunk07 v1 launch is intent only.
- V2 local prepare SHA-256: `ff1b87073ca1bd7ecbf48999265a89e2559c2ff85ddc3fdf2f8475cf5aaba910`.
- V1 cancellation successor audit SHA-256: `ed9755fdfeb1b19846845c9858ab05e825902011350bc43abe19f1f3afba0d3f`.
- V2 stage SHA-256: `498a4cf13537bfffa9a90f601e4f909838583e3f334fc1d8b458c55f33bb3d3e`; config SHA-256: `d796b7def03ef1a56d0303b9af6ddc0c1e58c69fd58ab97dc2b858c69942d7b3`; remote manifest SHA-256: `a828a02ef88bd313a30da12aca8eb2a956337c3641c4dc2851e49e50a203fade`; plan SHA-256: `583fdae80ed8145ceca92d2405e69a6093b26700acc8986540a5f0ace6afcbd2`.
- Frozen assignment, selected checkpoint and source preregistration are revalidated through `coordinate_exp227_target6bba.frozen_inputs()`.

## Check-only and receipt mode

After the reviewed v2 attempt actually launches and finishes, substitute its actual integer attempt number for `N`:

```powershell
python scripts/finalize_exp227_target6bba_waitsafe_v2.py --attempt N
```

The default reads local receipts, remote queue/process/graph output and does not write a receipt. It requires the exact launched attempt, any earlier safe wait or cancelled lease, all eight exit-zero and no-timeout supervisor releases, no surviving worker/group/GPU process, a fresh final queue release snapshot, exact revalidation of the first 102 graph and receipt hashes, and the last 14 graph/receipt hashes and graph invariants. The remote graph verifier installs a no-label audit hook before reading image metadata and graph CSVs.

Only after review of that successful check-only output, create the separate sealed final receipt once:

```powershell
python scripts/finalize_exp227_target6bba_waitsafe_v2.py --attempt N --write-receipt
```

Output path: `reports/exp227_target6bba_all116_waitsafe_v2_final_20260927.json`. It records the actual attempt and lease ID. For a later attempt, the effective stage snapshot explicitly marks its derived lease binding and retains the original stage receipt SHA and base lease. The original STOPPED coordinator and all launch receipts remain untouched. If attempt 0 does not launch, the prepared scorer v3b must be versioned to bind the winning attempt before any scorer stage; its current successor lease pin is attempt 0.

## Local validation

- `python -m py_compile scripts/finalize_exp227_target6bba_waitsafe_v2.py tests/test_finalize_exp227_target6bba_waitsafe_v2.py` passed.
- `python -m pytest -q tests/test_finalize_exp227_target6bba_waitsafe_v2.py --basetemp work/_pytest_exp227_finalizer_3`: **8 passed**. Fixtures cover attempts 0 and 1, check-only versus one-shot write, first-seven graph tamper, last receipt-hash tamper, timeout, GPU worker, unreleased queue row, and no-launch fail-closed behavior.
- Script SHA-256: `e1fc385cf3b28262cacd0b48184d45a35fe92708576c57f2171770ebaec9fa73`.
- Test SHA-256: `874fdf4f8eff4e389d7641390ac149f21b369f51b6fd72fb34d99dbb1d42ccbe`.
