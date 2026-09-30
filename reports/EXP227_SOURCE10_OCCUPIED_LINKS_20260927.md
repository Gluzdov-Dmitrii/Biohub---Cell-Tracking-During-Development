# EXP227 epoch10 source8 occupied-link diagnostic

**Evidence:** post hoc analysis of the same eight source44 inner-validation movies monitored during training, not target OOF. The exact sealed source graph/evaluator gate passed before source-label access; all eight graph CSV/receipt and source GEFF tree hashes and official node matching reproduced score `0.8114014924249717`. Full 20-node and 87-edge classifications are in `exp227_source10_occupied_links_20260927.json` (SHA256 `7362f5c1ca1f3135828b050a50dc1086dd90b694556c9b3481552e59d656613d`).

Of the **20** missed GT nodes with officially matched, edge-supported neighbors at `t−1` and `t+1`, none has an open predicted gap. In **six**, both anchors connect through the **same** intermediate predicted node; in three they use different intermediate nodes; eight have only the source anchor occupied, and three only the target anchor occupied. The source anchor has 18 outgoing occupant edges: 17 end at an officially **unmatched** predicted node and one at a node matched to another GT. Only that one matched-other occupant lies within 7 µm of the missed GT position; the other 17 are farther than 7 µm. The target anchor has 12 incoming occupant edges, all from officially unmatched predicted nodes farther than 7 µm. Six shared intermediates appear in both directional edge counts, so these counts are not distinct cells.

| Source movie | Occupied missed GT nodes | Same intermediate | Different intermediates | Source only | Target only | Association FN: unmatched / absent / other GT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 44b6_996155de | 1 | 0 | 0 | 1 | 0 | 2 / 0 / 0 |
| 44b6_c50204e0 | 9 | 3 | 1 | 4 | 1 | 24 / 5 / 1 |
| 44b6_c96cfa10 | 5 | 2 | 1 | 1 | 1 | 19 / 6 / 0 |
| 44b6_551a5dba | 2 | 0 | 1 | 0 | 1 | 16 / 4 / 0 |
| 44b6_90724892 | 1 | 1 | 0 | 0 | 0 | 5 / 0 / 0 |
| 44b6_f28707c6 | 0 | 0 | 0 | 0 | 0 | 1 / 0 / 0 |
| 44b6_deabac95 | 2 | 0 | 0 | 2 | 0 | 2 / 0 / 1 |
| 44b6_341df25f | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 1 |
| **Total** | **20** | **6** | **3** | **8** | **3** | **69 / 15 / 3** |

The **87** association-limited GT edge FNs have both endpoints officially matched but lack the correct predicted link. Their predicted source has outgoing edge(s) exclusively to officially unmatched predicted nodes in **69** cases, no outgoing edge in **15**, and edge(s) to another officially matched GT in **3**. No mixed outgoing class occurred. These are 87 distinct GT source anchors, but edge outcomes remain clustered by movie. An unmatched predicted node may represent an unannotated biological cell; it is not automatically a false detection.

**Interpretation:** the zero-gap rescue remains rejected. The six shared intermediates are all outside the 7 µm GT matching radius, so a coordinate or node-replacement mechanism is conceivable, but this audit does not show a hidden-compatible way to choose the correct position. The 69 wrong links to unmatched predictions make source-only reassociation worth *diagnosing* after the paired epoch20 result, but changing an occupied link can create counted FPs, divisions, or lineage violations. No candidate or promotion follows from these counts.

Synthetic-node status cannot be assigned per occupant: Horaz `Node.synthetic` is omitted by the sealed CSV serializer, and each graph receipt records only aggregate synthetic additions. Raw neural logits and ILP candidate probabilities are also absent. Official node matching is conditional on the fixed epoch10 graph; editing it can change the classifications. CPU-only execution used nsu-quadro affinity 24–27, `CUDA_VISIBLE_DEVICES=`, 16 GiB virtual-memory limit and 1,800-second timeout (20.3 seconds actual). Analysis source SHA256 `906b4b84a167bb99facbcd0ae338031d0b0f8a2cecaa1146debaef78f77f4279`; no target6bba access, GPU, active-run mutation or Kaggle POST.
