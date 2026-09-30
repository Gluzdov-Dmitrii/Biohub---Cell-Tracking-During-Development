# LOEO secondary full fold1 v2 — local correction handoff

Prepared 2026-09-28, local only. The correction preregistration
`reports/LOEO_SECONDARY_FULL_F1_V2_RELEASE_CORRECTION_PREREG_20260928.md`
SHA256 `8feaf30b43355ed473e0f372db746b4989dacd2f55c92ec24dfe9d442e2d1240`
preceded this package. Rejected fold1 v1 remains untouched and unlaunched:
plan SHA256 `bd99d3ebe23a7038e6c56a2f6ea39b668966b2e5cfedd47bd1b2525ff378ba06`,
21-file manifest SHA256 `3349a7619ab47fcfa0c2a12a50c3ee276b56b6068873d979488f28b6e4298f6a`.

## New sealed identity

- Package: `work/loeo-secondary-full-f1-v2-20260928/`.
- Attempt `380c7f31c25a`; lease `loeo-secondary-full-f1-v2-380c7f31c25a`.
- Plan `full_plan.json` SHA256 `4b2c375f55e0260e55dc900c056c78a39dd4ad57c4e875d12affac0dd887c570`.
- Exact 21-file bundle `full_bundle/bundle_manifest.json` SHA256 `13b244ae4728de83c04c8d8eec13d82f32e2bf433c3e375a64d18eb6de81f871`.
- Contract SHA256 `d37a1d40ff2a348e42634a3bf2fb4fa9c297f3f2834462e8fee3409cf57f6b16`;
  supervisor `451209c3b7e71bde342b92bfdf8936a3c2dc20e1e3ee13831a2bf429ada74fea`;
  controller `7e98fbb85b7871f78af38bcacb6381db5198047666ef4d79a30b38587c6765ad`;
  independent completion auditor `a88f9b26ebca546c367f2784865d415722a84583b36a983ccc0914ee09cd4816`.
- Builder SHA256 `c0b1c3518a92cab80bb461dc91993414b160b5f2e698d44d2476af45f380cdea`;
  source metadata reader `2c28563e1587bec3850a178c4b592edd6233f97730de1cbfad40dc0b09e6d3d1`;
  local test source `118246c98e8dbf33d771966d46a1180cc8e7bfc1b434a946ebf0281658751209`.
- Remote code/run stems, if later authorized, are
  `loeo_secondary_full_f1_v2_380c7f31c25a` under the pinned Biohub project
  `code/` and `runs/` roots. Neither path has been created.

The fold1 scientific experiment is unchanged: pinned split SHA256
`2a4b013db53599b33a64dc9b4a03b851c7bafbcc40ee039060845feaf945adb1`,
102 fit and 26 inner source `6bba` movies, all 71 outer `44b6` movies excluded,
9,949/2,443 exact windows, 50 epochs, seed `20260929` before model import,
no warm start, latest-tie source-inner selection and the original
0.80/0.80/0.97 quality thresholds. Trainer runner SHA256
`d59da08bceade68c7b8125c051be42faffe651e6add4f6cb6b777268e30f891c`
and wrapper SHA256 `d1d8b4a19786cbf2950783f4d9eee12ec397cb77a09be3809cb1d091b0a27648`
are byte-identical to v1. Source-only window metadata remains SHA256
`584945c1e66b9fd5f7debcae8f5056a52bb5629599ad42b655a64d1b3a2ce1f7`.

## Release correction and validation

The controller now rejects a queue reservation unless the exact lease ID,
project, run path, token, reserved/current state, A100 alias, one GPU and
planned resources all match before launch. Supervisor completion requires a
saved raw release reply with this lease ID and `state=RELEASED`. Manual and
verified-unlaunched reconciliation save the raw reply and report
`RELEASE_REPLY_UNVERIFIED` for an empty, wrong-ID or wrong-state response.
Manual release receipts bind the empty-GPU probe time to the release request;
a stale probe aborts before the queue call.
The auditor does not let a present invalid supervisor completion fall back to
a manual receipt. It checks matching launch and exit PID/start identity,
process-group death, release-time empty GPU, clean exit, exact live queue
release identity and source-only evidence. Automatic completion accepts an
absent optional `full_reconcile_latest.json`; a present one is hashed.

The auditor retains the same **28 exact named checks in the same order** as
v1, including `remote_source_metadata_matches`. `python -B
work/loeo-secondary-full-f1-v2-20260928/test_full_local.py` passed **16/16**
synthetic tests. The adversarial fixtures cover empty/wrong-ID/wrong-state
supervisor and manual replies, invalid-supervisor-plus-valid-manual conflict,
wrong reservation lease/project/run/GPU and state, launch/exit PID/start
mismatch, an absent optional reconciliation, valid supervisor/manual replies,
source split/window and seed. `validate-inputs` found 128 source IDs, 71
sealed outer IDs and 13 pinned support files. Final local `read_plan()` and
`verify_bundle()` performed exact 21-file/hash readback; AST parsing passed
for 27 local/bundled Python files without bytecode cache.

## Remaining gates

An independent read-only second review must pass before any remote stage.
The active primary fold0 lease remains untouched. Later stage, queue request,
GPU launch, target image/GEFF read, x138 source emission and Kaggle POST are
outside this local handoff. The x138 reciprocal assembler still pins the
rejected v1 auditor and must be corrected in a distinct version before it can
consume v2 evidence. No outer OOF or 0.9+ result is claimed.
