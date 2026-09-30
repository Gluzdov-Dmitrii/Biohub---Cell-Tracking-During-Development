# EXP221 approved and running remotely

The previous transfer block was resolved by the user's explicit approval:
“ок пусть грок запустит расчеты все удаленно, на удаленных ресурсах”.
Exact source/config staging succeeded via the approved SSH path; no local
model training. The earlier BLOCKED report remains historical evidence.

Both two-step A100 smoke runs passed finite-loss checks, exited0 without
timeout and released shared-queue leases before production launch.
Control smoke edge/detection losses: 0.00049327 / 0.00996947.
Domain smoke: 0.00038742 / 0.01060555. These are smoke diagnostics, not
model-quality comparisons or CV.

Production jobs are RUNNING on ngpu01, one A100 80GB per arm:

| Arm | Shared queue lease | Wrapper PID |
|---|---|---|
| Control | exp221-control-44b6-s2026-20260921 | 546206 |
| Domain augmentation | exp221-domain-44b6-s2026-20260921 | 546304 |

Remote project root:
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development`.
Runs: `runs/exp221_{control,domain}_44b6_s2026_20260921`.
Both have live child process identities, GPU allocations and initial backward
execution observed. Training starts from source44b6 clean epoch12, seed2026,
1499 training and672 source-validation windows; fixed endpoint epoch24.
The exact model+optimizer initialization SHA matches both smoke contracts:
`f8a43239be4136bc0d3d44ff19cfb8d69deb7b852e3abfc39f4a44c54a78a638`.

Chunk budget7200s at epoch boundary, finite24epoch cap, wrapper hard timeout
10800s; queue leases180min. Do not automatically expand beyond the pilot.
Both target labels and Kaggle POST remain closed. Source accuracy*recall
is only checkpoint-selection proxy. PyTorch warns that existing trilinear
and max-pool backward kernels are not bitwise deterministic; RNG pairing
does not imply bitwise-identical GPU results.

Receipts:
- `reports/exp221_staging_20260921.json`
- `reports/exp221_smoke_live_20260921.json`
- `reports/exp221_training_live_20260921.json`
- `reports/exp221_{control,domain}_44b6_s2026_20260921_config_launch.json`

Epoch13 completed in181.65s control and170.01s domain, both finite. At this
measured rate, fixed12epoch continuation should complete roughly35–45min
after launch (08:11UTC), approximately08:46–08:56UTC /15:46–15:56 Novosibirsk.
Allow1h for checkpoint verification and lease release. Official paired graph
evaluation must follow as a separate guarded stage.

Supervision handoff COMPLETE: no owned local monitor remains. Exact local
monitor processes10868/29248 were commandline-verified and stopped only after
remote readiness checks. Remote observer PID546712 on ngpu01 writes fresh
PID/start/group/GPU observations to the registered project NFS directory.
Remote controller PID358751 on canonical prepost consumes those observations
and calls the existing shared queue helper. Both successful remote heartbeats
and CURRENT leases verified after activation. No credentials were copied and
no node-to-node SSH configuration changed. Both helpers are bounded to4h,
never launch training, and release only after a fresh observation proves exit,
no original process identity, no process group and no GPU process. Unknown or
stale observations retain allocations. Thus training, timeout and supervision
are all remote and do not depend on the user's desktop remaining connected.

Remote supervision directory:
`code/exp221_supervision_v1_20260921/state/`.
Check `observations.json`, `control_status.json`, eventual `complete.json`,
and any `*_errors.jsonl` / `*_deadline.json` through canonical nsu-quadro.
Local receipts: `reports/exp221_remote_supervision_launch_20260921.json`,
`reports/exp221_monitor_handoff_local_stop_20260921.json`,
`reports/exp221_remote_supervision_verified_20260921.json`.

Local launcher monitor-file naming was corrected before production. The two
smoke monitor snapshots were preserved in separate `_smoke_monitor.json` files
and smoke configs restored; remote source/config and training were unaffected.
