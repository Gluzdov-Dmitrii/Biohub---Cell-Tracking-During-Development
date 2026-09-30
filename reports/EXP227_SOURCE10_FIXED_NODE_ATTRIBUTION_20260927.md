# EXP227 epoch10 source8 fixed-node attribution

Evidence class: post hoc diagnostic on the same eight source44 inner-validation movies used for training monitoring. This is neither target OOF evidence nor a candidate-selection result. The pinned inputs, eight graph and GEFF tree hashes, official evaluator pins, and per-movie decomposition are in `exp227_source10_fixed_node_attribution_20260927.json` (SHA256 `d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7`).

The official source8 score reproduced exactly: **0.8114014924249717**. Across 2,039 ground-truth edges, there were 1,799 TP, 240 FN, and 207 counted FP. Of the FN, **153 (63.75%) lacked at least one matched predicted endpoint**: 64 lacked both, 46 lacked the source, and 43 lacked the target. The remaining **87 (36.25%) had both endpoints matched but lacked the correct link**. The division result was 2 TP, 6 FP, 3 FN (Jaccard 0.18181818181818182).

| Source movie | Edge FN | Endpoint-limited FN | Association-limited FN | Counted edge FP |
| --- | ---: | ---: | ---: | ---: |
| 44b6_996155de | 12 | 10 | 2 | 6 |
| 44b6_c50204e0 | 82 | 52 | 30 | 72 |
| 44b6_c96cfa10 | 64 | 39 | 25 | 61 |
| 44b6_551a5dba | 28 | 8 | 20 | 38 |
| 44b6_90724892 | 16 | 11 | 5 | 14 |
| 44b6_f28707c6 | 20 | 19 | 1 | 8 |
| 44b6_deabac95 | 8 | 5 | 3 | 7 |
| 44b6_341df25f | 10 | 9 | 1 | 1 |

With the predicted nodes and official node matching fixed, assigning every recoverable edge correctly and removing every counted association FP gives an **optimistic adjusted-edge ceiling of 0.916028767863141**. Adding the *observed* division Jaccard yields 0.9342105860449592 as an arithmetic projection, **not an achievable official score ceiling**: changing links can change division TP/FP/FN. Allowing a perfect division Jaccard gives 1.016028767863141 as a loose theoretical combined upper bound; lineage constraints may make it unattainable. The official combined formula can exceed 1 because it adds 0.1 times division Jaccard to the adjusted-edge term.

The official evaluator ignored 232,286 predicted edges with neither a relevant ground-truth source nor target anchor; only 207 predicted edges counted as edge FP. This distinction matters when reading the raw graph density. The calculation leaves detection and node count unchanged and makes no claim about a realizable graph, target performance, or improvement from tuning. Execution used CPU affinity 24–27 with `CUDA_VISIBLE_DEVICES=`; no target6bba access, GPU use, or Kaggle POST occurred.
