# EXP227 target6bba v3 all116 finalizer and v4 scorer: local preparation

2026-09-27 09:07 UTC. **Prepared only.** V3 chunk07 attempt 1 was launched by the root coordinator, but its 14 outputs, exit and release have not been accepted here. The v3 all116 final receipt and all v4 stage, launch and score receipts are absent. No target GEFF, metric, GPU launch, scorer stage or Kaggle POST was performed in this preparation.

## Identity and sealed inputs

- Original v1 recovered STOPPED receipt SHA256: `8b9123bfb6b75371466fe1605cd31ddde2c630ebe585f18f7295f14a525932b3`.
- Failed v2 reconciliation SHA256: `5c777467215e6fe4f984cdcf4920070d07a2f704c819144b1cd4896af0981796`.
- V3 local prepare/stage/config SHA256: `9bae3cfe842e9772aadf07bce8572fc84802ed54af0a84838fad450dfa24e0d8`, `9f27d647ef0f10bb41a228ecebb4b64599b2218d241258a7dc6fc2f59815f08f`, `6452ba4a4d41f28068559f940144a141ff4c5ed1bd388183a625f864f580c8db`.
- V3 remote manifest/plan/runner SHA256: `b17d5baf85ddde704b863753bea2eaae9e5684405024c17c39aaf69d1c5d7e06`, `9e87d40ad89816f171f32bd888e55421531486c86cde9c8af0ba8d196af8031a`, `43e0b87893242d2fcf830d514f184ed3da8485ebebf3d32dee7ace370f0cec35`.
- Actual launch is v3 **attempt 1**, lease `exp227-target6bba-chunk07-v3a01-20260927`, launch receipt SHA256 `800c78e010bef37eac0f6f167f9ddb28fca819577b2aa41c6a1092c30599b9bf`. Attempt 0 is a preserved no-request fair wait. Stage and launch of the v4 scorer reject any different actual attempt, lease, or launch receipt.
- Finalizer source `scripts/finalize_exp227_target6bba_waitsafe_v3.py` SHA256 `ac368bdedade09531f7ae7dc0d865792a04b22b44514e4432c307344a4e61dc6`. It replays the first seven accepted v1 receipt/graph hashes, all eight graph gates, the v3 attempt chain, 116 ordered IDs/hashes and invariants, exit0/no timeout, live RELEASED leases, no worker/GPU process, and no-label status. Check-only is default; `--write-receipt` is one shot to a separate v3 final file.

## Separate current-organizer v4 scorer

The 16-file bundle is `work/exp227_target6bba_scorer_local_v4_20260927`; `local_manifest.json` SHA256 is `f56ac397e853c93162a418d437b0afec6a1848b728d3af746021bf1fb94b4a40`. Local prepare receipt `reports/exp227_target6bba_scorer_local_prepare_v4_20260927.json` SHA256 is `4d5467ab0acd148a35e0109dcd6b2fd0a69e2dd14e1867f7318a862d46521530`. The bundled scorer source SHA256 is `16e52534f27ce84dfc89e09fa7bdd19ded77acde3a6c74e686eb8bea5bfa303e`. The bundle pins EXP214 historical metrics SHA256 `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5`, the 116 target baseline rows digest `2c34eea867f7bf71bd0a511dee0a0e0b8bd4cf7a040416c654ede6cdab0a1952`, organizer `metrics.py` SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`, `division_metrics.py` SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`, organizer commit `075fc5f5a52d11077f9dc2b074644618f26939e2`, and tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`.

The scorer's staged `--gate-only` mode must validate the final receipt, frozen assignment/checkpoint, all 116 exact graph hashes and IDs, the first seven v1 plus v3 chunk07 lineage, full eight lease release and current metric/environment pins before output or target label access. The CPU worker writes and fsyncs `no_metric_gate.json` before any target GEFF access; it then replays every historical EXP214 baseline row within `1e-12` before current-organizer paired candidate/baseline scoring. The evidence class remains **leakage-controlled reciprocal evaluation with historically exposed target labels**, not an honest untouched OOF estimate.

Local orchestration sources and SHA256:

| Source | SHA256 |
| --- | --- |
| `scripts/prepare_exp227_target6bba_scorer_local_v4.py` | `051073d4ee1dfffb6c0ccd661bf3ec6cc5f3f1f8748c3ab849954be3865f0bf0` |
| `scripts/stage_exp227_target6bba_scorer_v4.py` | `93952c16c414713b4e968320bc8840606bbfa4d37bce22ba082f97c6e5f7d547` |
| `scripts/launch_exp227_target6bba_scorer_v4.py` | `7e88b78c2c741928aa8030bf4ebf21d728af3e9f5a89297f796522346b7e6a2a` |
| `scripts/verify_exp227_target6bba_scorer_v4.py` | `10e1d18a49ddbcad88b84107aeaba84ee0fef3b772d3cad2eeec317270a1918f` |

Stage and launch require an explicit SHA256 of the completed v3 final receipt. They compare that value to live local bytes and validate the attempt 1 receipt and lease before remote access. Stage uses a separate code/run namespace, creates an intent before mutation, verifies staged source bytes and executes one label-free 116-graph remote gate. Launch repeats that gate and starts one CPU4, 32 GiB, 3600 s worker in isolated Python 3.11 at `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/envs/current-organizer-py311-e13cf-v1/bin/python`, with CUDA hidden. The independent verifier checks process exit0/no timeout/absence, exact remote source/config/result and graph-gate hashes, 116 historical EXP214 row replay, current metric pins, and finite paired scores before writing a separate result receipt.

## Review commands, after v3 worker completion

Run the first command read-only after confirming the v3 worker has exited and the lease is RELEASED. Its output must be reviewed before the one-shot final receipt write:

```powershell
python scripts/finalize_exp227_target6bba_waitsafe_v3.py --attempt 1 --stage-sha256 9f27d647ef0f10bb41a228ecebb4b64599b2218d241258a7dc6fc2f59815f08f --config-sha256 6452ba4a4d41f28068559f940144a141ff4c5ed1bd388183a625f864f580c8db --manifest-sha256 b17d5baf85ddde704b863753bea2eaae9e5684405024c17c39aaf69d1c5d7e06
```

After review, the same command plus `--write-receipt` writes `reports/exp227_target6bba_all116_waitsafe_v3_final_20260927.json`. Record its exact SHA256 as `<FINAL_SHA256>`. Only then, after reviewing all gates, the prepared commands are:

```powershell
python scripts/stage_exp227_target6bba_scorer_v4.py --coordinator "C:\Users\Dmitry\Desktop\Kaggle\Biohub - Cell Tracking During Development\reports\exp227_target6bba_all116_waitsafe_v3_final_20260927.json" --final-sha256 <FINAL_SHA256>
python scripts/launch_exp227_target6bba_scorer_v4.py --final-sha256 <FINAL_SHA256>
python scripts/verify_exp227_target6bba_scorer_v4.py --final-sha256 <FINAL_SHA256>
```

The final command is for after the CPU scorer exits. This preparation invoked none of the four commands above.

Validation: `python -m pytest -q tests/test_finalize_exp227_target6bba_waitsafe_v3.py tests/test_exp227_target6bba_current_scorer_v4.py --basetemp work/_pytest_exp227_v3v4_bound` gave **19 passed**. Source compilation passed for all six new scripts and both tests. Synthetic tests cover 116 ordered IDs/graph hashes, wrong lineage/hash/lease rejection before labels, actual v3 attempt 1 identity, explicit final SHA before remote access, historical EXP214 row replay before current candidate scoring, durable gate order, and generated remote launch/probe Python compilation.
