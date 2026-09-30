# V1284 independent source-inner head audit v1 — local handoff

Prepared locally under `LOEO_V1284_HEAD_AUDIT_V1_PREREG_20260928.md`
(SHA256 `1915d5931aa097b1814c0c065537e126a1b5776e4123e96217b4aef3bc4adec8`).
No real fold head, GEFF label, capture shard, remote host, queue, GPU, Kaggle
artifact, or submission was accessed. The trainer and sealed capture package
were not modified. `EXPERIMENTS.md` was not edited by this task.

## Local artifacts

- Auditor: `work/loeo-v1284-head-audit-v1-20260928/audit_head.py`, SHA256
  `d8c048cd60392b6fb3bc34a13ee4957cdb45f9af52d96a868695dc9c07935b30`.
- Synthetic tests: `work/loeo-v1284-head-audit-v1-20260928/test_audit_head.py`,
  SHA256 `82d5f2d8fb4cb49ce87ca3569d796a9e4c1198b7d81482d70411023e110f3b37`.
- Package manifest: `work/loeo-v1284-head-audit-v1-20260928/package_manifest.json`,
  SHA256 `2b27bb3a3010dfdaf4cf6f37415c077b5d389ec9d0d83da6bfb70754cec537a9`.
- Test transcript: `work/loeo-v1284-head-audit-v1-20260928/test_evidence.txt`,
  SHA256 `09ed22563218f6a80c0f5e79fff5c7d833f1e94da37d87cee427bf85130cc896`.

The auditor pins trainer SHA256 `acc24bf0ac2e8dba019d907acf3c92b0652124243b645f8b79c6606a0f198d02`
and split SHA256 `2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`.
It independently rehashes code, plan, completion, capture verification and
seal receipts, runtime identities, frame counts, every shard, both parent
checkpoint/config/audit receipts, source GEFF trees, head report and checkpoint.
It checks the primary/secondary audits' same-fold source IDs and quality
receipts, captured model loads and released process evidence. It rejects
missing/extra/outer source IDs, bad label parents, unsafe GEFF tree links and
changed capture bytes before calling the label loader.

For a complete fold it reconstructs 5 µm greedy one-to-one matches from the
captured `(t,z,y,x)` coordinates and native GEFF nodes divided by `(1,4,4)`;
both are compared in 1.625 µm grid spacing. It verifies fit/inner counts,
fit-only normalization, exact 224→32→3 finite SiLU checkpoint schema and
lineage, all 80 finite history values and earliest selected argmin. CPU head
inference recomputes bounded offsets, pooled and per-movie before/after mean
and p95, applying the preregistered `1e-5`/`1e-4` µm tolerances. It independently
checks the absolute/relative/movie-fraction promotion gate. A gate failure
is recorded as a rejected diagnostic; only a complete pass emits
`PASS_AUDITED_HEAD`. Terminal receipts are exclusive; missing/unreadable
inputs return `INCONCLUSIVE` without a receipt.

## Validation

`python -B -m unittest discover -s work/loeo-v1284-head-audit-v1-20260928 -p test_audit_head.py -v`
finished exit 0: **17 synthetic tests passed**. They cover success,
source-only loader calls, greedy uniqueness/radius, pinned-code and parent
hash failure, fold mismatch, shard tampering, missing/extra/outer GEFF IDs,
unapproved label parent, malformed/NaN checkpoint, wrong selected epoch,
metric and gate mismatch, a legitimate rejected gate, inconclusive missing
input, and immutable receipt refusal. Both Python files parsed as AST.
The synthetic loader returns in-memory coordinates and never opens any real
GEFF file.

## Gate for future use

The separate capture verifier must have completed successfully before
head training. A future real invocation must supply its immutable plan,
release completion, `capture_verified.json`, trainer capture seal, source
shards and the matching report/checkpoint. The operational CLI fixes the
source-label parents to the observed official training directories; synthetic
parent overrides exist only in the Python API for tests. This preparation
does not replay the 80-epoch training run or validate a real Linux source
view, full x138 outer graph, or outer OOF score. An assembled-x138 builder
must separately require a `PASS_AUDITED_HEAD` receipt and exact head hash.
