# V1284 independent source-inner head audit v2 — local correction handoff

Implemented under `LOEO_V1284_HEAD_AUDIT_V2_CORRECTION_PREREG_20260928.md`,
SHA256 `b46cf55aa7900115d4f49d504436f5c7dc5ea207716a7c8304d4f514f5fe2558`.
The v1 auditor and manifest remain preserved, unrun on a real head and
rejected as a production gate. The new v2 package is separate.

## Sealed local artifacts

- Auditor `work/loeo-v1284-head-audit-v2-20260928/audit_head.py` SHA256
  `a77a286a95867eaf817a02c2d1b9e62e498a12ae0e7a544bb0fe21c5915808bd`.
- Tests `work/loeo-v1284-head-audit-v2-20260928/test_audit_head.py` SHA256
  `cafc54d955eae0f4a38038ede2113d3bc513070d10604f2e430c8d2b0a1664e7`.
- Package manifest `work/loeo-v1284-head-audit-v2-20260928/package_manifest.json`
  SHA256 `757f1942a4b5580d350c31aab23784c026c4eac4f024ec98b79c2fe61d4b1033`.
- Test transcript `work/loeo-v1284-head-audit-v2-20260928/test_evidence.txt`
  SHA256 `5b1275e1f6d42cd3bd7808366ea54d715228e2ef64b92d5de8a46b07c964e0a3`.

The auditor pins and rehashes the complete capture v3 manifest
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`
and control v3 manifest
`e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`.
It requires capture schema 3/purpose, correction preregistration and both
rejected capture-manifest fields, exact fold/outer IDs, approved source-image
and component parents, and same-fold primary/secondary quality audit and
model hashes. The plan, runtime code, parent artifacts, frame counts, every
shard and the trainer capture seal are rehashed before GEFF access.

The independent completion must be `completion.json` with protocol outcome
`PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2`, exact control/capture/plan
hashes, launch intent and executed wrapper hashes, five remote runtime file
hashes, bound lease/run/GPU/PID, ordered fresh release-time dead-group and
empty-GPU observation, matching raw RELEASED reply and live queue row. The
remote `denied_access.jsonl` must exist as a regular zero-byte file with
SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
A supplied local copy is checked too. `capture_verified.json` must bind the
same completion SHA, control manifest and zero-denial SHA. Watcher-only
completions cannot reach the label loader.

After these gates, v2 retains the v1 numeric protocol: independent 5 µm
greedy one-to-one source matches, fit-only normalization, exact finite
224→32→3 SiLU checkpoint, 80-epoch earliest argmin, bounded displacement,
pooled and per-movie mean/p95 replay at `1e-5`/`1e-4` µm tolerances, and the
fixed 0.05 µm/3%/60% gate. A passing gate emits `PASS_AUDITED_HEAD`; a
correctly reported failed gate emits `FAIL_QUALITY_GATE`. Contradictory
present artifacts emit `FAIL_AUDIT`; missing/unreadable inputs are
`INCONCLUSIVE` and write no receipt. Terminal receipts use exclusive creation.

## Validation and limits

`python -B -m unittest discover -s work/loeo-v1284-head-audit-v2-20260928 -p test_audit_head.py -v`
finished exit 0: **33 synthetic tests passed**. The fixture uses a v3-shaped
plan and independent-auditor-shaped completion. It exercises both v1 P1
failures, absent/nonregular/nonempty denial logs, bad raw reply/live row,
wrong control manifest and disconnected shard verification, stale probe,
parent/shard tampering, and the preserved numeric, epoch and gate cases.
Every prelabel rejection asserts zero GEFF-loader calls. Both Python files
AST-parse, exact package readback passed, and no generated cache is present.
The synthetic label loader returns in-memory coordinates.

No real GEFF, SSH, stage, queue, GPU, training, Kaggle or outer scoring was
performed, and `EXPERIMENTS.md`, trainer and capture/control packages were not
edited. The control v3 package's independent second review passed locally;
the head auditor v2 still needs its own separate review before real use.
A real fold and Linux source view remain unverified. This audit does not
replay training byte for byte or prove an outer OOF improvement.
