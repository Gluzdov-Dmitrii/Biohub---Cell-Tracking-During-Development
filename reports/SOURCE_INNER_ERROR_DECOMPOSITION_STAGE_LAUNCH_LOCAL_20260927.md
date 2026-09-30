# SOURCE-INNER audit stage and CPU launch: local handoff

Status: **prepared, not staged or launched**. Original seven-file SOURCE-INNER bundle is unchanged at `work/source_inner_error_decomposition_20260927`, manifest SHA256 `17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e`. Its preregistration is `reports/SOURCE_INNER_ERROR_DECOMPOSITION_PREREG_20260927.md`. No GEFF labels, target score, GPU or Kaggle POST were touched by this handoff.

The separate one-shot scripts are `scripts/stage_source_inner_error_decomposition.py` SHA256 `ba3e4f73d6dfe91a80e9e1dc5b33a1f36a27b456c4ec06ddf8b6de9a9f9c2190` and `scripts/launch_source_inner_error_decomposition.py` SHA256 `f99ff010bef33ab14deb207091626e4eb15458c56f250cc250a96b87d7b26bfe`. Neither was invoked in its mutation mode. Expected remote code is `/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/source_inner_error_decomposition_v1_20260927`; expected run is the matching `runs/source_inner_error_decomposition_v1_20260927`. Both namespaces were absent at the read-only preflight. Original source scorer graph/run paths are inputs only.

## Read-only runtime preflight already performed

`python scripts/stage_source_inner_error_decomposition.py --preflight-only` used `nsu-quadro`'s existing `envs/current-organizer-py311-e13cf-v1/bin/python -B` with CUDA hidden and bytecode writes disabled. It rehashed both pinned source scorer code manifests/configs and all pinned legacy evaluator files, then imported the exact `score_exp227_source_graph10.py`, `score_exp236_source_graph10.py`, their `score_exp214_paired.py`/`score_exp223_official.py` dependencies from each scorer directory, and `biohub_tracking.metrics` from the pinned EXP214 repository. The preflight installed an audit hook rejecting any GEFF access. Result: `PASS_SOURCE_INNER_EXACT_IMPORT_PREFLIGHT_NO_LABELS`; `torch_available=false`; code absent, run absent, labels unread. Local receipt `reports/source_inner_error_decomposition_import_preflight_20260927.json` SHA256 `28a3f79e62c30c079d23e9e6196aca89aca76d67209af270cc30ab0fbe05739b`. This demonstrates those imports succeed despite torch being absent. Both future stage and launch repeat the preflight and fail closed on an import error or unexpected torch availability.

## One-shot safeguards and review commands

Stage revalidates the exact local bundle SHA and all seven payload hashes, performs fresh read-only remote import and namespace-absence checks, then creates and `fsync`s `reports/source_inner_error_decomposition_stage_intent_20260927.json` with exclusive creation **before** remote mutation. It sends the original bytes, including `tracking_cellmot_official/*` nested paths and `manifest.json`, as base64 payloads; the remote writes them once into an absent code directory. A separate readback rehashes every file, checks the exact file set, AST-parses each Python source, and confirms the run namespace remains absent. Only then does stage create its receipt. Any intent without a final receipt requires reconciliation; no blind retry.

Launch requires that stage receipt and intent, repeats the exact read-only import and staged byte/AST gates while the run namespace is absent, then creates and `fsync`s its own exclusive launch intent before the one-shot remote run directory and detached CPU wrapper. The worker uses the pinned isolated Python with `--bundle-sha256 17f7ee386ade78237574e17fde616c7ffb2acab24c31c19f3926c673439a018e`, CPU affinity 24–27, CUDA hidden, four numerical-library threads, 16 GiB address-space cap, 2400 CPU-second cap, and 2700-second wall timeout. The wrapper records child identity, stdout/stderr, timeout, exit status and error in the dedicated run directory. Launch readback rehashes the wrapper and all staged source bytes, AST-parses Python sources, and records live wrapper or exit evidence. Launch itself makes no metric claim.

Safe preview commands already exercised without SSH or remote mutation:

```powershell
python scripts/stage_source_inner_error_decomposition.py --dry-run
python scripts/launch_source_inner_error_decomposition.py --dry-run
```

After separate root review, the stage and launch entry points are, in order:

```powershell
python scripts/stage_source_inner_error_decomposition.py
python scripts/launch_source_inner_error_decomposition.py
```

Before running the second command, review the stage receipt and live remote code/run state. No stage or launch command above has been run in mutation mode. Estimated CPU analysis time remains about 2–10 minutes based on previous source diagnostics, with a hard 45-minute wall cap. A completed worker still needs independent verification of its `no_label_gate.json`, `result.json`, 19 source GEFF tree hashes, exit code and unchanged source graph receipts before interpreting the detection research signal. Adaptive detector threshold testing would separately require GPU inference or a feature cache, since the saved Horaz graph artifacts have no logits or proposal features.

Local verification: `tests/test_source_inner_stage_launch.py` plus the endpoint fixture passed **6/6**, including simulated uncertain stage and launch replies that leave durable intents without final receipts; both new scripts compile; stage/launch dry-run command plans generated; the original bundle manifest rehashed unchanged. At sealing, all four stage/launch intent and receipt paths were absent.
