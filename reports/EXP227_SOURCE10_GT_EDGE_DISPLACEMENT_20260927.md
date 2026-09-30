# EXP227 epoch10 source8 GT edge displacement diagnostic

Preregistered in `EXPERIMENTS.md` before opening new displacement aggregates. This is a post hoc diagnostic on the eight source44 inner-validation movies used during training monitoring. It is not honest OOF, a candidate selection, or target6bba evidence.

The sealed graph/evaluator/GEFF hash gate passed before label access. The audit reproduced official source score **0.8114014924249717**, all 2,039 GT edge classifications (1,799 TP, 153 endpoint-limited FN, 87 association-limited FN), and the prior 87 association case identities. All 2,039 GT edges joined consecutive frames. Distances below use GT source and target (z,y,x) multiplied by each movie's physical scale. The previous 8.938 µm median for the 69 occupied-link cases measured **predicted** matched endpoints and is a different quantity.

| Class | GT edges | Median GT displacement (µm) | Q1–Q3 (µm) |
| --- | ---: | ---: | ---: |
| Official edge TP | 1,799 | 1.675 | 0.908–2.071 |
| Endpoint-limited FN | 153 | 2.031 | 1.285–3.275 |
| Association-limited FN | 87 | 2.031 | 1.285–3.054 |

The association-FN/TP median ratio is **1.213**, below the preregistered 2.0 threshold. Official TP recall is 1,798/2,031 = **0.8853** for GT edges at most 7 µm, and 1/8 = **0.1250** above 7 µm. The recall ratio is 0.1412, meeting that one pooled threshold, but only eight GT edges are above 7 µm, all in two movies. Seven are FN: six lack at least one matched predicted endpoint, and only one is association-limited. The data give little support for long motion as an explanation of the 87 association errors.

| Source movie | TP median | Endpoint-FN median | Association-FN median | ≤7 µm TP/GT | >7 µm TP/GT | Direction consistent |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `44b6_996155de` | 1.219 | 1.650 | 1.504 | 365/377 | 0/0 | No bin |
| `44b6_c50204e0` | 1.675 | 1.770 | 1.839 | 243/325 | 0/0 | No bin |
| `44b6_c96cfa10` | 1.724 | 2.031 | 2.188 | 552/616 | 0/0 | No bin |
| `44b6_551a5dba` | 1.285 | 1.049 | 1.817 | 196/224 | 0/0 | No bin |
| `44b6_90724892` | 2.438 | 2.334 | 2.958 | 87/103 | 0/0 | No bin |
| `44b6_f28707c6` | 2.633 | 5.203 | 3.679 | 40/54 | 1/7 | Yes |
| `44b6_deabac95` | 2.031 | 3.723 | 3.300 | 116/124 | 0/0 | No bin |
| `44b6_341df25f` | 1.675 | 1.817 | 7.141 | 199/208 | 0/1 | Yes |

Association-FN medians exceed TP medians in all eight movies, but the required joint direction (also lower long-bin recall with both bins present) holds in **2/8**, below 6/8. The preregistered long-motion research gate **FAILS** on both the pooled median ratio and movie replication criteria. Do not promote a long-motion model intervention from this diagnostic. The optional 63-train-movie label comparison was not opened after this decisive source8 result.

Detailed immutable case-level receipt: `exp227_source10_gt_edge_displacement_20260927.json`. It contains all per-movie distributions, scale vectors, bin counts, edge IDs/classes/distances, exact source input hashes, scorer pins, source and bundle hashes, and execution bounds. Run used nsu-quadro CPU24–27, `CUDA_VISIBLE_DEVICES=`, 16 GiB virtual memory limit and 1800s timeout; measured analysis time is in the receipt. No target6bba labels, GPU, training, active-run change or Kaggle POST. Official node matching is conditional on the fixed predicted graph, and cells/edges cluster within movies.
