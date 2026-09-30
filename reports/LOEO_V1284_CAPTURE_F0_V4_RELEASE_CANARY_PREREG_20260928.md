# V1284 fold0 capture v4 — released GPU row and CPU canary addendum

Written 2026-09-28 before the v4 queue-gate and canary edits. The first v4
preregistration and predictor-hash correction remain unchanged. The failed
v3 attempt's saved `work/loeo-v1284-f0-capture-prep-20260928/control-prepare-v1/watch/release_control.json`
and `watch/complete.json` contain an actual `RELEASED` queue row with
`gpus=[]`. The inherited control-v3 final auditor and source-v3 verifier
instead demand `gpus=[allocated_gpu]`; their synthetic positive fixture used
the invented populated shape. A clean v4 run would therefore fail after
release even if feature capture succeeded.

Change only the **live terminal** queue-row requirement to `gpus=[]` in the
control auditor and source verifier, while preserving exact lease ID, run
path, state, earlier reserved GPU identity, release-time process/group/GPU
empty checks, and raw release reply lineage. Add positive tests for the real
empty shape and negative tests for retained, wrong, or extra allocated GPUs,
wrong run, and non-RELEASED state. Do not infer the allocated GPU from an empty
terminal row.

Add a sealed, CPU-only canary in the v4 source package. It must execute the
exact stored cell4 against a temporary copy of the sealed support predictor,
mock CUDA availability/device identity and both model-launch subprocess APIs,
and verify both generated Python file byte lengths, LF-only newlines and exact
v4 plan hashes. It must not read target GEFF, request a queue lease, launch a
real model, create a graph, or report a score. The future operator should run
this canary after exact remote stage readback and before any GPU request, with
the same Python interpreter as capture. The canary is another local/static
gate; it does not itself authorize stage or launch. Seal it in the source
manifest, then update the control manifest's source pin. Independent second
review remains required for both v4 packages before remote stage.
