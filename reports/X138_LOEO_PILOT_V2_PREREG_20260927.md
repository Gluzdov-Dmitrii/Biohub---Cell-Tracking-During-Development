# x138 fold-0 source-only technical pilot v2 — additive preregistration, 2026-09-27

Status: **local preparation only**. This note supplements
`X138_LOEO_PILOT_PREREG_20260927.md`; it does not revise attempt0 or count as
training, an outer-embryo evaluation, or a competition submission. No v2 remote
stage, GPU lease, launch, Kaggle push or POST has occurred.

## Attempt0 failure and narrow correction

The original attempt `50420aa01a60` completed all 71 source movie loads, then
failed at the first batch when its Python audit hook denied `socket.connect` to
`/tmp/pymp-ulpydsrb/listener-8288m_n2`, PyTorch multiprocessing
`resource_sharer` local IPC. It exited 1 without a timeout or checkpoint. The
queue is `RELEASED`, the process group is gone, and no GPU PID remains. The
read-only reconciliation receipt is
`work/x138_loeo_runtime/pilot_attempt0_failure_reconciliation.json` SHA256
`dfb43c9937817ee28ec8da7b5b1b5f8a58a6c57a3a627e978274081c1623afe7`.
Attempt0 code, plan, run and receipts remain immutable and must not be reused.

V2 changes only the network audit rule: the hook reads `args[0].family` and
`args[1]` for `socket.connect` / `socket.connect_ex`, and permits `AF_UNIX`
connections only to `/tmp/pymp-*/listener-*`. `AF_INET`, `AF_INET6`, unknown
families and other Unix socket destinations are denied and logged. This is a
Python audit guard, not an OS sandbox. If PyTorch uses another local IPC path,
the pilot fails visibly; widening the rule requires separate review. The v2
guard source `work/x138_loeo_runtime_v2/pilot_contract.py` has SHA256
`d007be577e48dd0645982528ade4be28154bf2737cacf17e93eecc7c2b1ade57`.

## Fixed v2 contract and identity

- Fold 0 only: all 71 `44b6` source IDs, 56 trainer `train`, 15 source-inner
  `test`/validation; all 128 `6bba` target IDs remain sealed. Pinned split
  SHA256 `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.
- Public support-pack 13-file manifest SHA256
  `a6f57ca8232e43711253326eb20356ae625ac123ba4e5d52ee4aba87c1c07d5b`;
  trainer SHA256 `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`.
  V2 references the local pinned public source and stages byte-identical copies.
- One A100, no pretrained weights, one epoch, 16 maximum training iterations,
  batch size 8, **two** DataLoader workers, single GPU. The trainer CLI default
  architecture, downsample `(1,4,4)`, LR `1e-4`, detection-loss weight `1.0`,
  negative weight `0.01`, window size 2 and pool kernel 5.0 are passed
  explicitly. All 15 validation movies are evaluated; the runtime can still
  hit the hard limit. Child termination and exit receipt remain bounded within
  3600 seconds.
- New method `x138_loeo_f0_technical_pilot_v2`, attempt `b8aa6aed390d`,
  lease ID `x138-loeo-f0-v2-b8aa6aed390d`. Remote code and run roots are
  respectively `code/x138_loeo_f0_tech_v2_b8aa6aed390d` and
  `runs/x138_loeo_f0_tech_v2_b8aa6aed390d` under the Biohub project root.
  No attempt0 path is reused.
- Sealed local bundle `work/x138_loeo_runtime_v2/pilot_bundle/` manifest SHA256
  `80d04f30aaeaba900b45f311f053834a4c3f89c0da24e9685b8f1b4e05582f1b`;
  immutable plan `work/x138_loeo_runtime_v2/pilot_plan.json` SHA256
  `90ec5f4bf9834458940a56e5532547fc33149e2c68a41f9b2b69deffea39a462`.

The runner creates exactly 71 source `.zarr` / `.geff` symlink pairs. Each
resolved pair must retain its `44b6` ID basename and resolve to one of the two
observed project-data source parents, `data/pilot_single_44b6` or
`data/honest195_missing/train`. The trainer's weights path points to the run
output, leaving staged code immutable. The loader wrapper records all 71
successful source loads; the audit hook denies outer IDs and external
checkpoints. The run records finite train/inner-validation metrics, elapsed
time, peak CUDA memory, checkpoint SHA and a public
`predict_unet_transformer.load_model` plus finite-tensor check. The wrapper
records process identity, hard timeout and exit; observer/controller and
read-only reconciliation follow the same lease-release rule as attempt0.

## Local gate and parent-only next action

Six focused tests passed with temporary bundle and fake remote/queue states:
split/catalog pin, source/outer path guard, allowed `AF_UNIX` resource-sharer
address, denied `AF_INET`/`AF_INET6`/unknown/other Unix addresses, and the
supervisor `token` contract. The non-mutating
`python work/x138_loeo_runtime_v2/pilot_control.py --preflight` passed: remote
v2 code/stage/run paths absent, exact 199 `.zarr` and 199 `.geff` stems, 142
unique approved source targets, required pinned-environment modules present,
and no foreign waiting queue request at that read. Queue state is volatile.

Only the parent may run `python work/x138_loeo_runtime_v2/pilot_control.py stage`
and then `python work/x138_loeo_runtime_v2/pilot_control.py launch`. Both modes
recheck identity and queue gates. After launch, verify status, denied log,
checkpoint, process group, GPU PIDs and lease release with the run receipts and
`python work/x138_loeo_runtime_v2/pilot_control.py reconcile`. A failure or
timeout remains evidence and is not retried under the same attempt ID. Pilot
success would establish technical compatibility only, not x138 OOF or a
competition POST gate.
