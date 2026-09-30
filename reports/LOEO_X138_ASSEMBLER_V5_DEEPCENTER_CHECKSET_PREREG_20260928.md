# x138 reciprocal assembler v5 DeepCenter exact-check correction preregistration

Date: 2026-09-28 04:30 UTC. Local-only correction before any successor code.
Parent x138 v4 is sealed manifest SHA256
`1a7680a4b3d20f2128f55f6c29ff304064826c8b9a1715fd074b77f42f73c27a`
and assembler SHA256
`2270f33fd8abce40f9d7d5c80accdfb135cb2fb7411a93dcdcbd22205aae6c6e`.
Preserve v4 unchanged and reject it for real source emission.

Independent read-only review found a deterministic gate mismatch: both
approved DeepCenter v4 auditors emit **18** named checks, including
`pre_reservation_frames_bound` and `queue_request_reply_bound`; v4 assembler's
`DEEPCENTER_REQUIRED_CHECKS` and fixture list only **16**. Its exact-set gate
rejects a synthetic all-true 18-key receipt from either fold. The 22 v4 tests
passed because the fixture still modeled the predecessor's 16-key schema.
Primary and secondary full fold1 auditor check sets match v4's 28-key gate.

Hypothesis: adding the two missing DeepCenter lineage keys to the exact set and
to realistic fixtures will accept valid approved v4 receipts while still
rejecting missing, false or additional keys. Change no model, graph, threshold,
image, role, source/outer split, release, or other audit policy. Retain the four
corrected auditor SHA pins from v4. Keep 52 plan/chunk files byte-identical.

Acceptance: create distinct immutable v5 package, rehash every manifest
entry, run local tests, and run an adversarial pair for both folds: the same
synthetic receipt with all 18 true keys is rejected by v4 and accepted by v5;
removing/false-setting either new key or adding an unapproved key is rejected
by v5. Compare actual auditor `checks` assignments in both DeepCenter v4
files to the v5 expected set. Preserve strict 27/28 training check sets,
same-fold asset/release gates, 50 chunks/199 IDs and image alias identity.
Require independent read-only second review before source emission. No SSH,
GPU, label read, graph score, Kaggle POST or OOF claim in this correction.
