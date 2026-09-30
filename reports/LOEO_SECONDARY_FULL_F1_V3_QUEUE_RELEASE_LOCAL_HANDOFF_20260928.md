# LOEO secondary full fold1 v3 — local queue and release handoff

Prepared 2026-09-28, local only, against preregistration
`reports/LOEO_SECONDARY_FULL_F1_V3_QUEUE_RELEASE_PREREG_20260928.md`
SHA256 `1236083be3656d37a26d1382e5f2710df2c732218aea5a0726b3b372683ed0e1`.
Rejected v1 and v2 remain untouched and unlaunched. V2 plan SHA256
`4b2c375f55e0260e55dc900c056c78a39dd4ad57c4e875d12affac0dd887c570`,
manifest SHA256 `13b244ae4728de83c04c8d8eec13d82f32e2bf433c3e375a64d18eb6de81f871`,
and auditor SHA256 `a88f9b26ebca546c367f2784865d415722a84583b36a983ccc0914ee09cd4816`
were verified unchanged. The historical v1 plan SHA256 is
`bd99d3ebe23a7038e6c56a2f6ea39b668966b2e5cfedd47bd1b2525ff378ba06`.

## New identity and unchanged science

- Package: `work/loeo-secondary-full-f1-v3-20260928/`.
- Attempt `01ec33225052`; lease `loeo-secondary-full-f1-v3-01ec33225052`.
- Plan `full_plan.json` SHA256 `9c1061c4d9e524aa572181834711c5414c07d7ff16f6aecd7af99ccfd8dc28d0`.
- Exact 21-file bundle manifest SHA256
  `07a957514e58047f81ec623a42437b39e25b899707238873b03a5c2eac063113`.
- Contract SHA256 `458c876d7382f765ba2fb1bf5767dc377d6a183b72a356061dd6338caad78c5e`;
  supervisor `451209c3b7e71bde342b92bfdf8936a3c2dc20e1e3ee13831a2bf429ada74fea`;
  controller `5103c1707343f63b2dd3d39b2230cfe8f985006d234e97b8791761d95a771943`;
  independent auditor `52285517ac376e0183d13d61190de5d12c9d606a19664b93749741e421c2fcb9`.
- Builder SHA256 `b85f5230c21cd6c165c9544b982d28b87c1f991942194768c45c2996ecaa83fb`;
  local tests `db6bce8bb942ecd7ee6964c7b6eef7ccb91796d5fc4b669b43d7ea5fb2181eca`.
- Proposed remote code/run stems are `loeo_secondary_full_f1_v3_01ec33225052`
  under the pinned Biohub project `code/` and `runs/` roots. They do not exist remotely.

The pinned scientific split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`
still fits 102 and selects on 26 source `6bba` movies, excludes all 71 outer
`44b6` movies, and consumes exactly 9,949/2,443 windows. It trains 50 epochs
with seed `20260929` before model import, no warm start, unchanged public
trainer/model/augmentation, latest-tie source-inner selection, and the
0.80/0.80/0.97 quality gates. Runner SHA256
`d59da08bceade68c7b8125c051be42faffe651e6add4f6cb6b777268e30f891c`
and wrapper SHA256 `d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`
are byte-identical to v2. Source-only window metadata SHA256 is
`584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`.

## Corrected controls

The final auditor checks a `RELEASED` queue row using stable lease ID,
project, run, owner, token, alias, pool, count and resource fields. It accepts
the real queue behavior `gpus=[]` after release; allocation remains bound to
the pinned `RESERVED` receipt, exact runtime config and saved empty-GPU
release observation. An unrelated nonempty allocation fails. The same 28
named final-audit checks remain in the same order, including
`remote_source_metadata_matches`.

Before a queue request, the controller writes an exclusive, fsynced intent
with exact plan, lease, run and resource identity. A lost or malformed request
response triggers live queue reconciliation without issuing a second request.
Only one matching, current, reserved lease can reach the unlaunched release
gate. A read-only remote probe must prove no run directory, no run-owned
process, no unreadable same-owner process, and zero memory, utilization and
compute PIDs on the assigned GPU. The queue row is reread immediately before
release. A separate exclusive, fsynced release intent prevents a second
release after a lost response. Raw release replies are saved; only this lease
ID with `state=RELEASED` can be reported as released. All uncertain states
produce explicit unresolved local receipts.

## Local verification and remaining gates

`python -B work/loeo-secondary-full-f1-v3-20260928/test_full_local.py`
passed **22/22** tests. They include the actual fold0 released-row shape
(`gpus=[]`), mismatched stable queue identity, accepted-before-timeout and
malformed reservation responses, wrong/active GPU or run, unknown release
response with no retry, the v2 raw release and PID/start adversarial cases,
nonzero CLI exit for unresolved state, and source/window/seed checks.
`validate-inputs` found 128 source IDs, 71
sealed outer IDs and 13 support files. Final `read_plan()` and
`verify_bundle()` performed exact 21-file/hash readback. Python compilation
passed for 27 local/bundled files without bytecode cache. The v2 auditor's
28 check keys matched v3 exactly.
One repeat test exposed a Windows clock-resolution collision between two
immediate local reconcile receipt names; a random suffix fixed it before
the final passing run. No queue call or remote action occurred.

An independent read-only second review is required before any remote stage.
The active primary fold0 lease remains untouched. No SSH, queue request, GPU,
outer image/GEFF read, Kaggle POST, source emission or OOF claim occurred.
The x138 assembler still pins a rejected predecessor and needs a distinct
version after this auditor passes review.
