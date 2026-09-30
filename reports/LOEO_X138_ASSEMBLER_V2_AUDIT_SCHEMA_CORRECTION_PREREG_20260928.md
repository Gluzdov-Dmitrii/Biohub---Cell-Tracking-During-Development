# x138 reciprocal assembler v2 — audited V1284 schema correction

Written 2026-09-28 Asia/Novosibirsk (2026-09-27 UTC), before successor code.
The locally sealed v1 assembler manifest SHA256
`1c8b16b5dcc85eb9b0524e56f8062072eb46a2261b2acf89638c3c6ddd110336`
is preserved; no real source was emitted. Its 50 chunks/199 outer IDs, frozen
x138 graph policy and x162 final writer clamp remain unchanged.

An independent read-only review found a deterministic **integration** block:
v1 `assemble.py:278-302` expects the older capture runtime outcome and
`denied_bytes`, plus a hypothetical flat head-audit PASS schema. The actually
sealed, independently source-reviewed control v3 emits
`runtime_audit.outcome=PASS_CAPTURE_V3_RUNTIME_RELEASE_CONTROL_V2` (a protocol
identifier) and `runtime_audit.denied_access={exists,regular,bytes,sha256}`;
the independently reviewed head auditor v2 emits `status=PASS_AUDITED_HEAD`,
`input_hashes`, `ids` and `metrics`. Even real passing receipts would be
rejected by v1. This was found before any assembled inference or outer label
read.

Create a distinct assembler v2 package. Pin the exact reviewed source hashes:
capture v3 verifier `verify_capture.py` SHA256
`de66ce299728dbe9517d5da48c54aa99a03d7968fc7aede0b06e8b83b39333fd`,
control v3 independent auditor `audit_capture_runtime.py` SHA256
`fc8fbfa847afbb409969c75bc619f1de3600858596cf376dbf33df15c2eb133a`,
head independent auditor v2 `audit_head.py` SHA256
`a77a286a95867eaf817a02c2d1b9e62e498a12ae0e7a544bb0fe21c5915808bd`.
Also pin their package manifests: capture v3
`bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`,
control v3 `e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`,
head audit v2 `757f1942a4b5580d350c31aab23784c026c4eac4f024ec98b79c2fe61d4b1033`.

For V1284 role, require the actual capture v3 plan/verified shard receipt,
independent control-v3 completion and head-audit-v2 receipt with their byte
SHAs and same fold/source/parent checkpoint identities. Verify the
version-specific runtime outcome, existing regular zero-byte denial log/hash,
matching raw RELEASED reply and live queue row, released GPU/PID evidence,
capture shard/source coverage and exact completion SHA. Verify head v2
`status=PASS_AUDITED_HEAD`, its `input_hashes` for checkpoint, head report,
capture seal, split, capture verification/completion and auditor code, plus
`ids.fit/inner`, selected epoch and independently recomputed quality gate.
Reject self-declared PASS attestations and any old v1/v2 capture or v1 head
receipt schema. The assembler must read the audited receipt structures, not
just hash arbitrary JSON. Other three role gates remain unchanged.

Keep source emission blocked without real audited primary, secondary,
V1284 head and DeepCenter artifacts for **both** folds, exact source-only
lineage and image-only outer views. No threshold, model, graph, chunk,
coordinate or scoring-policy change is authorized. Synthetic tests must
cover the new positive nested receipt schema, old-schema rejection,
wrong parent/fold/hash/release/head gate, 50-chunk/199-ID coverage and
output diagnostics, with exact manifest/AST/no-cache readback. A separate
independent review is required before any real source emission. This task is
local only: no SSH, stage, GPU, real GEFF, outer label, Kaggle or OOF claim.
