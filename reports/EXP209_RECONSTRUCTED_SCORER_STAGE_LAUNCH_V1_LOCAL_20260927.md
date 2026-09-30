# EXP209 reconstructed scorer v1 — guarded stage and CPU launch handoff

Status: **PREPARED_LOCAL_ONLY_UNINVOKED**, 2026-09-27. Root review is required
before either command below. No stage, launch, GEFF access, historical or current
metric execution, GPU work, or Kaggle POST occurred in this preparation.

## Sealed input and namespace

The existing 14-payload scorer bundle remains byte-identical in
`work/exp209_reconstructed_scorer_v1_local_20260927/bundle`. The
`bundle_manifest.json` SHA256 is
`2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb`,
`config.json` is
`d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335`,
and `score_exp209_reconstructed_current_v1.py` is
`72e24bc53128c1e35ffe7dc806c74ccf0ad36575b52c5d7753ee60e2b3771b79`.
The scorer config binds the completed reconstruction no-metric gate SHA256
`8379ffc4435b01d0a8b7c90087302001b0b7738914e84fdd0286b888e8ff32f1`.

The one-shot stage creates exactly
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/code/exp209_reconstructed_current_scorer_v1_20260927`.
The scorer output must initially be absent at
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/exp209_reconstructed_current_scorer_v1_20260927`.
The separate launch control path is the sibling
`/home/scientists/gluz_d_s/kaggle/projects/biohub-cell-tracking-during-development/runs/.exp209_reconstructed_current_scorer_v1_20260927.control`.
The stage/launch scripts neither overwrite an existing path nor resolve an
ambiguous attempt by retrying it. Existing local or remote intents require
manual reconciliation and a new reviewed version if necessary.

## Guard sequence

1. `stage_exp209_reconstructed_scorer_v1.py` checks the exact reviewed
   manifest/config/runner bytes, the 14 manifest rows, all 15 file names,
   nested path safety and symlinks. It packages binary file bytes, preserving
   the archived CRLF source. It writes and fsyncs a local exclusive stage
   intent before SSH. Remote code/run/stage-intent/stage-complete namespaces
   must be absent. Remote stage writes its exclusive intent before creating
   the code directory, writes each nested file with `O_EXCL` and `fsync`, and
   hashes every remote file. A **separate** bounded SSH readback rehashes all
   15 files and stage receipts before the local stage receipt is written.
2. `launch_exp209_reconstructed_scorer_v1.py` requires the exact root-reviewed
   SHA256 of that newly created local stage receipt. It rechecks the local
   bundle and stage receipt and writes an exclusive, durable local launch
   intent before SSH. The remote program rehashes the staged code, stage
   receipt and reconstruction gate and requires absent scorer output/control.
   In the isolated
   `envs/current-organizer-py311-e13cf-v1/bin/python` environment, with CUDA
   hidden and GEFF path access denied, it runs only the current-organizer
   runtime import and synthetic directed-fork contract (240-second bound).
   It then creates a sibling control directory and durable remote launch
   intent, starts the CPU supervisor once, and waits up to 30 seconds for a
   worker-start receipt. Its SSH bound is 600 seconds.
3. The separately transmitted
   `supervise_exp209_reconstructed_scorer_v1.py` is outside the sealed scorer
   bundle. It records a worker intent, starts the exact reviewed scorer CLI
   once in a new process group, selects eight CPUs from the available affinity,
   applies a 32 GiB address-space cap, hides CUDA, and bounds the run to eight
   hours. On timeout it terminates then kills the process group with bounded
   grace periods. Its sibling completion receipt records exit code, timeout,
   original worker identity/absence, and hashes of any scorer gate, historical
   replay and result receipts. The launcher itself does not read a score.
4. The scorer's own previously reviewed graph verifier is the label boundary:
   it rehashes all 175 actual reconstructed graph bytes, IDs, controls,
   telemetry, source functions and image inputs and fsyncs its no-metric gate
   before any target GEFF open. Historical EXP209 row and aggregate replay
   must pass before current-organizer scoring. Original EXP209 graph hashes
   remain unavailable; any eventual result is a new-reconstruction reciprocal
   estimate with historically exposed labels, not byte-exact original OOF.

Stage creates `reports/exp209_reconstructed_scorer_v1_stage_intent_20260927.json`
and, only after remote readback PASS,
`reports/exp209_reconstructed_scorer_v1_stage_20260927.json`. Launch creates
the analogous `launch_intent` and `launch` JSON receipts in `reports/`. All
four paths were absent at local handoff.

## Reviewed future invocation (not executed)

From the project root, after explicit root code and hash review:

```powershell
python scripts/stage_exp209_reconstructed_scorer_v1.py `
  --expected-manifest-sha256 2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb `
  --expected-config-sha256 d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335 `
  --execute-reviewed-stage
```

After independently reviewing the actual stage receipt and taking its SHA256:

```powershell
python scripts/launch_exp209_reconstructed_scorer_v1.py `
  --expected-manifest-sha256 2484dfcacdfb47b2b33d6ab00ff0e9fa58b99943ad23421f5f9de253ff2255fb `
  --expected-config-sha256 d9a060b3d115db817f40fb9f81f8793c524fb112d9efb21b5767ad1ea3399335 `
  --expected-stage-receipt-sha256 <actual-reviewed-stage-receipt-sha256> `
  --execute-reviewed-launch
```

The stage receipt SHA is deliberately not known in advance. A timeout,
transport error, unexpected response or preflight failure leaves one-shot
intent evidence and requires inspection; neither helper retries.

## Local validation and exact new source hashes

| File | SHA256 |
|---|---|
| `scripts/stage_exp209_reconstructed_scorer_v1.py` | `b7c029b0601b112a7a1faa19c95dfb3ea013f19ad79b7ca38982d254fb5c8758` |
| `scripts/launch_exp209_reconstructed_scorer_v1.py` | `0afb83744bad9ea18d7157208c55a0466459c6cfc88c8edda4cc1394d42226ee` |
| `scripts/supervise_exp209_reconstructed_scorer_v1.py` | `e4831efe7d7d76c28f8e77ad3b6306226984bffae52e8de6fda45a9830f11204` |
| `tests/test_exp209_reconstructed_scorer_stage_launch_v1.py` | `1db6a52026a9ceeeec60e129a1c3c2aa3a90bb8ca1f24f3aa1d8558212a8bc7e` |

`python -m pytest tests/test_exp209_reconstructed_scorer_stage_launch_v1.py -q
--basetemp=work/t209_stage_launch_final` passed **14/14**. Tests cover exact
nested binary transfer including CRLF, extra/tampered/traversal rejection,
remote program syntax and pre-intent rejection, absent namespace, durable
local intents, one-shot and ambiguous SSH outcomes, remote readback mismatch,
stage receipt SHA binding, no-GEFF synthetic preflight source and resource
constants. SSH is mocked and generated remote programs use disposable local
paths; no target label, metric, remote stage/launch, GPU or POST was used.
All three new scripts and their test compiled with `py_compile`.
