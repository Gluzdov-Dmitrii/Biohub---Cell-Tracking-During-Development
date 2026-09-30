# EXP227 epoch10 source8 endpoint-FN node features

**Evidence:** post hoc analysis of the same eight source44 inner-validation movies used to monitor EXP227 training. This is not target OOF or a candidate score. The full receipt is `exp227_source10_fn_features_v3_20260927.json` (SHA256 `b9864920024d5ea6e49c0cda24a09debb71b3626967e7cccdcfb0c8d4be41a19`). Its parent attribution receipt is SHA256 `d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7`.

The exact no-label source graph/evaluator gate passed before opening source labels, and official epoch10 matching reproduced score **0.8114014924249717**. All eight graph CSV/receipt and source GEFF tree hashes matched the parent attribution receipt. Of 2,039 GT edges, 153 endpoint-limited FNs involve **115 distinct missed GT nodes** among 2,080 edge-bearing GT nodes. The node is the analysis unit below; repeated edges do not count as independent examples.

For each GT node, local contrast SNR is `(mean of 3×5×5 core − median of 5×13×13 outer volume) / SD of outer volume` in the raw image, with patches clipped at image borders. The outer volume includes the core. "Low" means the bottom quartile of this feature **within each movie**. Miss rate was **51/523 (9.75%)** in the low group versus **64/1,557 (4.11%)** elsewhere. The low group had a higher miss rate in **7/8 movies**; the median per-movie risk difference was **+4.64 percentage points**. Restricting to nodes at least 5 µm from the image border, the rates were **32/459 (6.97%)** versus **31/1,316 (2.36%)**; differences were positive in six movies, negative in one and tied in one. This weakens a pure border explanation, but does not establish causality.

| Source movie | Missed / GT nodes | Low-SNR miss-rate difference | Interior difference |
| --- | ---: | ---: | ---: |
| 44b6_996155de | 7 / 380 | +3 pp | +3 pp |
| 44b6_c50204e0 | 37 / 333 | +7 pp | +7 pp |
| 44b6_c96cfa10 | 30 / 629 | +7 pp | +5 pp |
| 44b6_551a5dba | 5 / 228 | +4 pp | +4 pp |
| 44b6_90724892 | 8 / 105 | −5 pp | −6 pp |
| 44b6_f28707c6 | 15 / 63 | +35 pp | +40 pp |
| 44b6_deabac95 | 3 / 126 | +5 pp | +3 pp |
| 44b6_341df25f | 10 / 216 | +1 pp | 0 pp |

Absolute center intensity and unnormalized local contrast were inconsistent across movies (3/8 and 4/8 positive risk differences). A fixed nearest-GT-neighbor distance <6 µm occurred in only one movie; <12 µm was evaluable in five and had no consistent direction (2/5 positive). Border <5 µm had higher miss rate in 5/8 movies, late time in 3/7, and proximity within two frames of a GT division in 2/4 evaluable movies. Division events and the dense-neighbor strata are too sparse for a useful conclusion.

**Source-only hypothesis for a separately registered experiment:** missed detections preferentially occur at low local contrast relative to nearby image variation. Test a detection sensitivity mechanism on held-out source movies, measuring recovered GT nodes, added false nodes, and the official graph score together. This diagnostic does not select a threshold, checkpoint, or target rollout. Official matching is conditional on the fixed epoch10 predictions; eight movies are the independent units, and the large +35 pp movie must not dominate a pooled claim.

Execution used CPU affinity 24–27 on nsu-quadro, `CUDA_VISIBLE_DEVICES=`, a 16 GiB virtual-memory limit and a 2,600-second command timeout. It completed in the bounded run without opening target6bba data, using a GPU or submitting to Kaggle. The first attempt failed before feature output on an incorrect GT node-ID field (`KeyError: 'id'`); its failure receipt is preserved. A corrected pass completed, and the final v3 pass added the border-stratified diagnostic without changing the graph, matching, image feature or candidate policy. Final feature source SHA256 `4f829dc3da7cae0d0f2e642e90a05000ac15afd7ce378ae04bedd75487a3826a`.
