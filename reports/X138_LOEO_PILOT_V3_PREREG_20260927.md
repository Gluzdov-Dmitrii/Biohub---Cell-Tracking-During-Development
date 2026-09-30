# x138 fold-0 source-only technical pilot v3 — additive preregistration, 2026-09-27

Status: **local preparation only**. This note adds a fresh technical attempt
after the v2 CUDA failure. V1 and v2 code, plans, remote runs and receipts remain
unchanged and must not be restarted. No v3 remote stage, lease, GPU run, Kaggle
push or competition POST has occurred.

## V2 observation and backend hypothesis

V2 attempt `b8aa6aed390d` loaded all 71 pinned source movies and passed its
source access guard (`denied_access_count=0`). Its first training forward then
raised `RuntimeError: CUDA error: invalid configuration argument` from
`_TemporalAttention` → `MultiheadAttention` →
`scaled_dot_product_attention`. It exited 1 without a timeout or checkpoint;
queue state is `RELEASED`, with no live child group or GPU PID. The immutable
read-only reconciliation copy is
`work/x138_loeo_runtime_v2/pilot_attempt_v2_failure_reconciliation.json` SHA256
`6cbc7cff772982a81679de9c532364d7093d9851b32ab535342410c13f136d13`.
This is a failed technical run, not model-quality evidence.

The public model reshapes temporal attention to batch `B × S`. Read-only
metadata for source movie `44b6_0113de3b` gives image shape
`[100,64,256,256]`; fixed spatial downsample `(1,4,4)` yields `[64,64,64]`,
then the first active temporal stage pools to `[32,32,32]`. At fixed training
batch 8, `B × S = 8 × 32³ = 262,144`. [PyTorch issue #142228](https://github.com/pytorch/pytorch/issues/142228)
documents the same CUDA invalid-configuration failure for large SDPA batches,
including the efficient attention kernel's reported 65,535-block limit; its
author gives the math backend as a workaround. This shape and matching stack
are a causal hypothesis, not proof that v3 will finish.

The pinned `nsu-a100` prepost Python reports PyTorch `2.6.0+cu124`, callable
`torch.nn.attention.sdpa_kernel` and `SDPBackend.MATH`. V3 uses the
[documented context manager](https://docs.pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html)
with **only** `SDPBackend.MATH` around the entire `trainer.train()` call,
covering forward, backward and checkpoint selection, and around public
`predict_unet_transformer.load_model()` validation. This changes dispatch only:
no public model file, architecture, tensor shape, state_dict key, source split,
training argument or source-access rule changes. Math SDPA can be slower and
may hit the existing 3600-second hard timeout.

## Fixed identity and unchanged source boundary

- New method `x138_loeo_f0_technical_pilot_v3`, attempt `dd6361c6d509`, lease
  ID `x138-loeo-f0-v3-dd6361c6d509`. The planned remote code and run paths are
  respectively `code/x138_loeo_f0_tech_v3_dd6361c6d509` and
  `runs/x138_loeo_f0_tech_v3_dd6361c6d509` under the Biohub project root.
- Sealed local `work/x138_loeo_runtime_v3/pilot_bundle/` manifest SHA256
  `dcedf2d2f217d622623dbc1a5fb98be1ca46868c374e2242364b509fc7dbb523`;
  `work/x138_loeo_runtime_v3/pilot_plan.json` SHA256
  `bf23757c373a90996c8cdf6c244c9a92df8e8e51551cfcc1240d743d5ac47acf`.
  V3 runner source SHA256
  `6c57dc54a254a6f25fbd4e6fd449966653daece81b27d851597a346429748c8f`.
- Exact same 13 public support-pack Python file hashes as v2; pinned trainer
  SHA256 `c4f6317736bb3bb1ec8f3f6e9a6d935a463e3f0f1f685481b2d13218d35dc9ea`,
  support manifest SHA256
  `a6f57ca8232e43711253326eb20356ae625ac123ba4e5d52ee4aba87c1c07d5b`,
  and split SHA256
  `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.
- Fold 0 remains 56 source `44b6` train and 15 disjoint source `44b6`
  validation IDs; all 128 `6bba` outer IDs are sealed. The isolated view has
  exactly 71 `.zarr`/`.geff` pairs. The v2 Python audit guard still allows
  only PyTorch's observed `AF_UNIX` `/tmp/pymp-*/listener-*` IPC, while denying
  target-data paths, external checkpoints and other sockets.
- One A100, no pretrained weights, one epoch, maximum 16 training iterations,
  batch 8, two workers, single GPU, explicit CLI-equivalent defaults
  (architecture `[32,64,128]`, downsample `(1,4,4)`, LR `1e-4`, detection loss
  weight `1.0`, negative weight `0.01`, window size 2, pool kernel 5.0). The
  entire 15-movie inner validation still runs. The bounded wrapper, output
  SHA/metric checks, public checkpoint loader, observer/controller and lease
  reconciliation remain as in v2.

## Local gate and parent-only actions

Eight focused local tests passed: a temporary sealed bundle and fake
remote/queue preflight, source/target and IPC guards, supervisor token mapping,
exact v2/v3 training-argument and 13-source-hash equality, and math-only SDPA
flags `(math=True, flash=False, efficient=False)` during a stub trainer call
with restored flags afterward. The local read-only
`python work/x138_loeo_runtime_v3/pilot_control.py --preflight` passed: v3
remote code/stage/run paths absent, exact 199 `.zarr`/`.geff` stems, 142 unique
approved source targets and required pinned-environment modules present, with
no foreign waiting queue request at that read. Resource state is volatile.

The parent may stage with `python work/x138_loeo_runtime_v3/pilot_control.py stage`,
then perform a CPU-only remote smoke of that exact staged code before
`python work/x138_loeo_runtime_v3/pilot_control.py launch` under refreshed
queue and resource checks. Afterward use run receipts and
`python work/x138_loeo_runtime_v3/pilot_control.py reconcile` to verify
source-only loads, zero denied access, finite metrics, checkpoint loadability,
timeout, no process/GPU PID and lease release. Any failure remains evidence;
never retry this identity. Technical success alone is not honest outer-embryo
OOF or a competition POST gate.
