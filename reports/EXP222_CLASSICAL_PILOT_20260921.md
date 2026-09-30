# EXP222 fixed classical baseline pilot, 2026-09-21

Four full movies: historical final-node failures `6bba_6feb10f0`, `6bba_ab78413d`, plus fixed SHA256 filename-ranked controls `44b6_eb2880fc`, `6bba_5c039895`. Two targets are selected because previous results exposed failures, so this is a targeted diagnostic, not untouched CV or the175-movie benchmark.

Model: original EXP002 multi-scale DoG detector, centroid refinement, physical-distance Hungarian, one-frame gap closure, original configuration. Original source SHA256 `e1edf7b5fc761ff713e818e01ecc5bc45349e8e8509b86d5932411b403294c1e`. No training or parameter sweep. All four prediction CSVs are represented in one combined file; all four must pass schema/graph/hash gates before official label scoring. EXP214 official counts are reproduced on the same four movies for comparison.

First remote attempt stopped before inference because immutable prepost environment has no pandas; failed logs retained under `outputs/research/exp222_classical_pilot_20260921/`. Operational retry removes the sole pandas import during module loading and writes the unchanged graph_to_rows dictionaries using stdlib CSV. Detector/linker source functions and parameters are unchanged, and original file SHA is checked before loading. No dependency install.

Retry remote run: `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp222_classical_pilot_stdlib_20260921`, nsu-quadro. Parent PID358862/start518814091. Budget4CPU,32GiB address-space limit, no GPU, hard timeout3600s. Launch `reports/exp222_stdlib_launch_20260921.json`, status `reports/exp222_stdlib_status_20260921.json`; poll/export `python scripts/poll_exp222_classical_pilot.py` using normal NSU permissions. CPU worker separate from EXP221's A100 work.

## Pilot result and full175 launch

Pilot PASS_FIXED_CLASSICAL_FOUR_MOVIE_DIAGNOSTIC,70.27s elapsed;4inference calls23.20s combined. All4prediction/hash/schema/graph gates passed before labels. Same-movie EXP214 official edgeTP/FP/FN reproduced exactly. Pilot process group verified ended. Exact result SHA256 `ed13de4c92d7bd5926580c7be5224c1cb7ff93ca9ff3a08da63f9de70a12c8a7`, files `outputs/research/exp222_classical_pilot_stdlib_20260921/`.

| Movie | Classical node recall | EXP214 node recall | Classical adjusted edge Jaccard | EXP214 adjusted edge Jaccard |
|---|---:|---:|---:|---:|
|6bba_6feb10f0|0.182749|0.193713|0.136279|0.152570|
|6bba_ab78413d|0.330789|0.393554|0.255857|0.291013|
|44b6_eb2880fc|0.956410|0.971795|0.793597|0.849434|
|6bba_5c039895|0.965077|0.974446|0.841518|0.716717|

Pooled official score on these targeted4:classical0.43852624329930656 vs EXP2140.4305243941507143. Classical does not rescue the two catastrophic movies and has lower node recall on all4. Gain on the other6bba movie comes with fewer association FP (93vs221), so this remains useful mechanism diversity. Both recover0/6divisions; do not interpret the small pooled gain as general superiority.

Full175 preregistered before launch with all frozen EXP214175movie IDs; no parameter change or score-based selection. Launched `nsu-quadro:/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp222_classical_full175_20260921`, parentPID358960/start518830517, 4CPU/32GiB/hard3600s/noGPU. Receipt `reports/exp222_full175_launch_20260921.json`; prereg `reports/exp222_full175_preregistration_20260921.json`. Estimated22–27minutes from measured4movie inference and previous scorer timing, not guaranteed. All175predictions must finish and pass structural/hash gates before any full benchmark target scoring. This is same-cohort fixed classical development benchmarking, not pristine unseen-embryo validation. Poll/export `python scripts/poll_exp222_classical_full175.py`; outputs `outputs/research/exp222_classical_full175_20260921/`. No further experiments or Kaggle action delegated by this runner.
