# EXP220: frozen final-node geometry diagnostic, 2026-09-21

Run: `nsu-quadro:/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp220_node_strata_20260921`.

Read-only CPU diagnostic on EXP214 gapfix90 public graphs (175 movies). Every input shard SHA is checked against frozen metrics. Official evaluator edge TP/FP/FN must match the recorded results exactly for every movie before node-miss strata are accepted.

Strata: embryo, physical nearest annotated neighbor distance (<3, 3–6, 6–12, >=12 micrometers), spatial array-depth quartile, movie-time quartile, physical boundary distance (<5 vs >=5 micrometers). This is a development-adapted target-label diagnostic, not fresh OOF or a model improvement. Array depth is not biological depth. All annotated nodes are included, including isolated nodes, so this node-miss summary is not equivalent to edge FN decomposition.

Limits: four CPU threads, 32 GiB address-space limit, no GPU visibility, two-hour hard timeout. No raw image/intensity reads, model changes or Kaggle POST. Initial preflight: no active common GPU leases; Quadro 6000 and both A100 80GB physically idle. This is a timestamped observation, not a reservation.

Receipts: `exp220_preregistration_20260921.json`, `exp220_launch_20260921.json`, `exp220_status_20260921.json`. Poll and export: `python scripts/poll_exp220_node_strata.py` via normal NSU permissions. Completion writes `reports/exp220_result_20260921.json`; inspect final status, process identity, and result before claiming completion.

Candidate-stage warning: the existing predictor telemetry writes the same per-movie NPZ name at its pre-ILP return; repeated model/TTA calls may overwrite it. Do not interpret that cache as the full detector-candidate union without provenance verification. A future stage-retention audit should instrument distinct model/TTA/fusion stages.

## Completion and decision

COMPLETE: 175/175 movies, official edge TP/FP/FN reproduced exactly. Diagnostic runtime 262.59 seconds (4.38 minutes). Timeout parent PID357841/start518583681 and its entire process group are confirmed stopped; no GPU was allocated. Exact exported artifact directory: `outputs/research/exp220_node_strata_20260921/`. Result SHA256: `8173556eab2015ba647a4b246f9903daf657e0ffe3b8f3dcc938ead2971b7571`. Completion receipt: `reports/exp220_completion_20260921.json`.

Total missed annotated nodes: 8972/118308 (7.584%). Target44b6: 903/17425 (5.182%); target6bba: 8069/100883 (7.998%). These are final graph node-match statistics, not the competition score or detector-only recall.

Target6bba is largely flat by time (7.84–8.34%), array depth (7.17–8.40%), and boundary (<5um: 2007/24829=8.083%; interior: 6062/76054=7.971%). Nearest annotated neighbor <6um has only 90 nodes, 12 misses (13.33%); >=12um has 7718/96796 misses (7.973%). Sparse annotation means annotated-neighbor distance is a weak proxy for actual cell density; tiny dense strata cannot establish crowding as the dominant cause. No strong depth/boundary/time failure mechanism is established.

Two catastrophic movies have genuinely high final node-miss rates: `6bba_6feb10f0` 1103/1368 (80.63%) and `6bba_ab78413d` 715/1179 (60.64%). Together they contribute 1818/8069=22.53% of target6bba node misses, but this alone does not identify a code defect or promise a recoverable metric gain.

Next diagnostic priority: verify named primary/secondary/TTA/fusion candidate-stage provenance, then inspect raw image signal and final filtering losses in these failures alongside ordinary matched controls. Source-only photometric robustness is a testable hypothesis, not demonstrated by this geometry pass. Preserve association/FP and division checks: EXP216 still attributes 42.69% of public edge FN to association failures. No new accuracy result, training, threshold selection, or Kaggle POST was performed by EXP220.
