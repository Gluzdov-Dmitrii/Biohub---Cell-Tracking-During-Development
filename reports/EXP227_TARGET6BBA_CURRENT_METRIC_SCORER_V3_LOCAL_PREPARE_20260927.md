# EXP227 target6bba current-metric scorer v3: local preparation

Status: **local-only prepared; no remote scorer stage, launch, target GEFF access, score, GPU claim, or Kaggle POST**. The EXP227 coordinator remained `STOPPED_NEEDS_RECONCILIATION` with 7 of 8 chunks verified when this bundle was sealed. The original stopped coordinator receipt and scorer v2 remain unchanged. The v3 local preregistration is `reports/EXP227_TARGET6BBA_CURRENT_SCORER_V3_LOCAL_PREREG_20260927.md`.

The v3 prepare receipt is `reports/exp227_target6bba_scorer_local_prepare_v3_20260927.json`. Its 13-file immutable bundle manifest SHA256 is `97c42a671a797d3b711a70cb7b036f23cf6ce0be9a207629e6f7224f53972035`. The v3 scorer source SHA256 is `2aa8c0f4e789369c93764f4681a7fe240eca7da9c907b6028ac360d11e42b4cb` and the torch-free graph adapter SHA256 is `d37e986e59ace5f10e363e058784b0b03ea19919823cd3941707514ad04034b0`.

The source44b6 epoch10 checkpoint SHA256 remains `df4ffd355201ae263bf3dfa57593daf9736eda89d5f7f24e9ef142790ba6bd79`. All 116 target6bba IDs remain frozen in the eight assignment chunks. The historical EXP214 baseline `metrics.json` SHA256 is `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5`; its target6bba 116-row canonical SHA256 is `2c34eea867f7bf71bd0a511dee0a0e0b8bd4cf7a040416c654ede6cdab0a1952`. All eight EXP214 input CSV and receipt hashes are checked in the label-free gate. The three target6bba pairs are:

| Part | CSV SHA256 | Receipt SHA256 |
| --- | --- | --- |
| 00 | `7a5a2e7b62a0761513ff255dcc2130eccc78b07d5a2c2db5a3c64ddcf0df37f0` | `05d2ad4330f6090bae3ed17836cf401b00f70ca0aed573799cef679552beb3c1` |
| 01 | `deb5d8991521473fcf805b1c100cacdfb7bc349c04f4959054c55682e47b179a` | `b785fc194d98cdad5c82c603bc6d2dc6b4052d2a9844ddebc51c5808fb42f8c7` |
| 02 | `94a31a65be11ca2618e042c7a711e4e885f2c6dd7a9190faf30a7ffdfb9303d3` | `a4bc168ae7715e8dedf46d1f208f70b7c85aa4d68245d8f719fb436586148e95` |

The current organizer metric is commit `075fc5f5a52d11077f9dc2b074644618f26939e2`, metrics SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`, division SHA256 `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`, tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9`, and shared verified Python 3.11 interpreter `envs/current-organizer-py311-e13cf-v1/bin/python`. The exact image-scale audit SHA256 is `7d49f54f6a2bb80c8148cbd2e110c23f24fe8c4dd5fddc363b6755418da87f1c`.

The v3 scorer checks all eight coordinator chunks, exact code/plan/checkpoint, 116 graph CSVs and receipts, graph schema/topology/shape, exit0/no timeout, supervisor/control releases, and fresh live queue `RELEASED` rows. It validates the isolated metric runtime and synthetic division contract before writing a durable `no_metric_gate.json`. Only then may it hash/open target GEFF. It replays historical EXP214 rows to `1e-12` as integrity control and computes EXP227 minus EXP214 after rescoring both graph sets with the same current metric. This remains historically label-exposed development evidence, not pristine OOF.

Local verification: `python -m pytest tests/test_exp227_target6bba_current_scorer_v3.py -q --basetemp=work/pytest_exp227_current_scorer_v3_20260927_0601` passed 6 tests, including full fake 116-graph gate, durable label ordering, four tamper blocks, generated CPU launcher/verifier compilation. The metric's synthetic division contract passed in the isolated local environment. All v3 scripts compiled; the 13-file prepared bundle rehashed successfully.

The separate future stage command is `python scripts/stage_exp227_target6bba_scorer_v3.py`, only after an independently reviewed all-eight-chunk final coordinator receipt and root approval. Staging remains blocked by the current stopped coordinator.
