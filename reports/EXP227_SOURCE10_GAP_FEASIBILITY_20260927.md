# EXP227 source8 weak-peak gap-rescue feasibility

**Decision: reject the proposed still-open, one-frame weak-peak rescue before GPU work.** Its epoch10 source8 topology-only maximum is **zero recovered endpoint-limited edge FNs**, below the preregistered ≥10-edge source promotion gate. This rejects the exact intervention in `EXP227_LOW_SNR_DETECTION_DESIGN_20260927.md`, not all detection improvements.

The CPU-only audit first reran the sealed EXP227 source10 graph/evaluator gate, verified all eight graph CSV/receipt and source GEFF tree hashes, and reproduced official node matching and score `0.8114014924249717` to `1e-12`. Machine receipt `exp227_source10_gap_feasibility_20260927.json` SHA256 `605c7f04129dc3613d582a6b4845bc5d47673af1955042b7d78785f8951d3b8a`; parent fixed-node attribution receipt SHA256 `d29f559438d14ad89f0ea41319e794927bb035b48d13b2ab0667894812bd8ca7`.

The design requires an unmatched GT node at frame `t` with one GT predecessor at `t−1` and one successor at `t+1`. Both must have official-matched retained predicted nodes, each supported by an adjacent predicted edge. The predicted predecessor must have no outgoing edge and the successor no incoming edge, leaving a gap for a new peak. Of **115** distinct missed edge-bearing GT nodes, **102** were linear one-frame GT gaps, **20** had both anchors officially matched and supported, and **zero** had the required still-open predicted gap. Thus geometry at 7 µm, the 3.2 µm reuse constraint, one-to-one gap assignment, and weak-logit availability cannot rescue any edge *within this mechanism* on the final epoch10 graphs. The topology-only bound is zero even before those additional gates.

| Source movie | Missed GT nodes | Linear GT gap | Matched, supported anchors | Still-open predicted gap | FN-edge bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| 44b6_996155de | 7 | 7 | 1 | 0 | 0 |
| 44b6_c50204e0 | 37 | 33 | 9 | 0 | 0 |
| 44b6_c96cfa10 | 30 | 26 | 5 | 0 | 0 |
| 44b6_551a5dba | 5 | 4 | 2 | 0 | 0 |
| 44b6_90724892 | 8 | 8 | 1 | 0 | 0 |
| 44b6_f28707c6 | 15 | 15 | 0 | 0 | 0 |
| 44b6_deabac95 | 3 | 2 | 2 | 0 | 0 |
| 44b6_341df25f | 10 | 7 | 0 | 0 | 0 |

This is a post hoc source-inner training-monitor audit, not target OOF. The epoch10 graph receipts do not retain weak logits, so the audit does not estimate how often the secondary `logit > 0.3` detector would find a peak. The zero bound is specific to **final retained epoch10 graph topology** and the proposed still-open-gap rule; earlier raw graphs, reassociation, postprocessing changes, or an epoch20 graph may differ. Those would be different interventions requiring separate source-only evidence and registration. No candidate was staged or scored.

Execution: nsu-quadro CPU affinity 24–27, `CUDA_VISIBLE_DEVICES=`, 16 GiB virtual-memory limit, 1,800-second command timeout; actual analysis 19.9 seconds. Analysis source SHA256 `a04b08563549f862160fed130450df7107d7f9a146b59093a1bd074713134ded`, combined pinned-source bundle SHA256 `f1f8e93330e83f88080142c61873bc5afe92c23dcf5b7cd82210ca5d3ca19884`. No target6bba access, GPU use, active-run mutation or Kaggle POST.
