# EXP221 fixed source-validation graph gate

Preregistered and launched after both24epoch training runs completed and
released their allocations. This evaluates the official final graph on the
original eight source-validation movies; it is not target6bba OOF evidence.

Primary checkpoints: control source-selected epoch13 SHA
`e4175019c11105ea8b87324f9f787f3b0710d9e4df5862cd2d03ff8204759b5e`,
domain source-selected epoch23 SHA
`7de53cee104baebd7d7c380bd41b90c55eaa223c8167b9938bf3f76c8be7dea8`.
The frozen secondary60 seed314159 and EXP180 center are identical in both
arms. The secondary training cohort excludes all8; center training10 and
checkpoint-selection2 also exclude all8, verified from live source manifests.
Public COMPACT47-v20 graph and all inference settings remain fixed.

An explicit source8 allowlist branch permits this diagnostic; default
opposite-embryo guard remains enforced. Tests cover valid source8, ordinary
opposite-embryo mode, forbidden source training movie, target movie, subset,
and overlapping training cohort. Both complete eight-movie prediction sets
must pass CSV/hash/model/graph gates before the official CPU scorer opens
source graph labels. No other checkpoint, target metric, retraining or POST.

Running on remote ngpu01 GPU61c... with shared lease
`exp221-source-graph8-20260921`; wrapper PID550552. Hard inference cap3600s,
lease70min. Remote observer550814 and canonical prepost controller359943
maintain verified ownership. The temporary local monitor20452 was stopped
after fresh remote observations/readiness checks, then remote control activated.
Upon verified GPU exit/release, the controller runs the fixed official scorer
on prepost with4CPU threads, GPU invisible, timeout900s. Failed or incomplete
prediction gates cannot open metrics. No training is launched by these workers.

Remote project root:
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development`.
Run: `runs/exp221_source_graph8_20260921`.
After completion: `score/metrics.json`, `score/no_metric_gate.json`.
Supervision: `code/exp221_source_supervision_v1_20260921/state/`;
check `control_status.json`, `score_exit.json`, `complete.json`, errors/logs.

Local receipts: `reports/exp221_source_graph8_prepare_20260921.json`,
`reports/exp221_source_graph_input_audit_20260921.json`,
`reports/exp221_source_supervision_launch_20260921.json`,
`reports/exp221_source_monitor_handoff_local_stop_20260921.json`.
Actual inference verified primary+secondary8viewTTA. Estimate up to1h for
16movie predictions plus up to15min scoring; refine after first complete movie.

Live followup checked at Unix1789977989 (~2026-09-21 10:46:29 UTC):
source8 inference remains RUNNING, heartbeat CURRENT, lease retained, no
supervisor errors. Candidate caches: control8/8, domain1/8. No completion
receipt or official metric exists yet; CPU label access has not begun.
Next compact check after roughly10–15min using
`python scripts/check_exp221_source_graph.py`; no additional jobs launched.
