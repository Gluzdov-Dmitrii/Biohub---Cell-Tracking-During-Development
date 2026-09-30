# x138 reciprocal assembler v2 — local schema-correction handoff

Date: 2026-09-28 Asia/Novosibirsk. This is a local-only successor to sealed
assembler v1; the v1 manifest remains SHA256
`1c8b16b5dcc85eb9b0524e56f8062072eb46a2261b2acf89638c3c6ddd110336`.
The governing correction preregistration is
`reports/LOEO_X138_ASSEMBLER_V2_AUDIT_SCHEMA_CORRECTION_PREREG_20260928.md`
SHA256 `227aae5f0df426fb1360ca5c3f4a0e69806bee3b5b2234b047a2bb976e4b6e0f`.

## Sealed package

`work/loeo-x138-assembled-reciprocal-v2-20260928/sealed_package_manifest.json`
SHA256 **`876894ec27d5e4b9c43827787d566554a34f10882fda57281b2ba8d026c5d9a3`**;
57 exact file hashes including the prereg, 56 package files, with no cache.
`assemble.py` SHA256 `c19e5753dc8d4a699652b17ac402de91236cb8470e622ba08eeccfc5909e64ad`;
`fixture_v2.py` SHA256 `60453592bb94e62bf48844c6364a4cc8c38e53a61d6e7f620e8d9513f465ab04`;
`test_assemble.py` SHA256 `1763b4e9863c372a55ccff87a0f4f778187cc615570734d0bec978308c6244dd`.

The V1284 role gate now consumes the actual capture-v3 plan, schema-1 head
capture seal, source-only `capture_verified.json`, independently audited
control-v3 `completion.json`, and head-auditor-v2 receipt. It checks exact
bundle copies and hashes of the three sealed package manifests, auditor
sources, runtime files, release observation, raw RELEASED reply, live queue
row, regular zero-byte denial log, source frame/shard inventory, parent
checkpoint/config/audit SHAs, and the selected source-inner quality gate.
Head-v2 `input_hashes` are bound by SHA to bundle copies because their path
strings are audit-time absolute paths. The real head-v2 receipt has no
auditor-code self-hash; `audit_head.py` is separately pinned and hashed.

The exact reviewed source pins are capture verifier
`de66ce299728dbe9517d5da48c54aa99a03d7968fc7aede0b06e8b83b39333fd`,
control auditor
`fc8fbfa847afbb409969c75bc619f1de3600858596cf376dbf33df15c2eb133a`,
head auditor
`a77a286a95867eaf817a02c2d1b9e62e498a12ae0e7a544bb0fe21c5915808bd`;
their manifest pins are `bc2847fe7e142aa9a20b8abea6185d87fdae7d9fb184cb0eb784de0d90b60486`,
`e6c996f95f2c6eb191c37b0278aa343fa27daa48f67f1778bce1d507849e7ad8`,
and `757f1942a4b5580d350c31aab23784c026c4eac4f024ec98b79c2fe61d4b1033`.
The other three role gates were not changed.

## Local validation

`python -B work/loeo-x138-assembled-reciprocal-v2-20260928/test_assemble.py -q`
passed **15 tests**. They cover nested positive receipts in both folds,
legacy runtime/head/plan schema rejection, wrong parent/fold/release
reply/live row/GPU probe/denial/completion/head input/quality/GEFF inventory,
source pin tampering, production CLI refusal of synthetic assets, all 50
chunks and 199 IDs, runtime preflight, fallback/deadline and output checks.
The synthetic fixture overrides pins only in its imported Python module;
the production CLI uses the fixed reviewed pins and rejects that fixture.

AST comparison found 12 inference/chunk/source/output functions identical
to sealed v1, including `assemble_text`, `runtime_preflight`, `check_output`,
`check_reciprocal`, and `check_bundle`; all 50 chunk manifests and both fold
plans are byte identical. Manifest readback rehashed every listed file,
confirmed no extra package file or `__pycache__`, compiled the three Python
files in memory, and rechecked the unchanged v1 manifest SHA.

## Blocking dependencies

No real fold bundle, assembled source, outer inference, or honest 199-embryo
OOF score exists. Both folds still require all four real same-fold source-trained
checkpoints, exact parent configs and independent quality/release audit
receipts, including actual capture-v3/control-v3/head-v2 artifacts. The
preregistered independent review of assembler v2 must pass before real source
emission. Then each of the 50 image-only outer chunks needs a fresh process,
distinct empty working directory, exact exit receipt, zero fallback/deadline
degradation, complete frame diagnostics, and a measured full-candidate
runtime with margin before any separate label scoring. The head-v2 receipt
does not cryptographically self-attest which program generated it; the gate
binds its content, audited input hashes, and a separately sealed auditor
source/manifest as specified by the preregistration.

No SSH, staging, GPU, real GEFF or target-label read, Kaggle action, source
emission, or `EXPERIMENTS.md` edit occurred in this package task.
