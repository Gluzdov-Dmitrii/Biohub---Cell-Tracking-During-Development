# EXP222 full175 fixed classical result, 2026-09-21

**COMPLETE:** original EXP002 DoG/physical-Hungarian pipeline scored **0.7409785635** against EXP214 gapfix90 **0.7427291486** on the exact same175movies. Classical-minus-EXP214 = **−0.0017505851**. This is a fixed same-cohort development benchmark, not pristine independentCV, a classical-method upper bound, or proof of equivalent generalization.

All175predictions completed and passed structural/hash gates before target scoring. No parameter was changed based on pilot scores. CPU-only runtime1722.576s = **28.71minutes**,4threads,32GiB address-space limit, noGPU. PID358960/start518830517 and entire process group confirmed ended. The latest polling receipt's elapsed7365s measures time since launch to the later check, not calculation runtime.

| Cohort | Movies | Classical score | EXP214 score | Delta | Classical better/worse movies* |
|---|---:|---:|---:|---:|---:|
|All|175|0.7409785635|0.7427291486|−0.0017505851|81/94|
|44b6|59|0.7172813987|0.8052068737|−0.0879254750|11/48|
|6bba|116|0.7453264974|0.7318060132|+0.0135204842|70/46|

*Movie signs use adjusted edge Jaccard. Pooled scores use the official edge-union weighting and pooled division term, not a simple average of movie/embryo scores. The mean movie adjusted-edge delta is−0.014457 overall,−0.080145 on44b6,+0.018953 on6bba. No uncertainty interval was estimated in this read-only summary; the close pooled point scores alone do not establish equivalence.

## Detection, edge and division tradeoff

| Metric, all175 | Classical | EXP214 | Classical minus EXP214 |
|---|---:|---:|---:|
|Mean movie annotated-node recall|0.912288|0.929493|−0.017205|
|Predicted nodes|4,026,228|4,368,356|−342,128|
|EdgeTP|94,198|96,353|−2,155|
|EdgeFP|12,997|15,188|−2,191|
|EdgeFN|20,158|18,003|+2,155|
|Adjusted edge Jaccard|0.7409785635|0.7406014891|+0.0003770745|
|DivisionTP/FP/FN|0/0/138|4/50/134|−4/−50/+4|

Classical is slightly ahead on the pooled adjusted-edge term but has no divisions; EXP214's division contribution0.0021276596 reverses the final ranking. Classical mean recall is lower in both embryos:44b6 0.924877 vs0.946121;6bba 0.905885 vs0.921035.

The strongest directional distinction is **6bba fewer false edges**: classical10,364 vs13,539 (−3,175), at the cost of−1,143edgeTP and+1,143FN. On44b6 it loses1,012TP and adds984FP, a clear regression. This supports testing a conservative physical-linking mechanism on identical clean DL detections. It does not isolate a causal linker improvement yet: EXP222 also changes detector, coordinates, candidate counts and graph pruning.

Largest positive per-movie adjusted-edge differences:6bba_718b21f9 +0.231370 (TP+65,FP−140);6bba_8b7818bf +0.230354 (TP+70,FP−131);6bba_2540cd90 +0.213406 (TP+47,FP−91). Largest negative:44b6_cf2536e8 −0.431784 (recall−0.368421);44b6_b2c44266 −0.283254;44b6_c50204e0 −0.259298.

The two catastrophic movies remain worse under classical detection:6bba_6feb10f0 node recall0.182749 vs0.193713;6bba_ab78413d0.330789 vs0.393554. Thus this baseline does not support a claim that classical detections rescue those failures. No embryo-selector or ensemble score is promoted from these observed directional results: selecting by these outcomes would be post-selection requiring a new frozen confirmation protocol.

## Integrity and evidence

Local analysis verified all exported files against the recorded remote hashes, exact175movie identity against preregistration/no-metric gate/frozen EXP214metrics, all baseline per-movie fields (float tolerance1e−12), and all8baseline CSV path/hash pairs. Pooled scores reconstructed from recorded sufficient statistics agree within1e−12; no evaluator or inference rerun occurred.

- Exact result: `outputs/research/exp222_classical_full175_20260921/result.json`.
- ResultSHA256: `ad975a14ad769565770f949c1ae2beec605d6abaf1aba1e5e2871e57e5e8e736`.
- GateSHA256: `5732a1877b683ceebb5ff950535e82f1bd5498d5de711929ec1176ffa0bcd62c`.
- PredictionCSV SHA recorded by gated remote run: `2297279e64f02a6b303d6312bfd02783ed074e859afeffd20137b1937641fab9`. CSV itself was not locally exported/rehashed in this analysis.
- Original baseline sourceSHA: `e1edf7b5fc761ff713e818e01ecc5bc45349e8e8509b86d5932411b403294c1e`; source functions/config unchanged, packaging-only pandas removal/stdlib CSV serialization documented in pilot.
- Machine-readable paired summary: `reports/exp222_classical_full175_analysis_20260921.json`.
- Process/completion receipt: `reports/exp222_full175_status_20260921.json`.

The classical baseline has no learned weights, so detector-weight training overlap is absent; historical rule/parameter selection and reuse of this development cohort still prevent claiming an independent final validation. No Kaggle submission occurred. No new experiment was launched by this analysis.
