# EXP227 chunk07 failed v2 and distinct v3 local handoff

Status: **v2 failed and reconciled; v3 prepared locally, not staged or launched**. The original v1 STOPPED receipt and failed v2 code/run/lease are preserved. No target GEFF labels, target score, Kaggle POST or v3 GPU request occurred.

## Failure boundary

The read-only v2 reconciliation receipt is `reports/exp227_target6bba_chunk07_v2_failed_reconciliation_20260927.json` SHA256 `5c777467215e6fe4f984cdcf4920070d07a2f704c819144b1cd4896af0981796`. The launched attempt0 receipt SHA256 is `fc713034eb4b674c3dbf4ffbe17205b7852d0228c21426581e5bd7a78a94d4be`. Remote exit is returncode 1 without timeout; `inference.log` SHA256 `ae7b5f77467d5abe341de573e3f24f017a30052c1ad4bea3ff878632d083b9c1` records `validate_plan` line 63 rejecting the v2 code path because the runner expects `_v1_20260927`. Live v2 lease is RELEASED with no GPU, process identity/group absent, assigned GPU compute PIDs empty, `output/` absent and no graph CSV. Remote v2 manifest and plan remain their staged hashes `a828a02ef88bd313a30da12aca8eb2a956337c3641c4dc2851e49e50a203fade` and `583fdae80ed8145ceca92d2405e69a6093b26700acc8986540a5f0ace6afcbd2`.

## V3 pins

| Artifact | SHA256 |
| --- | --- |
| `work/exp227_target6bba_chunk07_waitsafe_v3_20260927/local_bundle_manifest.json` | `5c87a39c3ea6c3a150b8086731cf7eed6fc7d85ee0362b7f7495efd27c205bc0` |
| Bundled `run_exp227_target_chunk.py` | `43e0b87893242d2fcf830d514f184ed3da8485ebebf3d32dee7ace370f0cec35` |
| Bundled `plan.json` | `9e87d40ad89816f171f32bd888e55421531486c86cde9c8af0ba8d196af8031a` |
| `reports/exp227_target6bba_chunk07_waitsafe_v3_local_prepare_20260927.json` | `9bae3cfe842e9772aadf07bce8572fc84802ed54af0a84838fad450dfa24e0d8` |
| `scripts/prepare_exp227_chunk07_waitsafe_v3.py` | `0fc072f8f67daa859172ac23bf1f50812bd5cef72cd3c2a1c53ed0e8ed949854` |
| `scripts/stage_exp227_chunk07_waitsafe_v3.py` | `7e10366635930ebc82041f9a430326895ab08ea596ca2901c9a36d37e9ac3364` |
| `scripts/launch_exp227_chunk07_waitsafe_v3.py` | `08967e55af6a40fe9c27ffce590489cd0d13b1d6fc5d6b664d542aafb0aaf6d9` |

V3 identity is code `/code/exp227_target6bba_chunk07_v3_20260927`, run `/runs/exp227_target6bba_chunk07_v3_20260927`, lease base `exp227-target6bba-chunk07-v3-20260927`, token `exp227_target6bba_chunk07_v3_20260927`. A fresh read-only check found the v3 code and run paths absent. The new runner changes exactly the old v1 namespace assertion to v3; all other runner bytes match v2. The exact bundled `validate_plan` function was executed against the generated v3 plan using local byte-identical assignment and selection copies. It accepted v3 and rejected both old v2 code and old v2 output paths. The prep receipt and stage/launch local gates pin this contract and every bundle file SHA before any remote operation.

## Reviewed next actions

The v3 stage script is review-gated and one-shot:

```powershell
python scripts/stage_exp227_chunk07_waitsafe_v3.py
```

After its new stage receipt, remote runner/manifest/plan readback, and fair queue review, attempt 0 is:

```powershell
python scripts/launch_exp227_chunk07_waitsafe_v3.py --attempt 0
```

No fair GPU yields a durable no-request wait. A `WAITING_RESOURCE` race is cancelled and independently confirmed with no run/worker/GPU before writing a nonfatal wait; a later retry uses a fresh `-v3aNN-` lease ID. Do not reuse the released v2 lease, failed v2 run or v1 STOPPED coordinator for a launch.

After a successful v3 inference, make a **separate v3 all116 finalizer**, leaving `scripts/finalize_exp227_target6bba_waitsafe_v2.py` and its receipt path unchanged. Precise changes to the v2 finalizer: use the pinned v3 local prepare receipt above and failed-v2 reconciliation receipt above; accept `PREPARED_EXP227_CHUNK07_WAITSAFE_V3_LOCAL_ONLY`, `STAGED_EXP227_CHUNK07_WAITSAFE_V3_NO_LABELS`, `LAUNCHED_EXP227_CHUNK07_WAITSAFE_V3`, and the V3 intent/reservation/partial statuses; require the failed-v2 source to show exit1, RELEASED, zero graphs, and no v3 reuse of its lease. Bind a reviewed new v3 stage receipt SHA, remote manifest SHA and config SHA before check-only or write mode. Use v3 attempt receipt names and lease IDs. Retain the v2 finalizer's first-seven exact 102-hash replay, chunk07 14-hash graph audit, all-eight exit0/no-timeout/RELEASED and no-process/GPU gates, frozen assignment/checkpoint, actual-attempt binding, and one-shot separate receipt. Version the v3b scorer bundle for v3 code/run/plan/stage/lease and final receipt before any scoring; v3b currently binds failed v2 attempt0.

## Local validation

`python -m py_compile` passed for the v2 failure reconciler, v3 preparer, stage, launch and focused test. `python -m pytest -q tests/test_exp227_chunk07_waitsafe_v3.py tests/test_exp227_chunk07_waitsafe_v2.py --basetemp work/_pytest_exp227_v3_3`: **8 passed**. Tests execute the bundled v3 `validate_plan` on the generated plan, reject wrong v2 identities, parse generated remote stage code, dry-run stage/launch local gates, and exercise no-request and cancelled-race wait states. Neither v3 stage nor launch was invoked.
