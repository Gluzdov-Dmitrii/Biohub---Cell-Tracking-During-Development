# SOURCE-INNER v2 error decomposition: local review handoff

## Correction and scope

The v1 audit stopped before its output directory or source GEFF access. Its target175 image-scale receipt covered 17 of the exact 19 source-inner movie IDs, omitting `44b6_f28707c6` and `44b6_341df25f`. Remote exit was 1 without timeout, zero movies completed, and the child process exited. Preserve v1 code, bundle, stage, launch, and exit. Failure receipt: `reports/source_inner_error_decomposition_v1_failure_20260927.json` SHA256 `994aedba0ab1e86683c9a0faa8f6c034d8d73ed8762395ecc1138932f60436cb`.

The new source19 image-only receipt was read from each exact source-plan Zarr root and `0/zarr.json` with GEFF denied. It compared direct metadata scale and shape against the pinned historical `open_dataset(..., require_tracks=False, load_image=False)` behavior and verified the scorer plan/config and evaluator file hashes. All 19 IDs passed at scale `(1.625, 0.40625, 0.40625)`. Receipt `reports/source_inner19_image_scale_audit_v2_20260927.json` SHA256 `d447f0d18f9c79f4d2397def9e7a196cb3e1075df402350bc8a792941beddfe6`. This image-only check used the compatible `prepost/py3.11-stdlib-v1` environment; the isolated current organizer environment lacks torch, which `biohub_tracking.io` imports. The v2 scorer itself uses the isolated current organizer environment and passed its separate exact module import preflight without torch.

## Sealed v2 package and gates

- Bundle: `work/source_inner_error_decomposition_v2_20260927`, seven payload files, manifest SHA256 `3216b95fe675de7b19d0cdb8c592dafa4c84174e26cc9b2b15b5ae3a10a3deec`.
- It contains only the exact source19 image receipt, no target175 image manifest. The image receipt, exact ordered IDs, Zarr paths, shape and metadata SHA values are checked before any graph or GEFF load. Source scorer code/config, plan, graph receipts and evaluator pins retain their previous gates. All v1 scoring and endpoint-classification functions are AST-identical; only the image/receipt gate and v2 output namespace changed.
- The existing preregistered matched-node, edge endpoint and division score decomposition remains in force. It is a source-inner training-monitor diagnostic, not target OOF.
- Remote code namespace: `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/source_inner_error_decomposition_v2_20260927`.
- Remote run namespace: `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/source_inner_error_decomposition_v2_20260927`. Both were absent at read-only import preflight.
- Read-only current-organizer import preflight receipt: `reports/source_inner_error_decomposition_v2_import_preflight_20260927.json` SHA256 `6003eeeeeb7ddbf44390d57c2f6474173353be7957049590db86f903d39dc293`. It imported both exact pinned scorer gate modules and `biohub_tracking.metrics`, with all GEFF denied, code/run absent, and `torch_available=false`.

## Review and future one-shot commands

The v2 stage and launch scripts are prepared locally. Their dry runs issue no SSH and both passed. The stage transfers nested paths as bytes, verifies every remote hash and Python AST, and creates a durable intent before the first remote mutation. Launch repeats the import/readback preflight, creates its own durable intent, then starts one child with CPU affinity 24–27, CUDA hidden, 16 GiB address space, 2400 CPU seconds and 2700 wall seconds. An existing intent or namespace fails closed for reconciliation.

```powershell
python -B scripts/stage_source_inner_error_decomposition_v2.py --dry-run
python -B scripts/launch_source_inner_error_decomposition_v2.py --dry-run
```

After review, the distinct one-shot mutation commands are:

```powershell
python -B scripts/stage_source_inner_error_decomposition_v2.py
python -B scripts/launch_source_inner_error_decomposition_v2.py
```

Stage source SHA256 `eb342beea4efb51dffa907b10e7fdcc5c9b4202d66fd0301cb5cf6827e127c89`; launch source SHA256 `09052962d3486decf0e058eec1d23d41e52a1ef48824d2513670e4f75a7071f6`. Dry-run generated remote stage source SHA256 `5b06678d14a4a7637ca74d856c45978171852a81d4cdfa72470cc102ec907b9b`, launch source SHA256 `5af6d1d33f967dd029abf38bfd818b32cbf422fa450a35e003df9d3e1377cb22`. The exact source image audit, stage bytes, dry-run commands, intent ordering, preserved scoring AST, and endpoint fixture passed `8` focused tests (`tests/test_source_inner_v2_stage_launch.py`, `tests/test_source_inner_error_decomposition.py`).

No v2 stage/launch or graph scoring was invoked. No source GEFF, reciprocal target labels, GPU inference or Kaggle POST were used in preparing v2. The retained Horaz graph artifacts do not contain proposal logits/features; adaptive peak-threshold variants require a separate GPU inference pass unless such features are cached.
