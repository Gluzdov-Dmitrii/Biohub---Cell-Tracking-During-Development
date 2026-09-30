# V1284 fold0 source-v4/control-v5 stage and CPU-canary workflow draft

Prepared 2026-09-28 from the immutable v3 preparation and the v4/v5 seals.
**No remote command in this draft has been run.** Independent control-v5
review must explicitly return PASS, then its exact schema/purpose/manifest
SHA must be appended to `EXPERIMENTS.md` before the first remote stage.
This draft does not authorize a queue request or GPU launch.

## Exact inputs and fresh identity

| Item | Pinned value |
| --- | --- |
| Source package | `work/loeo-v1284-source-capture-v4-20260928`, manifest SHA256 `31d1a8c632c5cee711772e784a023bca377d4b9863a2ef9c3760a1aa54c8e55d`, 28 entries plus manifest |
| Control package | `work/loeo-v1284-capture-v4-control-v5-20260928`, manifest SHA256 `9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`, seven entries plus manifest; remote copy is inert evidence, Windows-side control remains the executable one |
| Remote project root `R` | `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development` |
| Production Python | `$R/envs/prepost/py3.11-stdlib-v1/bin/python` |
| Queue host and file | `nsu-quadro`, `/home/scientists/gluz_d_s/kaggle/_control/resource_queue.py` |
| Source image root | `$R/data/exp213_source_view_20260912` |
| Approved image parents | `$R/data/pilot_single_44b6`, `$R/data/honest195_missing/train` |
| Primary weight/config parent | `$R/runs/loeo_primary_full_f0_v2_eeb0880f73f7/output/weights/loeo_primary_full_f0_v2_20260928/split_0` |
| Secondary weight/config parent | `$R/runs/loeo_secondary_full_f0_v1_07911298d0f9/output/weights/loeo_secondary_full_f0_v1_20260927/split_0` |
| Audit receipt parent | `$R/plans/loeo_v1284_capture_f0_v3_1de3d2be98c3.receipts` |

Under the model parents, use `edge_predictor_best.pth` and `config.json`.
Under the audit parent, use `primary_full_final_reconciliation.json` and
`secondary_full_final_reconciliation.json`. The audited hashes are primary
weight `b2da409d45206309bf68d8028d2554bafbffd346419250c9bc04990bd16ee3e2`,
secondary weight `82115428795e51a31a6a44a8fa983c6743ef4d052539b0daccc04db4ffd568ae`,
both configs `e9b4e396c58081bca08adf8275bd0bd1c2d3fd6eb091a1912a5116cb6de7b50a`,
primary audit `4c466db4c66cc474d51f86df362c8a6ca6b0174f191bf9db1e06c9a77985bd2c`,
secondary audit `6e0db16db9d2398e3f21be7ac9198013b2b399de5ef19f42d479702c3ac1d768`.
Those audit receipts may be read as model evidence; their v3-named storage
path does not authorize reusing the failed v3 plan, code, run or lease.

Generate a new random 12-hex attempt only when the review gate opens. For
this prepared attempt, the exclusive local `stage_intent.json` already fixes
`ba382850b115` and identity `loeo_v1284_capture_f0_v4_ba382850b115`;
**do not generate a second attempt**. This differs from
`loeo_v1284_capture_f0_v3_1de3d2be98c3` in both version and suffix.
Before any upload, read only the exact code/plan/run paths and the queue
status; all four must have no existing entry for the fixed identity. Record
those checks and the review receipt SHA outside both sealed packages.

## Deferred exact commands

On the Windows host, verify both local manifests byte by byte first. Use
binary `scp -r` to copy the **unmodified** source directory to a new
`$R/code/.loeo-v1284-f0-v4-stage-<fresh nonce>` and the unmodified control
directory to a new `$R/plans/.loeo-v1284-f0-control-v5-stage-<fresh nonce>`.
The staging destinations must not exist. Do not use a text transfer or edit
files after transfer. If either transfer is interrupted, preserve its staging
directory and stop; do not resume by overwriting files.

On `nsu-a100`, run this script via the production Python with `-B` from the
exact staged source directory. The direct sealed API fixes the attempt that
the local stage intent already recorded; the CLI's auto-random attempt must
not be used for this attempt.

```python
from pathlib import Path
from plan_capture import make_component, seal_plan

R = Path('/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development')
primary = R / 'runs/loeo_primary_full_f0_v2_eeb0880f73f7/output/weights/loeo_primary_full_f0_v2_20260928/split_0'
secondary = R / 'runs/loeo_secondary_full_f0_v1_07911298d0f9/output/weights/loeo_secondary_full_f0_v1_20260927/split_0'
audits = R / 'plans/loeo_v1284_capture_f0_v3_1de3d2be98c3.receipts'
parents = [primary, secondary, audits]
primary_component = make_component(primary / 'edge_predictor_best.pth',
                                   primary / 'config.json',
                                   audits / 'primary_full_final_reconciliation.json', parents)
secondary_component = make_component(secondary / 'edge_predictor_best.pth',
                                     secondary / 'config.json',
                                     audits / 'secondary_full_final_reconciliation.json', parents)
plan_path = seal_plan(
    fold=0, input_root=R / 'data/exp213_source_view_20260912',
    run_parent=R / 'runs', plan_dir=R / 'plans',
    approved_image_parents=[R / 'data/pilot_single_44b6',
                            R / 'data/honest195_missing/train'],
    approved_component_parents=parents,
    primary=primary_component, secondary=secondary_component,
    attempt='ba382850b115')
print(plan_path)
```

Require stdout to contain exactly one path
`$R/plans/loeo_v1284_capture_f0_v4_ba382850b115.json`. Parse the plan,
assert schema 4, purpose
`v1284_source_image_capture_v4`, fold 0, the v4 source manifest and both LF
hashes. Require all source IDs to be the 71 `44b6_*` IDs from the sealed
split; `work_dir` is `$R/runs/<identity>` and must still be absent. Query
queue status again and reject any row with lease ID
`loeo-v1284-capture-f0-v4-<attempt>`. Then rename the verified source
staging directory to `$R/code/<identity>` only if that final path is absent;
copy the inert control staging directory to
`$R/plans/<identity>.control-v5` without changing bytes.

Read back both remote package inventories before any canary: every path
except `package_manifest.json` or `control_manifest.json` must equal the
respective manifest path set, be a regular non-symlink file, and match both
byte count and SHA256. Require 28/28 source entries and 7/7 control entries,
no `__pycache__`, and both remote manifest-file hashes equal the values
above. Save the raw JSON readback and its SHA locally. From the final source
directory, call `capture_contract.require_package_manifest()` and
`capture_contract.validate_plan(plan)` with default `require_files=True`;
this rehashes all six approved model/audit inputs and verifies the independent
same-fold audit fields. Save the plan's exact raw bytes locally and require
the local and remote plan SHA256 to match.

The CPU canary command, executed from the final code directory on
`nsu-a100`, is:

```bash
cd "$R/code/<identity>"
env -u V1284_HEAD PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH="$R/code/<identity>" CUDA_VISIBLE_DEVICES=-1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 \
  "$R/envs/prepost/py3.11-stdlib-v1/bin/python" -B \
  "$R/code/<identity>/canary_patch_hashes.py" \
  --plan "$R/plans/<identity>.json"
```

Capture stdout/stderr/exit code as raw local files with exclusive fsynced
writes. Accept only exit 0 and JSON status
`PASS_V1284_V4_CPU_PATCH_HASH_CANARY`, exact plan/source-manifest hashes,
`model_launch=MOCKED_ONLY`, `child_import_smoke=PASS`, LF and CRLF input
variants equal, predictor SHA256
`330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e5`,
module SHA256 `940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`,
and zero CR bytes in both generated files. The canary internally executes
exact cell4 with a mocked model subprocess and a real CPU subprocess using
the captured model-child cwd/environment to import `capture_guard` and
`biohub_tracking`. It never runs inference or requests a GPU.

Finally, invoke Windows-side control-v5 `prepare` with the absolute final
code and plan paths, a new local receipt directory, and external expected
control manifest SHA
`9879b85193d74415e5afc14ec613e02190f64d6bf93f02fff97fc99ebf918ed2`.
Require `PASS_LOCAL_PREPARATION_NO_LEASE`, exactly 71 approved source image
symlinks, all runtime modules, absent run, no existing lease and a physically
idle A100. Save its absolute config path and preparation receipt. **Stop
there** until a separate one-shot queue/GPU launch decision.

## Source-only readback and current blocker

Local read-only proof passed: sealed manifest 28 entries, 71 source IDs all
`44b6_*`, 128 disjoint outer IDs all `6bba_*`, five executed cells stopping
after cell4, and `capture_guard.check_path` rejected synthetic outer GEFF,
source GEFF and published Kaggle input paths. The canary uses a temporary
synthetic source `.zarr` and no labels. Cell4 contains dormant GEFF output
merge code for multi-GPU prediction, but this control requests one A100;
`capture_guard` forbids GEFF access in the child. Actual remote source-image
symlink targets and zero denied-access lines still require live readback.

As of this draft, independent control-v5 PASS has not been sent to this
worker. The required `EXPERIMENTS.md` control-v5 pin is likewise not
recorded by this workflow. Remote stage, plan creation, CPU canary and queue
request remain pending those gates.
