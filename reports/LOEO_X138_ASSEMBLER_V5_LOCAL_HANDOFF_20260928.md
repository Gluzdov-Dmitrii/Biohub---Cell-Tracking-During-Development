# x138 reciprocal assembler v5 local handoff

Date: 2026-09-28. Status: local static package only. No real fold bundle,
production source emission, SSH, GPU, Kaggle mutation, outer label access,
outer prediction, or OOF score.

## Governing lineage

- Preregistration:
  `reports/LOEO_X138_ASSEMBLER_V5_DEEPCENTER_CHECKSET_PREREG_20260928.md`,
  SHA256 `17817cc2fcfa2746e1f5edde6f6fbab9456cb6defee442369304afd5be373a42`.
- Independently rejected v4 parent manifest:
  `work/loeo-x138-assembled-reciprocal-v4-20260928/sealed_package_manifest.json`,
  SHA256 `1a7680a4b3d20f2128f55f6c29ff304064826c8b9a1715fd074b77f42f73c27a`.
- New v5 package: `work/loeo-x138-assembled-reciprocal-v5-20260928`.
  Sealed manifest SHA256:
  `c81c283ffca812e8bdc90056cff1fc199ba303bfcd1637bc4fc459602c6fd137`.

## Exact correction

V4's DeepCenter gate expected 16 checks, while both approved DeepCenter
control v4 auditors emit 18. V5 adds exactly
`pre_reservation_frames_bound` and `queue_request_reply_bound` to
`DEEPCENTER_REQUIRED_CHECKS` in `assemble.py` and to the synthetic
`DEEPCENTER_CHECKS` fixture. No other assembler source text changed from
v4. The four corrected fold-specific auditor SHA pins, all other check and
graph policies, and all 52 plan/chunk JSON files remain unchanged.

## Validation

- `python -B -m unittest discover -s work/loeo-x138-assembled-reciprocal-v5-20260928 -p test_assemble.py -v`:
  **24 passed**. The new tests parse the actual DeepCenter fold0/fold1
  `audit.py` assignments as AST, match their SHA256 pins, and confirm
  their key sets exactly equal v5's 18-key set.
- For both folds, the same synthetic all-true 18-key DeepCenter receipt is
  rejected by v4 and accepted by v5. V5 rejects either new key missing,
  either false, and any additional key. The existing tests still cover exact
  27/28 full-training checks, both fold0 secondary release branches,
  50 chunks/199 unique IDs, 10 frozen inference function ASTs, and
  wrong-target image alias rejection.
- No-cache compilation of the three v5 Python source files passed.
- Exact source comparison: removing the one added two-key line from
  `assemble.py` reproduces the sealed v4 source byte for byte. All 52
  plan/chunk files match v4 byte for byte.
- Independent manifest readback: all 57 mapped files exist and match
  SHA256, with no unlisted package files. The v4 parent manifest and v5
  prereg hashes match their governing values.

Key v5 SHA256 values:

| File | SHA256 |
|---|---|
| `assemble.py` | `9d5aff8b742ba12c0d57beca0829fa88934881fb10eca62dd0a9cb0ffe938fa1` |
| `fixture_v5.py` | `96f8e92044851eec655aadf99daeae3126e3ee0fce9ac35be02a44635bb3286f` |
| `test_assemble.py` | `e6c727c08c3e1399c97bfe26f7d032c9bb67168c30420131f7b30a704870d58e` |
| `README.md` | `d02af8a2ac0eaf12fafd6687ec791a78e9f3d8c221dba09c3b9e5539987c5719` |

## Remaining gates

Independent read-only static review of v5, then real fold-matched source-only
primary, secondary, DeepCenter and V1284 assets with terminal independent
receipts before source emission. Runtime chunks and label-free output audit
remain future work. Any reciprocal OOF score requires separately locked
predictions and a separate outer-label analysis.
