# x138 reciprocal assembler v4 local handoff

Date: 2026-09-28. Status: local static package only. No real fold bundle,
production source emission, SSH, GPU, Kaggle mutation, outer label access,
outer prediction, or OOF score.

## Governing lineage

- Preregistration: `reports/LOEO_X138_ASSEMBLER_V4_AUDITOR_PIN_PREREG_20260928.md`,
  SHA256 `4e8c2385a3835fbe428574ea355c6c296a8881a061b8e865f50ebebd770ab145`.
- Independently reviewed v3 parent manifest:
  `work/loeo-x138-assembled-reciprocal-v3-20260928/sealed_package_manifest.json`,
  SHA256 `6554e44c5a8320b8bc51eb832fb8649197bc75f29f6507a0d30ace7b6c96c77f`.
- New v4 package: `work/loeo-x138-assembled-reciprocal-v4-20260928`.
  Its sealed manifest SHA256 is
  `1a7680a4b3d20f2128f55f6c29ff304064826c8b9a1715fd074b77f42f73c27a`.

## Exact correction

Only four auditor SHA256 constants changed in `assemble.py`: primary fold1
`1b40e92766d34c3854817590cf43c6fb85a7c1fdf47a2c7915056d44603dd723`,
secondary fold1
`57f4ccec30cac54b13d34b45a7f804eb8b0dd17106728452805324f01384ecaf`,
DeepCenter fold0
`bf453de8242c1c9a7cdb6813e9ae18c98b37e20c0ea4642a9a41c44306835227`,
and DeepCenter fold1
`d08245efa4293a591db8b2231279af6d32de6fb524ed031c95946f696f90f249`.
Direct local SHA256 readback matched, respectively, the primary fold1 v6 and
secondary fold1 v5 `audit_completed_full.py` files and DeepCenter fold0/fold1
control v4 `audit.py` files. The primary and secondary fold0 pins remain unchanged.

The 52 plan/chunk JSON files match v3 byte for byte. A full text comparison of
`assemble.py` against v3 after exactly these four substitutions passed.
The fixture and tests were copied to v4; the fixture name and import were
updated, and existing v2-policy probes were given their v2 auditor pins so
that they isolate their intended check-set behavior.

## Validation

- `python -B -m unittest discover -s work/loeo-x138-assembled-reciprocal-v4-20260928 -p test_assemble.py -v`:
  **22 passed**. The new adversarial test confirms that v3 accepts each of
  the four stale auditor pins and v4 rejects each.
- No-cache compilation of `assemble.py`, `fixture_v4.py`, and
  `test_assemble.py`: passed.
- Exact source-audit check sets: primary/secondary fold0 27, fold1 28;
  DeepCenter 16. Both secondary fold0 release branches, 50 reciprocal chunks,
  199 unique IDs, 10 frozen function ASTs, and wrong-target image alias
  rejection passed in the test suite.
- Independent manifest readback: all 57 mapped files exist and match SHA256,
  with no unlisted package files. V3 manifest and v4 prereg hashes match their
  governing values.

Key v4 SHA256 values:

| File | SHA256 |
|---|---|
| `assemble.py` | `2270f33fd8abce40f9d7d5c80accdfb135cb2fb7411a93dcdcbd22205aae6c6e` |
| `fixture_v4.py` | `1a2fef9e318528179621e0465ae5f000cc69d740074d0aea61bcd8ecde77288a` |
| `test_assemble.py` | `f1800aabdb593e5485f7ef8720ab9ebb2621e7aa632ecff891935db8cc6fca0d` |
| `README.md` | `1199e7140ba94f71e5baf7f6e449b97924f8ef9a387030f6c4ca5c40ae64ed15` |

## Remaining gates

Independent read-only static review of this v4 package, then real fold-matched
source-only primary, secondary, DeepCenter, and V1284 assets with terminal
independent receipts before any source emission. Runtime chunk execution and
label-free output audit remain future work. Any eventual reciprocal OOF score
requires separately locked predictions and a separate outer-label analysis.
