# EXP227 source10 association occupant geometry

**Result:** The preregistered 5 µm co-location gate fails: **5/69** association-limited cases have an unmatched outgoing predicted occupant within 5 µm of the officially matched predicted target, versus the required **35/69**. No duplicate-based reassociation or graph intervention is promoted by this result.

The pinned epoch10 source8 graph and evaluator gate passed before source-label access. All eight final-graph CSVs and graph receipts and all eight source GEFF trees matched their pinned SHA256 hashes; the official source score reproduced as `0.8114014924249717`. The reconstructed 87 association-limited FN records matched the earlier occupied-link receipt exactly, including predicted source/target IDs and outgoing classes. The 69 selected cases have 69 unmatched outgoing occupants, one per source. Distances use the official source dataset's `(z,y,x)` physical scale and the sealed final predicted node coordinates.

| Source movie | Cases | Within 5 µm | Occupants | Median occupant→matched target (µm) | Median source→matched target (µm) | Median source→occupant (µm) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 44b6_996155de | 2 | 0 | 2 | 9.452 | 7.936 | 1.675 |
| 44b6_c50204e0 | 24 | 1 | 24 | 9.618 | 8.025 | 1.675 |
| 44b6_c96cfa10 | 19 | 2 | 19 | 8.760 | 8.993 | 1.465 |
| 44b6_551a5dba | 16 | 1 | 16 | 9.288 | 9.038 | 0.908 |
| 44b6_90724892 | 5 | 0 | 5 | 11.788 | 9.228 | 2.031 |
| 44b6_f28707c6 | 1 | 0 | 1 | 9.817 | 9.918 | 1.817 |
| 44b6_deabac95 | 2 | 1 | 2 | 6.470 | 6.402 | 1.267 |
| 44b6_341df25f | 0 | 0 | 0 | — | — | — |
| **All** | **69** | **5** | **69** | **9.120** | **8.938** | **1.625** |

Across the 69 cases, occupant→matched-target distance ranges **3.565–16.255 µm** (Q1 7.982, median 9.120, Q3 10.539). Source→matched-target ranges **3.495–15.865 µm** (median 8.938). Source→occupant ranges **0–3.495 µm** (median 1.625). The occupants are much closer to the source positions than to the matched target positions in this fixed graph. This is an observation about geometry, not proof of why the links were chosen or that the occupant nodes are false detections.

## Audit hashes

- Immutable detailed receipt: `reports/exp227_source10_association_geometry_20260927.json`, SHA256 `9e688773ee2f42f9c8a92cf6f34420a57338423d909ca4693402102458e64023`. It contains every case, occupant ID and all three requested distances, plus all exact input hashes.
- Prior occupied-link receipt SHA256 `7362f5c1ca1f3135828b050a50dc1086dd90b694556c9b3481552e59d656613d`; analysis source SHA256 `ae39f7d75f41fffc7ad0be39d71b12b7d5dab0827837612353e2c426b1162f16`; complete transmitted bundle SHA256 `aeae31e94de66a5fafe1876b3ad36509ec504791e34367931013fe4fad6405e1`.
- Sealed scorer manifest SHA256 `9eb0172ad130c693c7c58fd528fdc14c64736cacb9c237158d3ca17221092731`; score config `23c3a19577abddb171332dd3a8354953190098cf90e25f143d6c4874149d173c`; graph status `d445f1858ca5efe9561667a6e21362d753f047bb5bd7d507c209f076193cde7d`; official score result `b9b2eacc8995bbcfb405a636698bc4e1be00cc4d2ae8d18b6231d66a7d18f0d4`; no-metric gate `949ed2f7ea1af9c18772650ae67e30917c8d934cdcd6e7ab0bf381c6a0a4f343`; evaluator config `45af14b5a6922324941a5f1d91052c373b1db7d7308a02cb6e9534ed47fce973`.

| Source movie | Final graph CSV SHA256 | Graph receipt SHA256 | Source GEFF tree SHA256 |
| --- | --- | --- | --- |
| 44b6_996155de | `ab4abc463eb91ae299eff5fa5a6031e45c5ffc54408cd7dc9613834d4b62b6b7` | `fa84776d80133c92d1725dfadf890c85507a31065d45c1df1b5448b0a5f99516` | `40d9b02706df6cbe85eee251eb863c8408f8e646c4e00566ae7ad961a2301a7b` |
| 44b6_c50204e0 | `df8d7326de5fd40b8bd6fb2e0fb65c7c937f77ce3495fbb84b550d6f0105aae1` | `48921579e0cc78690d462fbfbf1d1dcbcd76651b37a65b11481da8436d43856b` | `62ea7080d1e477d81b28263f53aecb911f1801332527f4e2bd323f80d877cc69` |
| 44b6_c96cfa10 | `7e347384b3bf031bef0785b45f23a1734b90a7ae997a05fea1f3068095e0f7e1` | `b593331f8130d2422671ce7dcba5622960b63e2d98124eaad3594a18ab720fd4` | `5f63c09329563cf53b74f64d283609eab5c88e3d218d90d9c9dab647671b2a13` |
| 44b6_551a5dba | `57f4f629a43b9f7408a8284dbb0cacee33fa392cec2256b15876df0422c49cd4` | `0aee3c19cbc8870a8d39a89fd35777d2351cee45569a48545a4afbbdf6f3cc8f` | `da705914c3ae0ec9efb8bdeeb2002a1b850401c83eb7beb71909e21f7e38f00f` |
| 44b6_90724892 | `7292325efcad75ec162fa4dc7983dab6e832fc54dd86c48d4a7024681b456812` | `591a4403a73fc06b8c097a660da006de5fff8aae21657501b74a4572cc8e6f60` | `b967502dc4e4a563733e4868218f6a10cfb9b3dfbfd48dc6086454ec6f648eb0` |
| 44b6_f28707c6 | `a352d1be2bc94cdcc1ba9dbcdde994ab447141583d2a5c5880f60e148777e8a0` | `75256035d6cfe74c6fff7cde45d2fc004c1905ba5444640cafe5c2ec7eff005d` | `5b0eee85fbb8e6772ee94a54d481a905107168686c40eb6eafc8f283d5338ade` |
| 44b6_deabac95 | `f4c65f93f3633ae83b6593f53321b037acb4c7e63ec173d7aeaed55d2b6e6657` | `8fe11441f695c1aeddd66ee055b39b13b49012e5febbcd6414f161fae3a65c5e` | `b024684791fd972bcb4a6acf0c7a0a5deb7516f5551c665a324d4b5bdcf154eb` |
| 44b6_341df25f | `c1dec0829eed7dd6be49938eb871d32cad07f6b6979e5d6d9fe68a86bba6af3a` | `1d9fdb1b8861510af204c7055d10a37f17bff6ea6d7b6bd61d80344f2cf4c236` | `225e560d40b936784575b83ff8dfa3700c020e27f75c85c3d61b1e8b8b7b2e3d` |

The run used `nsu-quadro` CPU affinity 24–27, `CUDA_VISIBLE_DEVICES=`, a 16 GiB virtual-memory limit and 1,800-second timeout; measured analysis time was 18.7 seconds. No target6bba data, GPU, training, active-run controller or Kaggle POST was used. The result is post hoc source-inner training-monitor evidence, not embryo-disjoint OOF. Official matches can change after any graph edit, and unmatched predictions may be real cells.
