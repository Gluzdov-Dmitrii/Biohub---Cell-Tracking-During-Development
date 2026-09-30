# EXP236 target44b6 current-metric scorer: local preparation

Status: **local-only prepared; no remote scorer staging, run, target GEFF access, score, GPU claim, or Kaggle POST**. The four-chunk coordinator was still `ACTIVE_NO_TARGET_LABELS` when this bundle was sealed. Its final `PASS_EXP236_TARGET44B6_59_GRAPHS_NO_LABELS_RELEASED` receipt is a mandatory gate before any stage.

The scorer preregistration is `reports/EXP236_TARGET44B6_CURRENT_METRIC_SCORER_PREREG_20260927.md`. The sealed prepare receipt is `reports/exp236_target44b6_scorer_local_prepare_v2_20260927.json`; its 15-file bundle manifest SHA256 is `fda68d3fe0c75997b72c1bd9e62504b85bbc259f0393b76a0803e73d22ff3aa0`. The scorer source SHA256 is `646b81ba6c6bf35fc8821c6c7b8219b46b838d6779a1ebd6093765087b976d82`.

The source6bba epoch10 checkpoint is pinned to `d043d5e15c8fbe84b097e6e4d8651acd5b102b747c33e655898ae78e2f879813`, and the parent source graph manifest to `92a9582cbe0f09d34d73865b1d09243971a94815c313a9b2225a7047388db3b2`. The 59 assigned `44b6_*` IDs remain ordered 15/15/15/14 from assignment SHA256 `9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4`.

The target historical EXP214 baseline is the exact 175-row `metrics.json` SHA256 `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5`; the target44b6 59-row canonical SHA256 is `aed7eec804658f57cb8c3a5cbdd37afa06499a038a781184d631a430f4c84493`. All eight historical CSV and receipt pairs are checked in the label-free gate. The five target44b6 pairs, in order, are:

| Part | CSV SHA256 | Receipt SHA256 |
| --- | --- | --- |
| 00 | `2aab4337e1f59674214bb06e051bb95c4501f53aed2d40cab19aaf9bbfec5ff6` | `8e9307a6d2ecc816c0a351ba0a9dff9bdfb6a8a620d5e0673c682c37590f69d9` |
| 01 | `c358fe448ca9268d748f40a2a3a084289e3b93c26d2c5ba5ce00dd9ff2da3303` | `d4450695eeee6bb841df9522041cd6e3fe61024845285a465840d648a63e746f` |
| 02 | `2e02c221f6fd3c87d6715338274e875b127d65711caeba221d3245a346595414` | `b8c153decb6794a310220e170131905f9fb49ceaa4581def33923cec7012ffd4` |
| 03 | `3b23ddb8a4c212afe36f48b25a8db53990f02510bf63fd596fd9adf1aeb5ab08` | `c9d276d8c9f1b5b08f0ff0e1fe8d8c8eda76a4f823f34b9e149dc53c3df8be9e` |
| 04 | `70cfa98f54cc1bbdcfac80a24fe2db95a49d538b4d45ce81a55808f484baec31` | `18f6fc4c16f2bd73aa5f790f3a72d090d105273b726536b5547a15ef53cf39d6` |

The current organizer metric is source commit `075fc5f5a52d11077f9dc2b074644618f26939e2`, `metrics.py` SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`, `division_metrics.py` SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`, and tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`. The future CPU interpreter is the verified shared `envs/current-organizer-py311-e13cf-v1/bin/python`. The scorer uses an in-memory tracksdata graph and `IndexedRXGraph.from_geff`; it does not import torch or the old image loader. Exact image-scale metadata is pinned to EXP234 audit SHA256 `7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c`.

The complete no-label gate checks four chunk code manifests/plans, 59 CSV and per-movie receipt hashes, graph schema/topology/shape, checkpoint/source chain, exit0/no timeout, supervisor/control release, coordinator process-probe evidence, and fresh live queue `RELEASED` rows. It imports and tests the current metric with a synthetic division contract, then writes `no_metric_gate.json` durably before any GEFF access. It replays the historical EXP214 rows to `1e-12` solely as integrity control and reports candidate minus EXP214 after rescoring both graph sets with the same current metric. It also hashes target GEFF trees after the gate and checks them again before writing the result. Source11 score `0.8458659187983504` is monitoring only; this reciprocal target evaluation remains historically label-exposed development evidence.

Local verification: `python -m pytest tests/test_exp236_target44b6_current_scorer.py -q --basetemp=work/pytest_exp236_target_scorer_20260927_0526` passed 7 tests; `scripts/check_current_organizer_metric_runtime.py --profile local_contract_py312 --package-root work/exp234_current_organizer_v1` passed the synthetic current metric contract; all five scorer scripts compiled; the prepared 15-file bundle rehashed successfully. The first pytest attempt hit the preexisting Windows temp-directory ACL and was rerun with a workspace basetemp. No target GEFF or target score was opened during this preparation.

After final coordinator review, the separate future stage command is `python scripts/stage_exp236_target44b6_scorer.py`. Staging and CPU launch remain outside this local-only handoff and require root review.
