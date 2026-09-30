# EXP227 source10 association velocity diagnostic

**Result:** The preregistered motion gate fails. **66/69** unmatched-outgoing association-FN cases have exactly one predicted predecessor from the preceding frame; three have none. For each valid case, the fixed forecast was `source + 0.5 × (source − predecessor)` in physical `(z,y,x)` units. **0/66** have the officially matched predicted target at least 2 µm closer to that forecast than the occupied unmatched child. The required gate was at least 20/69 cases spread across at least four source movies; the observed count is zero in every movie. No graph edit, candidate or score gain is inferred.

The v2 audit replayed the exact sealed source8 graph/evaluator/input hashes before new aggregates, reproduced the official score `0.8114014924249717`, and matched all 69 prior case identities and raw distances exactly. It rebuilt the evaluator graph so the predecessor and coordinate IDs use the same namespace as the official node matching. The first attempt stopped before motion aggregates because it mixed serialized CSV IDs with evaluator-assigned IDs. Its failure receipt remains at `reports/exp227_source10_association_velocity_failure_20260927.json`, SHA256 `3ba052923a60d6987234abbc7aa2991875175d575fbd6ca01acfb2dc875f51d6`.

| Source movie | All cases | Valid predecessor | Target advantage ≥2 µm | Median raw source→target / source→occupant (µm) | Median motion→target / motion→occupant (µm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 44b6_996155de | 2 | 2 | 0 | 7.936 / 1.675 | 7.979 / 1.662 |
| 44b6_c50204e0 | 24 | 24 | 0 | 8.025 / 1.675 | 8.344 / 1.228 |
| 44b6_c96cfa10 | 19 | 17 | 0 | 8.993 / 1.465 | 9.293 / 1.236 |
| 44b6_551a5dba | 16 | 15 | 0 | 9.038 / 0.908 | 8.875 / 0.812 |
| 44b6_90724892 | 5 | 5 | 0 | 9.228 / 2.031 | 9.510 / 2.031 |
| 44b6_f28707c6 | 1 | 1 | 0 | 9.918 / 1.817 | 9.826 / 0.908 |
| 44b6_deabac95 | 2 | 2 | 0 | 6.402 / 1.267 | 6.474 / 0.740 |
| 44b6_341df25f | 0 | 0 | 0 | — | — |
| **All** | **69** | **66** | **0** | **8.938 / 1.625** | **8.840 / 1.094** |

Across all 69 cases, raw source→matched-target distance has Q1/median/Q3 **7.187/8.938/10.083 µm**, while raw source→occupant is **0.908/1.625/1.817 µm**. Among the 66 with a valid predecessor, motion→matched-target is **7.159/8.840/10.089 µm** and motion→occupant is **0.752/1.094/1.687 µm**. Defined as occupant motion distance minus target motion distance, the target advantage is negative for all 66 (range **−15.613 to −1.623 µm**, median **−7.798 µm**). Full per-case distances, predecessor IDs, raw and motion quartiles by movie, and the exact eight graph CSV/receipt/GEFF tree SHA256 values are in the JSON receipt.

## Immutable evidence

- V2 receipt `reports/exp227_source10_association_velocity_v2_20260927.json`, SHA256 `babe24ab84e80d4fad592b1b8b30babee30e710cd6a90c0216c3d07103417c26`.
- Source script SHA256 `e04f499c7f61d17add38fcf3e71ef2c2e13da8f7a4e0ced18171a518591a1a29`; transmitted bundle SHA256 `a0b4528b99563bbcf09c269a1864894d32262098ca22608d64e5ec3ede303fb3`.
- Prior geometry receipt SHA256 `9e688773ee2f42f9c8a92cf6f34420a57338423d909ca4693402102458e64023`; prior occupied-link receipt SHA256 `7362f5c1ca1f3135828b050a50dc1086dd90b694556c9b3481552e59d656613d`.
- Sealed scorer manifest SHA256 `9eb0172ad130c693c7c58fd528fdc14c64736cacb9c237158d3ca17221092731`; score config `23c3a19577abddb171332dd3a8354953190098cf90e25f143d6c4874149d173c`; graph status `d445f1858ca5efe9561667a6e21362d753f047bb5bd7d507c209f076193cde7d`; official result `b9b2eacc8995bbcfb405a636698bc4e1be00cc4d2ae8d18b6231d66a7d18f0d4`; no-metric gate `949ed2f7ea1af9c18772650ae67e30917c8d934cdcd6e7ab0bf381c6a0a4f343`; evaluator config `45af14b5a6922324941a5f1d91052c373b1db7d7308a02cb6e9534ed47fce973`.

The bounded run used `nsu-quadro` CPU affinity 24–27, `CUDA_VISIBLE_DEVICES=`, 16 GiB virtual-memory limit and 1,800-second timeout; v2 analysis time was 31.8 seconds. This is post hoc source-inner training-monitor evidence, not target OOF. Unmatched occupants may represent real cells and official matching can change after graph edits. No target6bba access, GPU, training, active-run mutation or Kaggle POST occurred.
