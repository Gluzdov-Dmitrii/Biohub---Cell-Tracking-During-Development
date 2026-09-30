# EXP227/EXP236 reciprocal full175 pooled current-organizer result

2026-09-27 09:55 UTC. The read-only check-only combiner `scripts/combine_exp227_exp236_current175.py` SHA256 `fc1931f41b84eec45176153ced1022c4b7218dfa2d7f256416e3031ac979a334` passed on the independently verified EXP227 target6bba 116 and EXP236 target44b6 59 scorer results. It read only pinned JSON receipts/results and compiled the exact `summarise` function plus its two helpers from organizer `metrics.py` SHA256 `cfdd596e3f8909cca14db0682889738b19ff75c3808b3773175aba9367ca7444`. The paired division source SHA256 is `0635c38621a38f1eb4b55a302b4a817a88e9094930dfc2dab16faeeee60f4dc9`; organizer commit `075fc5f5a52d11077f9dc2b074644618f26939e2` and tracksdata commit `e13cf379b5127deeb8301ce56410fda35b5a3cf9` match both scorer receipts.

| Evidence | SHA256 |
| --- | --- |
| EXP227 independently verified v4 score receipt | `4d6bdde3cf06b26255009db9ab3cbff5c81cb4827851ca0a63c5423fed56c550` |
| EXP227 remote result | `eb13954f1cc98d84f8b40c69bd31b595e51fef8d1fffdd8639d2f8d20622ae24` |
| EXP227 remote durable no-metric gate | `81d36f0b58e14c48d7e36170ad78d5417811a25e540a0822f0879d0dabaf2720` |
| EXP227 all116 no-label final receipt | `69f110c302a4a3fed21993f5ce7083e036b345ee2e53e917cc4382c3291effa3` |
| EXP236 independently verified v2 score receipt | `cc34349e766aa339888ee0ecdbeaa0bb9e3447c97d8a9f08cdc843c48bcef77c` |
| EXP236 remote result | `f846ee8e6a554551373bc3a853bde14c2e7b3f5fd12a5a13159216de2ce9cae6` |
| EXP236 remote durable no-metric gate | `2f7de560ac68d0e7deec2f2ed50285c77d5c9ba977d8e65de1bda5a19973b007` |
| EXP236 all59 no-label coordinator | `0ccc0b6a10f141ae3e356b9970ff0062242493cb0163f186fea4a11caef7a545` |
| Frozen assignment | `9e9f15ad5e3497cd74d3c91b10f19a53686deb8f16412d3b239c7455d9f749f4` |
| Archived paired EXP214 baseline metrics | `c2746b182d061fede4a255056cf177a245ad365485f46ba9f376cd240013b2e5` |
| EXP209 reconstructed current-score verifier | `54aa103c7b8799196b2068e43c8d80e43fc216771671066a497b8b21c60f4d5c` |

The combiner independently required exact local stage/launch/verification SHA chains, both scorer code/config manifests, result/gate SHA readback, original graph hashes from the two no-label coordinators, 116+59 unique assignment IDs, identical baseline metric bytes and input graph hashes, 175 historical EXP214 row replays, per-fold current summary replay, and exact metric source pins. Its remote probe read only `code_manifest.json`, staged source/config JSON, `no_metric_gate.json`, `label_tree_hashes.json` bytes for hashing, and `result.json`; it did not open GEFF, image data, graph CSV, or a metric worker. The pooled graph-hash digest is `37ea4c28a1217ab6c7b788dea0b03c0fcdb1bc03acab06d361444a061c621adf`.

**Pinned organizer pooled score:** `0.7488419428035248` across all 175 per-movie sufficient-stat rows. Paired EXP214 baseline on these same 175 IDs and metric is `0.7427291486246141`; delta **`+0.006112794178910641`**. Separate EXP209 reconstructed current-organizer comparator is `0.6815218332750073`; delta **`+0.0673201095285175`**. The full175 value was computed with organizer `summarise` on the row union, not an average of the two fold scores.

This is a **historically exposed, leakage-controlled reciprocal development estimate**. It is not untouched embryo OOF or hidden Kaggle validation; EXP209 uses new reconstructed graphs rather than byte-exact original final graphs. The score is below 0.9. No new scorer run, target GEFF access, remote mutation, competition POST, or pooled receipt write occurred in the combiner check. The one-shot local `--write-receipt` mode remains unused and the existing fold receipts are unchanged.

Review command:

```powershell
python scripts/combine_exp227_exp236_current175.py
```

Focused tests: `python -m pytest -q tests/test_combine_exp227_exp236_current175.py --basetemp work/_pytest_exp227236_pool175` gave **8 passed**; the source compiled. Tests cover the exact 116+59 disjoint cohort, pooled sufficient-stat math, wrong graph hash, duplicate ID, changed historical row, changed metric source, missing verified receipt before SSH, and a JSON-only read-only remote probe. Test source SHA256 `6e39bf07f84522c49bf3c017fdaf98f10eea5c82c9aba5ae8211d110beb4b5b8`.
