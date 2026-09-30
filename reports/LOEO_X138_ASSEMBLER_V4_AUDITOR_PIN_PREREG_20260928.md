# x138 reciprocal assembler v4 auditor-pin correction preregistration

Date: 2026-09-28 04:05 UTC. Scope: local package only; no emitted production
source, SSH, GPU, label access, Kaggle POST, or outer OOF scoring.

Parent is independently reviewed x138 assembler v3, sealed manifest SHA256
`6554e44c5a8320b8bc51eb832fb8649197bc75f29f6507a0d30ace7b6c96c77f`.
V3 pins rejected, unrun fold1 and DeepCenter v1 auditor files. Preserve v3.

Hypothesis: replacing only four stale auditor SHA256 pins with the independently
reviewed local static successors will allow the assembler to validate their
eventual real audited receipts without weakening any check. Pin changes:

| Role | V3 SHA256 | V4 SHA256 |
|---|---|---|
| primary fold1 | `32479bb6fababab765260c86438f8c6942a0b915b4b4a0ffcbda0a4d3ae19534` | `1b40e92766d34c3854817590cf43c6fb85a7c1fdf47a2c7915056d44603dd723` |
| secondary fold1 | `df1eb40bfcc0237e7ad57c421f599d59437dc9dec08ea30c8fe5ee409f5000c8` | `57f4ccec30cac54b13d34b45a7f804eb8b0dd17106728452805324f01384ecaf` |
| DeepCenter fold0 | `028fa9dea1080b8f1f9f4e9097ae337bac23857733093a95bac37220e36093ad` | `bf453de8242c1c9a7cdb6813e9ae18c98b37e20c0ea4642a9a41c44306835227` |
| DeepCenter fold1 | `5ea6d61d3ac6535126f0d4cebdd4bf1a9d3635126892adb67b51492266b34db8` | `d08245efa4293a591db8b2231279af6d32de6fb524ed031c95946f696f90f249` |

The new SHA256 values were read from the exact local auditor files. The primary
fold1 v6, secondary fold1 v5 and DeepCenter v4 fold0/fold1 packages each
passed independent local static review. Fold0 primary and secondary pins are
already current and must remain unchanged.

Acceptance: create a distinct immutable v4 package, retain every other v3
source/check/science policy and all 52 plan/chunk files byte-identical; update
fixtures only where the four SHA pins require it. Rehash the full package,
run local tests and negative stale-pin tests, verify exact 27/28 full-training
and 16 DeepCenter audit check sets, 50 chunks/199 IDs and strict image alias
identity. Obtain independent read-only static review. This is preparation for
future real assets, not evidence of an outer score. No source emission until
all fold-matched checkpoints and independent receipts exist.
