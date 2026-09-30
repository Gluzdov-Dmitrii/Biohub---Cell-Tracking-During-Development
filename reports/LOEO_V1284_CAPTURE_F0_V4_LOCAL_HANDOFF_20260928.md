# V1284 fold0 capture v4 — local source/control handoff

Status: **local static and synthetic validation passed; control v4 launch
blocked**. No v4 plan/attempt was sealed against remote model files; no v4
remote stage, queue request, GPU run, target GEFF read, score, or Kaggle POST.
The failed v3 source/control manifests remain byte-identical to their parent
seals, SHA256 `bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`
and `e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`.

## Preregistered corrections and resulting seals

The append-only preregistration chain preceded its respective code edits:

| Receipt | SHA256 |
| --- | --- |
| `LOEO_V1284_CAPTURE_F0_V4_LF_WATCHER_PREREG_20260928.md` | `7363649db2f4d7a75114d822552f0d338bec8308839dcbe0e9b87e3a05337541` |
| `LOEO_V1284_CAPTURE_F0_V4_LF_HASH_CORRECTION_PREREG_20260928.md` | `4a4fc882b405f246a5d0a31a4cab2208b1d0fb8cfb8d419977412780cb1029c0` |
| `LOEO_V1284_CAPTURE_F0_V4_RELEASE_CANARY_PREREG_20260928.md` | `daeed330d940fb4c54d5832300e67c95373d6f406cb3f5924f94b2b3cb359c8c` |
| `LOEO_V1284_CAPTURE_F0_V4_CHILD_IMPORT_PREREG_20260928.md` | `7ed15e65b306a1c1b0f5a0eb1c0ea3083a805e54ee95e84d6cc197d183c022f8` |

The first prereg copied a 63-character predictor LF hash; the second records
the observed full 64-character hash. Neither historical statement was erased.

| Local package/artifact | SHA256 |
| --- | --- |
| `work/loeo-v1284-source-capture-v4-20260928/package_manifest.json` (28 files) | `31d1a8c632c5cee711772e784a023bca377d4b9863a2ef9c3760a1aa54c8e55d` |
| `work/loeo-v1284-source-capture-v4-20260928/capture_cells.json` | `71b3e89f2ea2d6c5edf26b00dd65cde52e4ee85bcd3fbb00a4065aa020166bd2` |
| `work/loeo-v1284-source-capture-v4-20260928/capture_cells_manifest.json` | `b8cdc14d23ded547e831a5e50c67860cf73a244ecba4dae1335f80d40106a91b` |
| `work/loeo-v1284-capture-v4-control-v4-20260928/control_manifest.json` (7 files) | `8a555620d025665b88e0b09013fe89c37c25c190eb6b745a9fb1a52257273bb7` |

The v4 plan protocol is schema 4, purpose `v1284_source_image_capture_v4`,
identity `loeo_v1284_capture_f0_v4_<new 12-hex attempt>`. The control protocol
is schema 4, purpose `v1284_capture_v4_one_shot_control_v4`; a successful
terminal audit would use `PASS_CAPTURE_V4_RUNTIME_RELEASE_CONTROL_V4`.
`plan_capture.py` still requires separately audited same-fold primary and
secondary weight/config/receipt files and creates a fresh identity; the v3
attempt `1de3d2be98c3` must never be reused.

Cell4 now writes both generated Python files as UTF-8 LF, independent of host
newline settings. Predictor bytes: 55,227, 1,235 LF, zero CR, SHA256
`330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e5`.
Refinement module bytes: 3,423, 79 LF, zero CR, SHA256
`940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`.
The predictor child now receives `PYTHONPATH=src` plus the absolute sealed
capture-code directory for both single and sharded launch branches, so its
imports of `biohub_tracking` and `capture_guard` resolve from the exact model
cwd. The control launcher resolves its prepared config before passing it to
the detached watcher. Both terminal auditors require the observed queue
behavior: an exact RELEASED row with `gpus=[]`, while the earlier RESERVED
receipt and runtime observations bind the allocated GPU.

## Local verification

- Source tests: 11/11 PASS, including LF/CRLF byte identity, exact two hashes,
  source-only scope, graph boundary, GEFF deny, release-row positive/negative,
  and CPU canary.
- Control tests: 18/18 PASS, including watcher launched from an arbitrary cwd
  with an absolute external config, actual empty-GPU release row, retained and
  extra GPU rejection, source manifest pins, and wrapper transport.
- Standalone `canary_patch_hashes.py --plan <synthetic-v4-plan>` CLI exited 0.
  It executed exact cell4 for LF and CRLF parent inputs with CUDA and model
  launch mocked, then ran a real CPU subprocess using the captured predictor
  cwd/env; `capture_guard` and `biohub_tracking` imports passed. No model
  child, graph or GPU ran. Its JSON status was
  `PASS_V1284_V4_CPU_PATCH_HASH_CANARY` with `model_launch=MOCKED_ONLY`.
- Independent local readback rehashed 28/28 source and 7/7 control entries;
  parsed 22 source Python files, 6 control Python files and all 5 executable
  capture cells. Parent v3 manifest hashes matched the original seals.

## Outstanding gates

1. **Control v4 must not launch.** In `capture_control.launch`, `request_lease`
   precedes any durable request intent or reservation receipt. Its imported
   `scripts/launch_exp221_job.py::queue_request` issues a 45-second SSH
   request and cancels a WAITING row only after receiving a JSON
   `WAITING_RESOURCE` reply. An accepted request followed by SSH timeout
   raises before the cancel branch and before `reservation.json`; an unlaunched
   WAITING or RESERVED lease can remain active. A distinct preregistered
   control-v5 request-intent/recovery correction, lost-reply tests and
   independent review are required before remote stage or queue mutation.
2. A separate downstream head-audit successor must update its v3
   capture/control/cell/predictor/module/identity pins and its fabricated
   RELEASED `gpus=[gpu]` expectation before any v4 capture can feed it.
3. Before any future GPU request, independently review both v4 package seals,
   create a fresh remote v4 plan/attempt from real audited model files,
   stage/read back exact package and plan bytes, and run the sealed CPU canary
   with the same prepost interpreter. The canary's real import smoke is a
   prerequisite, not feature capture or OOF evidence.
